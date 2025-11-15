from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/extract")
async def extract_text_from_slides(file: UploadFile = File(...)):
    """
    Extract text from slides using OCR
    Input: slides (PDF, images, etc.)
    Output: raw transcript text
    """
    pass

