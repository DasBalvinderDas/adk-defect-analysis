# Release Note

This update resolves an issue that previously prevented the application from reliably storing data in containerized environments. Your application data will now persist correctly.

# Internal Changelog

*   Updated `DB_PATH` in `app.py` from a hardcoded absolute path (`/var/lib/myapp/data.db`) to a container-safe relative path (`./data.db`).
*   Resolved `sqlite3.OperationalError: unable to open database file` encountered when running the application in a containerized environment.

# Technical RCA Note

**Root Cause Analysis (RCA):**

*   **Cause:** The application's SQLite database path was hardcoded to `/var/lib/myapp/data.db`, an absolute local filesystem path. In a containerized runtime, this path is often not present, not writable by the application's user, or unsuitable for durable state, leading to a `sqlite3.OperationalError: unable to open database file`.
*   **Fix:** The `DB_PATH` variable in `app.py` was modified from `/var/lib/myapp/data.db` to `./data.db`. This change directs the SQLite database to be created in the application's working directory, which is typically writable and suitable for data persistence within a container or a mounted volume.
*   **Prevention:**
    *   **Avoid Hardcoded Paths:** Do not hardcode absolute filesystem paths for persistent data storage within container images.
    *   **Environment Variables:** Utilize environment variables (e.g., `DB_PATH_ENV`) to configure persistent data locations, allowing flexible specification at container runtime.
    *   **Relative Paths for Ephemeral/Local Data:** Use relative paths for data files intended to reside within the container's working directory or alongside the application code, especially for non-critical or development databases.
    *   **Volume Mounts for Durable State:** For production and durable application state, always leverage container orchestration mechanisms (e.g., Docker volumes, Kubernetes Persistent Volumes) to mount external, persistent storage locations.
    *   **Containerization Testing:** Implement comprehensive testing early in the development lifecycle to validate application behavior in containerized environments, specifically checking for filesystem access and persistence issues.
