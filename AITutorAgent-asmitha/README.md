## AI Tutor Agent:

- This Agent is a learning assistant designed to provide personalized educational responses. 
- It can generate explanations, retrieve images, fetch video resources, and summarize Wikipedia articles based on the user's query and selected user type (Kids, Students, or Professionals).


# Technologies Used:

- Programming Language: Python
- Development Environment: VS Code


# Libraries & APIs:

- Spacy (NLP for subject classification)
- Google Gemini AI (Text-based response generation)
- Wikipedia API (Summarized article retrieval)
- Google Search API (Image retrieval)
- YouTube API (Educational video suggestions)
- Streamlit (User Interface)


# Workflow:

- User Input: The user enters a query and selects their category (Kids, Students, or Professionals).
# Query Processing:
- NLP Subject Classification: Identifies subject type (Math, Science, etc.).
- AI Response Generation: Gemini AI formulates an explanation.
- Image Retrieval: Google Search API fetches relevant images.
- Video Suggestions: YouTube API provides educational videos.
- Wikipedia Summary: Retrieves a brief, structured summary.
- Response Formatting: Data is compiled and structured.
- Streamlit UI: Displays results interactively.


# Deployment:

- Currently designed for local hosting using Streamlit.
- Can be extended for global access using FastAPI/Flask (if required in the future).
