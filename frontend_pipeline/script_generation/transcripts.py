# transcript.py

from google import genai
import os

def extract_transcript(audio_file_path, video_file_type): # video_file_type is either 'mc' or 'sub'
    # Function to extract transcript from video using Gemini API
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Transcribe the following audio file: {}".format(audio_file_path),
    )
    return response.text