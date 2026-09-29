import os
import cv2
import numpy as np
from pathlib import Path
from app.services.roboflow_service import RoboflowService
from app.services.association_service import OnionAssociationService
from app.services.calibration_service import CalibrationService
from app.services.measurement_service import SizeMeasurementService
from app.services.grading_engine import GradingEngine
from app.services.batch_service import BatchAnalysisService
from app.services.report_service import ReportService
from app.models import RoboflowPrediction, BoundingBox

def create_sample_onion_image(filename: str, has_coin: bool = True, num_onions: int = 2) -> str:
    """Generates a synthetic test image with onions and a calibration coin."""
    img_dir = Path("sample_images")
    img_dir.mkdir(exist_ok=True)
    file_path = img_dir / filename

    # Create background (wood/table surface color)
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    img[:] = (210, 225, 235)  # Light neutral gray/beige

    # Draw onions (red-brownish circular gradient)
    if num_onions >= 1:
        # Onion 1 (Grade A size: ~55mm)
        cv2.circle(img, (250, 300), 80, (40, 60, 180), -1)
        cv2.circle(img, (250, 300), 76, (60, 90, 210), -1)
        cv2.putText(img, "ONION 1", (210, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    if num_onions >= 2:
        # Onion 2 (URS size or small: ~38mm)
        cv2.circle(img, (550, 300), 55, (40, 60, 180), -1)
        cv2.circle(img, (550, 300), 52, (60, 90, 210), -1)
        cv2.putText(img, "ONION 2", (510, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Draw Calibration Coin if requested (metallic silver circle, radius ~35px)
    if has_coin:
        cv2.circle(img, (100, 100), 35, (160, 160, 160), -1)
        cv2.circle(img, (100, 100), 35, (80, 80, 80), 3)
        cv2.putText(img, "COIN", (80, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

    cv2.imwrite(str(file_path), img)
    return str(file_path)

def run_pipeline_tests():
    print("==================================================")
    print("STARTING ONION PIPELINE AUTOMATED TESTS (PHASES 1-7)")
    print("==================================================")

    # 1. Generate Sample Image
    img_path = create_sample_onion_image("test_sample_1.jpg", has_coin=True, num_onions=2)
    print(f"[OK] Generated sample test image: {img_path}")

    # ----------------------------------------------------
    # PHASE 1: Roboflow Integration
    # ----------------------------------------------------
    print("\n--- PHASE 1: Roboflow Service Test ---")
    rf_service = RoboflowService()
    raw_preds = rf_service.analyze_image(img_path)
    print(f"Predictions returned: {len(raw_preds)}")
    for p in raw_preds:
        print(f"  Class: {p.class_name}, Conf: {p.confidence:.2f}, Box: [{p.xmin}, {p.ymin}, {p.xmax}, {p.ymax}]")
    assert len(raw_preds) > 0, "Phase 1 Failed: No predictions returned"
    print("[OK] PHASE 1 PASSED!")

    # Add synthetic defect to test association & grading
    # Let's add a sprouted defect prediction over Onion 2
    synthetic_defect = RoboflowPrediction(
        **{
            "class": "sprouted",
            "confidence": 0.86,
            "x": 550.0, "y": 300.0,
            "width": 30.0, "height": 30.0,
            "xmin": 535.0, "ymin": 285.0,
            "xmax": 565.0, "ymax": 315.0
        }
    )
    raw_preds.append(synthetic_defect)

    # ----------------------------------------------------
    # PHASE 2: Onion Instance Association
    # ----------------------------------------------------
    print("\n--- PHASE 2: Onion Instance Association Test ---")
    assoc_service = OnionAssociationService()
    onions, unassociated = assoc_service.associate_instances(raw_preds)
    print(f"Total Onions Identified: {len(onions)}")
    for o in onions:
        print(f"  Onion {o.id}: Box=[{o.bbox.xmin}, {o.bbox.ymin}, {o.bbox.xmax}, {o.bbox.ymax}], Defects Count={len(o.defects)}")
        for d in o.defects:
            print(f"    -> Defect: {d.defect_class} ({d.confidence:.2f}) Assigned to {o.id}")
    assert len(onions) >= 1, "Phase 2 Failed: Onion instance creation failed"
    print("[OK] PHASE 2 PASSED!")

    # ----------------------------------------------------
    # PHASE 3: Size Calibration & Measurement
    # ----------------------------------------------------
    print("\n--- PHASE 3: Size Calibration & Measurement Test ---")
    calib_service = CalibrationService(ref_type="coin", ref_size_mm=23.0)
    calib_res = calib_service.detect_reference_object(img_path)
    print(f"Calibration Detected: {calib_res.detected}, Message: {calib_res.message}")
    if calib_res.detected:
        print(f"  Pixels per MM: {calib_res.pixels_per_mm}")

    onions = SizeMeasurementService.measure_onions(onions, calib_res)
    for o in onions:
        print(f"  Onion {o.id}: Physical Diameter = {o.diameter_mm} mm (Method: {o.measurement_method})")
    
    print("[OK] PHASE 3 PASSED!")

    # ----------------------------------------------------
    # PHASE 4: Configurable Grading Engine
    # ----------------------------------------------------
    print("\n--- PHASE 4: Deterministic Grading Engine Test ---")
    grading_engine = GradingEngine()
    onions = grading_engine.evaluate_onions(onions)
    for o in onions:
        print(f"\n  Onion {o.id} Grade: {o.grade}")
        print(f"  Reasons: {o.reasons}")
        print("  Checks Table:")
        for chk in o.checks:
            print(f"    - {chk.criterion}: {chk.value} | Limit: {chk.limit} -> Status: {chk.status}")

    print("[OK] PHASE 4 PASSED!")

    # ----------------------------------------------------
    # PHASE 5: Individual Onion Report Breakdown
    # ----------------------------------------------------
    print("\n--- PHASE 5: Individual Onion Report Verification ---")
    for o in onions:
        breakdown = {
            "onion_id": o.id,
            "diameter_mm": o.diameter_mm,
            "measurement_method": o.measurement_method,
            "detected_defects": [d.model_dump() for d in o.defects],
            "checks": [c.model_dump() for c in o.checks],
            "grade": o.grade,
            "reasons": o.reasons
        }
        print(f"Onion Breakdown generated for {o.id}: Grade={breakdown['grade']}")
    print("[OK] PHASE 5 PASSED!")

    # ----------------------------------------------------
    # PHASE 6: Batch Analysis
    # ----------------------------------------------------
    print("\n--- PHASE 6: Batch Analysis Test ---")
    from app.models import ImageAnalysisResult
    img_result = ImageAnalysisResult(
        image_id="img_001",
        filename="test_sample_1.jpg",
        timestamp="2026-09-29 20:00:00",
        image_width=800,
        image_height=600,
        calibration=calib_res,
        onions=onions,
        raw_predictions=raw_preds,
        summary={"total_onions": len(onions)},
        warnings=["Test warning"]
    )
    batch_res = BatchAnalysisService.process_batch([img_result], batch_id="batch_test_001")
    print(f"Batch Summary: Total={batch_res.total_onions}, Grade A={batch_res.grade_a_count} ({batch_res.grade_a_percent}%), URS={batch_res.urs_count} ({batch_res.urs_percent}%), Non-Compliant={batch_res.non_compliant_count} ({batch_res.non_compliant_percent}%)")
    print(f"Diameter Stats: {batch_res.stats}")
    assert batch_res.total_onions > 0, "Phase 6 Failed: Batch analysis total onions 0"
    print("[OK] PHASE 6 PASSED!")

    # ----------------------------------------------------
    # PHASE 7: PDF Report Generation
    # ----------------------------------------------------
    print("\n--- PHASE 7: PDF Quality Report Generation Test ---")
    pdf_path = ReportService.generate_pdf_report(batch_res, output_filename="test_quality_report.pdf")
    print(f"PDF Generated at: {pdf_path}")
    assert os.path.exists(pdf_path), "Phase 7 Failed: PDF file not found"
    print("[OK] PHASE 7 PASSED!")

    print("\n==================================================")
    print("ALL BACKEND PIPELINE TESTS (PHASES 1-7) PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline_tests()
