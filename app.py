import os
import sqlite3
import threading
import subprocess
import logging
from flask import Flask, request

app = Flask(__name__)

# FIX: DB path is now configurable and uses a container-writable demo path
DB_PATH = os.getenv("DB_PATH", "/tmp/myapp/data.db")


def ensure_db_directory() -> None:
    """
    Ensure the SQLite database directory exists before opening the DB file.
    Step 1 – Extract the directory path from DB_PATH
    Step 2 – Create the directory if it does not already exist
    Step 3 – Allow sqlite3.connect(DB_PATH) to open the database safely
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


# BLOCKER: Hardcoded secret Security Issue
API_KEY = "sk_test_1234567890abcdef"

# BLOCKER: Uses privileged port
PORT = 80  # Should be 8080+ in containers

# BLOCKER: Logging to file instead of stdout
LOG_FILE_PATH = "/tmp/app.log"
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO)

# BLOCKER: Host filesystem read route is enabled by default
HOSTPATH_ROUTE_ENABLED = True

# BLOCKER: Background worker has no graceful shutdown flag
BACKGROUND_WORKER_HAS_STOP_EVENT = False


class ConfigurationError(Exception):
    """Raised when one or more startup configuration checks fail."""
    pass


def validate_config() -> None:
    """
    Runs all container-readiness checks in one pass and fails fast with a
    single aggregated error if any check fails, instead of letting the app
    boot into a broken/insecure state.
    """
    errors = []

    if API_KEY.startswith("sk_test_"):
        errors.append("API_KEY is a hardcoded test key — must be loaded from environment/secret manager")

    if PORT < 1024:
        errors.append(f"PORT={PORT} is a privileged port — use PORT >= 1024 in containers")

    if LOG_FILE_PATH != "stdout":
        errors.append(f"Logging writes to '{LOG_FILE_PATH}' instead of stdout — breaks log aggregation in containers")

    if HOSTPATH_ROUTE_ENABLED:
        errors.append("/hostpath route exposes host filesystem reads and must be disabled by default")

    if not BACKGROUND_WORKER_HAS_STOP_EVENT:
        errors.append("background_worker() has no graceful shutdown mechanism (infinite loop, no stop signal)")

    if errors:
        raise ConfigurationError(
            f"Startup validation failed with {len(errors)} issue(s):\n- " + "\n- ".join(errors)
        )


@app.route("/")
def index():
    logging.info("Received request")
    return "Hello from a potentially insecure container!"


@app.route("/write")
def write_to_db():
    try:
        ensure_db_directory()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS visits (ip TEXT)")
        cursor.execute("INSERT INTO visits (ip) VALUES (?)", (request.remote_addr,))
        conn.commit()
        conn.close()
        return "Data written!"
    except Exception as e:
        return f"DB error: {str(e)}"


@app.route("/hostpath")
def list_host_path():
    try:
        with open("/etc/passwd", "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading host file: {str(e)}"


@app.route("/shell")
def run_shell():
    try:
        output = subprocess.check_output(["ls", "-l", "/tmp"])
        return output.decode()
    except Exception as e:
        return f"Shell error: {str(e)}"


def background_worker():
    while True:
        with open("/tmp/heartbeat.txt", "a") as f:
            f.write("alive\n")


threading.Thread(target=background_worker, daemon=True).start()

if __name__ == "__main__":
    # Fail fast: run config validation before the server ever binds a socket
    validate_config()
    app.run(host="0.0.0.0", port=PORT)
