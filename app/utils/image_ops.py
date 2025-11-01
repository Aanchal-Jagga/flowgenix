import cv2
import numpy as np
from io import BytesIO
from PIL import Image

def preprocess_for_symbol(image_bytes: bytes) -> bytes:
    """
    Preprocess the image to enhance symbol visibility and reduce noise.
    """
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = np.array(image)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Contrast enhancement
    gray = cv2.equalizeHist(gray)

    # Adaptive thresholding for sharper edges
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 10
    )

    # Morphological opening to clean small noise
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(cleaned, h=15)

    # Convert back to bytes
    _, buffer = cv2.imencode(".jpg", denoised)
    return buffer.tobytes()
