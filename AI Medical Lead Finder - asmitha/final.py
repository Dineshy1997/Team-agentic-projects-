import streamlit as st
import pandas as pd
import requests
import re
from googleapiclient.discovery import build
import spacy
from bs4 import BeautifulSoup
import scrapy
from scrapy.crawler import CrawlerProcess
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import io
from io import BytesIO
import time
import os
import google.generativeai as genai
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

import firecrawl
from firecrawl import FirecrawlApp
firecrawl_app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

GOOGLE_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")                          
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

logging.basicConfig(filename='scrape_errors.log', level=logging.WARNING)

try:
    nlp = spacy.load("en_core_med7_trf")
except:
    nlp = spacy.load("en_core_web_sm")
    
INDIAN_STATES = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Tirupati"],
    "Arunachal Pradesh": ["Itanagar", "Tawang", "Ziro"],
    "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur"],
    "Chhattisgarh": ["Raipur", "Bilaspur", "Durg", "Korba"],
    "Goa": ["Panaji", "Margao", "Vasco da Gama"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat", "Ambala"],
    "Himachal Pradesh": ["Shimla", "Manali", "Dharamshala"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad"],
    "Karnataka": ["Bangalore", "Mysore", "Mangalore", "Hubli"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "Manipur": ["Imphal", "Churachandpur"],
    "Meghalaya": ["Shillong", "Tura"],
    "Mizoram": ["Aizawl", "Lunglei"],
    "Nagaland": ["Kohima", "Dimapur"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela"],
    "Punjab": ["Chandigarh", "Amritsar", "Ludhiana", "Jalandhar"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur", "Ajmer"],
    "Sikkim": ["Gangtok", "Pelling"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Erode", "Tirunelveli", "Vellore", "Thoothukudi", "Dindigul", "Thanjavur", "Karur", "Nagapattinam", "Pudukkottai", "Perambalur", "Sivaganga", "Virudhunagar", "Krishnagiri", "Tiruvannamalai", "Kanyakumari", "Namakkal", "Dharmapuri", "Ramanathapuram", "Cuddalore", "Ariyalur", "Tenkasi", "Tiruvarur", "Viluppuram", "Kallakurichi", "Chengalpattu", "Ranipet", "Tirupattur", "Theni", "Nilgiris", "Kanchipuram", "Tiruvallur", "Mayiladuthurai", "Udhagamandalam"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
    "Tripura": ["Agartala", "Udaipur"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra"],
    "Uttarakhand": ["Dehradun", "Haridwar", "Nainital"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Siliguri"]
}

CATEGORIES = ["Buyer/Seller", "Job Seeking/Hiring"]

def extract_location(query):
    query_lower = query.lower()
    for state, districts in INDIAN_STATES.items():
        for dist in districts:
            if dist.lower() in query_lower:
                return dist, state
        if state.lower() in query_lower:
            return state, state
    return "India", "India"

def get_search_query(category, location, user_query, state):
    medical_keywords = "hospital clinic medical healthcare doctors nurses pharmacies"
    query_lower = user_query.lower()
    if category == "Buyer/Seller":
        intent = "needs" if "need" in query_lower or "buy" in query_lower else "selling"
        product = user_query.split(" in ")[0].replace("hospitals", "").strip()
        return f"{product} {intent} in {location} {state} {medical_keywords} -site:linkedin.com -site:indeed.co.in -inurl:(grocery cookware)"
    else:  # Job Seeking/Hiring
        intent = "jobs" if "seek" in query_lower or "job" in query_lower else "hiring"
        return f"medical {user_query} in {location} {state} {medical_keywords} {intent} -site:linkedin.com"
    
def google_search(query):
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    res = service.cse().list(q=query, cx=GOOGLE_CSE_ID).execute()
    return res.get("items", [])

import logging

logging.basicConfig(filename='scrape_errors.log', level=logging.WARNING)

def scrape_website(url):
    # Try Firecrawl first
    try:
        response = requests.get(f"https://api.firecrawl.dev/v0/scrape", params={"url": url}, headers={"Authorization": f"Bearer {firecrawl_app}"}).json()
        content = response.get("content", "")
        if content and any(kw in content.lower() for kw in ["hospital", "medical", "healthcare", "clinic", "pharmacy", "patient", "doctor", "nurse", "surgeon", "physician", "pharmacies"]):
            return content
    except Exception as e:
        logging.warning(f"Firecrawl failed on {url}: {e}")

    # Fallback to Selenium
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(10)
        driver.get(url)
        content = driver.page_source
        driver.quit()
        if content and any(kw in content.lower() for kw in ["hospital", "medical", "healthcare", "clinic", "pharmacy", "patient", "doctor", "nurse", "surgeon", "physician", "pharmacies"]):
            return content
    except Exception as e:
        logging.warning(f"Selenium failed on {url}: {e}")

    # Fallback to BS4
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text()
        if content and any(kw in content.lower() for kw in ["hospital", "medical", "healthcare", "clinic", "pharmacy", "patient", "doctor", "nurse", "surgeon", "physician", "pharmacies"]):
            return content
    except Exception as e:
        logging.error(f"BS4 failed for {url}: {e}")
        return None
    
def extract_lead_info(content, location, state):
    content = re.sub(r'[^\x20-\x7E]', '', content)
    doc = nlp(content[:10000])
    lead_name = next((ent.text for ent in doc.ents if ent.label_ == "PERSON"), "Unknown")
    hospital_name = next((ent.text for ent in doc.ents if ent.label_ in ["ORG", "FACILITY"] and any(kw in ent.text.lower() for kw in ["hospital", "clinic"])), "Unknown")
    email = re.findall(r"[\w\.-]+@[\w\.-]+", content)
    phone = re.findall(r"\d{10}", content)
    return {
        "Lead Name": lead_name,
        "Hospital/Clinic Name": hospital_name,
        "Email ID": email[0] if email else "Not found",
        "Contact Number": phone[0] if phone else "Not found",
        "Location": f"{location}, {state}",
        "Short Snippet": content[:200] + "..." if len(content) > 200 else content,
        "URL Link": "URL not extracted"
    }

def classify_priority(snippet):
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Classify this medical lead as 'high', 'medium', or 'low' priority based on urgency and relevance. Use these keywords: 'high' if urgent, immediate, critical; 'medium' if standard, regular, moderate; 'low' if optional, future, non-urgent. Snippet: {snippet}"
        response = model.generate_content(prompt)
        result = response.text.strip().lower()
        if result in ["high", "medium", "low"]:
            return result
        return "medium"
    except Exception as e:
        st.error(f"Gemini error: {e}")
        return "medium"

def generate_leads(category, query):
    location, state = extract_location(query)
    search_query = get_search_query(category, location, query, state)
    results = google_search(search_query)
    
    leads = []
    for result in results:
        url = result["link"]
        snippet = result["snippet"]
        content = scrape_website(url)
        if not content:
            continue
        
        lead_info = extract_lead_info(content, location, state)
        lead_info["Priority"] = classify_priority(snippet)
        lead_info["URL Link"] = url
        leads.append(lead_info)
    
    return pd.DataFrame(leads)
    
# Streamlit UI
with st.sidebar:
    st.header("Lead Finder Options 🏥")
    CATEGORIES = ["🛒📦Buyer/Seller", "👩‍⚕️🏥Job Seeking/Hiring"]
    category = st.selectbox("Select Category", CATEGORIES)
    st.markdown("🏥 Find Medical Leads Easily!")

# Centered heading with emoji
st.markdown("<h1 style='text-align: center;'>AI Medical Lead Finder - India 🩺</h1>", unsafe_allow_html=True)

# Custom CSS for styling
st.markdown("""
    <style>
    .main {background: linear-gradient(to right, #e6f0fa, #f0f8ff); padding: 20px;}
    .stButton>button {background-color: #007bff; color: white; border-radius: 8px; font-size: 16px; padding: 10px 20px;}
    .stTextInput>div>input {border-radius: 8px; border: 2px solid #007bff; padding: 10px; font-size: 16px;}
    .stSelectbox>div>select {border-radius: 8px; border: 2px solid #007bff; padding: 10px; font-size: 16px;}
    h2, h3 {color: #0056b3; font-family: 'Helvetica', sans-serif;}
    .stMarkdown {font-family: 'Helvetica', sans-serif; font-size: 16px; color: #333; text-align: center;}
    .stDataFrame {border-radius: 8px; overflow: hidden;}
    .center {text-align: center;}
    </style>
""", unsafe_allow_html=True)

# Center the input field
_, col2, _ = st.columns([1, 2, 1])
with col2:
    query = st.text_input("Enter Search Query (e.g., 'hospitals needing masks in Chennai')")

    if st.button("Generate Leads 🔍"):
        if query:
            with st.spinner("Generating leads..."):
                leads_df = generate_leads(category, query)
                st.session_state.leads_df = leads_df  # Store in session state

# Display results if available in session state
if "leads_df" in st.session_state and not st.session_state.leads_df.empty:
    leads_df = st.session_state.leads_df
    priority_counts = leads_df["Priority"].value_counts()
    high = priority_counts.get("high", 0)
    medium = priority_counts.get("medium", 0)
    low = priority_counts.get("low", 0)
    
    st.subheader("Lead Statistics 📊")
    st.markdown(f"**High Priority**: {high} 🚨 | **Medium Priority**: {medium} ⚠️ | **Low Priority**: {low} 🟢")
    
    st.subheader("Leads Table 📋")
    edited_df = st.data_editor(
        leads_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Lead Name": st.column_config.TextColumn("Lead Name", width=180),
            "Hospital/Clinic Name": st.column_config.TextColumn("Hospital/Clinic", width=250),
            "Email ID": st.column_config.TextColumn("Email", width=200),
            "Contact Number": st.column_config.TextColumn("Phone", width=150),
            "Location": st.column_config.TextColumn("Location", width=180),
            "Short Snippet": st.column_config.TextColumn("Snippet", width=300),
            "URL Link": st.column_config.LinkColumn("URL", width=350),
            "Priority": st.column_config.TextColumn("Priority", width=120)
        },
        height=600,
        key="lead_table"
    )
    
    buffer = BytesIO()
    edited_df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="Download Leads as Excel 💾",
        data=buffer,
        file_name="leads.xlsx",
        mime="application/vnd.ms-excel"
    )