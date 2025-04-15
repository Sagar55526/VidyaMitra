from datetime import datetime
from flask import session
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_config import initialize_firebase
import uuid
from pre_processing import preprocess_text

db = initialize_firebase()

def calculate_question_accuracy(model_answer, user_answer):
    """Calculate accuracy based on word overlap after preprocessing."""
    processed_model_answer = preprocess_text(model_answer)
    processed_user_answer = preprocess_text(user_answer)

    model_words = set(processed_model_answer.split())  
    user_words = set(processed_user_answer.split())

    if not model_words:
        return 0.0

    matched_words = model_words.intersection(user_words)
    accuracy = (len(matched_words) / len(model_words)) * 100  

    return round(accuracy, 2)


def start_user_session(user_id):
    """Ensure each user gets their own Firestore session document."""
    session_ref = db.collection("sessions").document(user_id)
    user_ref = db.collection("PRNUsers").document(user_id)

    # Fetch user data to get the username
    user_doc = user_ref.get()
    user_data = user_doc.to_dict() if user_doc.exists else {}

    username = user_data.get("username", "Unknown User")  # Default if missing

    session_data = {
        "user_id": user_id,
        "username": username,  # Store username in session
        "start_time": datetime.utcnow().isoformat(),
        "attempts": [],
        "correct_answers": 0,
        "incorrect_answers": 0,
        "partial_answers": 0,
        "questions_attempted": 0
    }

    if not session_ref.get().exists:
        session_ref.set(session_data)

    session["session_id"] = user_id
    return user_id  


def update_session(user_id, question, model_answer, user_answer, result, difficulty):
    """Update session and PRNUsers with user performance, response time, and weighted accuracy."""
    session_id = session.get("session_id", user_id)
    session_ref = db.collection("sessions").document(session_id)
    user_ref = db.collection("PRNUsers").document(user_id)

    session_doc = session_ref.get()
    if not session_doc.exists:
        start_user_session(user_id)
        session_doc = session_ref.get()

    session_data = session_doc.to_dict()

    # Fetch username again in case it's missing
    user_doc = user_ref.get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    session_data["username"] = user_data.get("username", "Unknown User")  

    accuracy = calculate_question_accuracy(model_answer, user_answer)

    session_data["attempts"].append({
        "question": question,
        "model_answer": model_answer,
        "user_answer": user_answer,
        "result": result,
        "accuracy": accuracy,
        "difficulty": difficulty
    })

    session_data["questions_attempted"] += 1

    # Initialize difficulty count fields if not present
    session_data.setdefault("correct_easy", 0)
    session_data.setdefault("correct_medium", 0)
    session_data.setdefault("correct_hard", 0)

    if result == "✅ Correct":
        session_data["correct_answers"] += 1
        if difficulty == "easy":
            session_data["correct_easy"] += 1
        elif difficulty == "medium":
            session_data["correct_medium"] += 1
        elif difficulty == "hard":
            session_data["correct_hard"] += 1
    elif result == "❌ Incorrect":
        session_data["incorrect_answers"] += 1
    elif result == "🤔 Partially Correct":
        session_data["partial_answers"] += 1


    # Initialize difficulty count fields if not present
    session_data.setdefault("total_easy", 0)
    session_data.setdefault("total_medium", 0)
    session_data.setdefault("total_hard", 0)

     # Update difficulty counts
    if difficulty == "easy":
        session_data["total_easy"] += 1
    elif difficulty == "medium":
        session_data["total_medium"] += 1
    elif difficulty == "hard":
        session_data["total_hard"] += 1


    # Weighted accuracy calculation
    correct_weight = 1.0
    partial_weight = 0.5

    weighted_score = (
        (session_data["correct_answers"] * correct_weight) +
        (session_data["partial_answers"] * partial_weight)
    )

    if session_data["questions_attempted"] > 0:
        session_data["total_accuracy"] = round(
            (weighted_score / session_data["questions_attempted"]) * 100, 2
        )
    else:
        session_data["total_accuracy"] = 0

    # Save updated session data to Firestore
    session_ref.set(session_data, merge=True)

    # Update PRNUsers collection
    updated_user_data = {
        "email": user_data.get("email", ""),
        "password": user_data.get("password", ""),
        "username": user_data.get("username", ""),
        "questions_attempted": session_data["questions_attempted"],
        "correct_answers": session_data["correct_answers"],
        "incorrect_answers": session_data["incorrect_answers"],
        "partial_answers": session_data["partial_answers"],
        "total_accuracy": session_data["total_accuracy"],
        "total_easy": session_data["total_easy"],
        "total_medium": session_data["total_medium"],
        "total_hard": session_data["total_hard"],
        "correct_easy":session_data["correct_easy"],
        "correct_medium":session_data["correct_medium"],
        "correct_hard":session_data["correct_hard"]
    }

    user_ref.set(updated_user_data, merge=True)


def end_user_session():
    """End the session by removing it from Flask session tracking."""
    session.pop("session_id", None)
