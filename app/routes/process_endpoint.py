# # from fastapi import APIRouter, UploadFile, File
# # import os
# # import asyncio 
# # from app.services.handwritten_ocr import azure_document_ai_service
# # # from app.services.handwritten_ocr import AzureDocumentAIService
# # from app.services.math_ocr_service import MathOCRService  # use singleton instance
# # from app.services.symbol_detection_service import detect_symbols
# # from app.services.export_service import merge_ocr_results , generate_notes_docx
# # from app.services.llm_services import structure_text_with_llm 

# # router = APIRouter()
# # math_ocr_service=MathOCRService()
# # # math_ocr_service is already a singleton from math_ocr_service.py
# # if math_ocr_service is None:
# #     raise RuntimeError("MathOCRService failed to initialize.")
# # @router.post("/process-whiteboard")
# # async def process_whiteboard(file: UploadFile = File(...)):
# #     temp_dir = "temp"
# #     os.makedirs(temp_dir, exist_ok=True)
# #     file_path = os.path.join(temp_dir, file.filename)
# #     with open(file_path, "wb") as f:
# #         f.write(await file.read())

# #     # 1️⃣ Azure OCR
# #     azure_result = await azure_document_ai_service.analyze_whiteboard(
# #         open(file_path, "rb").read(), file.filename
# #     )

# #     # 2️⃣ Math OCR (sync -> async)
# #     loop = asyncio.get_event_loop()
# #     latex_formulas = await loop.run_in_executor(None, math_ocr_service.analyze_formula, file_path)

# #     # 3️⃣ Symbol detection
# #     with open(file_path, "rb") as f:
# #         image_bytes = f.read()

# #     symbols_detected = detect_symbols(image_bytes)
# #     # 4️⃣ Merge OCR + formulas + symbols
# #     combined_results = merge_ocr_results(
# #         text_data=azure_result,
# #         formulas=latex_formulas,
# #         symbols=symbols_detected
# #     )
# #     llm_structured = await structure_text_with_llm(combined_results)
# #     # notes_path = generate_notes_docx(llm_structured["notes"], file.filename)
# #     notes_path = generate_notes_docx(llm_structured["notes"], file.filename)

# #     return {
# #         "status": "success",
# #         "structured_output": llm_structured,
# #         "notes_file": notes_path
# #     }

# # app/routes/process_endpoint.py
# import os
# import asyncio
# import logging
# import uuid
# from typing import Dict, Any, List

# from fastapi import APIRouter, UploadFile, File, HTTPException
# from fastapi.responses import JSONResponse

# # Import your existing services (singletons / functions)
# from app.services.handwritten_ocr import azure_document_ai_service
# from app.services.math_ocr_service import MathOCRService
# from app.services.symbol_detection_service import detect_symbols
# from app.services.export_service import merge_ocr_results, generate_notes_docx
# # UPDATED IMPORT
# from app.services.llm_services import structure_text_with_llm, get_explanations_for_nodes

# logger = logging.getLogger(__name__)
# router = APIRouter()

# math_ocr_service = MathOCRService()
# if math_ocr_service is None:
#     raise RuntimeError("MathOCRService failed to initialize.")


# def _normalize_bbox(bbox: Dict[str, float]) -> Dict[str, float]:
#     """
#     Ensure bbox contains x_min,y_min,x_max,y_max as floats.
#     Accepts either dict with these keys or polygon list.
#     """
#     if bbox is None:
#         return None
#     # already in desired format
#     if {"x_min", "y_min", "x_max", "y_max"}.issubset(bbox.keys()):
#         return {k: float(bbox[k]) for k in ("x_min", "y_min", "x_max", "y_max")}
#     # polygon/list [x1,y1,...]
#     if isinstance(bbox, (list, tuple)):
#         xs = bbox[0::2]
#         ys = bbox[1::2]
#         return {
#             "x_min": float(min(xs)),
#             "y_min": float(min(ys)),
#             "x_max": float(max(xs)),
#             "y_max": float(max(ys)),
#         }
#     return None


# def build_nodes_from_ocr_and_symbols(azure_result: Dict[str, Any], symbols: Dict[str, Any]) -> List[Dict]:
#     """
#     Heuristic node builder:
#     - Create a node for each text line / paragraph from Azure OCR
#     - Merge or prefer paragraphs when present
#     - Add symbol-label nodes for clear boxes/circles if they have no text overlap
#     Returns list of nodes with id,label,x,y (x,y are centers in image coordinates)
#     """
#     nodes = []
#     next_id = 1
#     # prefer paragraphs if available else lines
#     for page in azure_result.get("content_structure", []):
#         page_w = page.get("width", None)
#         page_h = page.get("height", None)
#         for para in page.get("paragraphs", []) or []:
#             bbox = _normalize_bbox(para.get("bounding_box"))
#             label = (para.get("content") or "").strip()
#             if not label:
#                 continue
#             cx = (bbox["x_min"] + bbox["x_max"]) / 2 if bbox else 0
#             cy = (bbox["y_min"] + bbox["y_max"]) / 2 if bbox else 0
#             nodes.append({"id": next_id, "label": label, "x": cx, "y": cy})
#             next_id += 1

#         # fallback to lines
#         for line in page.get("lines", []) or []:
#             label = (line.get("content") or "").strip()
#             bbox = _normalize_bbox(line.get("bounding_box"))
#             if not label:
#                 continue
#             cx = (bbox["x_min"] + bbox["x_max"]) / 2 if bbox else 0
#             cy = (bbox["y_min"] + bbox["y_max"]) / 2 if bbox else 0
#             nodes.append({"id": next_id, "label": label, "x": cx, "y": cy})
#             next_id += 1

#     # Add symbol-only nodes for rectangles/circles that don't overlap existing text nodes
#     sym_nodes = []
#     for sym in (symbols.get("symbols") or []):
#         stype = sym.get("type")
#         sbbox = _normalize_bbox(sym.get("bbox") or sym.get("bounding_box") or sym.get("polygon"))
#         # compute center
#         if not sbbox:
#             continue
#         cx = (sbbox["x_min"] + sbbox["x_max"]) / 2
#         cy = (sbbox["y_min"] + sbbox["y_max"]) / 2

#         # check overlap with existing nodes (simple center-in-bbox test)
#         overlaps = False
#         for n in nodes:
#             # find node bbox by approximating from x,y and a small neighborhood
#             nx, ny = n["x"], n["y"]
#             # threshold: if symbol center is within 30px of node center treat as overlap
#             if abs(nx - cx) < 30 and abs(ny - cy) < 30:
#                 overlaps = True
#                 break
#         if not overlaps:
#             label = stype if stype else "shape"
#             sym_nodes.append({"id": next_id, "label": label, "x": cx, "y": cy})
#             next_id += 1

#     nodes.extend(sym_nodes)
#     return nodes


# def build_edges_from_arrows(symbols: Dict[str, Any], nodes: List[Dict]) -> List[Dict]:
#     """
#     Heuristic edges:
#     - For each detected 'arrow' symbol, map its tail/head positions to the closest node centers.
#     - Fallback: If symbol detection provides connection points, use them.
#     Returns list of edges {from: id, to: id}
#     """
#     edges = []

#     def closest_node_id(x, y):
#         best_id = None
#         best_dist = float("inf")
#         for n in nodes:
#             dx = n["x"] - x
#             dy = n["y"] - y
#             d = (dx * dx + dy * dy) ** 0.5
#             if d < best_dist:
#                 best_dist = d
#                 best_id = n["id"]
#         return best_id

#     for sym in (symbols.get("symbols") or []):
#         if sym.get("type") != "arrow":
#             continue
#         # arrow might include 'points': [(x1,y1),(x2,y2)] or bbox
#         points = sym.get("points")
#         if points and len(points) >= 2:
#             tail = points[0]
#             head = points[-1]
#             from_id = closest_node_id(tail[0], tail[1])
#             to_id = closest_node_id(head[0], head[1])
#             if from_id and to_id and from_id != to_id:
#                 edges.append({"from": from_id, "to": to_id})
#         else:
#             bbox = _normalize_bbox(sym.get("bbox") or sym.get("bounding_box") or sym.get("polygon"))
#             if not bbox:
#                 continue
#             # assume arrow direction roughly top->bottom or left->right by bbox orientation
#             cx = (bbox["x_min"] + bbox["x_max"]) / 2
#             cy = (bbox["y_min"] + bbox["y_max"]) / 2
#             # pick two closest nodes on opposite sides
#             from_id = closest_node_id(bbox["x_min"] - 1, bbox["y_min"] - 1)
#             to_id = closest_node_id(bbox["x_max"] + 1, bbox["y_max"] + 1)
#             if from_id and to_id and from_id != to_id:
#                 edges.append({"from": from_id, "to": to_id})

#     # Deduplicate edges
#     seen = set()
#     deduped = []
#     for e in edges:
#         key = (e["from"], e["to"])
#         if key not in seen:
#             seen.add(key)
#             deduped.append(e)
#     return deduped


# def build_flowchart(nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
#     # Optionally normalize coordinates (e.g., center them) so frontend can render
#     # For now return raw nodes & edges
#     return {"nodes": nodes, "edges": edges}


# @router.post("/process-whiteboard")
# async def process_whiteboard(file: UploadFile = File(...)):
#     """
#     Full pipeline:
#       1. Save file
#       2. Azure: text + layout analysis (document AI / vision read)
#       3. Math OCR (sync wrapped)
#       4. Symbol detection (arrows, boxes, circles)
#       5. Merge results and call LLM (Gemini) to generate well-structured notes + flow structure
#       6. Build nodes/edges heuristically (fallback if LLM doesn't provide them)
#       7. **NEW: Call LLM to get deep explanations for topics**
#       8. Write .docx and return structured JSON + flowchart
#     """
#     temp_dir = "temp"
#     os.makedirs(temp_dir, exist_ok=True)
#     unique_name = f"{uuid.uuid4().hex}_{file.filename}"
#     file_path = os.path.join(temp_dir, unique_name)

#     # Save uploaded file
#     contents = await file.read()
#     if not contents:
#         raise HTTPException(status_code=400, detail="Uploaded file is empty")
#     with open(file_path, "wb") as f:
#         f.write(contents)

#     # Prepare image bytes for services
#     image_bytes = contents

#     # 1) Azure OCR / layout analysis
#     try:
#         # azure_document_ai_service is the singleton from app.services.handwritten_ocr
#         azure_result = await azure_document_ai_service.analyze_whiteboard(image_bytes, file.filename)
#         logger.info("Azure analysis done")
#     except Exception as e:
#         logger.exception("Azure analysis failed")
#         raise HTTPException(status_code=500, detail=f"Azure analysis failed: {str(e)}")

#     # 2) Math OCR (run in executor if sync)
#     loop = asyncio.get_event_loop()
#     try:
#         latex_formulas = await loop.run_in_executor(None, math_ocr_service.analyze_formula, file_path)
#     except Exception as e:
#         logger.exception("Math OCR failed")
#         latex_formulas = []

#     # 3) Symbol detection (expects bytes)
#     try:
#         symbols_detected = detect_symbols(image_bytes)
#     except Exception as e:
#         logger.exception("Symbol detection failed")
#         symbols_detected = {"symbols": []}

#     # 4) THIS IS THE DATA FOR THE LLM
#     llm_input_data = {
#         "azure_layout_data": azure_result,
#         "detected_formulas": latex_formulas,
#         "detected_symbols": symbols_detected
#     }

#     # 5) Build an LLM prompt to structure content and produce flowchart
#     #    (This prompt is now USED by the new llm_services.py)
#     prompt = {
#         "instruction": (
#             "You are an expert spatial reasoning assistant. You will receive a JSON object "
#             "containing all text, math equations, and symbols (like arrows) detected on a whiteboard, "
#             "along with their (x, y) bounding box coordinates from 'azure_layout_data'."
#             "Your task is to analyze the layout and flow to generate two things:\n"
#             "1) 'notes': A clear, hierarchical, human-friendly summary of all the text content, "
#             "   correctly formatting any LaTeX from 'detected_formulas' inline.\n"
#             "2) 'flowchart': A precise node/edge graph. Nodes must be text elements, and "
#             "   edges must represent the arrows connecting them. Use the coordinates to determine "
#             "   what an arrow points 'from' and 'to'."
#             "\n"
#             "Respond ONLY with a valid JSON object containing these two keys: {\"notes\": \"...\", \"flowchart\": {\"nodes\": [], \"edges\": []}}.\n"
#             "NODE SCHEMA: {\"id\": int, \"label\": string, \"x\": float, \"y\": float} (use center coordinates from bounding boxes)\n"
#             "EDGE SCHEMA: {\"from\": int_node_id, \"to\": int_node_id}\n"
#         ),
#         "data": llm_input_data
#     }

#     try:
#         llm_response = await structure_text_with_llm(llm_input_data, prompt_object=prompt)
#     except Exception as e:
#         logger.exception("LLM structuring failed")
#         llm_response = None

#     # 6) If LLM didn't provide flow_elements, build heuristics from OCR + symbols
#     nodes = []
#     edges = []
#     structured_notes = "" # Renamed from 'notes' for clarity
    
#     if llm_response and isinstance(llm_response, dict):
#         structured_notes = llm_response.get("notes") or llm_response.get("summary") or ""
#         flow_elements = llm_response.get("flowchart") or llm_response.get("flow_elements") or None
#         if flow_elements and isinstance(flow_elements, dict):
#             nodes = flow_elements.get("nodes", [])
#             edges = flow_elements.get("edges", [])
    
#     # fallback heuristics:
#     if not nodes:
#         nodes = build_nodes_from_ocr_and_symbols(azure_result, symbols_detected)
#     if not edges:
#         edges = build_edges_from_arrows(symbols_detected, nodes)

#     flowchart = build_flowchart(nodes, edges)

#     # If LLM didn't produce notes, produce a simple notes text by combining OCR + formulas
#     if not structured_notes:
#         text_parts = [azure_result.get("full_text", "").strip()]
#         if latex_formulas:
#             text_parts.append("Formulas:")
#             text_parts.extend(latex_formulas if isinstance(latex_formulas, list) else [str(latex_formulas)])
#         structured_notes = "\n\n".join([p for p in text_parts if p])

#     # 7) *** NEW STEP: GET DEEP EXPLANATIONS ***
#     try:
#         # We pass the nodes from the flowchart to get topics
#         deep_explanations = await get_explanations_for_nodes(flowchart.get("nodes", []))
#     except Exception as e:
#         logger.exception("Failed to get deep explanations")
#         deep_explanations = {"Error": f"Could not generate explanations: {str(e)}"}

#     # 8) Generate .docx (UPDATED CALL)
#     try:
#         notes_path = generate_notes_docx(
#             structured_notes=structured_notes,
#             explanations=deep_explanations,  # <-- NEW
#             original_filename=file.filename,
#             azure_data=azure_result
#         )
#     except Exception as e:
#         logger.exception("Generating notes docx failed")
#         notes_path = None

#     # UPDATED OUTPUT
#     structured_output = {
#         "notes": structured_notes,
#         "deep_explanations": deep_explanations, # <-- NEW
#         "llm_raw": llm_response,
#         "azure": azure_result,
#         "formulas": latex_formulas,
#         "symbols": symbols_detected
#     }

#     return JSONResponse(status_code=200, content={
#         "status": "success",
#         "structured_output": structured_output,
#         "flowchart": flowchart,
#         "notes_file": notes_path
#     })
# app/routes/process_endpoint.py
import os
import asyncio
import logging
import uuid
from typing import Dict, Any, List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# --- UPDATED IMPORTS ---
from app.services.export_service import generate_notes_docx
from app.services.llm_services import (
    structure_whiteboard_with_vision, 
    get_explanations_for_topics  # <-- RENAMED
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/process-whiteboard")
async def process_whiteboard(file: UploadFile = File(...)):
    """
    Full pipeline using Gemini Vision:
      1. Get image bytes
      2. Call Gemini Vision to get notes, flowchart (with inferred edges), AND key topics
      3. Call Gemini Text to get deep explanations for ONLY the key topics
      4. Write .docx and return structured JSON
    """
    
    # 1. Get image bytes
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    image_bytes = contents
    llm_response = None
    
    try:
        # 2. Call Gemini Vision for initial analysis
        logger.info("Calling Gemini Vision to analyze whiteboard...")
        llm_response = await structure_whiteboard_with_vision(image_bytes)
    
    except Exception as e:
        logger.exception("LLM Vision structuring failed")
        raise HTTPException(status_code=500, detail=f"LLM Vision analysis failed: {str(e)}")

    if not llm_response:
        raise HTTPException(status_code=500, detail="LLM response was empty.")

    # Extract data from the vision call
    structured_notes = llm_response.get("notes", "No structured notes generated.")
    flowchart = llm_response.get("flowchart", {"nodes": [], "edges": []})
    key_topics = llm_response.get("key_topics", []) # <-- NEW
    
    # 3. Call Gemini Text for Deep Explanations (using key_topics)
    try:
        logger.info(f"Calling Gemini Text to get deep explanations for topics: {key_topics}")
        deep_explanations = await get_explanations_for_topics(key_topics) # <-- UPDATED
    except Exception as e:
        logger.exception("Failed to get deep explanations")
        deep_explanations = {"Error": f"Could not generate explanations: {str(e)}"}

    # 4. Generate .docx (Pass empty Azure data for now)
    try:
        notes_path = generate_notes_docx(
            structured_notes=structured_notes,
            explanations=deep_explanations,
            original_filename=file.filename,
            azure_data=None 
        )
    except Exception as e:
        logger.exception("Generating notes docx failed")
        notes_path = None

    # 5. Return the final JSON response
    structured_output = {
        "notes": structured_notes,
        "deep_explanations": deep_explanations,
        "llm_raw": llm_response,
        "azure": "null (pipeline now uses Gemini Vision)",
        "formulas": "null (pipeline now uses Gemini Vision)",
        "symbols": "null (pipeline now uses Gemini Vision)"
    }

    return JSONResponse(status_code=200, content={
        "status": "success",
        "structured_output": structured_output,
        "flowchart": flowchart,
        "notes_file": notes_path
    })