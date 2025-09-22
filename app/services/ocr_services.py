from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import cv2
import numpy as np
from spellchecker import SpellChecker

# Load model once (not on every request)
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-large-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-large-handwritten")
spell = SpellChecker()

def preprocess_image(file_bytes: bytes) -> Image.Image:
    file_bytes = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=30)

    # Threshold
    _, thresh = cv2.threshold(
        denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return Image.fromarray(thresh)

def extract_handwritten_text(image: Image.Image) -> str:
    """
    Extract handwritten text from an image using Microsoft TrOCR.
    Ensures image is converted to RGB before processing.
    """
    # 🔹 Ensure RGB format (fixes grayscale issue)
    if image.mode != "RGB":
        image = image.convert("RGB")

    pixel_values = processor(images=image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return text.strip()
def correct_text(text: str) -> str:
    corrected_words = [spell.correction(word) or word for word in text.split()]
    return " ".join(corrected_words)
