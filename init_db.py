import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()

# =========================
# USERS TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL,

    email TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL
)
""")

# =========================
# TASKS TABLE
# =========================


cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT,

    task TEXT NOT NULL,

    subject TEXT,

    priority TEXT,

    due_date TEXT,

    completed INTEGER DEFAULT 0
)
""")

conn.commit()

conn.close()

print("Database Created Successfully")