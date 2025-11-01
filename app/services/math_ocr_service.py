# # app/services/math_ocr_service.py
# import os
# import base64
# import requests
# import cv2
# import io
# import logging
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

# class MathOCRService:
#     """
#     Cloud-based Math OCR using Mathpix API
#     """
#     def __init__(self):
#         self.app_id = os.getenv("MATHPIX_APP_ID")
#         self.app_key = os.getenv("MATHPIX_APP_KEY")
#         if not self.app_id or not self.app_key:
#             raise ValueError("Missing Mathpix credentials in .env (MATHPIX_APP_ID and MATHPIX_APP_KEY)")

#         # Test connection
#         self.check_api()

#         logger.info("✅ MathOCRService initialized successfully with Mathpix API")

#     def check_api(self):
#         """Check if Mathpix credentials are valid"""
#         test_data = {"src": "data:image/png;base64,"}  # Empty image base64
#         response = requests.post(
#             "https://api.mathpix.com/v3/text",
#             headers={
#                 "app_id": self.app_id,
#                 "app_key": self.app_key,
#                 "Content-type": "application/json"
#             },
#             json=test_data
#         )
#         if response.status_code == 200 or response.status_code == 400:
#             # 400 is expected because we sent empty data, credentials are fine
#             logger.info("✅ Mathpix API credentials are valid")
#         else:
#             logger.error(f"❌ Mathpix API check failed: {response.status_code} {response.text}")
#             raise RuntimeError(f"Mathpix API check failed: {response.status_code}")

#     def preprocess_image(self, image_path: str) -> str:
#         """Preprocess image (grayscale, threshold) and return base64 string"""
#         img = cv2.imread(image_path)
#         if img is None:
#             raise ValueError(f"Cannot read image: {image_path}")

#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

#         # Encode image to PNG bytes
#         _, buf = cv2.imencode(".png", thresh)
#         img_bytes = buf.tobytes()

#         # Convert to base64
#         img_base64 = base64.b64encode(img_bytes).decode()
#         return img_base64

#     def analyze_formula(self, image_path: str) -> str:
#         """Send image to Mathpix API and get LaTeX"""
#         img_base64 = self.preprocess_image(image_path)

#         payload = {
#             "src": f"data:image/png;base64,{img_base64}",
#             "formats": ["latex_styled"]
#         }

#         response = requests.post(
#             "https://api.mathpix.com/v3/text",
#             headers={
#                 "app_id": self.app_id,
#                 "app_key": self.app_key,
#                 "Content-type": "application/json"
#             },
#             json=payload,
#             timeout=60
#         )

#         if response.status_code != 200:
#             logger.error(f"Mathpix API error: {response.text}")
#             raise RuntimeError(f"Mathpix API request failed: {response.text}")

#         data = response.json()
#         latex = data.get("latex_styled", "")
#         logger.info(f"🧮 Extracted LaTeX: {latex}")
#         return latex


# # Singleton instance
# try:
#     math_ocr_service = MathOCRService()
# except Exception as e:
#     math_ocr_service = None
#     logger.error(f"MathOCRService failed to initialize: {e}")

# app/services/mathocr_service.py
# app/services/math_ocr_service.py
import os
import time
import re
import sympy as sp
from dotenv import load_dotenv
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials

load_dotenv()

class MathOCRService:
    def __init__(self):
        key = os.getenv("AZURE_VISION_KEY")
        endpoint = os.getenv("AZURE_VISION_ENDPOINT")

        if not key or not endpoint:
            raise ValueError("❌ Missing Azure credentials (AZURE_VISION_KEY / AZURE_VISION_ENDPOINT).")

        self.client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))
        print("✅ Azure MathOCRService initialized successfully.")

    def _to_latex(self, text: str) -> str:
        """Convert detected math text into LaTeX."""
        try:
            cleaned = re.sub(r"[^0-9a-zA-Z+\-*/^=().]", "", text)
            expr = sp.sympify(cleaned)
            return sp.latex(expr)
        except Exception:
            return text.replace("^", "^{").replace("*", "\\times ")

    def analyze_formula(self, image_path: str):
        """Analyze image for formulas (synchronous method for your endpoint)."""
        with open(image_path, "rb") as img:
            ocr_result = self.client.read_in_stream(img, raw=True)

        operation_location = ocr_result.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]

        while True:
            result = self.client.get_read_result(operation_id)
            if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
                break
            time.sleep(1)

        extracted_text = ""
        if result.status == OperationStatusCodes.succeeded:
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    extracted_text += line.text + "\n"

        latex = self._to_latex(extracted_text)
        return latex or "No formula detected"

# Singleton instance
try:
    math_ocr_service = MathOCRService()
except Exception as e:
    print(f"⚠️ MathOCRService failed to initialize: {e}")
    math_ocr_service = None
