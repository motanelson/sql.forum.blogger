from flask import Flask, request, redirect
import sqlite3
import hashlib

app = Flask(__name__)

DB = "blog.db"

lista1 = [
    "off_topic",
    "operation_system",
    "cosmos_os",
    "assembly",
    "programming",
    "hardware"
]

# ---------- DB ----------
def get_db():
    return sqlite3.connect(DB)


def init_db():
    db = get_db()
    c = db.cursor()

    # tabela de utilizadores
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        url TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    # tabela de posts
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        url TEXT,
        message TEXT
    )
    """)

    db.commit()
    db.close()


# ---------- UTIL ----------
def sanitize(text):
    return text.replace("<", "").replace(">", "")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ---------- USERS ----------
def check_user(url, password):
    db = get_db()
    c = db.cursor()

    c.execute("SELECT password FROM users WHERE url=?", (url,))
    row = c.fetchone()

    if row:
        return row[0] == hash_password(password)
    return None  # user não existe


def create_user(url, password):
    db = get_db()
    c = db.cursor()

    c.execute(
        "INSERT INTO users (url, password) VALUES (?, ?)",
        (url, hash_password(password))
    )

    db.commit()
    db.close()


# ---------- POSTS ----------
def save_post(category, url, message):
    db = get_db()
    c = db.cursor()

    c.execute(
        "INSERT INTO posts (category, url, message) VALUES (?, ?, ?)",
        (category, url, message)
    )

    db.commit()
    db.close()


def load_posts(category):
    db = get_db()
    c = db.cursor()

    c.execute(
        "SELECT url, message FROM posts WHERE category=? ORDER BY id DESC",
        (category,)
    )

    posts = c.fetchall()
    db.close()
    return posts


# ---------- HOME ----------
@app.route("/")
def home():
    html = """
    <html>
    <head>
        <style>
            body { background:black; color:white; font-family:Arial; }
            a { color:#00ffff; display:block; margin:10px 0; }
        </style>
    </head>
    <body>
        <h1>Categorias</h1>
    """

    for cat in lista1:
        html += f'<a href="/{cat}">{cat}</a>'

    html += "</body></html>"
    return html


# ---------- CATEGORY ----------
@app.route("/<category>", methods=["GET", "POST"])
def category_page(category):
    if category not in lista1:
        return "Categoria inválida", 404

    error = ""

    if request.method == "POST":
        url = sanitize(request.form.get("url", ""))
        message = sanitize(request.form.get("message", ""))
        password = request.form.get("password", "")

        if url and message and password:
            result = check_user(url, password)

            if result is True:
                save_post(category, url, message)
                return redirect(f"/{category}")

            elif result is False:
                error = "❌ Password errada!"

            else:
                # criar novo utilizador
                create_user(url, password)
                save_post(category, url, message)
                return redirect(f"/{category}")

    posts = load_posts(category)

    html = f"""
    <html>
    <head>
        <style>
            body {{ background:black; color:white; font-family:Arial; }}
            textarea, input {{
                width:100%;
                background:#111;
                color:white;
                border:1px solid #555;
                padding:10px;
                margin-top:5px;
            }}
            button {{
                margin-top:10px;
                padding:10px;
                background:#333;
                color:white;
                border:none;
            }}
            hr {{ border:1px solid #444; }}
            a {{ color:#00ffff; }}
        </style>
    </head>
    <body>

        <a href="/">⬅ Voltar</a>

        <h2>{category}</h2>

        <form method="POST">
            <label>Endereço (URL):</label>
            <input type="text" name="url" required>

            <label>Password:</label>
            <input type="password" name="password" required>

            <label>Mensagem:</label>
            <textarea name="message" rows="4" required></textarea>

            <button type="submit">Submit</button>
        </form>

        <p style="color:red;">{error}</p>

        <hr>
        <h2>Mensagens</h2>
    """

    for url, msg in posts:
        html += f"""
        <div>
            <b>{url}</b><br>
            <p>{msg}</p>
        </div>
        <hr>
        """

    html += "</body></html>"
    return html


# ---------- START ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
