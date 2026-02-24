from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
from db import get_connection
import os

app = Flask(__name__)
app.secret_key = "supersecret"
bcrypt = Bcrypt(app)

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, password, role FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        if user and bcrypt.check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["role"] = user[2]

            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT name, designation FROM faculty")
    faculty = cur.fetchall()

    cur.execute("SELECT semester, code, name FROM subjects ORDER BY semester")
    subjects = cur.fetchall()

    cur.execute("SELECT rule FROM exam_rules")
    rules = cur.fetchall()

    cur.execute("SELECT policy FROM mark_policy")
    policy = cur.fetchall()

    cur.execute("SELECT * FROM class_strength")
    strength = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        faculty=faculty,
        subjects=subjects,
        rules=rules,
        policy=policy,
        strength=strength,
        role=session["role"]
    )

# ---------------- ADMIN ADD FACULTY ----------------
@app.route("/add_faculty", methods=["POST"])
def add_faculty():
    if session.get("role") != "admin":
        return redirect("/dashboard")

    name = request.form["name"]
    designation = request.form["designation"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO faculty (name, designation, department) VALUES (%s,%s,%s)",
        (name, designation, "AI&DS")
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/dashboard")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
