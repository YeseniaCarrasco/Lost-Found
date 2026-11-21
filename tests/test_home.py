# Home page test: checks that the home page loads (200) and lists at least one found item.
# If the test database happens to be empty, it posts one item first.
import html

from conftest import post_item, query, register


def test_home_page_shows_an_item(app, client):
    if not query(app, "SELECT 1 FROM items LIMIT 1"):
        register(client, "home_tester")
        post_item(client, "Test umbrella")

    # The newest item is the one the home page lists first.
    newest = query(app, "SELECT title FROM items ORDER BY found_date DESC, id DESC LIMIT 1")[0]

    resp = client.get("/")
    assert resp.status_code == 200
    assert newest["title"] in html.unescape(resp.get_data(as_text=True))
