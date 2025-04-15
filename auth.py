from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
from firebase_config import initialize_firebase

auth_bp = Blueprint('auth', __name__)

# Firebase initialization (adjust with your credentials file)
# cred = credentials.Certificate("C:/Users/ahire/Downloads/dialogflow-quiz-bot-firebase-adminsdk-fbsvc-3028d3753f.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()
db = initialize_firebase()

# Login page (POST method to handle login)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not all(k in data for k in ["prnnumber", "password"]):
        return jsonify({"error": "PRN number and password are required."}), 400

    prnnumber = data["prnnumber"]
    password = data["password"]

    user_ref = db.collection('PRNUsers').document(prnnumber)
    user = user_ref.get()

    if user.exists:
        user_data = user.to_dict()
        
        # If passwords are stored as plain text, use direct comparison
        if user_data['password'] == password:
            session['user_id'] = prnnumber
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"error": "Invalid password"}), 400
    else:
        return jsonify({"error": "User not found"}), 404


# Registration page (POST method to handle registration)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not all(k in data for k in ["username", "prnnumber", "email"]):
        return jsonify({"error": "All fields are required."}), 400

    username = data["username"]
    prnnumber = data["prnnumber"]
    email = data["email"]
    # password = data["password"]

    # Example registration logic (store in Firebase)
    user_ref = db.collection('PRNUsers').document(prnnumber)
    user = user_ref.get()
    if user.exists:
        return jsonify({"error": "User already exists."}), 400

    # Hash the password before storing it
    # hashed_password = generate_password_hash(password)

    # Save user details to Firebase (or another database)
    user_ref.set({
        'username': username,
        'email': email,
        'status': "pending",
        # 'password': hashed_password,
    })

    return jsonify({"message": "Registration successful"}), 201


@auth_bp.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('index.html')  
