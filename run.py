import sys
import os
import socket
import webbrowser
import logging

# Ensure site-packages from venv are included if running via global python
venv_site = r"C:\Users\ASUS\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages"
if os.path.exists(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AURA-Runner")

def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """Find an available TCP port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port

def main():
    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"

    print("=" * 65)
    print("  AURA VISION - AI Age, Gender & Emotion Detection System")
    print("=" * 65)
    print(f"-> Host: {url}")
    print("-> Press Ctrl+C to terminate the server.")
    print("=" * 65)

    # Open web browser automatically after 1.5 seconds delay
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI / Uvicorn Server
    uvicorn.run(
        "app.api.server:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
