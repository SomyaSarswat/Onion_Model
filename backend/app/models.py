from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x: float = Field(..., description="Center X coordinate")
    y: float = Field(..., description="Center Y coordinate")
    width: float = Field(..., description="Width of bounding box")
    height: float = Field(..., description="Height of bounding box")
    xmin: float = Field(..., description="Top-left X coordinate")
    ymin: float = Field(..., description="Top-left Y coordinate")
    xmax: float = Field(..., description="Bottom-right X coordinate")
    ymax: float = Field(..., description="Bottom-right Y coordinate")

class RoboflowPrediction(BaseModel):
    class_name: str = Field(..., alias="class")
    confidence: float
    x: float
    y: float
    width: float
    height: float
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    class Config:
        populate_by_name = True

class DefectInstance(BaseModel):
    defect_class: str
    confidence: float
    bbox: BoundingBox
    is_confirmed: bool
    status_text: str

class OnionCheck(BaseModel):
    criterion: str
    value: str
    limit: str
    status: str  # "PASS" or "FAIL"

class OnionInstance(BaseModel):
    id: str
    bbox: BoundingBox
    confidence: float
    defects: List[DefectInstance] = []
    diameter_px: float
    diameter_mm: Optional[float] = None
    measurement_method: Optional[str] = None
    grade: Optional[str] = None  # "GRADE_A", "URS", "NON_COMPLIANT"
    reasons: List[str] = []
    checks: List[OnionCheck] = []

class CalibrationResult(BaseModel):
    detected: bool
    ref_type: str
    ref_size_mm: float
    ref_pixel_width: Optional[float] = None
    pixels_per_mm: Optional[float] = None
    ref_bbox: Optional[Dict[str, float]] = None
    message: str

class ImageAnalysisResult(BaseModel):
    image_id: str
    filename: str
    timestamp: str
    image_width: int
    image_height: int
    calibration: CalibrationResult
    onions: List[OnionInstance]
    raw_predictions: List[RoboflowPrediction]
    summary: Dict[str, Any]
    warnings: List[str]

class BatchAnalysisResult(BaseModel):
    batch_id: str
    timestamp: str
    total_images: int
    total_onions: int
    grade_a_count: int
    grade_a_percent: float
    urs_count: int
    urs_percent: float
    non_compliant_count: int
    non_compliant_percent: float
    stats: Dict[str, Optional[float]]  # mean, median, min, max diameter
    defect_counts: Dict[str, int]
    images: List[ImageAnalysisResult]
    warnings: List[str]

class GradeLimits(BaseModel):
    min_diameter_mm: float
    max_diameter_mm: float
    max_staining_percent: float = 0.0
    max_sunburn_percent: float = 0.0
    sprouted_allowed: bool = False
    spoiled_allowed: bool = False
    double_split_allowed: bool = False
    black_smut_allowed: bool = False

class GradingStandard(BaseModel):
    standard_name: str
    description: Optional[str] = ""
    grade_a: GradeLimits
    urs: GradeLimits

class AnalysisRequestSettings(BaseModel):
    min_defect_confidence: float = 0.70
    min_onion_confidence: float = 0.30
    reference_type: str = "coin"  # "coin", "aruco", "manual", "none"
    reference_size_mm: float = 23.0
    manual_pixels_per_mm: Optional[float] = None
