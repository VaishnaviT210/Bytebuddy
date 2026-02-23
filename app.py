import os
import psycopg2
import requests
from flask import Flask, render_template, request, redirect, session, jsonify

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE_URL = os.environ.get("DATABASE_URL")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# ---------------- DATABASE ----------------

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS placements (
        id SERIAL PRIMARY KEY,
        company TEXT,
        date TEXT,
        details TEXT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ---------------- AI FUNCTION ----------------

def get_ai_response(user_message):

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT company,date,details FROM placements;")
    data = cur.fetchall()
    cur.close()
    conn.close()

    db_info = ""
    for row in data:
        db_info += f"Company: {row[0]}, Date: {row[1]}, Details: {row[2]}\n"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {
                "role": "system",
                "content": f"You are a college placement assistant. Use this data:\n{db_info}"
            },
            {"role": "user", "content": user_message}
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )

    result = response.json()
    return result["choices"][0]["message"]["content"]

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        password = request.form["password"]

        if password == "1234":
            session["logged_in"] = True
            return redirect("/student")
        else:
            return "Invalid Password"

    return render_template("login.html")

@app.route("/admin", methods=["GET","POST"])
def admin_dashboard():

    if request.method == "POST":
        company = request.form["company"]
        date = request.form["date"]
        details = request.form["details"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO placements (company,date,details) VALUES (%s,%s,%s);",
            (company,date,details)
        )
        conn.commit()
        cur.close()
        conn.close()

    return render_template("admin_dashboard.html")

@app.route("/student")
def student_dashboard():
    if not session.get("logged_in"):
        return redirect("/login")
    return render_template("student_dashboard.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json["message"]
    reply = get_ai_response(user_msg)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
