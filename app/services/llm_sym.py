#app/services/llm_sym.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Choose model
MODEL_NAME = "gemini-2.5-flash"   # or "gemini-1.5-pro" for better reasoning

def refine_symbols(text: str) -> str:
    """
    Uses Gemini to refine and correct OCR-recognized symbols.
    Ensures mathematical, logical, and special symbols are corrected.
    """
    prompt = f"""
    The following OCR text may contain incorrect or missing mathematical symbols.
    Please correct all errors, normalize symbols, and output only the corrected text.

    Text:
    {text}
    """

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Error] {e}")
        return text  # fallback to raw text
