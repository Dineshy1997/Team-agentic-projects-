import google.generativeai as genai

API_KEY = "AIzaSyC2nimv1uHQgXlwxCg6OEoHgiGvjSPbGa0"
genai.configure(api_key=API_KEY)

def generate_ai_reply(email_body):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(f"Reply to this email professionally:\n{email_body}")
    return response.text

# Example usage
latest_email_body = "Hello, we are interested in your proposal."
ai_reply = generate_ai_reply(latest_email_body)
print(f"🤖 AI-generated Reply:\n{ai_reply}")
