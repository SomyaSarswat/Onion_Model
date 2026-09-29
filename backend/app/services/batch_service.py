import statistics
from typing import List, Dict, Any
from app.models import ImageAnalysisResult, BatchAnalysisResult
from datetime import datetime

class BatchAnalysisService:
    @staticmethod
    def process_batch(
        image_results: List[ImageAnalysisResult],
        batch_id: str = None
    ) -> BatchAnalysisResult:
        """Aggregates individual image results into a comprehensive batch analysis report."""
        if not batch_id:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        all_onions = []
        batch_warnings = []

        for img_res in image_results:
            all_onions.extend(img_res.onions)
            for w in img_res.warnings:
                if w not in batch_warnings:
                    batch_warnings.append(w)

        total_images = len(image_results)
        total_onions = len(all_onions)

        grade_a_count = sum(1 for o in all_onions if o.grade == "GRADE_A")
        urs_count = sum(1 for o in all_onions if o.grade == "URS")
        non_compliant_count = sum(1 for o in all_onions if o.grade == "NON_COMPLIANT")

        if total_onions > 0:
            grade_a_pct = round((grade_a_count / total_onions) * 100, 1)
            urs_pct = round((urs_count / total_onions) * 100, 1)
            non_compliant_pct = round((non_compliant_count / total_onions) * 100, 1)
        else:
            grade_a_pct = 0.0
            urs_pct = 0.0
            non_compliant_pct = 0.0

        # Calculate diameter statistics for onions with physical measurement
        valid_diameters = [o.diameter_mm for o in all_onions if o.diameter_mm is not None]
        
        if valid_diameters:
            stats = {
                "mean": round(statistics.mean(valid_diameters), 1),
                "median": round(statistics.median(valid_diameters), 1),
                "min": round(min(valid_diameters), 1),
                "max": round(max(valid_diameters), 1)
            }
        else:
            stats = {
                "mean": None,
                "median": None,
                "min": None,
                "max": None
            }
            batch_warnings.append("No calibration reference found in batch images — physical diameters unmeasured.")

        # Per-defect type counts
        defect_counts = {
            "sprouted": 0,
            "spoiled": 0,
            "double_split": 0,
            "black_smut": 0,
            "staining": 0
        }

        for o in all_onions:
            for d in o.defects:
                cls_key = d.defect_class.lower().replace(" ", "_")
                if cls_key in defect_counts:
                    defect_counts[cls_key] += 1
                else:
                    defect_counts[cls_key] = 1

        return BatchAnalysisResult(
            batch_id=batch_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_images=total_images,
            total_onions=total_onions,
            grade_a_count=grade_a_count,
            grade_a_percent=grade_a_pct,
            urs_count=urs_count,
            urs_percent=urs_pct,
            non_compliant_count=non_compliant_count,
            non_compliant_percent=non_compliant_pct,
            stats=stats,
            defect_counts=defect_counts,
            images=image_results,
            warnings=batch_warnings
        )
