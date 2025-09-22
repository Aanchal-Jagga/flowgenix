from fastapi import APIRouter, UploadFile,File,HTTPException
from app.services import ocr_services
import app.services.llm_services as llm_services

#An APIRouter is used to group related endpoints.
# We will include this router in our main app.
router=APIRouter()

@router.post("/api/v1/process")
async def process_whiteboard_image(file: UploadFile = File(...)):
    '''
    The main endpoint processing the OCR and LLM services
    :param file:
    :return:
    '''
    try:
        #1.Read Image Bytes from Upload
        image_bytes = await file.read()

        #2.Call the ocr serivices to get the raw text
        raw_ocr_results = ocr_services.perform_ocr(image_bytes)

        #3.Call the llm services to get the structured data
        # (logic implemented inside the LLM_services.py)
        structured_content=await llm_services.structure_text_with_llm(raw_ocr_results)

        #4.Return the response
        final_response = {
            "rawOcr": raw_ocr_results,
            "structuredContent": structured_content
        }
        return final_response

    except Exception as e:
        # A simple error handling mechanism.
        raise HTTPException(status_code=500, detail=str(e))
