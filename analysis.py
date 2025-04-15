from flask import jsonify, session
from firebase_admin import firestore
import firebase_config

db = firestore.client()

def get_user_analysis():
    """Fetch user session data and return insights for visualization."""
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 403

    user_id = session["user_id"]
    session_ref = db.collection("sessions").document(user_id)
    session_doc = session_ref.get()

    if not session_doc.exists:
        return jsonify({"error": "No session data found"}), 404

    session_data = session_doc.to_dict()

    # Extract data
    attempts = session_data.get("attempts", [])
    total_attempts = len(attempts)

    # Weight values
    correct_weight = 1.0
    partial_weight = 0.5

    # Cumulative weighted accuracy calculation
    correct_count = 0
    weighted_score = 0
    accuracy_trend = []
    attempt_labels = []

    for index, attempt in enumerate(attempts):
        result = attempt.get("result", "")

        if result == "✅ Correct":
            correct_count += 1
            weighted_score += correct_weight
        elif result == "🤔 Partially Correct":
            weighted_score += partial_weight
        
        accuracy = (weighted_score / (index + 1)) * 100  # Calculate weighted accuracy
        accuracy_trend.append(round(accuracy, 2))
        attempt_labels.append(f"Q{index + 1}")

    # Compute overall weighted accuracy
    if total_attempts > 0:
        total_accuracy = round((weighted_score / total_attempts) * 100, 2)
    else:
        total_accuracy = 0

    # Prepare structured data for individual user
    analysis_data = {
        "correct_answers": session_data.get("correct_answers", 0),
        "incorrect_answers": session_data.get("incorrect_answers", 0),
        "partial_answers": session_data.get("partial_answers", 0),
        "questions_attempted": total_attempts,
        "total_accuracy": total_accuracy,
        "attempts": attempts,
        "accuracy_trend": accuracy_trend,
        "attempt_labels": attempt_labels,
        "total_easy": session_data["total_easy"],
        "total_medium": session_data["total_medium"],
        "total_hard": session_data["total_hard"],
        "correct_easy":session_data["correct_easy"],
        "correct_medium":session_data["correct_medium"],
        "correct_hard":session_data["correct_hard"]

    }

    # Fetch leaderboard data
    users_ref = db.collection("sessions").stream()
    leaderboard = []

    for user in users_ref:
        user_data = user.to_dict()
        username = user_data.get("username", "Unknown User")  # Assuming username exists
        user_attempts = user_data.get("attempts", [])
        user_total_attempts = len(user_attempts)
        user_correct_answers = user_data.get("correct_answers", 0)
        user_partial_answers = user_data.get("partial_answers", 0)

        # Calculate weighted accuracy for leaderboard
        user_weighted_score = (user_correct_answers * correct_weight) + (user_partial_answers * partial_weight)

        if user_total_attempts > 0:
            user_accuracy = round((user_weighted_score / user_total_attempts) * 100, 2)
        else:
            user_accuracy = 0

        leaderboard.append({
            "username": username,
            "total_attempts": user_total_attempts,
            "accuracy": user_accuracy
        })

    # Sort leaderboard by accuracy, then by total attempts
    leaderboard = sorted(leaderboard, key=lambda x: (-x["accuracy"], -x["total_attempts"]))

    # Add rank to each user
    for rank, user in enumerate(leaderboard, start=1):
        user["rank"] = rank

    analysis_data["leaderboard"] = leaderboard[:10]  # Return only the top 10 users

    return jsonify(analysis_data)
