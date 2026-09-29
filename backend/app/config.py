import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

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
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "app" / "data"
    STANDARDS_FILE: Path = DATA_DIR / "grading_standards.json"
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    REPORTS_DIR: Path = BASE_DIR / "reports"

settings = Settings()

# Ensure directories exist
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
