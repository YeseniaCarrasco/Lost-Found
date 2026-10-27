"""Campus Lost & Found — a small Flask + SQLite web app."""
import bootstrap; bootstrap.ensure_dependencies()  # noqa: E401,E702  (must run before other imports)
import os
from datetime import date, datetime
from urllib.parse import urlparse

from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import db
from forms import CATEGORIES, ItemForm, LoginForm, RegisterForm

PER_PAGE = 12
FILTER_COOKIE = "unclaimed_only"   # remembers the "still unclaimed" checkbox
COOKIE_MAX_AGE = 60 * 60 * 24 * 90


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
    production = bool(os.environ.get("K_SERVICE"))  # set automatically on Cloud Run
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get("DATABASE_PATH",
                                os.path.join(app.instance_path, "lostfound.db")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=production,
    )
    if production and app.config["SECRET_KEY"] == "dev-only-change-me":
        raise RuntimeError("Set the SECRET_KEY environment variable in production.")

    # Cloud Run terminates HTTPS in front of the container.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    login_manager.init_app(app)
    csrf.init_app(app)
    app.teardown_appcontext(db.close_db)
    db.init_db(app.config["DATABASE"])

    register_routes(app)
    return app


def owned_item_or_abort(item_id):
    item = db.get_db().execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if item is None:
        abort(404)
    if item["user_id"] != current_user.id:
        abort(403)
    return item


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

    @app.context_processor
    def inject_globals():
        return {"categories": CATEGORIES}

    # ---------- browsing ----------

    @app.route("/")
    def index():
        q = request.args.get("q", "").strip()
        category = request.args.get("category", "")
        page = max(request.args.get("page", 1, type=int), 1)

        # "f" marks a submitted filter form; otherwise fall back to the cookie.
        if "f" in request.args:
            unclaimed_only = request.args.get("unclaimed") == "1"
        else:
            unclaimed_only = request.cookies.get(FILTER_COOKIE) == "1"

        where, params = [], []
        if q:
            like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            where.append("(i.title LIKE ? ESCAPE '\\' OR i.description LIKE ? ESCAPE '\\'"
                         " OR i.location LIKE ? ESCAPE '\\')")
            params += [like, like, like]
        if unclaimed_only:
            where.append("i.status = 'unclaimed'")
        if category in CATEGORIES:
            where.append("i.category = ?")
            params.append(category)
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        conn = db.get_db()
        total = conn.execute(f"SELECT COUNT(*) FROM items i {where_sql}", params).fetchone()[0]
        items = conn.execute(
            f"""SELECT i.*, u.username FROM items i JOIN users u ON u.id = i.user_id
                {where_sql}
                ORDER BY i.found_date DESC, i.id DESC
                LIMIT ? OFFSET ?""",
            params + [PER_PAGE, (page - 1) * PER_PAGE],
        ).fetchall()
        stats = conn.execute(
            "SELECT COUNT(*) AS total, SUM(status = 'unclaimed') AS open FROM items"
        ).fetchone()

        resp = app.make_response(render_template(
            "index.html", items=items, q=q, category=category,
            unclaimed_only=unclaimed_only, page=page, total=total,
            pages=max((total + PER_PAGE - 1) // PER_PAGE, 1), stats=stats,
        ))
        if "f" in request.args:
            resp.set_cookie(FILTER_COOKIE, "1" if unclaimed_only else "0",
                            max_age=COOKIE_MAX_AGE, samesite="Lax",
                            httponly=True, secure=request.is_secure)
        return resp

    @app.route("/items/<int:item_id>")
    def item_detail(item_id):
        item = db.get_db().execute(
            """SELECT i.*, u.username FROM items i JOIN users u ON u.id = i.user_id
               WHERE i.id = ?""", (item_id,)).fetchone()
        if item is None:
            abort(404)
        return render_template("item_detail.html", item=item)

    @app.route("/u/<username>")
    def user_page(username):
        conn = db.get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user is None:
            abort(404)
        items = conn.execute(
            """SELECT i.*, u.username FROM items i JOIN users u ON u.id = i.user_id
               WHERE i.user_id = ? ORDER BY i.found_date DESC, i.id DESC""",
            (user["id"],)).fetchall()
        returned = sum(1 for i in items if i["status"] == "returned")
        return render_template("user.html", user=user, items=items, returned=returned)

    # ---------- posting ----------

    @app.route("/items/new", methods=["GET", "POST"])
    @login_required
    def new_item():
        form = ItemForm()
        if form.validate_on_submit():
            conn = db.get_db()
            cur = conn.execute(
                """INSERT INTO items (user_id, title, description, category, location,
                                      found_date, photo_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (current_user.id, form.title.data.strip(), (form.description.data or "").strip(),
                 form.category.data, form.location.data.strip(),
                 form.found_date.data.isoformat(), (form.photo_url.data or "").strip()))
            conn.commit()
            flash("Thanks! Your found item is posted.", "success")
            return redirect(url_for("item_detail", item_id=cur.lastrowid))
        return render_template("item_form.html", form=form, editing=False)

    @app.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_item(item_id):
        item = owned_item_or_abort(item_id)
        form = ItemForm()
        if request.method == "GET":
            form.title.data = item["title"]
            form.category.data = item["category"]
            form.location.data = item["location"]
            form.found_date.data = date.fromisoformat(item["found_date"])
            form.photo_url.data = item["photo_url"]
            form.description.data = item["description"]
        if form.validate_on_submit():
            conn = db.get_db()
            conn.execute(
                """UPDATE items SET title = ?, description = ?, category = ?, location = ?,
                                    found_date = ?, photo_url = ?
                   WHERE id = ?""",
                (form.title.data.strip(), (form.description.data or "").strip(),
                 form.category.data, form.location.data.strip(),
                 form.found_date.data.isoformat(), (form.photo_url.data or "").strip(),
                 item_id))
            conn.commit()
            flash("Post updated.", "success")
            return redirect(url_for("item_detail", item_id=item_id))
        return render_template("item_form.html", form=form, editing=True, item=item)

    @app.route("/items/<int:item_id>/status", methods=["POST"])
    @login_required
    def toggle_status(item_id):
        item = owned_item_or_abort(item_id)
        conn = db.get_db()
        if item["status"] == "unclaimed":
            conn.execute("UPDATE items SET status = 'returned', returned_at = ? WHERE id = ?",
                         (datetime.now().isoformat(timespec="seconds"), item_id))
            flash(f"Marked “{item['title']}” as returned. Nice work!", "success")
        else:
            conn.execute("UPDATE items SET status = 'unclaimed', returned_at = NULL WHERE id = ?",
                         (item_id,))
            flash(f"“{item['title']}” is back to unclaimed.", "info")
        conn.commit()
        return redirect(safe_next(request.form.get("next"))
                        or url_for("item_detail", item_id=item_id))

    @app.route("/items/<int:item_id>/delete", methods=["POST"])
    @login_required
    def delete_item(item_id):
        owned_item_or_abort(item_id)
        conn = db.get_db()
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        flash("Post deleted.", "info")
        return redirect(url_for("user_page", username=current_user.username))

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

    @app.route("/healthz")
    def healthz():
        return "ok"

    @app.errorhandler(CSRFError)
    def csrf_error(_e):
        return render_template("error.html", code=400,
                               message="That form expired. Go back, refresh the page, and try again."), 400

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403,
                               message="That post belongs to someone else."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404,
                               message="We couldn't find that page. Maybe it got lost too?"), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return render_template("error.html", code=405,
                               message="That action isn't available from this page."), 405

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("error.html", code=500,
                               message="Something went wrong on our end. Please try again."), 500


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
