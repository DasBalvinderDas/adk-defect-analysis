# Defect Fix Documentation

## Repository
- URL: https://github.com/DasBalvinderDas/adk-defect-analysis
- Base Branch: main
- Fix Branch: fix/permission-denied-port

## Error
```
PermissionError: [Errno 13] Permission denied

Trace -
Traceback (most recent call last): File "/app/app.py", line 66, in <module> app.run(host="0.0.0.0", port=PORT) File "/usr/local/lib/python3.11/site-packages/flask/app.py", line 662, in run run_simple(host, port, self, **options) File "/usr/local/lib/python3.11/site-packages/werkzeug/serving.py", line 1093, in run_simple srv = make_server( File "/usr/local/lib/python3.11/site-packages/werkzeug/serving.py", line 930, in make_server return ThreadedWSGIServer( File "/usr/local/lib/python3.11/site-packages/werkzeug/serving.py", line 759, in init self.server_bind() File "/usr/local/lib/python3.11/http/server.py", line 136, in server_bind socketserver.TCPServer.server_bind(self) File "/usr/local/lib/python3.11/socketserver.py", line 472, in server_bind self.socket.bind(self.server_address) PermissionError: [Errno 13] Permission denied
```

## Root Cause
The application attempted to bind to a privileged port (port 80) without the necessary permissions, leading to a PermissionError.

## Fix Summary
Changed the application's listening port from 80 to 5000, which is a non-privileged port, resolving the PermissionError.

## Files Changed
- app.py

---

### Release Note
This update resolves an issue that prevented the application from starting correctly on some systems. The application will now launch reliably, improving its availability and ease of use.

### Internal Changelog
- Fixed application startup failure caused by a `PermissionError` when binding to a privileged port.
- Changed the application's default listening port from 80 to 5000 in `app.py`.

### Technical RCA Note
**Root Cause Analysis (RCA):**
- **Cause**: The application attempted to bind to a privileged port (port 80) without the necessary root permissions, resulting in a `PermissionError: [Errno 13] Permission denied` during server initialization.
- **Fix**: The application's listening port was changed from the privileged port 80 to the non-privileged port 5000 within `app.py`.
- **Prevention Steps**:
  - Avoid hardcoding privileged ports (0-1023) in application code, particularly for applications not intended to run as root.
  - Utilize non-privileged ports (e.g., 1024-65535) for standard user-space applications.
  - Implement configurable port settings (e.g., via environment variables or configuration files) to allow for flexible port assignments at deployment time.
  - Ensure applications adhere to the principle of least privilege, running with only the necessary permissions.
  - Conduct thorough testing in target environments to identify and resolve port conflicts or permission issues early in the development cycle.
