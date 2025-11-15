# Video Generation API

A FastAPI application that generates videos from slides using OCR, Gemini AI, ElevenLabs TTS, and FFmpeg.

## Architecture

```
Input (Slides) 
    ↓
[OCR] Extract text → Raw transcript
    ↓
[Gemini] Generate script → [{t1, c1, s}, {t2, c2, s}, ...]
    ↓
[ElevenLabs] Generate audio + timing → Shot list with durations
    ↓
[FFmpeg] Assemble video → Final video with synchronized captions
```

### Pipeline Breakdown

1. **OCR Service** (`app/services/ocr_service.py`)
   - Extracts text from slides (PDF, images)
   - Returns raw transcript

2. **Gemini Service** (`app/services/gemini_service.py`)
   - Takes raw transcript
   - Returns structured script: `[{t, c, s}, ...]`
     - `t`: Full line for speaker
     - `c`: Short caption for screen
     - `s`: Speaker ID

3. **ElevenLabs Service** (`app/services/elevenlabs_service.py`)
   - Loops through script lines
   - Generates audio for each line with correct voice
   - Measures duration with ffprobe
   - Builds shot list with timing

4. **FFmpeg Service** (`app/services/ffmpeg_service.py`)
   - Concatenates audio files
   - Assembles final video with background + audio
   - Adds synchronized captions using drawtext filter

## Project Structure

```
app/
├── main.py                 # FastAPI app initialization
├── api/
│   └── routes/
│       ├── ocr.py         # OCR endpoints
│       ├── script.py      # Script generation endpoints
│       ├── audio.py       # Audio generation endpoints
│       └── video.py       # Video assembly endpoints
├── services/
│   ├── ocr_service.py     # OCR logic
│   ├── gemini_service.py  # Gemini API integration
│   ├── elevenlabs_service.py  # ElevenLabs TTS + timing
│   └── ffmpeg_service.py  # Video assembly
├── models/
│   └── schemas.py         # Pydantic models
├── core/
│   └── config.py          # App configuration
└── utils/
    └── helpers.py         # Utility functions
```

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## API Endpoints

### OCR
- `POST /api/ocr/extract` - Extract text from slides

### Script Generation
- `POST /api/script/generate` - Generate structured script from transcript

### Audio Generation
- `POST /api/audio/generate` - Generate audio files with timing

### Video Assembly
- `POST /api/video/assemble` - Assemble final video

## Development

### Working on Different Features

The project is organized so multiple developers can work independently:

- **Developer 1**: Can work on OCR + Script Generation
  - Files: `ocr.py`, `script.py`, `ocr_service.py`, `gemini_service.py`

- **Developer 2**: Can work on Audio + Video Assembly
  - Files: `audio.py`, `video.py`, `elevenlabs_service.py`, `ffmpeg_service.py`

## Requirements

- Python 3.9+
- FFmpeg (system installation required)
- Tesseract OCR (for OCR functionality)
- API Keys:
  - Gemini API
  - ElevenLabs API
