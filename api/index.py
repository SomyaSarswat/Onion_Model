import sys
import os
from pathlib import Path

# Ensure api directory and root directory are in sys.path
api_dir = Path(__file__).resolve().parent
root_dir = api_dir.parent

for p in [str(api_dir), str(root_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.main import app
except Exception as e:
    try:
        from api.app.main import app
    except Exception as e2:
        from fastapi import FastAPI
        app = FastAPI()
        @app.get("/api/health")
        def error_health():
            return {"status": "error", "message": f"e1: {e}, e2: {e2}"}
