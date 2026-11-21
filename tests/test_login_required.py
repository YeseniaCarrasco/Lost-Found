# Login-required test: checks that submitting the new-item form while logged out
# sends the visitor to the login page instead of posting anything.
from urllib.parse import urlparse

from conftest import post_item


def test_posting_while_logged_out_redirects_to_login(client):
    resp = post_item(client, "Sneaky visitor umbrella")
    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/login"
