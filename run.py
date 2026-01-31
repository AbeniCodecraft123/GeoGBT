import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # THIS IS IMPORTANT

client = genai.Client(api_key=os.getenv("GEMINI_AI"))



response = client.models.generate_content(
    model="models/gemini-2.5-flash",
    contents="Define porosity in petrophysics"
)

print(response.text)
