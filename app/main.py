# app/main.py
from fastapi import FastAPI
from .routes import health
from firebase import db  # Import Firestore client
from firebase_admin import firestore

app = FastAPI(title="FlowGenix Backend")

app.include_router(health.router)

@app.get("/")
async def root():
    return {"message": "FlowGenix Backend is running 🚀"}


@app.get("/users/{user_id}")
def get_user(user_id: str):
    user_ref = db.collection("users").document(user_id).get()
    if user_ref.exists:
        return user_ref.to_dict()
    return {"error": "User not found"}


@app.get("/test-write")
def write_test():
    doc_ref = db.collection("users").document("testUser")
    doc_ref.set({
        "email": "test@example.com",
        "name": "Tester",
        "createdAt": firestore.SERVER_TIMESTAMP
    })
    return {"status": "ok"}


@app.get("/test-read")
def read_test():
    doc_ref = db.collection("users").document("testUser").get()
    if doc_ref.exists:
        return doc_ref.to_dict()
    return {"error": "not found"}
