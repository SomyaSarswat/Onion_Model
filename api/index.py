import sys
import os
from pathlib import Path

# Add backend directory and current root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from app.main import app
except Exception as e:
    print(f"Error importing FastAPI app: {e}")
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/api/health")
    def error_health():
        return {"status": "error", "message": str(e)}
