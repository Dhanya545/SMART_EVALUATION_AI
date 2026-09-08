from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pytesseract
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from fuzzywuzzy import fuzz
import os, re, tempfile, json
from datetime import datetime

# ----------------- Flask App -----------------
app = Flask(__name__)
app.secret_key = "your_secret_key_here"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ----------------- Users -----------------
USERS_FILE = "users.json"
EVAL_FILE = "evaluations.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def verify_user(username, password):
    users = load_users()
    if username in users:
        return check_password_hash(users[username]['password'], password)
    return False

# ----------------- Evaluations -----------------
def load_evaluations():
    if os.path.exists(EVAL_FILE):
        with open(EVAL_FILE, "r") as f:
            return json.load(f)
    return []

def save_evaluation(data):
    evaluations = load_evaluations()
    evaluations.append(data)
    with open(EVAL_FILE, "w") as f:
        json.dump(evaluations, f)

# ----------------- Flask-Login User -----------------
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ----------------- Routes -----------------
# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']

        users = load_users()
        if username in users:
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        users[username] = {
            "fullname": fullname,
            "password": generate_password_hash(password)
        }
        save_users(users)
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            user = User(username)
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password!", "danger")
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

# ----------------- AI Evaluator -----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def load_model_answers(file_path):
    model_answers = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        sections = re.split(r"Sentence Database\s+[A-Za-z0-9\-\(\)]+", content)
        sections = [s.strip() for s in sections if s.strip()]
        for i, section in enumerate(sections, start=1):
            model_answers[f"Answer {i}"] = section
    except Exception as e:
        print("Error loading model answers:", e)
    return model_answers

def clean_text(txt):
    txt = txt.lower()
    txt = re.sub(r'[^a-z0-9\s]', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt)
    return txt.strip()

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
@login_required
def evaluate():
    try:
        if 'image' not in request.files or 'model_file' not in request.files:
            return jsonify({'error': 'Both image and model file are required'}), 400

        image = request.files['image']
        model_file = request.files['model_file']

        if image.filename == '' or model_file.filename == '':
            return jsonify({'error': 'Missing file(s)'}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
            image.save(temp_img.name)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_txt:
            model_file.save(temp_txt.name)

        extracted_text = pytesseract.image_to_string(Image.open(temp_img.name))
        os.remove(temp_img.name)

        if not extracted_text.strip():
            os.remove(temp_txt.name)
            return jsonify({'error': 'No text detected in image'}), 400

        model_answers = load_model_answers(temp_txt.name)
        os.remove(temp_txt.name)
        if not model_answers:
            return jsonify({'error': 'No valid answers found in uploaded file'}), 400

        extracted_clean = clean_text(extracted_text)
        model_clean = [clean_text(a) for a in model_answers.values() if a.strip()]

        vectorizer = CountVectorizer().fit_transform([extracted_clean] + model_clean)
        similarities = cosine_similarity(vectorizer[0:1], vectorizer[1:]).flatten()
        fuzzy_scores = [fuzz.ratio(extracted_clean, a) / 100 for a in model_clean]

        combined_scores = [(0.7 * cos + 0.3 * fuzz_s) for cos, fuzz_s in zip(similarities, fuzzy_scores)]
        best_index = combined_scores.index(max(combined_scores))
        best_match = list(model_answers.keys())[best_index]
        similarity_score = combined_scores[best_index] * 100

        if similarity_score > 75: marks = "10/10"
        elif similarity_score > 55: marks = "8/10"
        elif similarity_score > 35: marks = "6/10"
        elif similarity_score > 20: marks = "4/10"
        else: marks = "2/10"

        result = {
            "text": extracted_text.strip(),
            "best_match": best_match,
            "similarity": f"{similarity_score:.2f}%",
            "marks": marks
        }

        # Save evaluation for user
        save_evaluation({
            "username": current_user.id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "best_match": best_match,
            "similarity": f"{similarity_score:.2f}%",
            "marks": marks
        })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----------------- Dashboard -----------------
@app.route('/dashboard')
@login_required
def dashboard():
    evaluations = load_evaluations()
    user_evals = [e for e in evaluations if e['username'] == current_user.id]
    return render_template('dashboard.html', evaluations=user_evals)

# ----------------- Run App -----------------
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
