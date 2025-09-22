from fastapi import APIRouter, Depends
from firebase_config import db, verify_token

router = APIRouter(prefix="/users", tags=["Users"])

# Get all users
@router.get("/")
def get_users(user=Depends(verify_token)):
    """
    Returns all users.
    Authorization header: Bearer <id_token>
    """
    docs = db.collection("users").stream()
    return [doc.to_dict() for doc in docs]

# Update profile
@router.post("/update-profile")
def update_profile(name: str, user=Depends(verify_token)):
    """
    Updates logged-in user's name.
    Authorization header: Bearer <id_token>
    """
    db.collection("users").document(user["uid"]).update({"name": name})
    return {"message": "Profile updated"}
