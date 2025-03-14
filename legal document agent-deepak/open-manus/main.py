import os
import httpx
import pdfplumber
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from bs4 import BeautifulSoup

app = FastAPI()

# Google Gemini API Key (Replace with an env variable in production)
GEMINI_API_KEY = "AIzaSyDyCyra9O4XRQlipVZzu3MCfkCndLzLI0s"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

class ContractAnalysisRequest(BaseModel):
    contract_text: str
    case_law_url: str

async def call_gemini_api(prompt: str):
    """Calls Google Gemini API for legal risk analysis with enhancements."""
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(GEMINI_API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            try:
                response_data = response.json()
                print("Gemini API Response:", response_data)  # Debugging
                return response_data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                return f"Error parsing Gemini API response: {str(e)}"
        return f"Error: {response.status_code} - {response.text}"

def extract_text_from_pdf(file):
    """Extracts text from a PDF file."""
    with pdfplumber.open(file) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages if page.extract_text() is not None)

async def extract_text_from_pdf_async(file):
    """Runs PDF text extraction asynchronously."""
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, extract_text_from_pdf, file.file)

async def scrape_case_law(website_url):
    """Scrapes case law from a legal website asynchronously."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(website_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            return " ".join(p.text for p in soup.find_all("p"))[:2000]  # Limit to 2000 characters
        return f"Failed to retrieve case law (Error {response.status_code})"

@app.get("/")
async def home():
    """Home route to prevent 404 errors."""
    return {"message": "Welcome to the Legal Risk Analysis API using Google Gemini!"}

@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    """Uploads and extracts text from a contract PDF."""
    contract_text = await extract_text_from_pdf_async(file)
    return {"contract_text": contract_text}

@app.post("/predict_legal_risk")
async def predict_legal_risk(contract_text: str = Form(...), case_law_url: str = Form(...)):
    """Analyzes the contract against case law, ISO validation, and provides best legal advice."""
    
    # Scrape case law if a URL is provided
    case_law_text = await scrape_case_law(case_law_url) if case_law_url else "No case law provided."

    # Enhanced prompt for Gemini AI
    prompt = f"""
    Analyze the following contract and provide:
    - A **detailed legal risk assessment**.
    - **Best legal advice** to mitigate these risks.
    - **Comparison with relevant case law** (if provided).
    - **ISO standard compliance check** (highlight missing elements).
    - **Recommendations before signing** the contract.

    Contract Text:
    {contract_text}

    Relevant Case Law:
    {case_law_text}

    Ensure the response includes actionable legal guidance and improvements.
    """

    response = await call_gemini_api(prompt)
    return {"legal_risk_analysis": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
