# app/routes/azure_document_ai_routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/azure/ai", tags=["Azure Document AI"])


def get_azure_service():
    """Get Azure service instance with proper error handling."""
    try:
        from app.services.handwritten_ocr import azure_document_ai_service
        return azure_document_ai_service
    except Exception as e:
        logger.error(f"Failed to get Azure service: {str(e)}")
        return None


@router.post("/analyze-whiteboard")
async def analyze_whiteboard(
        file: UploadFile = File(..., description="Whiteboard image to analyze")
):
    """
    Analyze a whiteboard image and extract structured text with layout information.

    Supports common image formats: JPEG, PNG, BMP, TIFF, etc.
    """
    # Check if service is available
    service = get_azure_service()
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Azure Document Intelligence service is not available. Please check service configuration."
        )

    try:
        # Validate file type
        allowed_content_types = [
            'image/jpeg', 'image/jpg', 'image/png',
            'image/bmp', 'image/tiff', 'image/webp'
        ]

        if file.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported types: {', '.join(allowed_content_types)}"
            )

        # Read file content
        image_content = await file.read()

        if len(image_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Analyze the image
        analysis_result = await service.analyze_whiteboard(
            image_content,
            file.filename
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Whiteboard analysis completed successfully",
                "data": analysis_result
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing whiteboard image {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze whiteboard image: {str(e)}"
        )


@router.get("/health")
async def azure_ai_health():
    """
    Health check for Azure Document Intelligence service.
    """
    service = get_azure_service()

    if service is None:
        return {
            "success": False,
            "service": "azure_document_intelligence",
            "status": {
                "status": "service_unavailable",
                "error": "Azure Document Intelligence service failed to initialize",
                "suggestion": "Check AZURE_ENDPOINT and AZURE_KEY environment variables"
            }
        }

    try:
        health_status = await service.health_check()
        return {
            "success": health_status.get("status") == "healthy",
            "service": "azure_document_intelligence",
            "status": health_status
        }
    except Exception as e:
        logger.error(f"Azure Document Intelligence health check failed: {str(e)}")
        return {
            "success": False,
            "service": "azure_document_intelligence",
            "status": {
                "status": "unhealthy",
                "error": str(e),
                "suggestion": "Check Azure service configuration and credentials"
            }
        }


@router.get("/capabilities")
async def get_capabilities():
    """
    Get information about Azure Document Intelligence capabilities.
    """
    return {
        "success": True,
        "data": {
            "service": "azure_document_intelligence",
            "features": [
                "text_extraction",
                "layout_analysis",
                "handwriting_recognition",
                "structured_output",
                "confidence_scoring",
                "spatial_analysis"
            ],
            "supported_formats": [
                "JPEG", "PNG", "BMP", "TIFF", "PDF", "WEBP"
            ],
            "max_file_size": "50MB",
            "languages": ["en", "es", "fr", "de", "it", "pt", "nl", "zh-Hans", "zh-Hant"]
        }
    }