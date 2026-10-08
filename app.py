import os
import json
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import mysql.connector as mysql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Database Configuration (loaded safely from environment variables)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "codelogic_db"),
    "port": int(os.getenv("DB_PORT", 3306))
}

# AI Engine Configuration
AI_API_URL = os.getenv("AI_API_URL", "https://openrouter.ai/api/v1/chat/completions")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-3.5-turbo")


def get_db_connection():
    """Establish and return a connection to MySQL database."""
    return mysql.connect(**DB_CONFIG)


def verify_answer(question: str, user_answer: str) -> str:
    """
    Evaluates student answer logic against the CBSE Class 12 standard.
    Instructs the LLM to verify conceptual and logical correctness,
    disregarding purely syntactic variations, and outputs the optimal solution.
    """
    prompt = (
        f"Verify whether the correct answer to the question '{question}' is '{user_answer}' or not in python, "
        f"according to the class 12 CBSE board syllabus. "
        f"If correct, return 'Correct'. If incorrect, return 'Incorrect'. "
        f"Also provide the most optimal solution in python according CBSE class 12 board syllabus "
        f"and explain it regardless but without including the word correct in the explanation."
    )

    headers = {
        "Content-Type": "application/json"
    }
    if AI_API_KEY:
        headers["Authorization"] = f"Bearer {AI_API_KEY}"

    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(AI_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        return "Verification completed, but no detailed output received."

    except requests.exceptions.RequestException as e:
        # Fallback explanation if API is unreachable during offline testing
        return (
            f"[AI Service Notice] Could not reach AI verification endpoint ({str(e)}). "
            f"Please verify your AI_API_KEY and AI_API_URL in .env."
        )


# ==========================================
# Authentication & User Management Routes
# ==========================================

@app.route('/api/login', methods=['POST'])
def login():
    """
    Handles user authentication.
    If the user does not exist, registers them automatically with progress starting at question 1.
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor()

        cursor.execute("SELECT name, password, currentq FROM userinfo WHERE name = %s", (username,))
        result = cursor.fetchone()

        if result is None:
            # New user registration
            cursor.execute(
                "INSERT INTO userinfo (name, password, currentq) VALUES (%s, %s, %s)",
                (username, password, 1)
            )
            con.commit()
            currentq = 1
        elif result[1] == password:
            # Successful login
            currentq = result[2]
        else:
            cursor.close()
            con.close()
            return jsonify({"error": "Invalid password"}), 401

        cursor.close()
        con.close()

        return jsonify({
            "success": True,
            "username": username,
            "current_question": currentq
        })

    except mysql.Error as err:
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


# ==========================================
# Question & Evaluation Routes
# ==========================================

@app.route('/api/question', methods=['GET'])
def get_question():
    """Fetches the user's current question based on saved database progress."""
    username = request.args.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor()

        cursor.execute("SELECT currentq FROM userinfo WHERE name = %s", (username,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            con.close()
            return jsonify({"error": "User not found"}), 404

        currentq = result[0]

        cursor.execute("SELECT question_text, reference_answer FROM questions LIMIT %s, 1", (currentq - 1,))
        question_data = cursor.fetchone()
        cursor.close()
        con.close()

        if not question_data:
            return jsonify({
                "success": True,
                "completed": True,
                "message": "All questions completed! Great job!"
            })

        return jsonify({
            "success": True,
            "question_number": currentq,
            "question": question_data[0],
            "reference_answer": question_data[1] if len(question_data) > 1 else None
        })

    except mysql.Error as err:
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    """
    Evaluates the submitted code answer using AI logic verification.
    If the logic is correct, advances the user's progress in the database.
    """
    data = request.get_json() or {}
    username = data.get('username')
    answer = data.get('answer')

    if not username or not answer:
        return jsonify({"error": "Username and answer are required"}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor()

        cursor.execute("SELECT currentq FROM userinfo WHERE name = %s", (username,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            con.close()
            return jsonify({"error": "User not found"}), 404

        currentq = result[0]

        cursor.execute("SELECT question_text FROM questions LIMIT %s, 1", (currentq - 1,))
        question_data = cursor.fetchone()

        if not question_data:
            cursor.close()
            con.close()
            return jsonify({"error": "Question not found"}), 404

        question = question_data[0]

        # Call AI verification engine
        verification_result = verify_answer(question, answer)
        is_correct = "Correct" in verification_result

        # Update user progress in database if correct
        if is_correct:
            cursor.execute(
                "UPDATE userinfo SET currentq = %s WHERE name = %s",
                (currentq + 1, username)
            )
            con.commit()

        cursor.close()
        con.close()

        return jsonify({
            "success": True,
            "correct": is_correct,
            "verification": verification_result,
            "next_question": currentq + 1 if is_correct else currentq
        })

    except mysql.Error as err:
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Returns the user's current progress percentage and question counters."""
    username = request.args.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor()

        cursor.execute("SELECT currentq FROM userinfo WHERE name = %s", (username,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            con.close()
            return jsonify({"error": "User not found"}), 404

        cursor.execute("SELECT COUNT(*) FROM questions")
        total_questions = cursor.fetchone()[0]

        cursor.close()
        con.close()

        currentq = result[0]
        percent = round(((currentq - 1) / total_questions * 100), 2) if total_questions > 0 else 0

        return jsonify({
            "success": True,
            "current_question": currentq,
            "total_questions": total_questions,
            "progress_percent": percent
        })

    except mysql.Error as err:
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


# ==========================================
# Frontend Serving Routes
# ==========================================

@app.route('/')
def index():
    """Serve the single page application."""
    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"🚀 LogicEval-AI starting on port {port} (Debug: {debug})...")
    app.run(debug=debug, host='0.0.0.0', port=port)
