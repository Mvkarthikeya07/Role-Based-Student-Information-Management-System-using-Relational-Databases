from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for login sessions

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    # Users (Teacher & Student accounts)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    # Students Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            course TEXT
        )
    """)

    # Add default teacher & student if not exists
    cur.execute("SELECT * FROM users WHERE username=?", ("teacher",))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("teacher", "1234", "teacher"))

    cur.execute("SELECT * FROM users WHERE username=?", ("student",))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("student", "1234", "student"))

    conn.commit()
    conn.close()

init_db()

# ---------- Routes ----------
@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    if session["role"] == "teacher":
        return redirect(url_for("teacher_dashboard"))
    else:
        return redirect(url_for("student_dashboard"))

# ---------- Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("students.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["username"] = user[1]
            session["role"] = user[3]
            return redirect(url_for("home"))
        else:
            error = "Invalid Credentials"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- Teacher Dashboard ----------
@app.route("/teacher")
def teacher_dashboard():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    conn = sqlite3.connect("students.db")
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("teacher_dashboard.html", students=students)

@app.route("/add", methods=["POST"])
def add_student():
    name = request.form["name"]
    course = request.form["course"]
    conn = sqlite3.connect("students.db")
    conn.execute("INSERT INTO students (name, course) VALUES (?, ?)", (name, course))
    conn.commit()
    conn.close()
    return redirect(url_for("teacher_dashboard"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    conn = sqlite3.connect("students.db")
    if request.method == "POST":
        name = request.form["name"]
        course = request.form["course"]
        conn.execute("UPDATE students SET name=?, course=? WHERE id=?", (name, course, id))
        conn.commit()
        conn.close()
        return redirect(url_for("teacher_dashboard"))
    student = conn.execute("SELECT * FROM students WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("edit.html", student=student)

@app.route("/delete/<int:id>")
def delete_student(id):
    conn = sqlite3.connect("students.db")
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("teacher_dashboard"))

@app.route("/search", methods=["POST"])
def search_student():
    keyword = request.form["keyword"]
    conn = sqlite3.connect("students.db")
    students = conn.execute("SELECT * FROM students WHERE name LIKE ? OR course LIKE ?", 
                            ('%' + keyword + '%', '%' + keyword + '%')).fetchall()
    conn.close()
    return render_template("teacher_dashboard.html", students=students)

@app.route("/export")
def export_students():
    conn = sqlite3.connect("students.db")
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    df.to_csv("students.csv", index=False)
    return send_file("students.csv", as_attachment=True)

# ---------- Student Dashboard ----------
@app.route("/student")
def student_dashboard():
    if "role" not in session or session["role"] != "student":
        return redirect(url_for("login"))
    conn = sqlite3.connect("students.db")
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("student_dashboard.html", students=students)

if __name__ == "__main__":
    app.run(debug=True)
