"""Campus Lost & Found — a small Flask + SQLite web app."""
import os
from datetime import date
from urllib.parse import urlparse

from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import (LoginManager, UserMixin, current_user,
                         login_user, logout_user)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

import db
from forms import LoginForm, RegisterForm

PER_PAGE = 12


class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.username = row["username"]


login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please log in to do that."
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id):
    row = db.get_db().execute("SELECT id, username FROM users WHERE id = ?",
                              (user_id,)).fetchone()
    return User(row) if row else None


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "lostfound.db"),
    )

    login_manager.init_app(app)
    csrf.init_app(app)
    app.teardown_appcontext(db.close_db)
    db.init_db(app.config["DATABASE"])

    register_routes(app)
    return app


def safe_next(target):
    """Only follow ?next= redirects that stay on this site."""
    if target:
        parsed = urlparse(target)
        if not parsed.scheme and not parsed.netloc and target.startswith("/"):
            return target
    return None


def register_routes(app):

    @app.template_filter("nicedate")
    def nicedate(value):
        try:
            d = date.fromisoformat(value[:10])
        except (TypeError, ValueError):
            return value
        return f"{d:%b} {d.day}, {d.year}"  # (%-d isn't supported on Windows)

    @app.template_filter("ago")
    def ago(value):
        try:
            days = (date.today() - date.fromisoformat(value[:10])).days
        except (TypeError, ValueError):
            return ""
        if days <= 0:
            return "today"
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days} days ago"
        if days < 60:
            return f"{days // 7} week{'s' if days >= 14 else ''} ago"
        return f"{days // 30} months ago"

    # ---------- browsing ----------

    @app.route("/")
    def index():
        page = max(request.args.get("page", 1, type=int), 1)
        conn = db.get_db()
        total = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        items = conn.execute(
            """SELECT i.*, u.username FROM items i JOIN users u ON u.id = i.user_id
               ORDER BY i.found_date DESC, i.id DESC
               LIMIT ? OFFSET ?""",
            (PER_PAGE, (page - 1) * PER_PAGE),
        ).fetchall()
        stats = conn.execute(
            "SELECT COUNT(*) AS total, SUM(status = 'unclaimed') AS open FROM items"
        ).fetchone()
        return render_template("index.html", items=items, page=page, total=total,
                               pages=max((total + PER_PAGE - 1) // PER_PAGE, 1), stats=stats)

    @app.route("/items/<int:item_id>")
    def item_detail(item_id):
        item = db.get_db().execute(
            """SELECT i.*, u.username FROM items i JOIN users u ON u.id = i.user_id
               WHERE i.id = ?""", (item_id,)).fetchone()
        if item is None:
            abort(404)
        return render_template("item_detail.html", item=item)

    # ---------- accounts ----------

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        form = RegisterForm()
        if form.validate_on_submit():
            conn = db.get_db()
            username = form.username.data.strip()
            if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
                form.username.errors.append("That username is taken.")
            else:
                # Werkzeug uses scrypt with a random 16-character salt per password.
                cur = conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(form.password.data)))
                conn.commit()
                login_user(User({"id": cur.lastrowid, "username": username}))
                flash(f"Welcome, {username}! Your account is ready.", "success")
                return redirect(url_for("index"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        form = LoginForm()
        if form.validate_on_submit():
            row = db.get_db().execute("SELECT * FROM users WHERE username = ?",
                                      (form.username.data.strip(),)).fetchone()
            if row and check_password_hash(row["password_hash"], form.password.data):
                login_user(User(row), remember=form.remember.data)
                flash(f"Welcome back, {row['username']}.", "success")
                return redirect(safe_next(request.args.get("next")) or url_for("index"))
            flash("Wrong username or password.", "error")
        return render_template("login.html", form=form)

    @app.route("/logout", methods=["POST"])
    def logout():
        logout_user()
        flash("You're logged out.", "info")
        return redirect(url_for("index"))

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404,
                               message="We couldn't find that page. Maybe it got lost too?"), 404


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
