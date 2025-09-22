from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse
from app.services.ocr_services import preprocess_image, extract_handwritten_text, correct_text
from app.utils.accuracy import evaluate_accuracy

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/handwritten")
async def ocr_handwritten(
    file: UploadFile = File(...),
    ground_truth: str = Form(None)  # Optional
):
    contents = await file.read()

    # Preprocess & OCR
    image = preprocess_image(contents)
    raw_text = extract_handwritten_text(image)
    final_text = correct_text(raw_text)

    response = {
        "raw_text": raw_text,
        "corrected_text": final_text
    }

    if ground_truth:
        cer, wer = evaluate_accuracy(final_text, ground_truth)
        response["cer"] = cer
        response["wer"] = wer

    return JSONResponse(content=response)
