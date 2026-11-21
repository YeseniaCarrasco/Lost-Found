"""Tests for the main rules of the Lost & Found app, using Flask's test client."""
import html
from urllib.parse import urlparse

from conftest import post_item, query, register


def item_count(app):
    return query(app, "SELECT COUNT(*) AS n FROM items")[0]["n"]


# 1. Home page ---------------------------------------------------------------

def test_home_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Campus Lost & Found" in html.unescape(resp.get_data(as_text=True))


# 2. Visitors must log in to post ----------------------------------------------

def test_visitor_cannot_open_post_form(client):
    resp = client.get("/items/new")
    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/login"


def test_visitor_post_is_redirected_to_login_and_creates_nothing(app, client):
    before = item_count(app)

    resp = post_item(client, "Sneaky visitor umbrella")

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/login"
    assert item_count(app) == before
    assert query(app, "SELECT 1 FROM items WHERE title = ?", ("Sneaky visitor umbrella",)) == []


# 3. Logged-in users can post ----------------------------------------------------

def test_logged_in_user_can_post_item_and_it_appears_on_list(app, client):
    register(client, "tester_one")
    before = item_count(app)

    resp = post_item(client, "Orange test water bottle", location="Quad fountain")

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path.startswith("/items/")
    assert item_count(app) == before + 1

    rows = query(app, """SELECT i.*, u.username FROM items i JOIN users u ON u.id = i.user_id
                         WHERE i.title = ?""", ("Orange test water bottle",))
    assert len(rows) == 1
    assert rows[0]["username"] == "tester_one"
    assert rows[0]["status"] == "unclaimed"

    # Found today, so it is first on page 1 of the list.
    home = client.get("/")
    assert home.status_code == 200
    assert "Orange test water bottle" in home.get_data(as_text=True)


# 4. Only the owner can edit or mark returned -------------------------------------

def test_user_cannot_edit_or_mark_returned_someone_elses_item(app):
    owner = app.test_client()
    register(owner, "item_owner")
    post_item(owner, "Owner's red notebook", location="Lecture hall B")
    item = query(app, "SELECT * FROM items WHERE title = ?", ("Owner's red notebook",))[0]

    other = app.test_client()
    register(other, "someone_else")

    # Opening the edit form is refused.
    assert other.get(f"/items/{item['id']}/edit").status_code == 403

    # Submitting an edit is refused.
    resp = other.post(f"/items/{item['id']}/edit", data={
        "title": "Hijacked title",
        "category": "Other",
        "location": "Nowhere",
        "found_date": item["found_date"],
        "photo_url": "",
        "description": "",
    })
    assert resp.status_code == 403

    # Marking it returned is refused.
    assert other.post(f"/items/{item['id']}/status").status_code == 403

    # And nothing changed in the database.
    after = query(app, "SELECT * FROM items WHERE id = ?", (item["id"],))[0]
    assert after["title"] == "Owner's red notebook"
    assert after["location"] == "Lecture hall B"
    assert after["status"] == "unclaimed"
    assert after["returned_at"] is None


def test_owner_can_still_mark_own_item_returned(app, client):
    """Control for the test above: the 403 is about ownership, not a broken route."""
    register(client, "item_owner")
    post_item(client, "Owner's blue mug")
    item = query(app, "SELECT id FROM items WHERE title = ?", ("Owner's blue mug",))[0]

    assert client.post(f"/items/{item['id']}/status").status_code == 302
    assert query(app, "SELECT status FROM items WHERE id = ?", (item["id"],))[0]["status"] == "returned"


# 5. Search ----------------------------------------------------------------------

def test_search_by_title_word_finds_item(app, client):
    register(client, "searcher")
    # The search word is only in the title, not the location or description.
    post_item(client, "Zebra-striped pencil case", location="Library front desk",
              description="Has a few pens inside")

    resp = client.get("/", query_string={"q": "Zebra"})
    page = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "Zebra-striped pencil case" in page
    # A seeded item that doesn't match shouldn't be listed.
    assert "Kindle Paperwhite" not in page
