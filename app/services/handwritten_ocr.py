# app/services/handwritten_ocr.py
import logging
import os
from datetime import datetime
from typing import Dict, List, Any

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError


logger = logging.getLogger(__name__)


class AzureDocumentAIService:
    """
    Service class for Azure Document Intelligence operations.
    Handles whiteboard image analysis and text extraction.
    """

    def __init__(self):
        self.endpoint = os.getenv("AZURE_ENDPOINT")
        self.key = os.getenv("AZURE_KEY")

        # Validate credentials
        if not self.endpoint or not self.key:
            raise ValueError("Azure Document Intelligence credentials not found in environment variables")

        # Ensure endpoint has trailing slash
        if not self.endpoint.endswith('/'):
            self.endpoint += '/'

        # Validate endpoint format
        if not self.endpoint.startswith('https://'):
            raise ValueError(f"Invalid endpoint format: {self.endpoint}. Must start with https://")

        try:
            self.client = DocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
            logger.info(f"Azure Document Intelligence client initialized for endpoint: {self.endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {str(e)}")
            raise

    async def analyze_whiteboard(self, image_content: bytes, original_filename: str) -> Dict[str, Any]:
        """
        Analyze a whiteboard image and extract structured text with layout information.

        Args:
            image_content: Binary content of the image
            original_filename: Original filename for logging

        Returns:
            Dictionary containing extracted text, structure, and metadata
        """
        try:
            logger.info(f"Analyzing whiteboard image: {original_filename}")

            # Analyze the document using prebuilt-layout for text + structure
            poller = self.client.begin_analyze_document(
                "prebuilt-layout",
                image_content
            )
            result: AnalyzeResult = poller.result()

            # Process and structure the response
            processed_result = self._process_analysis_result(result, original_filename)

            logger.info(f"Successfully analyzed {original_filename}")
            return processed_result

        except HttpResponseError as e:
            error_msg = f"Azure API error analyzing {original_filename}: {str(e)}"
            logger.error(error_msg)

            # Provide more specific error information
            if e.status_code == 401:
                logger.error("Authentication failed. Check your Azure key and endpoint.")
            elif e.status_code == 403:
                logger.error("Access forbidden. Check your subscription and permissions.")
            elif e.status_code == 429:
                logger.error("Rate limit exceeded. Try again later.")

            raise HttpResponseError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error analyzing {original_filename}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _process_analysis_result(self, result: AnalyzeResult, filename: str) -> Dict[str, Any]:
        """
        Process the raw Azure response into a structured format for our application.
        """
        # Extract basic document information
        # noinspection PyDeprecation
        document_data = {
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat(),
            "page_count": len(result.pages) if result.pages else 0,
            "full_text": result.content if result.content else "",
            "content_structure": []
        }

        # Process each page
        if result.pages:
            for page_idx, page in enumerate(result.pages):
                page_data = {
                    "page_number": page_idx + 1,
                    "width": page.width,
                    "height": page.height,
                    "unit": page.unit,
                    "lines": [],
                    "paragraphs": []
                }

                # Extract lines with confidence scores
                if page.lines:
                    for line in page.lines:
                        line_data = {
                            "content": line.content,
                            "confidence": float(line.confidence) if hasattr(line, 'confidence') else None,
                            "bounding_box": self._extract_bounding_box(line.polygon) if hasattr(line,
                                                                                                'polygon') else None
                        }
                        page_data["lines"].append(line_data)

                # Extract paragraphs if available
                if hasattr(result, 'paragraphs') and result.paragraphs:
                    for para in result.paragraphs:
                        if hasattr(para, 'spans') and para.spans:
                            # Extract paragraph content from spans
                            para_content = ""
                            for span in para.spans:
                                if span.offset is not None and span.length is not None:
                                    para_content = result.content[span.offset:span.offset + span.length]
                                    break

                            para_data = {
                                "content": para_content or para.content if hasattr(para, 'content') else "",
                                "bounding_box": self._extract_bounding_box(para.polygon) if hasattr(para,
                                                                                                    'polygon') else None
                            }
                            page_data["paragraphs"].append(para_data)

                document_data["content_structure"].append(page_data)

        # Calculate overall confidence
        confidences = [line["confidence"] for page in document_data["content_structure"]
                       for line in page["lines"] if line["confidence"] is not None]
        document_data["overall_confidence"] = sum(confidences) / len(confidences) if confidences else 0

        return document_data

    def _extract_bounding_box(self, polygon: List[float]) -> Dict[str, float]:
        """
        Extract bounding box coordinates from polygon points.
        """
        if not polygon or len(polygon) < 8:
            return None

        # Polygon format: [x1, y1, x2, y2, x3, y3, x4, y4]
        x_coords = polygon[0::2]  # All x coordinates
        y_coords = polygon[1::2]  # All y coordinates

        return {
            "x_min": min(x_coords),
            "y_min": min(y_coords),
            "x_max": max(x_coords),
            "y_max": max(y_coords),
            "width": max(x_coords) - min(x_coords),
            "height": max(y_coords) - min(y_coords)
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the Azure Document Intelligence service.
        """
        try:
            logger.info("Starting Azure Document Intelligence health check")

            # Create a minimal test image
            test_image = self._create_minimal_test_image()

            # Try to analyze it
            poller = self.client.begin_analyze_document(
                "prebuilt-layout",
                test_image
            )
            result = poller.result()

            logger.info("Azure Document Intelligence health check passed")
            return {
                "status": "healthy",
                "service": "azure_document_intelligence",
                "endpoint": self.endpoint,
                "timestamp": datetime.utcnow().isoformat()
            }

        except HttpResponseError as e:
            error_msg = f"Azure Document Intelligence health check failed: {str(e)}"
            logger.error(error_msg)

            # Provide specific error details
            status_info = {
                "status": "unhealthy",
                "service": "azure_document_intelligence",
                "error": str(e),
                "error_code": e.status_code if hasattr(e, 'status_code') else None,
                "endpoint": self.endpoint,
                "timestamp": datetime.utcnow().isoformat()
            }

            if e.status_code == 401:
                status_info["error_type"] = "authentication_failed"
                status_info["suggestion"] = "Check your Azure key and endpoint in environment variables"
            elif e.status_code == 403:
                status_info["error_type"] = "access_forbidden"
                status_info["suggestion"] = "Check your subscription and permissions"
            elif e.status_code == 429:
                status_info["error_type"] = "rate_limit_exceeded"
                status_info["suggestion"] = "Try again later"

            return status_info

        except Exception as e:
            error_msg = f"Azure Document Intelligence health check failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "unhealthy",
                "service": "azure_document_intelligence",
                "error": str(e),
                "error_type": "unexpected_error",
                "endpoint": self.endpoint,
                "timestamp": datetime.utcnow().isoformat()
            }

    def _create_minimal_test_image(self) -> bytes:
        """
        Create a minimal test image for health checks.
        This creates a simple 10x10 pixel white PNG image.
        """
        # Simple 10x10 white PNG image as bytes
        # This is a valid minimal PNG that Azure can process
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n\x00\x00\x00\n\x08\x02\x00\x00\x00\x02P\xc0\r\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x1aiTXtComment\x00\x00\x00\x00\x00Created with GIMP\xd0\xe1\x10\x00\x00\x00\x1dIDATx\x9cc\xf8\x0f\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\xff\xff\x03\x00\x00\x00\xd4\x00\x00\x04M\x00\x00\x00\x00IEND\xaeB`\x82'

        return png_data

    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the Azure service configuration.
        """
        issues = []

        if not self.endpoint:
            issues.append("AZURE_ENDPOINT environment variable is not set")
        elif not self.endpoint.startswith('https://'):
            issues.append("AZURE_ENDPOINT must start with https://")
        elif not self.endpoint.endswith('/'):
            issues.append("AZURE_ENDPOINT should end with '/' (will be auto-corrected)")

        if not self.key:
            issues.append("AZURE_KEY environment variable is not set")
        elif len(self.key) < 32:
            issues.append("AZURE_KEY appears to be too short (should be 32+ characters)")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "endpoint": self.endpoint,
            "key_length": len(self.key) if self.key else 0
        }


# Singleton instance
try:
    azure_document_ai_service = AzureDocumentAIService()
    logger.info("Azure Document AI Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Azure Document AI Service: {str(e)}")
    azure_document_ai_service = None