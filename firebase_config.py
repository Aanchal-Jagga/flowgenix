# import os
# from dotenv import load_dotenv
# import firebase_admin
# from firebase_admin import credentials, firestore, auth as admin_auth
# from fastapi import HTTPException, Header, Depends

# load_dotenv()

# # Initialize Firebase Admin SDK
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)

# # Firestore client
# db = firestore.client()

# # Firebase Web API Key
# FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")


# def verify_token(id_token: str = Header(..., alias="Authorization")):
#     """
#     Expects Authorization header: Bearer <id_token>
#     """
#     try:
#         if id_token.startswith("Bearer "):
#             id_token = id_token.split(" ")[1]
#         decoded = admin_auth.verify_id_token(id_token)
#         return decoded
#     except Exception:
#         raise HTTPException(status_code=401, detail="Invalid user token")
