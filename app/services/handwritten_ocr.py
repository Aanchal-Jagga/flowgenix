import cv2
import numpy as np
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# Load model + processor
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

def preprocess_image(image_path: str) -> Image.Image:
    """
    Preprocess the image to improve OCR accuracy.
    Steps:
    - Convert to grayscale
    - Remove noise
    - Threshold (binarization)
    - Resize for better clarity
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Denoise
    img = cv2.fastNlMeansDenoising(img, h=30)

    # Threshold (black & white)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Resize to ensure readability (keep aspect ratio)
    height, width = img.shape
    if width < 800:
        scale = 800 / width
        img = cv2.resize(img, (int(width * scale), int(height * scale)))

    # Convert back to PIL
    pil_img = Image.fromarray(img).convert("RGB")
    return pil_img


def extract_handwritten_text(image_path: str) -> str:
    try:
        # Preprocess image
        image = preprocess_image(image_path)

        # OCR
        pixel_values = processor(images=image, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return text.strip()
    except Exception as e:
        return f"Error: {e}"
