from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

if __name__ == "__main__":
    # Generate audio
    audio = client.text_to_speech.convert(
        text="Our next step is a coordinated effort with international partners to focus multiple arrays on the signal's origin point to gather more data. To the public, I would say: This is a moment of profound discovery. It is a time for curiosity and patience, not fear. Whatever we learn, it will fundamentally expand our understanding of the universe. We are on the verge of a new chapter in human history.",
        voice_id="zE6Bt8QH1noub5xkOEVo",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    
    # Save audio to file
    output_file = "assets/audio/test_audio.mp3"
    with open(output_file, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    
    print(f"✅ Audio saved to {output_file}")
    print(f"Now you can use ffprobe to measure duration!")
