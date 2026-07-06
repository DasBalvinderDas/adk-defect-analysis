import os
import sqlite3
import threading
import subprocess
import logging
import sys # Import sys for stdout
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


# FIX: Hardcoded secret Security Issue - load from environment
API_KEY = os.getenv("API_KEY")

# FIX: Uses privileged port - load from environment, default to 8080
PORT = int(os.getenv("PORT", 8080))

# FIX: Logging to file instead of stdout - log to stdout by default
LOG_TO_STDOUT = os.getenv("LOG_TO_STDOUT", "true").lower() == "true"
if LOG_TO_STDOUT:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
else:
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/tmp/app.log")
    logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO)

# FIX: Host filesystem read route is enabled by default - disable by default
HOSTPATH_ROUTE_ENABLED = os.getenv("HOSTPATH_ROUTE_ENABLED", "false").lower() == "true"

# FIX: Background worker has no graceful shutdown flag - implement graceful shutdown
stop_event = threading.Event() # Create a stop event for the worker
BACKGROUND_WORKER_HAS_STOP_EVENT = True # This is now true


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

    if not API_KEY or API_KEY.startswith("sk_test_"):
        errors.append("API_KEY is missing or is a hardcoded test key — must be loaded from environment/secret manager")

    if PORT < 1024:
        errors.append(f"PORT={PORT} is a privileged port — use PORT >= 1024 in containers")

    # The logging check now depends on LOG_TO_STDOUT
    if not LOG_TO_STDOUT:
        errors.append("Logging writes to a file instead of stdout — breaks log aggregation in containers (set LOG_TO_STDOUT=true)")

    if HOSTPATH_ROUTE_ENABLED:
        errors.append("/hostpath route exposes host filesystem reads and must be disabled by default (set HOSTPATH_ROUTE_ENABLED=false)")

    if not BACKGROUND_WORKER_HAS_STOP_EVENT: # This should now always be true
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
    if not HOSTPATH_ROUTE_ENABLED:
        return "Hostpath route is disabled.", 403
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
    while not stop_event.is_set(): # Loop until stop_event is set
        with open("/tmp/heartbeat.txt", "a") as f:
            f.write("alive\n")
        stop_event.wait(5) # Wait for a short period or until signaled to stop


threading.Thread(target=background_worker, daemon=True).start()

if __name__ == "__main__":
    # Fail fast: run config validation before the server ever binds a socket
    validate_config()
    app.run(host="0.0.0.0", port=PORT)