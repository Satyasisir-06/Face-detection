# Vercel-compatible entrypoint — auto-detected at app/main.py
# Re-exports the FastAPI instance from the actual server module.
from app.api.server import app  # noqa: F401
