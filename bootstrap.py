"""Makes `python3 app.py` work on a fresh copy of the project.

If Flask and friends aren't installed, create ./.venv, install requirements.txt
into it, and re-run the same command with that environment's Python.
Uses only the standard library, so it runs before any third-party import.
"""
import os
import subprocess
import sys
import venv

HERE = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(HERE, ".venv")
REQUIREMENTS = os.path.join(HERE, "requirements.txt")
GUARD = "LOSTFOUND_BOOTSTRAPPED"


def _have_dependencies():
    try:
        import flask, flask_login, flask_wtf, wtforms  # noqa: F401,E401
        return True
    except ImportError:
        return False


MANUAL_FIX = ("Install the packages yourself, then run the app again:\n"
              "    python3 -m pip install -r requirements.txt")


def ensure_dependencies():
    if sys.version_info < (3, 9):
        raise SystemExit(f"This app needs Python 3.9 or newer (you have "
                         f"{sys.version.split()[0]}). Please update Python.")
    if _have_dependencies():
        return
    # Only self-install when a project script was run directly (not under gunicorn etc.).
    if os.path.dirname(os.path.abspath(sys.argv[0])) != HERE or os.environ.get(GUARD):
        raise SystemExit("Required packages are missing. " + MANUAL_FIX)

    if os.name == "nt":
        py = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        py = os.path.join(VENV_DIR, "bin", "python")
    print("First run: installing required packages into .venv (one time only)...", flush=True)
    try:
        if not os.path.exists(py):
            venv.create(VENV_DIR, with_pip=True)
        subprocess.check_call([py, "-m", "pip", "install", "--quiet",
                               "--disable-pip-version-check", "-r", REQUIREMENTS])
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"\nCouldn't set up the environment automatically ({exc}).\n"
                         "(No internet, or on Linux the python3-venv package may be missing.)\n"
                         + MANUAL_FIX)
    print("Done. Starting the app...\n", flush=True)
    env = dict(os.environ, **{GUARD: "1"})
    try:
        sys.exit(subprocess.call([py] + sys.argv, env=env))
    except KeyboardInterrupt:  # Ctrl+C reaches the child too; exit quietly
        sys.exit(130)
