# Campus Lost & Found

A Flask web app where anyone can browse items found on campus. Logged-in users can post found items (what, where, when, a photo URL), edit them, and mark their own posts as **returned**. Search and filters let visitors find things fast.

## Features

| Requirement | Where |
|---|---|
| Browse found items (no login needed) | `/`, with pagination, plus item pages at `/items/<id>` |
| Search box | Matches title, description and location (`LIKE`, with wildcards escaped) |
| “Still unclaimed” filter | Checkbox on the home page; also a category filter |
| User accounts | `/register`, `/login`, `/logout` (Flask-Login) |
| Post items: what, where, when, photo URL | `/items/new` (WTForms validation: no future dates, http/https URLs only) |
| Mark own posts returned / unclaimed | Button on the item page and on your user page (owner-only, else 403) |
| Each user has a page with their posts | `/u/<username>` |
| Forms | Flask-WTF / WTForms, with CSRF protection on every POST |
| Cookies | Signed session cookie, “Keep me signed in” remember-me cookie, and an `unclaimed_only` cookie that remembers the filter choice for 90 days |
| SQLite database | `instance/lostfound.db`; schema in [db.py](db.py) |
| Fictitious data | [seed.py](seed.py): 6 users and 40 items; the database is seeded automatically when it's empty |

### Password security
Passwords are never stored as entered. `werkzeug.security.generate_password_hash` stores **scrypt** hashes, each with its own random 16-character **salt**, for example `scrypt:32768:8:1$<salt>$<hash>`. Logins are checked with `check_password_hash`.

Other protections:
- Every POST form has a CSRF token.
- Session cookies are `HttpOnly` and `SameSite=Lax`, and `Secure` on Cloud Run.
- Every query is parameterized, which prevents SQL injection.
- Jinja escapes all output automatically, which prevents XSS.
- `?next=` redirects can only point to pages on this site.

## Python packages used

| Package | Why |
|---|---|
| **Flask** | Web framework (routing, Jinja templates, sessions) |
| **Flask-Login** | User sessions, `@login_required`, remember-me cookie |
| **Flask-WTF** / **WTForms** | Form classes, validation, CSRF protection |
| **Werkzeug** (installed with Flask) | Salted password hashing (`scrypt`), `ProxyFix` for Cloud Run |
| **gunicorn** | Production WSGI server inside the container |
| `sqlite3` (standard library) | Database access, with plain SQL |

## Run locally

Requires Python 3.9 or newer. No setup needed:

```bash
python3 app.py          # then open http://127.0.0.1:5000
```

On the first run, if Flask isn't installed, [bootstrap.py](bootstrap.py) creates a local `.venv`, installs `requirements.txt` into it (one time, about 10 seconds) and starts the app. If you prefer to install the packages yourself, run `python3 -m pip install -r requirements.txt`.

The SQLite database (`instance/lostfound.db`) is created and filled with demo data automatically. Reset it at any time with `python3 seed.py --reset`.

**Demo accounts.** Every account uses the password `demo-pass-123`:
`maria.lopez`, `jchen`, `priya_k`, `sam.okafor`, `lib_desk`, `rec_center`.

## Project layout

```
app.py          routes, login, cookies, app factory
db.py           SQLite connection and schema
forms.py        WTForms classes
seed.py         fictitious demo data
templates/      Jinja templates (base layout, macros, pages)
static/         CSS, placeholder image, favicon
Dockerfile      container used by Cloud Run
```

## Deploying to Cloud Run (later)

```bash
gcloud run deploy lost-found --source . --region us-west1 --allow-unauthenticated \
  --set-env-vars SECRET_KEY=<long random string> \
  --min-instances 1 --max-instances 1
```

On Cloud Run the app refuses to start without a `SECRET_KEY`.

**SQLite on Cloud Run.** The container's disk is temporary. The demo database is built into the image, so the site always starts populated. New accounts and posts last as long as the running instance does. Pinning the service to exactly one instance (`--min-instances 1 --max-instances 1`) means every visitor sees the same data, and that data survives between requests. A redeploy, or a restart by Cloud Run, resets the database to the demo data.
