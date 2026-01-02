# app.py
import os, sqlite3
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

from acad_rag import query_rag

from routes.documents import documents_bp

# ---------------- App ----------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

app.register_blueprint(documents_bp)

# ---------------- DB ----------------
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- Auth ----------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

# ---------------- One-time RAG init ----------------
print("📚 Initializing AcadRAG (one-time)...")
print("✅ AcadRAG ready")

# ---------------- Routes ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password required", "error")
            return render_template("register.html")

        try:
            pw_hash = generate_password_hash(password)
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users(username, password_hash) VALUES (?, ?)",
                (username, pw_hash)
            )
            conn.commit()
            conn.close()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists", "error")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and check_password_hash(row[1], password):
            session["user_id"] = row[0]
            session["username"] = username
            return redirect(url_for("dashboard"))

        flash("Invalid credentials", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def root():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username"))

@app.route("/documents")
@login_required
def documents():
    return render_template("documents.html", username=session.get("username"))

@app.route("/ask", methods=["POST"])
@login_required
def ask():
    data = request.json or {}
    q = (data.get("question") or "").strip()
    top_k = int(data.get("top_k", 3))

    user_id = session["user_id"]   

    res = query_rag(q, user_id=user_id, top_k=top_k)
    return jsonify(res)

# ---------------- Run ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=False)
