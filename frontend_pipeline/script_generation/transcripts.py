import base64
import os
import json
import dotenv
from google import genai
from google.genai import types


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
            types.Part.from_text(text="""You are to generate short-form educational dialogues between Peter Griffin and Stewie Griffin.

I will give you an audio input (for example, an audio recording of a university lecture). Your job is to:

Listen to or process the audio's content.

Identify the distinct subtopics discussed in the audio.

For EACH distinct subtopic, generate a separate short-form educational dialogue (~1 minute transcript, 120-150 words) summarizing that specific subtopic.

Output a SINGLE JSON object that contains all of these transcripts, structured exactly like this:

JSON
{
  "subtopic_transcripts": [
    {
      "subtopic_title": "A short title for the first distinct subtopic.",
      "dialogue": [
        {
          "caption": "A single sentence under 20 words.",
          "speaker": "PETER"
        },
        {
          "caption": "Another single sentence under 20 words.",
          "speaker": "STEWIE"
        }
      ]
    },
    {
      "subtopic_title": "A short title for the second distinct subtopic.",
      "dialogue": [
        {
          "caption": "This dialogue is about the second subtopic.",
          "speaker": "PETER"
        },
        {
          "caption": "Fascinating! But what about...?",
          "speaker": "STEWIE"
        }
      ]
    }
  ]
}
RULES:

You must generate one transcript object (with a "subtopic_title" and "dialogue" array) for each main, distinct subtopic you identify in the audio.

Each "caption" must be one sentence only, 20 words or fewer.

Speakers must be only "PETER" or "STEWIE".

The "subtopic_title" should be a brief, descriptive string.

The tone for EACH dialogue should resemble Peter teaching and Stewie asking curious questions.

EACH dialogue must be conversational and humorous, but still educational about its subtopic.

In EACH "dialogue" array, Stewie must ask at least one question about that specific subtopic.

EACH "dialogue" array should total roughly 1 minute of spoken dialogue (approx. 120-150 words).
                                 
Make NO reference to images or visual elements, aside from examples such as "imagine a chart showing..." or "picture this scenario...".

NO extra text—only the single JSON object containing all generated transcripts.

After I provide the audio input, respond ONLY with the JSON result."""),
        ]
    elif file_type == "text":
        text_data = bytes.decode("utf-8")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=text_data),
                ],
            ),
        ]
        prompt = [
            types.Part.from_text(text="""You are to generate short-form educational dialogues between Peter Griffin and Stewie Griffin.

I will give you a text input (for example, a transcript from a lecture or video). Your job is to:

Read and process the text's content.

Identify the distinct subtopics discussed in the text.

For EACH distinct subtopic, generate a separate short-form educational dialogue (~1 minute transcript, 120-150 words) summarizing that specific subtopic.

Output a SINGLE JSON object that contains all of these transcripts, structured exactly like this:

JSON
{
  "subtopic_transcripts": [
    {
      "subtopic_title": "A short title for the first distinct subtopic.",
      "dialogue": [
        {
          "caption": "A single sentence under 20 words.",
          "speaker": "PETER"
        },
        {
          "caption": "Another single sentence under 20 words.",
          "speaker": "STEWIE"
        }
      ]
    },
    {
      "subtopic_title": "A short title for the second distinct subtopic.",
      "dialogue": [
        {
          "caption": "This dialogue is about the second subtopic.",
          "speaker": "PETER"
        },
        {
          "caption": "Fascinating! But what about...?",
          "speaker": "STEWIE"
        }
      ]
    }
  ]
}
RULES:

You must generate one transcript object (with a "subtopic_title" and "dialogue" array) for each main, distinct subtopic you identify in the text.

Each "caption" must be one sentence only, 20 words or fewer.

Speakers must be only "PETER" or "STEWIE".

The "subtopic_title" should be a brief, descriptive string.

The tone for EACH dialogue should resemble Peter teaching and Stewie asking curious questions.

EACH dialogue must be conversational and humorous, but still educational about its subtopic.

In EACH "dialogue" array, Stewie must ask at least one question about that specific subtopic.

EACH "dialogue" array should total roughly 1 minute of spoken dialogue (approx. 120-150 words).
                                 
Make NO reference to images or visual elements, aside from examples such as "imagine a chart showing..." or "picture this scenario...".

NO extra text—only the single JSON object containing all generated transcripts.

After I provide the text input, respond ONLY with the JSON result."""),
        ]
    elif file_type == "youtube":
        youtube_url = bytes.decode("utf-8")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=youtube_url),
                ],
            ),
        ]
        prompt = [
            types.Part.from_text(text="""You are to generate short-form educational dialogues between Peter Griffin and Stewie Griffin.

I will give you a YouTube link. Your job is to:

Watch or process the video’s content.

Identify the distinct subtopics discussed in the video.

For EACH distinct subtopic, generate a separate short-form educational dialogue (~1 minute transcript, 120-150 words) summarizing that specific subtopic.

Output a SINGLE JSON object that contains all of these transcripts, structured exactly like this:

JSON
{
  "transcripts": [
    {
      "subtopic_title": "A short title for the first distinct subtopic.",
      "dialogue": [
        {
          "caption": "A single sentence under 20 words.",
          "speaker": "PETER"
        },
        {
          "caption": "Another single sentence under 20 words.",
          "speaker": "STEWIE"
        }
      ]
    },
    {
      "subtopic_title": "A short title for the second distinct subtopic.",
      "dialogue": [
        {
          "caption": "This dialogue is about the second subtopic.",
          "speaker": "PETER"
        },
        {
          "caption": "Fascinating! But what about...?",
          "speaker": "STEWIE"
        }
      ]
    }
  ]
}
RULES:

You must generate one transcript object (with a "subtopic_title" and "dialogue" array) for each main, distinct subtopic you identify in the video.

Each "caption" must be one sentence only, 20 words or fewer.

Speakers must be only "PETER" or "STEWIE".

The "subtopic_title" should be a brief, descriptive string.

The tone for EACH dialogue should resemble Peter teaching and Stewie asking curious questions.

EACH dialogue must be conversational and humorous, but still educational about its subtopic.

In EACH "dialogue" array, Stewie must ask at least one question about that specific subtopic.

EACH "dialogue" array should total roughly 1 minute of spoken dialogue (approx. 120-150 words).
                                 
Make NO reference to images or visual elements, aside from examples such as "imagine a chart showing..." or "picture this scenario...".

NO extra text—only the single JSON object containing all generated transcripts.

After I send the YouTube link, respond ONLY with the JSON result."""
                                )
        ]
    elif file_type == "pptx":
        pptx_data = bytes.decode("utf-8")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=pptx_data),
                ],
            ),
        ]
        prompt = [
            types.Part.from_text(text="""You are to generate short-form educational dialogues between Peter Griffin and Stewie Griffin.

I will give you a text input (for example, a transcript from a lecture or video). Your job is to:

Read and process the text's content.

Identify the distinct subtopics discussed in the text.

For EACH distinct subtopic, generate a separate short-form educational dialogue (~1 minute transcript, 120-150 words) summarizing that specific subtopic.

Output a SINGLE JSON object that contains all of these transcripts, structured exactly like this:
JSON
{
  "subtopic_transcripts": [
    {
      "subtopic_title": "A short title for the first distinct subtopic.",
      "dialogue": [
        {
          "caption": "A single sentence under 20 words.",
          "speaker": "PETER"
        },
        {
          "caption": "Another single sentence under 20 words.",
          "speaker": "STEWIE"
        }
      ]
    },
    {
      "subtopic_title": "A short title for the second distinct subtopic.",
      "dialogue": [
        {
          "caption": "This dialogue is about the second subtopic.",
          "speaker": "PETER"
        },
        {
          "caption": "Fascinating! But what about...?",
          "speaker": "STEWIE"
        }
      ]
    }
  ]
}
RULES:

You must generate one transcript object (with a "subtopic_title" and "dialogue" array) for each main, distinct subtopic you identify in the text.

Each "caption" must be one sentence only, 20 words or fewer.

Speakers must be only "PETER" or "STEWIE".

The "subtopic_title" should be a brief, descriptive string.

The tone for EACH dialogue should resemble Peter teaching and Stewie asking curious questions.

EACH dialogue must be conversational and humorous, but still educational about its subtopic.

In EACH "dialogue" array, Stewie must ask at least one question about that specific subtopic.

EACH "dialogue" array should total roughly 1 minute of spoken dialogue (approx. 120-150 words).
                                 
Make NO reference to images or visual elements, aside from examples such as "imagine a chart showing..." or "picture this scenario...".

NO extra text—only the single JSON object containing all generated transcripts.

After I provide the text input, respond ONLY with the JSON result."""
                                )
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
        system_instruction=prompt
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
    file = "C:\\Users\\Chris\\Downloads\\The essence of calculus.mp3"
    file_type = "audio/mp3"
    transcripts = extract_transcripts(file, file_type)
    print(transcripts)