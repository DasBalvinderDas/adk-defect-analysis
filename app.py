import os
import sqlite3
import threading
import subprocess
import logging
from flask import Flask, request

app = Flask(__name__)

# ❌ BLOCKER: Writes to host filesystem (local persistence)
DB_PATH = "/var/lib/myapp/data.db"  # NOT recommended for containers

# ❌ BLOCKER: Hardcoded secret (Security Issue)
API_KEY = "sk_test_1234567890abcdef"

# ❌ BLOCKER: Uses privileged port
PORT = 80  # Should be 8080+ in containers

# ❌ BLOCKER: Logging to file instead of stdout
logging.basicConfig(filename='/tmp/app.log', level=logging.INFO)

@app.route("/")
def index():
    logging.info("Received request")
    return "Hello from a potentially insecure container!"

@app.route("/write")
def write_to_db():
    try:
        # ❌ BLOCKER: Writes to a fixed location on host volume
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
    # ❌ BLOCKER: Tries to read host /etc/passwd
    try:
        with open("/etc/passwd", "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading host file: {str(e)}"

@app.route("/shell")
def run_shell():
    # ❌ BLOCKER: Using subprocess in web app
    try:
        output = subprocess.check_output(["ls", "-l", "/tmp"])
        return output.decode()
    except Exception as e:
        return f"Shell error: {str(e)}"

def background_worker():
    while True:
        # ❌ BLOCKER: Infinite loop, no exit signal handling
        with open("/tmp/heartbeat.txt", "a") as f:
            f.write("alive\n")

# ❌ BLOCKER: Background thread not managed or stopped gracefully
threading.Thread(target=background_worker, daemon=True).start()

if __name__ == "__main__":
    # ❌ BLOCKER: Running on privileged port, without container health checks or shutdown hooks
    app.run(host="0.0.0.0", port=PORT)
