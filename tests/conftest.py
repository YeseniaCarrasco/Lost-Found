"""Shared pytest fixtures.

Every test gets a brand-new SQLite file inside pytest's tmp_path, so the real
instance/lostfound.db is never opened. DATABASE_PATH is set *before* app.py is
imported, because app.py builds an app (and its database) at import time.
"""
import importlib
import sqlite3
from datetime import date

import pytest

PASSWORD = "test-pass-123"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-not-for-production")
    monkeypatch.delenv("K_SERVICE", raising=False)  # never run in "production" mode

    app_module = importlib.import_module("app")  # first import happens here, env already set
    flask_app = app_module.create_app()           # fresh app for this test's database
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    assert flask_app.config["DATABASE"] == str(tmp_path / "test.db")
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def query(app, sql, params=()):
    """Read straight from this test's database."""
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def register(client, username, password=PASSWORD):
    """Create an account; the app logs the new user in straight away."""
    resp = client.post("/register", data={
        "username": username, "password": password, "confirm": password,
    })
    assert resp.status_code == 302, "registration should redirect on success"
    return resp


def post_item(client, title, location="Library front desk", description="",
              category="Other"):
    return client.post("/items/new", data={
        "title": title,
        "category": category,
        "location": location,
        "found_date": date.today().isoformat(),
        "photo_url": "",
        "description": description,
    })
