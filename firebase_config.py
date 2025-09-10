import firebase_admin
from firebase_admin import credentials, firestore

# Load service account key
cred = credentials.Certificate("serviceAccountKey.json")

# Initialize app
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()
