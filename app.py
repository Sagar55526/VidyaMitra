# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import random
from similarity import calculate_similarity
from pre_processing import preprocess_text
from gemini_test import compare_answers
from sentence_transformers import SentenceTransformer, util
import google.generativeai as genai
from grading import grade_answer
import json
from session_manager import update_session, start_user_session
from firebase_config import initialize_firebase
from analysis import get_user_analysis
import admin_routes

# utme zvqt xgdd vgzo


from auth import register, login, auth_bp


app = Flask(__name__)
app.secret_key = "your_secret_key"
db = initialize_firebase()
# Firebase Initialization (already done in auth.py)
# cred = credentials.Certificate("C:/Users/ahire/Downloads/dialogflow-quiz-bot-firebase-adminsdk-fbsvc-3028d3753f.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

app.register_blueprint(auth_bp, url_prefix='/auth') 
app.register_blueprint(admin_routes.admin_bp)
semantic_model = SentenceTransformer("all-mpnet-base-v2")

@app.route('/')
def landing():
    # If the user is logged in (i.e., has 'user_id' in session), redirect to the index page
    if 'user_id' in session:
        return redirect(url_for('auth.index'))  
    return render_template('home.html') 

# Index page (only accessible to logged-in users)
@app.route('/index')
def index():
    if 'user_id' not in session:  
        return redirect(url_for('auth.login'))  
    return render_template('index.html')  

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/analysis')
def analysis_page():
    return render_template('analysis.html')

@app.route('/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  
    return redirect(url_for('landing'))  

@app.route('/user_analysis', methods=['GET'])
def user_analysis():
    return get_user_analysis()  

@app.route('/chat', methods=['POST'])
def chat():
    try:
        req = request.get_json()
        if not req or "message" not in req:
            return jsonify({"error": "Invalid request format."}), 400
        
        user_message = req["message"].strip().lower()

        if "user_id" not in session:
            return jsonify({"error": "User not logged in"}), 403

        user_id = session["user_id"]

        if user_message in ["start quiz", "next question"]:
            start_user_session(user_id)
            return send_random_question()
        else:
            
            if session.get("numeric", False):  
                return evaluate_user_numeric_answer(user_message, user_id)
            else:
                return evaluate_user_answer(user_message, user_id)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/send_random_question', methods=['POST'])
def send_random_question():
    try:
        if "user_id" not in session:
            return jsonify({"error": "User not logged in"}), 401

        user_id = session["user_id"]
        data = request.get_json()
        subject = data.get("subject")

        if not subject:
            return jsonify({"error": "No subject selected"}), 400

        
        questions_ref = db.collection(subject).stream()
        questions = [doc.to_dict() for doc in questions_ref]

        if not questions:
            return jsonify({"reply": "No questions available for the selected subject."}), 404

        random_question = random.choice(questions)
        session["last_question"] = random_question.get("question", "No question found")
        session["model_answer"] = random_question.get("model_answer", "No answer found")
        session["difficulty"] = random_question.get("difficulty", "Unknown")
        session["numeric"] = random_question.get("numeric", False) 

        return jsonify({"reply": session["last_question"]})

    except Exception as e:
        return jsonify({"error": f"Failed to fetch question: {str(e)}"}), 500


genai.configure(api_key="AIzaSyAQjrz2GIJSame8yuxg2IJ1nmt_6s3Ad5s")

def generate_hint(model_answer, user_answer):
    HINT_COST = 10  

    query = f"""
    The user provided an answer: '{user_answer}', but it's not fully correct. 
    The expected model answer is: '{model_answer}'.
    
    Provide a short, helpful hint (1-2 sentences) to guide the user 
    closer to the correct answer without revealing the full model answer.
    """

    try:
        response = genai.GenerativeModel("gemini-1.5-flash-latest").generate_content(query)
        hint_text = response.text.strip()  
        return hint_text
    except Exception as e:
        return "⚠️ Unable to generate hint at the moment. Try again later."

@app.route('/get_hint', methods=['POST'])
def get_hint():
    if "model_answer" not in session:
        return jsonify({"reply": "Start the quiz first by clicking 'Next question'."}), 400

    model_answer = session["model_answer"]
    user_answer = session.get("last_user_answer", "")
    hint = generate_hint(model_answer, user_answer)

    return jsonify({
        "hint": hint
    })



@app.route('/get_subjects', methods=['GET'])
def get_subjects():
    try:
        subjects = [collection.id for collection in db.collections()] 
        return jsonify(subjects)  
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch subjects: {str(e)}"}), 500




@app.route('/get_questions', methods=['GET'])
def get_question_answers():
    subject_name = request.args.get('subject')  
    if not subject_name:
        return jsonify({"error": "No subject provided"}), 400

    collection_name = f"subject_{subject_name}"  
    questions_ref = db.collection(collection_name)  

    try:
        questions = []
        docs = questions_ref.stream() 
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id  
            questions.append(data)

        if not questions:
            return jsonify({"message": "No questions available for the selected subject."}), 200

        return jsonify(questions)  

    except Exception as e:
        return jsonify({"error": f"Failed to fetch questions: {str(e)}"}), 500




def evaluate_user_numeric_answer(user_answer, user_id):
    """Evaluate numeric answers using Gemini with enhanced unit conversion and tolerance handling."""
    if "model_answer" not in session:
        return jsonify({"reply": "Start the quiz first by clicking 'Next question'."}), 400

    model_answer = session["model_answer"]

    try:
        query = f"""
        The user provided a numerical answer: '{user_answer}' for which the correct model answer is: 

        The correct numerical answer is: '{model_answer}'.

        Your task:
        - firstly convert both answers to respective SI unit and then check whether user answer is correct with respect to model answer while considering further tasks also.
        - if unit is missing in user answer respond with false
        - Consider equivalent unit conversions (e.g., "1.5 meters" = "150 cm").
        - Allow small rounding variations (e.g., if correct is "1.6316", accept "1.6314").
        - Normalize different number formats (e.g., "two degree Celsius" = "2°C").
        - Accept equivalent representations (e.g., "2 degrees Celsius" = "2°C").
        - If the user's answer is **numerically equivalent** to the correct answer within reasonable precision, respond with 'true'. Otherwise, respond with 'false'.
        - Only return 'true' or 'false' and nothing else.
        """

        response = genai.GenerativeModel("gemini-1.5-flash-latest").generate_content(query)
        gemini_result = response.text.strip().lower()

        if "true" in gemini_result:
            evaluation_result = "✅ Correct"
            response_message = f"{evaluation_result}\n\n📖 Model Answer: {model_answer}"
        else:
            evaluation_result = "❌ Incorrect"
            response_message = evaluation_result  

        
        update_session(user_id, session["last_question"], model_answer, user_answer, evaluation_result, session["difficulty"])

        return jsonify({"reply": response_message})

    except Exception as e:
        return jsonify({"error": f"Numeric evaluation failed: {str(e)}"}), 500




def evaluate_user_answer(user_answer, user_id):
    if "model_answer" not in session:
        return jsonify({"reply": "Start the quiz first by clicking 'Next question'."}), 400

    model_answer = session["model_answer"]
    
    clean_user_answer = preprocess_text(user_answer)
    clean_model_answer = preprocess_text(model_answer)

    try:
        gemini_result = compare_answers(model_answer, user_answer)
        similarity_score = calculate_similarity(clean_user_answer, clean_model_answer)
        word_count = len(user_answer.split())

        evaluation_result = "❌ Incorrect"
        response_message = "Your answer is incorrect. Try again!"
        points_earned = 0
        grading_result = None

        if gemini_result == "TRUE":
            if similarity_score >= 0.65:
                evaluation_result = "✅ Correct"
                points_earned = 10
                grading_result = grade_answer(model_answer, user_answer)
                response_message = f"Great job! Your answer is correct! 🎉\n\n📖 Model Answer: {model_answer}"
            elif 0.50 <= similarity_score < 0.65 and word_count >= 3:
                evaluation_result = "🤔 Partially Correct"
                points_earned = 5
                grading_result = grade_answer(model_answer, user_answer)
                response_message = "You're on the right track! Keep refining your answer."

        if grading_result:
            response_message += f"\n\n📝 GRADE: {grading_result}"

        response = f"{evaluation_result}\n\n{response_message}"
        print(gemini_result)
        print(similarity_score)

        difficulty = session.get("difficulty", "Unknown")

        # Log the answer in Firestore (separate per user)
        update_session(user_id, session["last_question"], model_answer, user_answer, evaluation_result, difficulty)

        return jsonify({"reply": response})

    except Exception as e:
        return jsonify({"error": f"Evaluation failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)


# swapnil pingale
# alphasense