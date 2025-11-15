from fastapi import APIRouter

router = APIRouter()

@router.post("/generate")
async def generate_script_from_transcript():
    """
    Generate structured script using Gemini
    Input: raw transcript text
    Output: [ {t1, c1, s}, {t2, c2, s}, ... ]
    where:
        t1 = full line for speaker
        c1 = short caption for screen
        s = speaker ID
    """
    pass

