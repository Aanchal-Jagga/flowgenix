# app/dependencies.py
from firebase_config import admin_auth

def verify_token(id_token: str):
    """Verify Firebase ID token"""
    try:
        decoded = admin_auth.verify_id_token(id_token)
        return decoded
    except:
        return None
