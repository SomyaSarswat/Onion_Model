import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.models import (
    ImageAnalysisResult, BatchAnalysisResult, CalibrationResult,
    AnalysisRequestSettings, GradingStandard
)
from app.services.roboflow_service import RoboflowService
from app.services.association_service import OnionAssociationService
from app.services.calibration_service import CalibrationService
from app.services.measurement_service import SizeMeasurementService
from app.services.grading_engine import GradingEngine
from app.services.batch_service import BatchAnalysisService
from app.services.report_service import ReportService

app = FastAPI(
    title="Onion Quality Assessment & Grading System API",
    description="Deterministic Grading Engine driven by Roboflow YOLOv8x visual detection",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
association_service = OnionAssociationService()
grading_engine = GradingEngine()

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "roboflow_model_id": settings.ROBOFLOW_MODEL_ID,
        "roboflow_api_key_configured": bool(settings.ROBOFLOW_API_KEY),
        "standards_file": str(settings.STANDARDS_FILE)
    }

@app.get("/api/standards")
def get_standards():
    try:
        grading_engine.reload_standards()
        return grading_engine.standards
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/standards")
def update_standards(standard: GradingStandard):
    try:
        data = standard.model_dump()
        with open(settings.STANDARDS_FILE, "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, indent=2)
        grading_engine.reload_standards()
        return {"status": "success", "message": "Grading standards updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
def get_system_settings():
    return {
        "roboflow_api_key_configured": bool(settings.ROBOFLOW_API_KEY),
        "roboflow_model_id": settings.ROBOFLOW_MODEL_ID,
        "min_defect_confidence": settings.MIN_DEFECT_CONFIDENCE,
        "min_onion_confidence": settings.MIN_ONION_CONFIDENCE,
        "default_ref_type": settings.DEFAULT_REF_TYPE,
        "default_ref_size_mm": settings.DEFAULT_REF_SIZE_MM
    }

@app.post("/api/analyze", response_model=ImageAnalysisResult)
async def analyze_image(
    file: UploadFile = File(...),
    min_defect_confidence: float = Form(0.70),
    min_onion_confidence: float = Form(0.30),
    reference_type: str = Form("coin"),
    reference_size_mm: float = Form(23.0),
    manual_pixels_per_mm: Optional[float] = Form(None)
):
    """
    Executes full multi-stage assessment pipeline on a single image:
    Image -> RoboflowService -> OnionAssociationService -> CalibrationService -> SizeMeasurementService -> GradingEngine
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    image_id = f"img_{uuid.uuid4().hex[:8]}"
    ext = Path(file.filename).suffix or ".jpg"
    temp_path = settings.UPLOADS_DIR / f"{image_id}{ext}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Get Image Dimensions using OpenCV
        import cv2
        img_mat = cv2.imread(str(temp_path))
        if img_mat is None:
            raise HTTPException(status_code=400, detail="Invalid or unreadable image file")
        h, w, _ = img_mat.shape

        # ----------------------------------------------------
        # PHASE 1 — Roboflow Integration
        # ----------------------------------------------------
        roboflow_service = RoboflowService()
        raw_predictions = roboflow_service.analyze_image(str(temp_path))

        # ----------------------------------------------------
        # PHASE 2 — Onion Instance Association
        # ----------------------------------------------------
        onions, unassociated = association_service.associate_instances(
            predictions=raw_predictions,
            min_defect_confidence=min_defect_confidence,
            min_onion_confidence=min_onion_confidence
        )

        # ----------------------------------------------------
        # PHASE 3 — Size Calibration & Measurement
        # ----------------------------------------------------
        calib_service = CalibrationService(ref_type=reference_type, ref_size_mm=reference_size_mm)
        calibration_res = calib_service.detect_reference_object(
            image_path=str(temp_path),
            manual_ppm=manual_pixels_per_mm
        )

        onions = SizeMeasurementService.measure_onions(
            onions=onions,
            calibration=calibration_res
        )

        # ----------------------------------------------------
        # PHASE 4 — Configurable Grading Engine
        # ----------------------------------------------------
        grading_engine.reload_standards()
        onions = grading_engine.evaluate_onions(
            onions=onions,
            min_defect_confidence=min_defect_confidence
        )

        # ----------------------------------------------------
        # PHASE 5 — Individual Onion Report & Warnings
        # ----------------------------------------------------
        warnings = []
        if not calibration_res.detected:
            warnings.append("Physical size could not be measured. Please include the calibration coin/marker in frame.")

        for pred in raw_predictions:
            if pred.confidence < min_defect_confidence:
                warnings.append(f"Low confidence detection ({pred.class_name} {int(pred.confidence*100)}%) — treated as unconfirmed note.")

        if not settings.ROBOFLOW_API_KEY:
            warnings.append("Roboflow API key not configured — using fallback CV detector.")

        # Construct Summary
        g_a = sum(1 for o in onions if o.grade == "GRADE_A")
        urs = sum(1 for o in onions if o.grade == "URS")
        nc = sum(1 for o in onions if o.grade == "NON_COMPLIANT")
        
        summary = {
            "total_onions": len(onions),
            "grade_a_count": g_a,
            "urs_count": urs,
            "non_compliant_count": nc,
            "defect_free_count": sum(1 for o in onions if len(o.defects) == 0)
        }

        return ImageAnalysisResult(
            image_id=image_id,
            filename=file.filename,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            image_width=w,
            image_height=h,
            calibration=calibration_res,
            onions=onions,
            raw_predictions=raw_predictions,
            summary=summary,
            warnings=warnings
        )

    except Exception as e:
        print(f"[Analysis Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch-analyze", response_model=BatchAnalysisResult)
async def batch_analyze_images(
    files: List[UploadFile] = File(...),
    min_defect_confidence: float = Form(0.70),
    min_onion_confidence: float = Form(0.30),
    reference_type: str = Form("coin"),
    reference_size_mm: float = Form(23.0)
):
    """
    Executes batch analysis across multiple images.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded for batch analysis")

    image_results: List[ImageAnalysisResult] = []

    for file in files:
        res = await analyze_image(
            file=file,
            min_defect_confidence=min_defect_confidence,
            min_onion_confidence=min_onion_confidence,
            reference_type=reference_type,
            reference_size_mm=reference_size_mm
        )
        image_results.append(res)

    batch_res = BatchAnalysisService.process_batch(image_results)
    return batch_res

@app.post("/api/generate-pdf")
async def export_pdf_report(batch_result: BatchAnalysisResult):
    """Generates and returns PDF report for download."""
    try:
        pdf_path = ReportService.generate_pdf_report(batch_result)
        return FileResponse(
            path=pdf_path,
            filename=Path(pdf_path).name,
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")
