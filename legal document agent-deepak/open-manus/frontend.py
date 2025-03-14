import streamlit as st
import fitz  # PyMuPDF for PDF text extraction
import requests

API_UPLOAD_URL = "http://127.0.0.1:5000/upload_contract"
API_ANALYZE_URL = "http://127.0.0.1:5000/predict_legal_risk"

# Function to send the PDF file to the backend for text extraction
def upload_contract(pdf_file):
    files = {"file": pdf_file}
    try:
        response = requests.post(API_UPLOAD_URL, files=files, timeout=20)
        if response.status_code == 200:
            return response.json().get("contract_text", "No text extracted.")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error connecting to API: {e}"

# Function to analyze legal risk using the extracted contract text and case law
def analyze_legal_risk(contract_text, case_law_url):
    data = {"contract_text": contract_text, "case_law_url": case_law_url}
    try:
        response = requests.post(API_ANALYZE_URL, data=data, timeout=30)
        if response.status_code == 200:
            return response.json().get("legal_risk_analysis", "No analysis result returned.")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error connecting to API: {e}"

# Streamlit UI
st.title("📄 Legal Risk Analysis AI")
st.write("Upload a contract, analyze case law, and predict potential legal risks.")

# File uploader
uploaded_file = st.file_uploader("Upload Contract PDF", type=["pdf"])
case_law_url = st.text_input("Enter Case Law Website URL (optional)")

if uploaded_file is not None:
    st.write("### Extracting Contract Text...")
    contract_text = upload_contract(uploaded_file)
    st.text_area("Extracted Contract Text", contract_text, height=200)

    if st.button("Analyze Legal Risks"):
        with st.spinner("Analyzing legal risks..."):
            analysis_result = analyze_legal_risk(contract_text, case_law_url)

        st.write("### AI Analysis Result:")
        st.success(analysis_result)
