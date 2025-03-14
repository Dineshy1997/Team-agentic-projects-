import os
from pydoc import doc
import re
import requests
import streamlit as st
from dotenv import load_dotenv
from typing import List, Dict, Any
import google.generativeai as genai
from googleapiclient.discovery import build
from youtubesearchpython import VideosSearch
from typing import List, Dict, Any
import wikipedia
import spacy
# Load environment variables
load_dotenv()

class AITutorAgent:
    def __init__(self):
        # Load NLP Model
        self.nlp = spacy.load("en_core_web_sm")
        
        # Gemini API Setup
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')

        # Google Search API Setup
        self.google_search_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')
        self.google_search_service = build("customsearch", "v1", developerKey=self.google_search_api_key)

        # YouTube API Setup
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.youtube_service = build('youtube', 'v3', developerKey=self.youtube_api_key)

    def classify_subject(self, query: str) -> str:
        doc = self.nlp(query.lower())  # Process query

        subject_terms = {
        "math": ["equation", "integral", "geometry", "algebra"],
        "physics": ["velocity", "force", "gravity", "momentum"],
        "chemistry": ["reaction", "compound", "molecule", "acid"],
        "biology": ["cell", "dna", "genetics", "organism"],
        "finance": ["stock", "investment", "economy", "banking"],
        "technology": ["ai", "machine learning", "software", "programming"],
        "health": ["disease", "medicine", "nutrition", "symptom"],
        "history": ["war", "historical", "revolution", "kingdom"],
        "general": []
    }

        for token in doc:
         for subject, keywords in subject_terms.items():
            if token.lemma_ in keywords:  # Check using lemma (root form)
                return subject
        return "general"
    
    def generate_explanation(self, query: str, user_type: str) -> str:
        """Generates an explanation using Gemini AI."""
        user_type_prompts = {
            'Kids': "Explain this in a fun and simple way for kids:",
            'Students': "Provide a detailed and structured explanation for students:",
            'Professionals': "Give a technical and advanced explanation for professionals:"
        }
        try:
            prompt = f"{user_type_prompts[user_type]} {query}"
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    def process_query(self, query: str, user_type: str):
        """Processes query and returns responses from different sources."""
        return {
            'explanation': self.generate_explanation(query, user_type),
            'images': self.search_images(query, user_type) or ["No related images available."],
            'videos': self.search_youtube_videos(query) or ["No related videos available."],
            'wikipedia': self.get_wikipedia_summary(query, user_type) or "No related article found."
        }
        
    def search_images(self, query: str, user_type: str):
        """Searches for images using Google Custom Search API."""
        try:
            search_query = f"{query} {user_type} related image"
            url = f"https://www.googleapis.com/customsearch/v1?q={search_query}&cx={self.google_cse_id}&searchType=image&key={self.google_search_api_key}"
            response = requests.get(url)
            data = response.json()

            if 'items' in data:
                return [item['link'] for item in data['items'][:2]]
            else:
                return ["No related images available."]
        except Exception as e:
            return [f"Error searching images:{str(e)}"]
            
    
    def search_youtube_videos(self, query: str):
        """Searches for YouTube videos using YouTube API."""
        try:
            search_response = self.youtube_service.search().list(
                q = query,
                part = "snippet",
                maxResults = 2,
                type = "video"
            ).execute()

            videos = []
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                videos.append(video_url)
            return videos if videos else ["No related videos available."]
        except Exception as e:
            return [f"Error retrieving YouTube videos: {str(e)}"]
        
    def get_wikipedia_summary(self, query: str, user_type: str):
        """Retrieves Wikipedia summary for the given query."""
        try:
            if user_type == "Kids":
                sentences =3
            elif user_type == "Students":
                sentences = 7
            elif user_type == "Professionals":
                sentences = 12
            else:
                sentences = 5
            summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
            return summary
        except wikipedia.exceptions.DisambiguationError as e:
            return f"Multiple results found: {e.options[:5]}..."  # Suggest first 5 options
        except wikipedia.exceptions.PageError:
            return "No Wikipedia page found for this topic."
        except Exception as e:
            return f"Error retrieving Wikipedia summary: {str(e)}"
    
def main():
    st.set_page_config(page_title="AI Tutor Agent", page_icon="🤖")
    tutor_agent = AITutorAgent()
    
    st.title("🤖 AI Tutor Agent")
    st.subheader("Ask anything! Get explanations, images, videos, or articles.")
    
    query = st.text_input("Enter your query:")
    user_type = st.radio("Select User Type:", ['Kids', 'Students', 'Professionals'], horizontal=True)
    
    if st.button("Submit"):
        if query:
            with st.spinner('Generating outputs...'):
                outputs = tutor_agent.process_query(query, user_type)
            
            st.subheader("Explanation")
            st.write(outputs['explanation'])
            
            st.subheader("Wikipedia Summary")
            st.write(outputs['wikipedia'])
            
            st.subheader("Related Images")
            for img in outputs['images']:
                st.image(img, use_container_width=True)
            
            st.subheader("Related YouTube Videos")
            for video in outputs['videos']:
                st.video(video)
        else:
            st.warning("Please enter a query!")
if __name__ == "__main__":
    main()
