"""Lab 3 — Lab 2 login/to-dos extended with a books & authors library."""
import os
from decimal import Decimal, InvalidOperation
from functools import wraps
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import bcrypt
import pymysql
from dotenv import load_dotenv
from PIL import Image, UnidentifiedImageError
from flask import Flask, flash, redirect, render_template, request, session, url_for
from pymysql.cursors import DictCursor

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=4 * 1024 * 1024,  # 4 MB request cap for photos
)
UPLOAD_ROOT = Path(app.static_folder) / "uploads"


def connection(database=None):
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=database or os.getenv("DB_NAME", "registration"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )


def query(sql, values=(), one=False, all_rows=False, database=None):
    # Values are always supplied separately, never interpolated into SQL.
    with connection(database=database) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, values)
            if one:
                return cursor.fetchone()
            if all_rows:
                return cursor.fetchall()
            return cursor.rowcount


def library_query(sql, values=(), one=False, all_rows=False):
    return query(sql, values, one=one, all_rows=all_rows,
                 database=os.getenv("LIBRARY_DB_NAME", "library"))


def login_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return inner


@app.context_processor
def csrf_context():
    # All mutations require a unique CSRF token stored in the session.
    import secrets
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return {"csrf_token": session["csrf_token"]}


@app.before_request
def protect_post():
    if request.method == "POST":
        import hmac
        expected = session.get("csrf_token", "")
        supplied = request.form.get("csrf_token", "")
        if not expected or not hmac.compare_digest(expected, supplied):
            return "Invalid form token. Refresh the page and try again.", 400


@app.route("/")
def home():
    return redirect(url_for("todos" if "user_id" in session else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    errors = []
    values = {"name": "", "email": ""}
    if request.method == "POST":
        values = {"name": request.form.get("name", "").strip(),
                  "email": request.form.get("email", "").strip()}
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not values["name"]:
            errors.append("Name is required")
        if not values["email"]:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")
        if not confirm:
            errors.append("Confirm password is required")
        if password and confirm and password != confirm:
            errors.append("Passwords do not match")
        if len(values["name"]) > 100 or len(values["email"]) > 255:
            errors.append("Name or email is too long")
        if not errors:
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            try:
                query("INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                      (values["email"], values["name"], hashed))
            except pymysql.err.IntegrityError as exc:
                if exc.args[0] == 1062:
                    errors.append("Email Already Exists")
                else:
                    raise
            if not errors:
                # Lab 3 demo: register -> login -> to-do list
                session.clear()
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
    return render_template("register.html", errors=errors, values=values)


@app.route("/login", methods=["GET", "POST"])
def login():
    errors = []
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")
        if not errors:
            user = query("SELECT user_id, name, password_hash FROM users WHERE email = %s", (email,), one=True)
            if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
                errors.append("Invalid email or password")
            else:
                session.clear()
                session["user_id"] = user["user_id"]
                session["name"] = user["name"]
                return redirect(url_for("todos"))
    return render_template("login.html", errors=errors, email=email)


@app.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/todos")
@login_required
def todos():
    items = query("SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC",
                  (session["user_id"],), all_rows=True)
    done_tasks = sum(1 for item in items if item["is_done"])
    open_tasks = len(items) - done_tasks
    return render_template("todos.html", items=items, done_tasks=done_tasks,
                           open_tasks=open_tasks)


def valid_title(title):
    if not title.strip():
        return "Title is required"
    if len(title.strip()) > 200:
        return "Title is too long"
    return None


@app.post("/todos/add")
@login_required
def add_todo():
    title = request.form.get("title", "")
    error = valid_title(title)
    if error:
        flash(error, "error")
    else:
        query("INSERT INTO todos (user_id, title) VALUES (%s, %s)", (session["user_id"], title.strip()))
        flash("Task added", "success")
    return redirect(url_for("todos"))


@app.post("/todos/<int:todo_id>/edit")
@login_required
def edit_todo(todo_id):
    title = request.form.get("title", "")
    error = valid_title(title)
    if error:
        flash(error, "error")
    else:
        query("UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
              (title.strip(), todo_id, session["user_id"]))
        flash("Task updated", "success")
    return redirect(url_for("todos"))


@app.post("/todos/<int:todo_id>/toggle")
@login_required
def toggle_todo(todo_id):
    done = request.form.get("is_done", "0")
    if done not in ("0", "1"):
        return "Invalid status", 400
    query("UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
          (int(done), todo_id, session["user_id"]))
    return redirect(url_for("todos"))


@app.post("/todos/<int:todo_id>/delete")
@login_required
def delete_todo(todo_id):
    query("DELETE FROM todos WHERE todo_id = %s AND user_id = %s", (todo_id, session["user_id"]))
    flash("Task deleted", "success")
    return redirect(url_for("todos"))


# ---------- Lab 3: Author / Book CRUD + bonus image uploads ----------

def save_optional_image(field_name, folder):
    """Validate and re-encode an uploaded image; store only a generated filename.

    Returns None when no new image was selected. ValueError for invalid uploads.
    """
    upload = request.files.get(field_name)
    if upload is None or not upload.filename:
        return None
    raw = upload.read()
    if not raw or len(raw) > 3 * 1024 * 1024:
        raise ValueError("Image must be nonempty and no larger than 3 MB")
    try:
        with Image.open(BytesIO(raw)) as image:
            if image.format not in ("JPEG", "PNG", "WEBP", "GIF"):
                raise ValueError("Use a JPG, PNG, WEBP, or GIF image")
            if image.width > 5000 or image.height > 5000:
                raise ValueError("Image dimensions are too large")
            image.load()
            image = image.convert("RGB")
            image.thumbnail((1200, 1200))
            filename = uuid4().hex + ".webp"
            target = UPLOAD_ROOT / folder
            target.mkdir(parents=True, exist_ok=True)
            image.save(target / filename, format="WEBP", quality=85)
            return filename
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("Please upload a valid JPG, PNG, WEBP, or GIF image") from exc


def delete_uploaded_image(filename, folder):
    """Delete only our own generated filenames from the expected upload folder."""
    import re
    if filename and re.fullmatch(r"[0-9a-f]{32}\.webp", filename):
        (UPLOAD_ROOT / folder / filename).unlink(missing_ok=True)


def author_inputs():
    name = request.form.get("name", "").strip()
    country = request.form.get("country", "").strip()
    if not name or not country or len(name) > 100 or len(country) > 80:
        raise ValueError("Author name and country are required (max 100/80 characters)")
    return name, country


def book_inputs():
    title = request.form.get("title", "").strip()
    value = request.form.get("price", "").strip()
    if not title or len(title) > 150:
        raise ValueError("Book title is required (max 150 characters)")
    try:
        price = Decimal(value)
        if not price.is_finite() or price < 0 or price > Decimal("99999999.99") or price != price.quantize(Decimal("0.01")):
            raise ValueError()
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid price with up to 2 decimal places") from None
    try:
        author_id = int(request.form.get("author_id", ""))
    except ValueError:
        raise ValueError("Choose an author") from None
    if not library_query("SELECT author_id FROM AUTHOR WHERE author_id = %s", (author_id,), one=True):
        raise ValueError("The selected author does not exist")
    return title, price, author_id


@app.get("/library")
@login_required
def library():
    authors = library_query("SELECT author_id, name, country, photo_filename FROM AUTHOR ORDER BY author_id", all_rows=True)
    books = library_query("SELECT book_id, title, price, author_id, cover_filename FROM BOOK ORDER BY book_id", all_rows=True)
    author_map = {author["author_id"]: author["name"] for author in authors}
    return render_template("library.html", authors=authors, books=books, author_map=author_map)


@app.post("/library/authors/add")
@login_required
def add_author():
    image = None
    try:
        name, country = author_inputs()
        image = save_optional_image("photo", "authors")
        library_query("INSERT INTO AUTHOR (name, country, photo_filename) VALUES (%s, %s, %s)",
                      (name, country, image))
        flash("Author added", "success")
    except (ValueError, pymysql.MySQLError) as exc:
        delete_uploaded_image(image, "authors")
        flash(f"Could not add author: {exc}", "error")
    return redirect(url_for("library"))


@app.post("/library/authors/<int:author_id>/edit")
@login_required
def edit_author(author_id):
    old = library_query("SELECT photo_filename FROM AUTHOR WHERE author_id = %s", (author_id,), one=True)
    if not old:
        flash("Author not found", "error")
        return redirect(url_for("library"))
    image = None
    try:
        name, country = author_inputs()
        image = save_optional_image("photo", "authors")
        new_image = image if image else old["photo_filename"]
        library_query("UPDATE AUTHOR SET name = %s, country = %s, photo_filename = %s WHERE author_id = %s",
                      (name, country, new_image, author_id))
        if image:
            delete_uploaded_image(old["photo_filename"], "authors")
        flash("Author updated", "success")
    except (ValueError, pymysql.MySQLError) as exc:
        delete_uploaded_image(image, "authors")
        flash(f"Could not edit author: {exc}", "error")
    return redirect(url_for("library"))


@app.post("/library/authors/<int:author_id>/delete")
@login_required
def delete_author(author_id):
    author = library_query("SELECT photo_filename FROM AUTHOR WHERE author_id = %s", (author_id,), one=True)
    if not author:
        flash("Author not found", "error")
        return redirect(url_for("library"))
    # Collect images of books that ON DELETE CASCADE will remove.
    books = library_query("SELECT cover_filename FROM BOOK WHERE author_id = %s", (author_id,), all_rows=True)
    library_query("DELETE FROM AUTHOR WHERE author_id = %s", (author_id,))
    delete_uploaded_image(author["photo_filename"], "authors")
    for book in books:
        delete_uploaded_image(book["cover_filename"], "books")
    flash("Author and their books deleted (ON DELETE CASCADE)", "success")
    return redirect(url_for("library"))


@app.post("/library/books/add")
@login_required
def add_book():
    image = None
    try:
        title, price, author_id = book_inputs()
        image = save_optional_image("cover", "books")
        library_query("INSERT INTO BOOK (title, price, author_id, cover_filename) VALUES (%s, %s, %s, %s)",
                      (title, price, author_id, image))
        flash("Book added", "success")
    except (ValueError, pymysql.MySQLError) as exc:
        delete_uploaded_image(image, "books")
        flash(f"Could not add book: {exc}", "error")
    return redirect(url_for("library"))


@app.post("/library/books/<int:book_id>/edit")
@login_required
def edit_book(book_id):
    old = library_query("SELECT cover_filename FROM BOOK WHERE book_id = %s", (book_id,), one=True)
    if not old:
        flash("Book not found", "error")
        return redirect(url_for("library"))
    image = None
    try:
        title, price, author_id = book_inputs()
        image = save_optional_image("cover", "books")
        new_image = image if image else old["cover_filename"]
        library_query("UPDATE BOOK SET title = %s, price = %s, author_id = %s, cover_filename = %s WHERE book_id = %s",
                      (title, price, author_id, new_image, book_id))
        if image:
            delete_uploaded_image(old["cover_filename"], "books")
        flash("Book updated", "success")
    except (ValueError, pymysql.MySQLError) as exc:
        delete_uploaded_image(image, "books")
        flash(f"Could not edit book: {exc}", "error")
    return redirect(url_for("library"))


@app.post("/library/books/<int:book_id>/delete")
@login_required
def delete_book(book_id):
    book = library_query("SELECT cover_filename FROM BOOK WHERE book_id = %s", (book_id,), one=True)
    if not book:
        flash("Book not found", "error")
        return redirect(url_for("library"))
    library_query("DELETE FROM BOOK WHERE book_id = %s", (book_id,))
    delete_uploaded_image(book["cover_filename"], "books")
    flash("Book deleted", "success")
    return redirect(url_for("library"))


@app.errorhandler(413)
def image_too_large(_):
    flash("Image upload is too large (max 3 MB per image)", "error")
    return redirect(url_for("library" if "user_id" in session else "login"))

# ========== LAB 4 - PART 2 + BONUS ==========

from decimal import Decimal, InvalidOperation
from flask import render_template_string

LAB4_REPORTS = {
    "catalogue": [
        ("All books: author, publisher and category", """
            SELECT b.book_id, b.title, b.price, b.publish_year,
                   a.name AS author_name,
                   p.name AS publisher_name,
                   c.name AS category_name
            FROM BOOK b
            JOIN AUTHOR a ON b.author_id = a.author_id
            JOIN PUBLISHER p ON b.publisher_id = p.publisher_id
            JOIN CATEGORY c ON b.category_id = c.category_id
            ORDER BY b.title
        """),
    ],

    "reports": [
        ("Books per category and average price", """
            SELECT c.name AS category_name,
                   COUNT(b.book_id) AS total_books,
                   ROUND(AVG(b.price), 2) AS average_price
            FROM CATEGORY c
            LEFT JOIN BOOK b
                ON b.category_id = c.category_id
            GROUP BY c.category_id, c.name
            ORDER BY c.name
        """),

        ("Authors with at least 2 books", """
            SELECT a.name AS author_name,
                   COUNT(b.book_id) AS total_books
            FROM AUTHOR a
            JOIN BOOK b ON b.author_id = a.author_id
            GROUP BY a.author_id, a.name
            HAVING COUNT(b.book_id) >= 2
            ORDER BY total_books DESC, a.name
        """),

        ("Total, minimum and maximum book price", """
            SELECT SUM(price) AS total_price,
                   MIN(price) AS minimum_price,
                   MAX(price) AS maximum_price
            FROM BOOK
        """),
    ],

    "loans": [
        ("Loans not returned yet", """
            SELECT l.loan_id,
                   b.title AS book_title,
                   m.name AS member_name,
                   l.loan_date,
                   l.return_date
            FROM LOAN l
            JOIN BOOK b ON b.book_id = l.book_id
            JOIN MEMBER m ON m.member_id = l.member_id
            WHERE l.return_date IS NULL
            ORDER BY l.loan_date
        """),

        ("Members who never borrowed", """
            SELECT m.member_id, m.name, m.email
            FROM MEMBER m
            LEFT JOIN LOAN l ON l.member_id = m.member_id
            WHERE l.loan_id IS NULL
        """),

        ("Books never borrowed", """
            SELECT b.book_id, b.title, b.price
            FROM BOOK b
            LEFT JOIN LOAN l ON l.book_id = b.book_id
            WHERE l.loan_id IS NULL
        """),
    ],

    "popular": [
        ("Top 3 most borrowed books", """
            SELECT b.book_id, b.title,
                   COUNT(l.loan_id) AS loan_count
            FROM BOOK b
            JOIN LOAN l ON l.book_id = b.book_id
            GROUP BY b.book_id, b.title
            ORDER BY loan_count DESC, b.book_id ASC
            LIMIT 3
        """),

        ("Member with the most loans", """
            SELECT m.member_id, m.name,
                   COUNT(l.loan_id) AS loan_count
            FROM MEMBER m
            JOIN LOAN l ON l.member_id = m.member_id
            GROUP BY m.member_id, m.name
            ORDER BY loan_count DESC, m.member_id ASC
            LIMIT 1
        """),
    ],

    "authors": [
        ("All authors, including authors with zero books", """
            SELECT a.author_id, a.name,
                   COUNT(b.book_id) AS total_books
            FROM AUTHOR a
            LEFT JOIN BOOK b ON b.author_id = a.author_id
            GROUP BY a.author_id, a.name
            ORDER BY a.name
        """),

        ("Books with author and publisher from same country", """
            SELECT b.book_id, b.title,
                   a.name AS author_name,
                   p.name AS publisher_name,
                   a.country AS common_country
            FROM BOOK b
            JOIN AUTHOR a ON a.author_id = b.author_id
            JOIN PUBLISHER p ON p.publisher_id = b.publisher_id
            WHERE a.country = p.country
            ORDER BY b.title
        """),
    ],
}


LAB4_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lab 4 - {{ title }}</title>

<style>
body {
    margin: 0;
    background: #f5f7fb;
    color: #182338;
    font-family: Arial, sans-serif;
}
header {
    background: #172c4b;
    color: white;
    padding: 24px 5%;
}
header h1 {
    margin: 0 0 8px;
    font-size: 26px;
}
header p {
    margin: 0;
    color: #cdd9eb;
}
nav {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    padding: 16px 5%;
    background: white;
    border-bottom: 1px solid #dfe5ee;
}
nav a {
    color: #173960;
    text-decoration: none;
    padding: 10px 13px;
    border-radius: 8px;
    font-weight: bold;
}
nav a.active, nav a:hover {
    background: #dceafa;
}
main {
    max-width: 1120px;
    margin: 28px auto;
    padding: 0 18px;
}
.card {
    background: white;
    padding: 22px;
    margin: 20px 0;
    border-radius: 12px;
    box-shadow: 0 2px 12px #172c4b12;
    overflow-x: auto;
}
form {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: end;
}
label {
    font-size: 13px;
    font-weight: bold;
    display: flex;
    flex-direction: column;
    gap: 7px;
}
input, select {
    padding: 11px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    min-width: 155px;
}
button {
    border: 0;
    background: #205dab;
    color: white;
    padding: 12px 22px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
}
table {
    border-collapse: collapse;
    width: 100%;
    min-width: 520px;
}
th, td {
    text-align: left;
    border-bottom: 1px solid #e5eaf2;
    padding: 12px;
}
th {
    background: #eff4fc;
    color: #173960;
}
.msg {
    padding: 14px;
    border-radius: 8px;
    background: #fff4df;
    color: #874d00;
}
</style>
</head>

<body>

<header>
    <h1>Library Management - Lab 4</h1>
    <p>Part II - Search, Catalogue, Reports and Loans</p>
</header>

<nav>
{% for key, label in tabs %}
    <a href="{{ url_for('lab4_all', page=key) }}"
       class="{{ 'active' if key == page else '' }}">
        {{ label }}
    </a>
{% endfor %}
<a href="{{ url_for('library') }}">Old Library</a>
</nav>

<main>

<h2>{{ title }}</h2>

{% if page == 'search' %}
<div class="card">
    <h3>Find a Book</h3>

    <form method="get"
          action="{{ url_for('lab4_all', page='search') }}">

        <label>Title keyword
            <input name="keyword"
                   value="{{ filters.keyword }}"
                   placeholder="Search title">
        </label>

        <label>Minimum price
            <input type="number"
                   min="0"
                   step="0.01"
                   name="min_price"
                   value="{{ filters.min_price }}">
        </label>

        <label>Maximum price
            <input type="number"
                   min="0"
                   step="0.01"
                   name="max_price"
                   value="{{ filters.max_price }}">
        </label>

        <label>Category
            <select name="category_id">
                <option value="">All categories</option>

                {% for cat in categories %}
                <option value="{{ cat.category_id }}"
                {{ 'selected' if filters.category_id ==
                   (cat.category_id|string) else '' }}>
                    {{ cat.name }}
                </option>
                {% endfor %}
            </select>
        </label>

        <button type="submit">Search</button>
    </form>

    {% if error %}
        <div class="msg">{{ error }}</div>
    {% endif %}
</div>
{% endif %}

{% for section_title, rows in sections %}

<section class="card">
    <h3>{{ section_title }}</h3>

    {% if rows %}
    <table>
        <thead>
            <tr>
                {% for key in rows[0].keys() %}
                <th>{{ key|replace('_',' ')|title }}</th>
                {% endfor %}
            </tr>
        </thead>

        <tbody>
        {% for row in rows %}
            <tr>
                {% for value in row.values() %}
                <td>
                    {{ value if value is not none else '—' }}
                </td>
                {% endfor %}
            </tr>
        {% endfor %}
        </tbody>
    </table>

    {% else %}
        <p>No matching rows.</p>
    {% endif %}
</section>

{% endfor %}

</main>
</body>
</html>
"""
@app.get("/lab4")
@login_required
def lab4_home():
    return redirect(url_for("lab4_all", page="search"))


@app.get("/lab4/<page>")
@login_required
def lab4_all(page):

    tabs = [
        ("search", "F2.1 Search"),
        ("catalogue", "F2.2 Catalogue"),
        ("reports", "F2.3 Reports"),
        ("loans", "F2.4 Loans"),
        ("popular", "F2.5 Most Borrowed"),
        ("authors", "F2.6 Authors"),
    ]

    titles = dict(tabs)

    if page not in titles:
        return redirect(url_for("lab4_home"))

    sections = []
    categories = []
    error = ""

    filters = {
        "keyword": request.args.get("keyword", "").strip(),
        "min_price": request.args.get("min_price", "").strip(),
        "max_price": request.args.get("max_price", "").strip(),
        "category_id": request.args.get("category_id", "").strip(),
    }

    if page == "search":

        categories = library_query(
            "SELECT category_id, name FROM CATEGORY ORDER BY name",
            all_rows=True
        )

        try:
            low = (
                Decimal(filters["min_price"])
                if filters["min_price"]
                else Decimal("0")
            )

            high = (
                Decimal(filters["max_price"])
                if filters["max_price"]
                else Decimal("99999999.99")
            )

            cat_id = (
                int(filters["category_id"])
                if filters["category_id"]
                else None
            )

            if (
                not low.is_finite()
                or not high.is_finite()
                or low < 0
                or high < low
            ):
                raise ValueError("Invalid price range")

            if cat_id is not None and cat_id <= 0:
                raise ValueError("Invalid category")

            # BONUS: Parameterized Query
            books = library_query(
                """
                SELECT b.book_id,
                       b.title,
                       b.price,
                       b.publish_year,
                       a.name AS author_name,
                       c.name AS category_name
                FROM BOOK b

                JOIN AUTHOR a
                    ON a.author_id = b.author_id

                JOIN CATEGORY c
                    ON c.category_id = b.category_id

                WHERE b.title COLLATE utf8mb4_unicode_ci
                    LIKE %s COLLATE utf8mb4_unicode_ci

                AND b.price BETWEEN %s AND %s

                AND (%s IS NULL OR b.category_id = %s)

                ORDER BY b.price ASC, b.book_id ASC
                """,
                (
                    "%" + filters["keyword"] + "%",
                    low,
                    high,
                    cat_id,
                    cat_id
                ),
                all_rows=True
            )

            sections = [
                ("Matching books (cheapest first)", books)
            ]

        except (ValueError, InvalidOperation):
            error = "Please enter valid search filters."
            sections = [("Matching books", [])]

    else:
        sections = [
            (
                heading,
                library_query(sql, all_rows=True)
            )
            for heading, sql in LAB4_REPORTS[page]
        ]

    return render_template_string(
        LAB4_HTML,
        title=titles[page],
        page=page,
        tabs=tabs,
        sections=sections,
        categories=categories,
        filters=filters,
        error=error
    )

# ========== END LAB 4 PART 2 ==========


if __name__ == "__main__":
    if not app.secret_key:
        raise RuntimeError("Set SECRET_KEY in your .env file before running the server")
    app.run(debug=False)
