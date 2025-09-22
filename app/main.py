# app/main.py
from fastapi import FastAPI
from app.routes.process_endpoint import router as  process_endpoint
from app.routes.handwritten_routes import router as handwritten_routes
from firebase_config import db  # Import Firestore client
from firebase_admin import firestore

from app.routes.auth_routes import router as auth_router
from app.routes.user_routes import router as user_router

app = FastAPI(title="FlowGenix Backend")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(process_endpoint)
app.include_router(handwritten_routes)
@app.get("/")
def root():
    return {"message": "FlowGenix API Running ✅"}
