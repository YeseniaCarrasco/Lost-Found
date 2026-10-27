"""Campus Lost & Found — a small Flask + SQLite web app."""
import os
from datetime import date

from flask import Flask, abort, render_template, request

import db

PER_PAGE = 12


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "lostfound.db"),
    )

    app.teardown_appcontext(db.close_db)
    db.init_db(app.config["DATABASE"])

    register_routes(app)
    return app


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

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404,
                               message="We couldn't find that page. Maybe it got lost too?"), 404


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
