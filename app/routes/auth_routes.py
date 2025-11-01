# from fastapi import APIRouter, HTTPException
# import requests
# import os
# import firebase_admin
# from firebase_admin import credentials, firestore, auth as admin_auth

# router = APIRouter(prefix="/auth", tags=["Auth"])

# # 🔹 Firebase Config
# FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
# FIREBASE_REST_URL = "https://identitytoolkit.googleapis.com/v1/accounts"

# # Firestore client
# if not firebase_admin._apps:
#     cred = credentials.Certificate("serviceAccountKey.json")
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

# # 🔹 Signup
# @router.post("/signup")
# def signup(name: str, email: str, password: str):
#     url = f"{FIREBASE_REST_URL}:signUp?key={FIREBASE_API_KEY}"
#     res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
#     if res.status_code != 200:
#         raise HTTPException(status_code=400, detail=res.json())

#     data = res.json()
#     user_id = data["localId"]

#     # Save user to Firestore with name
#     db.collection("users").document(user_id).set({
#         "email": email,
#         "name": name
#     })

#     # Send verification email
#     verify_url = f"{FIREBASE_REST_URL}:sendOobCode?key={FIREBASE_API_KEY}"
#     requests.post(verify_url, json={"requestType": "VERIFY_EMAIL", "idToken": data["idToken"]})

#     return {"message": "Signup successful. Verification email sent.", "idToken": data["idToken"],"userId": user_id, "name": name}


# # 🔹 Login
# @router.post("/login")
# def login(email: str, password: str):
#     url = f"{FIREBASE_REST_URL}:signInWithPassword?key={FIREBASE_API_KEY}"
#     res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
#     if res.status_code != 200:
#         raise HTTPException(status_code=400, detail=res.json())

#     data = res.json()

#     # Check if email is verified
#     decoded = admin_auth.verify_id_token(data["idToken"])
#     if not decoded.get("email_verified", False):
#         raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

#     # Fetch name from Firestore
#     user_doc = db.collection("users").document(data["localId"]).get()
#     name = user_doc.to_dict().get("name") if user_doc.exists else None

#     return {
#         "message": "Login successful",
#         "token": data["idToken"],
#         "userId": data["localId"],
#         "name": name
#     }


# # 🔹 Forgot Password
# @router.post("/forgot-password")
# def forgot_password(email: str):
#     url = f"{FIREBASE_REST_URL}:sendOobCode?key={FIREBASE_API_KEY}"
#     res = requests.post(url, json={"requestType": "PASSWORD_RESET", "email": email})
#     if res.status_code != 200:
#         raise HTTPException(status_code=400, detail=res.json())
#     return {"message": "Password reset email sent"}


# # 🔹 Send verification email (manual trigger)
# @router.post("/verify-email")
# def send_verification_email(token: str):
#     url = f"{FIREBASE_REST_URL}:sendOobCode?key={FIREBASE_API_KEY}"
#     res = requests.post(url, json={"requestType": "VERIFY_EMAIL", "idToken": token})
#     if res.status_code != 200:
#         raise HTTPException(status_code=400, detail=res.json())
#     return {"message": "Verification email sent. Please check your inbox."}


# # 🔹 Get Current User
# @router.get("/me")
# def get_current_user(token: str):
#     try:
#         decoded = admin_auth.verify_id_token(token)
#         user_record = admin_auth.get_user(decoded["uid"])
#         user_doc = db.collection("users").document(decoded["uid"]).get()
#         user_data = user_doc.to_dict() if user_doc.exists else {}

#         return {
#             "uid": user_record.uid,
#             "email": user_record.email,
#             "email_verified": user_record.email_verified,
#             "name": user_data.get("name")
#         }
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

