# # import google.generativeai as genai
# # import asyncio
# # async def structure_text_with_llm(ocr_results: dict, prompt_text: str = None):
# #     """
# #     Calls Gemini model to structure OCR text into notes, sections, and flowchart.
# #     """
# #     model = genai.GenerativeModel("gemini-2.5-flash")

# #     base_prompt = (
# #         "You are an expert visual note taker. "
# #         "Given OCR text, math formulas, and detected symbols from a whiteboard, "
# #         "create structured notes in JSON with the following keys: "
# #         "notes, sections, flowchart (nodes + edges)."
# #     )

# #     if prompt_text:
# #         full_prompt = f"{base_prompt}\n\n{prompt_text}\n\nInput JSON:\n{ocr_results}"
# #     else:
# #         full_prompt = f"{base_prompt}\n\nInput JSON:\n{ocr_results}"

# #     try:
# #         response = await asyncio.to_thread(model.generate_content, full_prompt)
# #         return response.text
# #     except Exception as e:
# #         return {"notes": f"LLM structuring failed: {str(e)}", "flowchart": {"nodes": [], "edges": []}}

# #app/services/llm_services.py# app/services/llm_services.py
# import google.generativeai as genai
# import logging
# import os
# import json
# from dotenv import load_dotenv
# import asyncio
# from typing import Dict, Any, List

# load_dotenv()
# logger = logging.getLogger(__name__)

# # ✅ Configure Gemini API key
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise RuntimeError("⚠️ GEMINI_API_KEY not found in environment variables.")

# genai.configure(api_key=GEMINI_API_KEY)

# # ✅ Use the model from your code
# MODEL_NAME = "gemini-2.5-flash"

# # -------------------------------------------------
# # Gemini Structuring Function (FIXED)
# # -------------------------------------------------
# async def structure_text_with_llm(input_data: dict, prompt_object: dict):
#     """
#     Sends the full OCR/symbol data and a specific prompt to Gemini
#     to get structured notes and a flowchart.
#     """
#     try:
#         model = genai.GenerativeModel(MODEL_NAME)

#         # Combine the prompt instruction and the data
#         prompt = f"""
# {prompt_object.get('instruction', 'Analyze the following data.')}

# INPUT DATA:
# {json.dumps(prompt_object.get('data', input_data), indent=2)}
# """

#         response = await asyncio.to_thread(
#             model.generate_content,
#             prompt,
#             # Tell Gemini to output JSON
#             generation_config=genai.types.GenerationConfig(
#                 response_mime_type="application/json"
#             )
#         )

#         raw_text = (response.text or "").strip()

#         # --- Try to parse valid JSON ---
#         try:
#             structured_output = json.loads(raw_text)
#         except json.JSONDecodeError:
#             logger.error(f"LLM output was not valid JSON. Raw text: {raw_text}")
#             # Fallback: Put the raw text in the notes
#             structured_output = {"notes": raw_text, "flowchart": {"nodes": [], "edges": []}}

#         return structured_output

#     except Exception as e:
#         logger.error(f"LLM structuring failed: {e}")
#         return {
#             "notes": f"LLM structuring failed: {str(e)}",
#             "flowchart": {"nodes": [], "edges": []}
#         }

# # -------------------------------------------------
# # Gemini Explanation Functions (NEW)
# # -------------------------------------------------
# async def get_deep_explanation(topic: str) -> str:
#     """Calls the LLM to get a deep explanation for a single topic."""
    
#     model = genai.GenerativeModel(MODEL_NAME)
    
#     system_prompt = (
#         "You are an expert educator and academic assistant. "
#         "Your goal is to provide a deep, clear, and comprehensive explanation "
#         "for the academic or technical topic provided by the user. "
#         "Structure your answer clearly with headings, bullets, or steps if appropriate. "
#         "Do not just define the term, explain it."
#     )
    
#     full_prompt = f"{system_prompt}\n\nTOPIC: {topic}"

#     # Define safety settings to be less restrictive
#     safety_settings = [
#         {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
#         {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
#         {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
#         {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
#     ]

#     try:
#         response = await asyncio.to_thread(
#             model.generate_content,
#             full_prompt,
#             generation_config=genai.types.GenerationConfig(
#                 temperature=0.7,
#                 max_output_tokens=1024
#             ),
#             safety_settings=safety_settings # <-- ADDED THIS
#         )

#         # --- DETAILED ERROR CHECKING ---
#         # Check if the response was blocked for safety
#         if not response.candidates:
#              # This happens if the prompt or response is blocked
#              finish_reason = response.prompt_feedback.block_reason
#              logger.warning(f"Explanation for '{topic}' was blocked. Reason: {finish_reason}")
#              return f"Error: Generation for '{topic}' was blocked by safety filters (Reason: {finish_reason})."

#         # Check for other abnormal finish reasons
#         if response.candidates[0].finish_reason != "STOP":
#             reason = response.candidates[0].finish_reason
#             logger.warning(f"Explanation for '{topic}' finished abnormally. Reason: {reason}")
#             return f"Error: Generation for '{topic}' failed (Reason: {reason})."
        
#         return response.text.strip()
    
#     except Exception as e:
#         # --- IMPROVED LOGGING ---
#         # Log the full exception traceback to your console
#         logger.error(f"Failed to get explanation for topic '{topic}'. Exception: {type(e).__name__}, Details: {str(e)}", exc_info=True)
#         return f"Error: Could not generate explanation for {topic} (Exception: {type(e).__name__})."
# async def get_explanations_for_nodes(nodes: List[Dict[str, Any]]) -> Dict[str, str]:
#     """
#     Gets deep explanations for a list of flowchart nodes.
#     Returns a dict mapping {node_label: explanation_text}
#     """
    
#     # Get unique topics from node labels, ignore generic/empty labels
#     unique_topics = sorted(list(set(
#         node.get("label", "").strip() 
#         for node in nodes 
#         if node.get("label") and len(node.get("label", "")) > 3 # Ignore short/empty labels
#     )))

#     if not unique_topics:
#         return {"Info": "No valid topics found in nodes to explain."}

#     tasks = []
#     for topic in unique_topics:
#         tasks.append(get_deep_explanation(topic))
        
#     explanations = await asyncio.gather(*tasks)
    
#     return dict(zip(unique_topics, explanations))

# app/services/llm_services.py# app/services/llm_services.py
import google.generativeai as genai
import logging
import os
import json
from dotenv import load_dotenv
import asyncio
from typing import Dict, Any, List
from PIL import Image
import io

load_dotenv()
logger = logging.getLogger(__name__)

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# -------------------------------------------------
# 1. VISION-BASED STRUCTURING (UPDATED PROMPT)
# -------------------------------------------------
async def structure_whiteboard_with_vision(image_bytes: bytes) -> Dict[str, Any]:
    """
    Uses Gemini's vision capability to analyze a whiteboard image and
    return structured notes, a flowchart, and key topics.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        img = Image.open(io.BytesIO(image_bytes))

        # --- THIS PROMPT IS UPDATED TO INFER EDGES AND GET TOPICS ---
        prompt = [
            "You are an expert whiteboard analyzer. Look at the provided image and perform the following tasks:\n"
            "1.  **Identify ALL text** on the image.\n"
            "2.  **Identify all arrows** (if any).\n"
            "3.  **Create a logical flowchart** based on the content.\n\n"
            "Return a single, valid JSON object with three keys:\n"
            "1.  `'notes'`: A clear, hierarchical, human-friendly summary of all the text content.\n"
            "2.  `'flowchart'`: A precise node/edge graph.\n"
            "    -   Create a 'node' for EVERY logical block of text (e.g., 'Aim', 'Step 1', 'import ...').\n"
            "    -   **CRITICAL RULE:** Create 'edges' by connecting the nodes. If you see arrows, use them. "
            "      **If there are NO arrows, INFER the logical top-to-bottom sequence** of the text blocks.\n"
            "3.  `'key_topics'`: A list of strings. These are the *main academic concepts* or *headings* from the "
            "     notes that are worth explaining (e.g., 'Experiment - 1', 'Simple Linear Regression', 'Load Dataset'). "
            "     **Do NOT include lines of code** (like 'import numpy as np') in this list.\n\n"
            "JSON SCHEMA:\n"
            "{\n"
            "  \"notes\": \"(string summary)\",\n"
            "  \"flowchart\": {\n"
            "    \"nodes\": [{\"id\": (int), \"label\": \"(string)\", \"x\": (int), \"y\": (int)}],\n"
            "    \"edges\": [{\"from\": (int_node_id), \"to\": (int_node_id)}]\n"
            "  },\n"
            "  \"key_topics\": [\"(string topic 1)\", \"(string topic 2)\"]\n"
            "}\n",
            img  # Pass the PIL image object
        ]

        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1 # Lower temperature for more predictable structure
            )
        )

        raw_text = (response.text or "").strip()
        
        try:
            structured_output = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.error(f"LLM output was not valid JSON. Raw text: {raw_text}")
            return {"notes": raw_text, "flowchart": {"nodes": [], "edges": []}, "key_topics": []}

        # Ensure all keys are present
        if 'notes' not in structured_output: structured_output['notes'] = ""
        if 'flowchart' not in structured_output: structured_output['flowchart'] = {"nodes": [], "edges": []}
        if 'key_topics' not in structured_output: structured_output['key_topics'] = []

        return structured_output

    except Exception as e:
        logger.error(f"LLM vision structuring failed: {e}", exc_info=True)
        return {
            "notes": f"LLM vision structuring failed: {str(e)}",
            "flowchart": {"nodes": [], "edges": []},
            "key_topics": []
        }

# -------------------------------------------------
# 2. FIXED DEEP EXPLANATION FUNCTION
# -------------------------------------------------
async def get_deep_explanation(topic: str) -> str:
    """Calls the LLM to get a deep explanation for a single topic."""
    
    model = genai.GenerativeModel(MODEL_NAME)
    
    system_prompt = (
        "You are an expert educator and academic assistant. "
        "Your goal is to provide a deep, clear, and comprehensive explanation "
        "for the academic or technical topic provided by the user. "
        "Structure your answer clearly with headings, bullets, or steps if appropriate. "
        "Do not just define the term, explain it."
        "**Limit your response to 2-3 short paragraphs.**"
    )
    
    full_prompt = f"{system_prompt}\n\nTOPIC: {topic}"

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    try:
        response = await asyncio.to_thread(
            model.generate_content,
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096
            ),
            safety_settings=safety_settings
        )

        # --- DETAILED ERROR CHECKING (BUG FIX) ---
        if not response.candidates:
             finish_reason = response.prompt_feedback.block_reason
             logger.warning(f"Explanation for '{topic}' was blocked. Reason: {finish_reason}")
             return f"Error: Generation for '{topic}' was blocked by safety filters (Reason: {finish_reason})."

        # ** THE BUG FIX IS HERE **
        # We must check the .name of the enum, not the enum itself
        if response.candidates[0].finish_reason.name != "STOP":
            reason = response.candidates[0].finish_reason.name
            logger.warning(f"Explanation for '{topic}' finished abnormally. Reason: {reason}")
            return f"Error: Generation for '{topic}' failed (Reason: {reason})."
        
        return response.text.strip()
    
    except Exception as e:
        logger.error(f"Failed to get explanation for topic '{topic}'. Exception: {type(e).__name__}, Details: {str(e)}", exc_info=True)
        return f"Error: Could not generate explanation for {topic} (Exception: {type(e).__name__})."

# -------------------------------------------------
# 3. RENAMED & MORE EFFICIENT EXPLANATION FUNCTION
# -------------------------------------------------
async def get_explanations_for_topics(topics: List[str]) -> Dict[str, str]:
    """
    Gets deep explanations for a specific list of topics.
    This is much more efficient and avoids rate limits.
    """
    
    if not topics:
        return {"Info": "No key topics were identified for explanation."}

    tasks = []
    for topic in topics:
        if topic and len(topic) > 3: # Final filter
            tasks.append(get_deep_explanation(topic))
        
    explanations = await asyncio.gather(*tasks)
    
    # Filter out topics that were skipped
    valid_topics = [topic for topic in topics if topic and len(topic) > 3]
    
    return dict(zip(valid_topics, explanations))