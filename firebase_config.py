# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    # Check if Firebase is already initialized
    if not firebase_admin._apps:
        # Initialize Firebase app with your service account credentials
        cred = credentials.Certificate("C:/Users/ahire/Downloads/dialogflow-quiz-bot-firebase-adminsdk-fbsvc-3028d3753f.json")
        firebase_admin.initialize_app(cred)

    # Return Firestore client
    return firestore.client()