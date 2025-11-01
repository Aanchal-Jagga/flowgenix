# import os
# from dotenv import load_dotenv
# import firebase_admin
# from firebase_admin import credentials, firestore, auth as admin_auth

# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)

# # Firestore
# db = firestore.client()

# load_dotenv()

# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)

# # Firestore client
# db = firestore.client()

# def verify_token(id_token: str):
#     """Verify Firebase ID token"""
#     try:
#         decoded = admin_auth.verify_id_token(id_token)
#         return decoded
#     except:
#         return None
