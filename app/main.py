# app/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routes.process_endpoint import router as  process_endpoint
from app.routes.handwritten_routes import router as handwritten_routes
from firebase_config import db  # Import Firestore client
from firebase_admin import firestore

from app.routes.auth_routes import router as auth_router
from app.routes.user_routes import router as user_router
from app.routes.math_ocr_endpoint import router as process_router
from app.routes.symb import router as detect_symbol
app = FastAPI(title="FlowGenix Backend")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(process_endpoint)
app.include_router(handwritten_routes)

app.include_router(detect_symbol, prefix="/symbol", tags=["Symbol Detection"])

# app.include_router(math_ocr_endpoint.router)

app.include_router(process_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "FlowGenix API Running ✅"}
