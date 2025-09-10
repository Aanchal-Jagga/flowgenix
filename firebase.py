import firebase_admin
from firebase_admin import credentials, firestore
import os

# Load Firebase service account key
cred = credentials.Certificate("serviceAccountKey.json")  
firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()
