import base64
import os
import json
import dotenv
from google import genai
from google.genai import types


def extract_transcripts(audio_file_path, video_file_type):
    dotenv.load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    model = "gemini-2.5-flash"

    # Read the audio file and provide base64-encoded data to the Blob.
    if not os.path.isfile(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    with open(audio_file_path, "rb") as f:
        audio_bytes = f.read()

    # Blob expects base64-encoded bytes (the pydantic validator rejects a plain path string).
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(inline_data=types.Blob(data=audio_b64, mime_type="audio/mp3")),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        image_config=types.ImageConfig(
            image_size="1K",
        ),
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            properties = {
                "transcripts": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        properties = {
                            "caption": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "speaker": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                        },
                    ),
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text="""Generate a conscise summary of the entire lecture audio in the form of a transcript for a educational TikTok/short form content video depicting Peter Griffin educating a curious Stewie Griffin on the subject matter. The transcript should correspond to roughly 1 minute of audio when fed to a text-to-speech model. Separate the outputs into JSON objects with a caption and speaker string, where the caption is at most a sentence long and the speaker is either 'PETER' or 'STEWIE'. Feel free to have multiple captions with the same speaker back to back, but ensure that each caption is at most one sentence long."""),
        ],
    )

    transcripts = []
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        # The streaming chunk may expose the generated text or structured response
        # in different attributes depending on SDK/version. First try parsing
        # the printed text as JSON (most reliable for structured outputs). If
        # that fails, fall back to attribute inspection.
        text = getattr(chunk, "text", None) or ""
        print(text, end="")

        # Try JSON parse of the text payload
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "transcripts" in parsed:
                transcripts.extend(parsed.get("transcripts", []))
                continue
        except Exception:
            # not JSON or not the structured payload we expect
            pass

        # Fallback: inspect attributes/model dump for structured data
        resp_data = None
        # older/newer SDKs may place data under chunk.response.data or inside
        # the model dump representation
        if hasattr(chunk, "response") and getattr(chunk, "response"):
            resp = getattr(chunk, "response")
            if hasattr(resp, "data") and getattr(resp, "data"):
                resp_data = getattr(resp, "data")

        if resp_data is None:
            # try pydantic model dump
            try:
                dumped = chunk.model_dump()
            except Exception:
                dumped = getattr(chunk, "__dict__", None)

            if isinstance(dumped, dict):
                # common places for the structured response
                if "response" in dumped and isinstance(dumped["response"], dict):
                    resp_data = dumped["response"].get("data")
                elif "data" in dumped and dumped["data"]:
                    resp_data = dumped["data"]
                elif "outputs" in dumped and dumped["outputs"]:
                    # sometimes outputs is a list of items containing 'content' or 'data'
                    for out in dumped["outputs"]:
                        if isinstance(out, dict) and "data" in out and out["data"]:
                            resp_data = out["data"]
                            break

        if resp_data:
            # resp_data might be a dict with our 'transcripts' key
            if isinstance(resp_data, dict) and "transcripts" in resp_data:
                transcripts.extend(resp_data.get("transcripts", []))

    return transcripts

if __name__ == "__main__":
    audio_file_path = "C:\\Users\\Chris\\Downloads\\The essence of calculus.mp3"
    video_file_type = "tiktok"
    transcripts = extract_transcripts(audio_file_path, video_file_type)
    print(transcripts)