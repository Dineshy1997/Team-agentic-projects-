import streamlit as st
import pytesseract
from PIL import Image
from fpdf import FPDF
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import cv2
import numpy as np
import os

#  Set Streamlit Page Configuration
st.set_page_config(page_title="Medical Report Extractor", layout="wide")


#  Hugging Face Token Input
#hf_token = st.text_input("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", type="password")
hf_token = os.getenv("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")

#  Set up Tesseract OCR path (Ensure this path is correct)
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    st.error("Tesseract not found! Please install from https://github.com/UB-Mannheim/tesseract")

#  Load AI Model from Hugging Face (Only if token is provided)
@st.cache_resource
def load_model(token):
    try:
        model_name = "google/gemma-2b"
        tokenizer = AutoTokenizer.from_pretrained(model_name, token=token)
        model = AutoModelForCausalLM.from_pretrained(
            model_name, token=token, torch_dtype=torch.float32, device_map="auto"
        )
        return tokenizer, model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None, None

if hf_token:
    tokenizer, model = load_model(hf_token)

#  Sidebar: Upload Medical Report Image
with st.sidebar:
    st.header("📄 Upload Medical Report")
    uploaded_file = st.file_uploader("Choose a report (JPG, PNG)", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Report Preview", use_container_width=True)

st.title("🩺  Bill Extractor")

#  Preprocess Image for Better OCR
def preprocess_image(image):
    img = np.array(image)
    if len(img.shape) == 3:  # Convert only if not already grayscale
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)

#  Process uploaded file
if uploaded_file:
    image = Image.open(uploaded_file)
    processed_image = preprocess_image(image)  # Apply preprocessing

    #  Perform OCR using Tesseract
    extracted_text = pytesseract.image_to_string(processed_image, lang="eng").strip()

    #  Show extracted raw text
    st.subheader("📝 Extracted OCR Text")
    st.text_area("Raw OCR Output", extracted_text, height=200)

    #  Extract structured details using regex
    def extract_details(text):
        text = text.upper()  # Normalize text to uppercase for better matching

        details = {
            "Patient Name": re.search(r"PATIENT NAME\s*\+?\s*{?\s*([\w\s.]+?)\s+IPD NO", text),
            "IPD No": re.search(r"IPD\s*NO\.\s*\+\s*\|\s*([\w\d-]+)", text),
            "Age": re.search(r"AGE\s*:\s*\|\s*(\d+\s*YRS?\s*\d*\s*MTH?)", text),
            "UHID": re.search(r"UHID\s*\+\s*\|\s*([\w\d-]+)", text),
            "Gender": re.search(r"GENDER\s*:\s*\|\s*(MALE|FEMALE|M|F)", text, re.IGNORECASE),
            "Bill No": re.search(r"BILL\s*NO\.\s*:\s*\|\s*([\w\d-]+)", text),

            "Referring Doctor": re.search(r"Ref\.?\s*Doctor\s*[:|\-]?\s*\|?\s*(DR\.\s+[A-Z\s]+?FBD)", text, re.IGNORECASE),
           # "Referring Doctor": re.search(r"REF\.?\s*DOCTOR\s*[:|\-]?\s*(DR\.\s+[A-Z\s]+)", text),
            "Bill Date": re.search(r"BILL\s*DATE\s*T\s*\|\s*([\d-]+\s[\d:]+)", text),
            "Ward / Bed": re.search(r"WARD\s*\d+\s*\|\s*(.*)", text),
            "Print Date": re.search(r"PRINT\s*DATE\s*\d*\s*\[\s*([\d-]+\s[\d:]+)", text),
            "Report Summary": re.search(r"ABDOMEN ERECT & SUPINE:\s*(.*?)\s*SEND OF REPORT", text, re.DOTALL)        }
        extracted_info = {key: (match.group(1).strip() if match else "Not Found") for key, match in details.items()}

        return extracted_info

    structured_data = extract_details(extracted_text)

    #  Display Extracted Details
    st.subheader("🔍 Extracted Details")
    for key, value in structured_data.items():
        st.write(f"{key}: **{value}**")

    #  Generate PDF function
    def generate_pdf(data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, "Medical Report", ln=True, align="C")
        pdf.ln(10)

        for key, value in data.items():
            pdf.cell(200, 10, f"{key}: {value}", ln=True)

        pdf_path = "Medical_Report.pdf"
        pdf.output(pdf_path, "F")
        return pdf_path

    #  Generate PDF button
    if st.button("📥 Generate PDF Report"):
        pdf_file = generate_pdf(structured_data)
        with open(pdf_file, "rb") as file:
            st.download_button("Download PDF", file, file_name="Medical_Report.pdf", mime="application/pdf")