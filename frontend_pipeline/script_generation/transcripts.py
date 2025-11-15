import base64
import os
import json
from typing import Any, List

import dotenv
from google import genai
from google.genai import types
from pydantic import ValidationError

try:
    from frontend_pipeline.script_generation.prompts import (
        AUDIO_PROMPT,
        TEXT_PROMPT,
        YOUTUBE_PROMPT,
        PPTX_PROMPT,
    )
    from frontend_pipeline.script_generation.models import (
        TranscriptResponse,
        SubtopicDialogue,
    )
except ImportError:  # pragma: no cover - fallback when run as script
    from script_generation.prompts import (  # type: ignore
        AUDIO_PROMPT,
        TEXT_PROMPT,
        YOUTUBE_PROMPT,
        PPTX_PROMPT,
    )
    from script_generation.models import (  # type: ignore
        TranscriptResponse,
        SubtopicDialogue,
    )


def _ensure_text(data):
    if isinstance(data, bytes):
        return data.decode("utf-8")
    return str(data)


def _extend_from_payload(payload: Any, subtopics: List[SubtopicDialogue]) -> bool:
    try:
        model = TranscriptResponse.model_validate(payload)
    except ValidationError:
        return False

    subtopics.extend(model.subtopic_transcripts)
    return True


def extract_transcripts(file, file_type):
    dotenv.load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    model = "gemini-2.5-flash"

    # Read the audio file and provide base64-encoded data to the Blob.
    #if not os.path.isfile(audio_file_path):
        #raise FileNotFoundError(f"Audio file not found: {audio_file_path}")


    # Blob expects base64-encoded bytes (the pydantic validator rejects a plain path string).
    if file_type == "audio/mp3":
        with open(file, "rb") as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(inline_data=types.Blob(data=audio_b64, mime_type="audio/mp3")),
                ],
            ),
        ]
        prompt = [
            types.Part.from_text(text=AUDIO_PROMPT),
        ]
    elif file_type == "text":
        text_data = _ensure_text(file)
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=text_data),
                ],
            ),
        ]
        prompt = [
            types.Part.from_text(text=TEXT_PROMPT),
        ]
    elif file_type == "youtube":
        youtube_url = _ensure_text(file)
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=youtube_url),
                ],
            ),
        ]
        prompt = [
            types.Part.from_text(text=YOUTUBE_PROMPT)
        ]
    elif file_type == "pptx":
        pptx_data = _ensure_text(file)
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=pptx_data),
                ],
            ),
        ]
        prompt = [
            types.Part.from_text(text=PPTX_PROMPT)
        ]
                                 
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        image_config=types.ImageConfig(
            image_size="1K",
        ),
        response_mime_type="application/json",
        response_schema = TranscriptResponse.model_json_schema(),
        system_instruction=prompt
    )

    subtopic_transcripts: List[SubtopicDialogue] = []
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
            if isinstance(parsed, dict) and _extend_from_payload(parsed, subtopic_transcripts):
                continue
        except Exception:
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

        if resp_data and isinstance(resp_data, dict):
            _extend_from_payload(resp_data, subtopic_transcripts)

    return subtopic_transcripts

if __name__ == "__main__":
    file = "C:\\Users\\Chris\\Downloads\\The essence of calculus.mp3"
    file_type = "audio/mp3"
    transcripts = extract_transcripts(file, file_type)
    for subtopic in transcripts:
        print(subtopic.model_dump())