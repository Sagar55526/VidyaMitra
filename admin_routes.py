from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from firebase_admin import firestore,credentials
from flask import jsonify
import random
import string
import smtplib
from email.mime.text import MIMEText


from auth import register, login, auth_bp
from firebase_config import initialize_firebase

db = firestore.client()



admin_bp = Blueprint('admin', __name__)


def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def send_email(to_email, password):
    sender_email = "ahiresagar06130@gmail.com"
    sender_password = "utme zvqt xgdd vgzo"
    
    subject = "🎉 Congratulations! Your Account is Now Approved 🎉"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">

        <div style="max-width: 600px; background: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);">
            <h2 style="color: #2c3e50; text-align: center;">🎉 Welcome to Our Platform! 🎉</h2>
            <p style="font-size: 16px; color: #555;">
                Dear User,
            </p>
            <p style="font-size: 16px; color: #555;">
                We are excited to inform you that your account has been successfully <b>approved</b> by the admin. 🎊  
            </p>

            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
                <p style="font-size: 18px; color: #2c3e50;"><b>🔑 Your Login Credentials</b></p>
                <p style="font-size: 16px; color: #555;"><b>Password:</b> <span style="color: #e74c3c;">{password}</span></p>
            </div>

            <p style="font-size: 16px; color: #555;">
                Please log in and update your password as soon as possible for security purposes. If you have any questions, feel free to contact our support team.
            </p>

            <p style="text-align: center; margin-top: 20px;">
                <a href="http://127.0.0.1:5000" style="display: inline-block; padding: 10px 20px; background: #3498db; color: #ffffff; text-decoration: none; font-size: 16px; border-radius: 5px;">🔐 Login Now</a>
            </p>

            <p style="font-size: 14px; color: #777; text-align: center; margin-top: 20px;">
                Best Regards,<br>
                <b>VidyaMitra Team</b> 🚀
            </p>
        </div>

    </body>
    </html>
    """

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")



@admin_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required."}), 400

        
        admin_ref = firestore.client().collection("admins").where("email", "==", email).limit(1).get()

        if admin_ref:
            admin_data = admin_ref[0].to_dict()

            if admin_data and admin_data.get("password") == password:
                
                session["admin"] = admin_data.get("email") 
                return redirect(url_for("admin.admin_dashboard"))
            else:
                return jsonify({"error": "Incorrect credentials."}), 401
        else:
            return jsonify({"error": "Admin not found."}), 404

    return render_template("admin_login.html")

from flask import jsonify
from firebase_admin import firestore

@admin_bp.route('/get_user_performance', methods=['GET'])
def get_user_performance():
    sessions_ref = firestore.client().collection("sessions").stream()
    user_data = {}

    for session in sessions_ref:
        session_dict = session.to_dict()
        user_id = session_dict.get("user_id")
        username = session_dict.get("username", "Unknown User")  

        if user_id not in user_data:
            user_data[user_id] = {
                "user_id": user_id,
                "username": username,
                "total_correct": 0,
                "total_partial": 0,
                "total_incorrect": 0,
                "total_attempted": 0,
                "total_accuracy": 0
            }

        user_data[user_id]["total_correct"] += session_dict.get("correct_answers", 0)
        user_data[user_id]["total_partial"] += session_dict.get("partial_answers", 0)
        user_data[user_id]["total_incorrect"] += session_dict.get("incorrect_answers", 0)
        user_data[user_id]["total_attempted"] += session_dict.get("questions_attempted", 0)

        
        total_attempted = user_data[user_id]["total_attempted"]
        weighted_score = (user_data[user_id]["total_correct"] * 1.0) + (user_data[user_id]["total_partial"] * 0.5)

        if total_attempted > 0:
            user_data[user_id]["total_accuracy"] = round((weighted_score / total_attempted) * 100, 2)
        else:
            user_data[user_id]["total_accuracy"] = 0

    
    users_list = list(user_data.values())

    users_list = sorted(users_list, key=lambda x: (-x["total_accuracy"], -x["total_attempted"]))

    # Assign ranks
    for rank, user in enumerate(users_list, start=1):
        user["rank"] = rank

    return jsonify({"user_performance": users_list})




@admin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    
    prn_users_ref = firestore.client().collection("PRNUsers").stream()
    prn_users = [{"id": u.id, "prnnumber": u.to_dict().get("prnnumber"), **u.to_dict()} for u in prn_users_ref]

    
    questions_ref = firestore.client().collection("questions").stream()
    questions = [{"id": q.id, **q.to_dict()} for q in questions_ref]

    if request.method == 'POST' and 'add_question' in request.form:
        question = request.form.get("question")
        model_answer = request.form.get("model_answer")

        if not question or not model_answer:
            flash('Question and model answer are required.')
        else:
            firestore.client().collection("questions").add({
                "question": question,
                "model_answer": model_answer
            })
            flash('Question added successfully.')

    return render_template('admin_dashboard.html', questions=questions, users=prn_users)

@admin_bp.route('/admin/update_user_status/<string:user_id>/<string:action>', methods=['POST'])
def update_user_status(user_id, action):
    user_ref = firestore.client().collection("PRNUsers").document(user_id)
    user = user_ref.get()

    if not user.exists:
        flash("User not found!", "error")
        return redirect(url_for('admin.admin_dashboard'))

    if action == "accept":
        new_password = generate_random_password()
        # hashed_password = hash_password(new_password)  

        user_ref.update({
            "status": "Accepted",
            "password": new_password 
        })

        send_email(user.to_dict().get("email"), new_password) 

        flash("User accepted successfully and password sent!", "success")

    elif action == "reject":
        user_ref.update({"status": "Rejected"})
        flash("User rejected successfully!", "error")

    else:
        flash("Invalid action!", "error")

    return redirect(url_for('admin.admin_dashboard'))




@admin_bp.route("/get_subjects", methods=["GET"])
def get_subjects():
    subjects = set()  

    try:
        collections = db.collections()
        for collection in collections:
            subjects.add(collection.id)  

        return jsonify(sorted(subjects)) 

    except Exception as e:
        print(f"Error fetching subjects: {str(e)}")  
        return jsonify({"error": "Failed to fetch subjects"}), 500


@admin_bp.route("/add_subject", methods=["POST"])
def add_subject():
    data = request.json
    subject_name = data.get("subject", "").strip()

    if not subject_name:
        return jsonify({"success": False, "message": "Subject name required"}), 400

    try:
        existing_collections = {col.id for col in db.collections()}
        if subject_name in existing_collections:
            return jsonify({"success": False, "message": "Subject already exists"}), 400

        
        db.collection(subject_name).document("placeholder").set({"info": "This is a placeholder document."})

        return jsonify({"success": True, "message": "Subject created successfully!"})

    except Exception as e:
        print(f"Error adding subject: {str(e)}")  
        return jsonify({"success": False, "message": "Error creating subject"}), 500


@admin_bp.route('/admin/add_question', methods=['POST'])
def add_question(): 
    data = request.json
    subject = data.get("subject", "").strip()
    question = data.get("question", "").strip()
    model_answer = data.get("model_answer", "").strip()
    numeric = data.get("numeric", False)  
    difficulty = data.get("difficulty", "").strip()

    if not subject or not question or not model_answer or not difficulty:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    try:
        
        existing_collections = {col.id for col in db.collections()}
        if subject not in existing_collections:
            return jsonify({"success": False, "message": "Invalid subject"}), 400

        
        db.collection(subject).add({
            "question": question,
            "model_answer": model_answer,
            "numeric": numeric,
            "difficulty": difficulty
        })

        return jsonify({"success": True, "message": "Question added successfully!"})

    except Exception as e:
        print(f"Error adding question: {str(e)}")  
        return jsonify({"success": False, "message": "Error adding question"}), 500


@admin_bp.route("/get_questions", methods=["GET"])
def get_questions():
    subject = request.args.get("subject") 

    if not subject:
        return jsonify([])  

    try:
        questions_ref = db.collection(subject).stream()  

        questions = []
        for doc in questions_ref:
            data = doc.to_dict()
            data["id"] = doc.id  
            questions.append(data)

        return jsonify(questions) 

    except Exception as e:
        print(f"Error fetching questions: {str(e)}") 
        return jsonify({"error": "Failed to fetch questions"}), 500



@admin_bp.route('/admin/edit_question/<string:question_id>', methods=['POST'])
def edit_question(question_id):
    subject = request.form.get("subject")  

    if not subject:
        flash("Invalid subject", "error")
        return redirect(url_for('admin.admin_dashboard'))

    try:
        question_ref = db.collection(subject).document(question_id)
        question = question_ref.get()

        if not question.exists:
            flash("Question not found", "error")
            return redirect(url_for('admin.admin_dashboard'))

        
        updated_question = request.form.get('question')
        updated_answer = request.form.get('model_answer')
        is_numeric = 'numeric' in request.form 
        difficulty = request.form.get('difficulty')

        if updated_question and updated_answer and difficulty:
            question_ref.update({
                'question': updated_question,
                'model_answer': updated_answer,
                'numeric': is_numeric,
                'difficulty': difficulty
            })
            flash('Question updated successfully.', 'success')
            return redirect(url_for('admin.admin_dashboard'))

        flash('All fields are required.', 'error')

    except Exception as e:
        print(f"Error updating question: {str(e)}")  
        flash("Error updating question.", "error")

    return redirect(url_for('admin.edit_question_page', id=question_id, subject=subject))




@admin_bp.route('/admin/delete_question', methods=['POST'])
def delete_question():
    subject = request.args.get("subject", "").strip()
    question_id = request.args.get("id", "").strip()

    if not subject or not question_id:
        return jsonify({"success": False, "message": "Subject and Question ID are required"}), 400

    try:
        
        existing_collections = [col.id for col in db.collections()]
        print("Existing collections:", existing_collections) 

        if subject not in existing_collections:
            return jsonify({"success": False, "message": "Invalid subject"}), 400

        
        question_ref = db.collection(subject).document(question_id)
        doc = question_ref.get()

        if doc.exists:
            question_ref.delete()
            return jsonify({"success": True, "message": "Question deleted successfully!"})
        else:
            return jsonify({"success": False, "message": "Question not found"}), 404

    except Exception as e:
        print(f"Error deleting question: {str(e)}") 
        return jsonify({"success": False, "message": "Error deleting question"}), 500



@admin_bp.route('/admin/edit_question', methods=['GET'])
def edit_question_page():
    question_id = request.args.get("id")
    subject = request.args.get("subject")

    if not question_id or not subject:
        return "Invalid request", 400

    try:
        doc_ref = db.collection(subject).document(question_id)  
        question_data = doc_ref.get()

        if not question_data.exists:
            return "Question not found", 404

        return render_template("edit_question.html", question=question_data.to_dict(), question_id=question_id, subject=subject)

    except Exception as e:
        print(f"Error fetching question: {str(e)}")  
        return "Internal Server Error", 500




@admin_bp.route('/admin/update_question', methods=['POST'])
def update_question():
    try:
        
        if not request.is_json:
            return jsonify({"success": False, "message": "Request must be JSON"}), 400

        data = request.get_json()

        question_id = data.get('id')
        subject = data.get('subject')  
        question_text = data.get('question')
        model_answer = data.get('model_answer')
        numeric = data.get('numeric')
        difficulty = data.get('difficulty')

        if not question_id or not subject:
            return jsonify({"success": False, "message": "Missing question ID or subject"}), 400

        
        question_ref = db.collection(subject).document(question_id)

        
        question_doc = question_ref.get()
        if not question_doc.exists:
            return jsonify({"success": False, "message": "Question not found"}), 404

        
        question_ref.update({
            "question": question_text,
            "model_answer": model_answer,
            "numeric": numeric,
            "difficulty": difficulty
        })

        return jsonify({"success": True, "message": "Question updated successfully!"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500