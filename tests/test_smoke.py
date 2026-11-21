# Smoke test: checks that the app starts and its health-check page (/healthz) answers with 200 OK.


def test_healthz_returns_200(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
