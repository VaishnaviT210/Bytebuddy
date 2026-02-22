from flask import Flask, render_template, request, redirect, jsonify
import psycopg2
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Load environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
client = OpenAI(api_key=OPENAI_API_KEY)

# Database connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Initialize database
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE,
        password TEXT,
        role VARCHAR(20)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        package VARCHAR(50),
        drive_date DATE,
        eligibility TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# User model
class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return User(user[0], user[1], user[2], user[3])
    return None

# Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):
            user_obj = User(user[0], user[1], user[2], user[3])
            login_user(user_obj)

            if user[3] == "admin":
                return redirect("/admin")
            else:
                return redirect("/student")

    return render_template("login.html")

@app.route("/admin")
@login_required
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/student")
@login_required
def student_dashboard():
    return render_template("student_dashboard.html")

@app.route("/chat", methods=["POST"])
def chat():
    message = request.json["message"]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a placement assistant."},
            {"role": "user", "content": message}
        ]
    )

    return jsonify({"reply": response.choices[0].message.content})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
