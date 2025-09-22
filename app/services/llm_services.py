import httpx
import json
from app.config import settings

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


async def structure_text_with_llm(ocr_results: list[dict]) -> dict:
    """Sends raw OCR results to the Gemini API for structuring."""

    full_text = "\n".join([result["text"] for result in ocr_results])

    prompt = f"""
    Analyze the following text extracted from a whiteboard. It might contain errors from the OCR process.
    Your task is to:
    1. Clean up the text, correcting any obvious OCR mistakes and grammatical errors.
    2. Structure the cleaned text into a logical JSON object.
    3. The JSON object must have a "title" (string) and a list of "items" (array of objects).
    4. Each item in the list must have a "type" (e.g., "heading", "bullet_point", "code_block") and "content" (string).

    Do not add any explanations or markdown formatting like ```json around your response.
    Only return the raw JSON object.

    Here is the raw text:
    ---
    {full_text}
    ---
    """

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": settings.GEMINI_API_KEY,
    }

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    timeout = httpx.Timeout(30.0, connect=10.0)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GEMINI_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()

            llm_response_data = response.json()

            # --- DEBUGGING STEP ---
            # The line below will print the full JSON response from Gemini to your terminal.
            # This is the key to finding the error.
            print("--- Full Gemini API Response ---")
            print(json.dumps(llm_response_data, indent=2))
            print("---------------------------------")

            # --- CRITICAL PARSING LOGIC ---
            # The error is almost certainly happening on the line below because the
            # structure of the response is not what we expect.
            try:
                generated_text = llm_response_data['candidates'][0]['content']['parts'][0]['text']
                structured_content = json.loads(generated_text)
                return structured_content
            except (KeyError, IndexError) as e:
                print("Response format mismatch. Full response below:")
                print(json.dumps(llm_response_data, indent=2))
                raise


        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - Body: {e.response.text}")
            raise Exception("Failed to get a valid response from the LLM API.")

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Failed to parse LLM response. The JSON structure is likely WRONG. Error: {e}")
            raise Exception("The LLM returned a malformed or unexpected response.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise Exception("An unexpected error occurred while contacting the LLM.")