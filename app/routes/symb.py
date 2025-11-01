#app/routes/symb.py
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.utils.image_ops import preprocess_for_symbol
from app.services.symbol_detection_service import detect_symbols
from app.services.llm_sym import refine_symbols

router = APIRouter()

@router.post("/symbol/detect")
async def detect_symbol(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()

        # Step 1: Preprocess image
        processed = preprocess_for_symbol(image_bytes)

        # Step 2: Detect symbols via Azure Vision
        raw_text = detect_symbols(processed)

        # Step 3: Refine output using LLM
        refined_text = refine_symbols(raw_text)

        return {
            "raw_text": raw_text,
            "refined_text": refined_text,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
