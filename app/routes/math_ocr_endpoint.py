# from fastapi import APIRouter, UploadFile, File, HTTPException
# from app.services.math_ocr_service import math_ocr_service

# router = APIRouter(prefix="/math-ocr", tags=["Math OCR"])


# @router.post("/process")
# async def process_math_image(file: UploadFile = File(...)):
#     """
#     Upload a handwritten math image and get LaTeX output
#     """
#     try:
#         contents = await file.read()
#         result = math_ocr_service.process_math_image(contents)
#         if not result["success"]:
#             raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
# app/routes/mathocr_endpoint.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from app.services.math_ocr_service import math_ocr_service

router = APIRouter()

@router.post("/mathocr/recognize")
async def recognize_math_formula(file: UploadFile = File(...)):
    try:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        result = math_ocr_service.analyze_formula(temp_path)
        os.remove(temp_path)

        
        return {"status": "success", "latex_output": result}


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
