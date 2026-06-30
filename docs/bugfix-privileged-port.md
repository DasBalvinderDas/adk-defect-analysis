# Bug Fix Documentation

## Repository
- **URL:** https://github.com/DasBalvinderDas/adk-defect-analysis

## Branches
- **Base Branch:** main
- **Fix Branch:** bugfix/privileged-port

## Error
```
PermissionError: [Errno 13] Permission denied
 
Traceback (most recent call last):
  File "/app/app.py", line 66, in <module>
    app.run(host="0.0.0.0", port=PORT)
  File "/usr/local/lib/python3.11/site-packages/flask/app.py", line 662, in run
    run_simple(host, port, self, **options)
  File "/usr/local/lib/python3.11/site-packages/werkzeug/serving.py", line 1093, in run_simple
    srv = make_server(
  File "/usr/local/lib/python3.11/site-packages/werkzeug/serving.py", line 930, in make_server
    return ThreadedWSGIServer(
  File "/usr/local/lib/python3.11/site-packages/werkzeug/serving.py", line 759, in __init__
    self.server_bind()
  File "/usr/local/lib/python3.11/http/server.py", line 136, in server_bind
    socketserver.TCPServer.server_bind(self)
  File "/usr/local/lib/python3.11/socketserver.py", line 472, in server_bind
    self.socket.bind(self.server_address)
PermissionError: [Errno 13] Permission denied
```

## Root Cause Analysis
The application attempted to bind to a privileged port (80) inside a container, leading to a PermissionError.

### Technical Note
- **Issue:** The application failed to start within a containerized environment, specifically reporting a `PermissionError: [Errno 13] Permission denied` during the port binding phase.
- **Root Cause:** The application was configured to bind to port 80. In Linux systems, ports numbered 0-1023 are considered 'privileged ports' and require root user privileges to bind. Containerized applications are often run as non-root users for security reasons, thus lacking the necessary permissions.
- **Resolution:** The application's configuration in `app.py` was modified to change its listening port from 80 to 8080. Port 8080 is an unprivileged port, allowing the application to bind successfully without requiring elevated permissions.
- **Prevention/Best Practices:**
  - **Prefer Unprivileged Ports:** Always configure containerized applications to listen on unprivileged ports (e.g., 8080, 5000) by default.
  - **Port Mapping:** If external access on a privileged port (like 80 or 443) is required, use container orchestration tools (e.g., Docker, Kubernetes) to map an external privileged port to the container's internal unprivileged port (e.g., `docker run -p 80:8080`).
  - **Non-Root Users:** Ensure container images are designed to run applications as non-root users to enhance security and prevent issues with privileged resources.

## Fix Summary
Changed the application's listening port from 80 to 8080 to avoid PermissionError when running in a container.

### Release Note
This update resolves an issue where the application might fail to start in certain containerized environments due to port binding restrictions. The application will now correctly start and be accessible without encountering permission errors.

### Internal Changelog
- Updated `app.py` to change the application's default listening port from 80 to 8080.
- Resolved `PermissionError: [Errno 13] Permission denied` encountered when binding to privileged ports in containerized deployments.

## Files Changed
- `app.py`