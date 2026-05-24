from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date
import os

app = Flask(__name__)
app.secret_key = "secret_key"


# =========================
# DATABASE PATH (RENDER SAFE)
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


# =========================
# INIT DATABASE
# =========================

def init_db():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT,
        xp INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        last_login TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task TEXT,
        subject TEXT,
        priority TEXT,
        due_date TEXT,
        completed INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# HOME ROUTE SAFETY
# =========================

@app.route("/")
def home():
    return redirect("/login")


# =========================
# SIGNUP
# =========================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        user = cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user:
            conn.close()
            return "User already exists"

        cursor.execute("""
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        """, (username, email, password))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        user = cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect("/dashboard")

        return "Invalid login"

    return render_template("login.html")


# =========================
# LOGIN CHECK HELPER
# =========================

def login_required():
    return "user_id" not in session


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if login_required():
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    subject = request.args.get("subject", "")
    priority = request.args.get("priority", "")
    status = request.args.get("status", "")

    query = "SELECT * FROM tasks WHERE user_id=?"
    params = [session["user_id"]]

    if subject:
        query += " AND subject LIKE ?"
        params.append(f"%{subject}%")

    if priority:
        query += " AND priority=?"
        params.append(priority)

    if status == "pending":
        query += " AND completed=0"
    elif status == "completed":
        query += " AND completed=1"

    tasks = cursor.execute(query, params).fetchall()
    tasks = [dict(t) for t in tasks]

    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t["completed"] == 1])
    pending_tasks = len([t for t in tasks if t["completed"] == 0])

    user = cursor.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    xp = user["xp"]
    streak = user["streak"]

    level = (xp // 150) + 1

    ai_recommendations = []

    if pending_tasks == 0:
        ai_recommendations.append("Great job! All tasks completed 🎉")
    elif pending_tasks <= 2:
        ai_recommendations.append("Low workload. Revise topics.")
    elif pending_tasks <= 5:
        ai_recommendations.append("Moderate workload. Focus priorities.")
    else:
        ai_recommendations.append("High workload! Use Pomodoro technique.")

    if completed_tasks < total_tasks:
        ai_recommendations.append("Try completing 2–3 tasks today.")

    conn.close()

    return render_template(
        "dashboard.html",

        tasks=tasks,

        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,

        xp=xp,
        streak=streak,
        level=level,

        ai_recommendations=ai_recommendations
    )


# =========================
# ADD TASK
# =========================

@app.route("/add_task", methods=["POST"])
def add_task():

    if login_required():
        return redirect("/login")

    task = request.form["task"]
    subject = request.form["subject"]
    priority = request.form["priority"]
    due_date = request.form["due_date"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (user_id, task, subject, priority, due_date)
        VALUES (?, ?, ?, ?, ?)
    """, (session["user_id"], task, subject, priority, due_date))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# COMPLETE TASK
# =========================

@app.route("/complete_task/<int:task_id>")
def complete_task(task_id):

    if login_required():
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks SET completed=1 WHERE id=?
    """, (task_id,))

    cursor.execute("""
        UPDATE users SET xp = xp + 10 WHERE id=?
    """, (session["user_id"],))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# DELETE TASK
# =========================

@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):

    if login_required():
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# RUN APP (RENDER SAFE)
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    