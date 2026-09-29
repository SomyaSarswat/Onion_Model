import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

_base_dir = Path(__file__).resolve().parent.parent
_is_serverless = os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

class Settings:
    ROBOFLOW_API_KEY: str = os.getenv("ROBOFLOW_API_KEY", "")
    ROBOFLOW_MODEL_ID: str = os.getenv("ROBOFLOW_MODEL_ID", "veg1-hcqsf-2/4")
    ROBOFLOW_API_URL: str = os.getenv("ROBOFLOW_API_URL", "https://detect.roboflow.com")
    
    # Model Classes
    ONION_CLASS_NAME: str = "onion"
    DEFECT_CLASSES: list[str] = [
        "Black smut",
        "double_split",
        "Spoiled",
        "sprouted",
        "Staining"
    ]
    
    # Confidence Thresholds
    MIN_DEFECT_CONFIDENCE: float = float(os.getenv("MIN_DEFECT_CONFIDENCE", "0.70"))
    MIN_ONION_CONFIDENCE: float = float(os.getenv("MIN_ONION_CONFIDENCE", "0.30"))
    
    # Calibration Defaults
    DEFAULT_REF_TYPE: str = "coin"
    DEFAULT_REF_SIZE_MM: float = 23.0  # standard coin diameter in mm
    
    # Paths
    BASE_DIR: Path = _base_dir
    DATA_DIR: Path = BASE_DIR / "app" / "data"
    STANDARDS_FILE: Path = DATA_DIR / "grading_standards.json"
    UPLOADS_DIR: Path = (Path(tempfile.gettempdir()) / "uploads") if _is_serverless else (BASE_DIR / "uploads")
    REPORTS_DIR: Path = (Path(tempfile.gettempdir()) / "reports") if _is_serverless else (BASE_DIR / "reports")

settings = Settings()

# Ensure directories exist
try:
    settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    settings.UPLOADS_DIR = Path(tempfile.gettempdir()) / "uploads"
    settings.REPORTS_DIR = Path(tempfile.gettempdir()) / "reports"
    settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
