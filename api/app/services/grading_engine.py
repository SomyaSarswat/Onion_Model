import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from app.models import OnionInstance, GradingStandard, OnionCheck, DefectInstance
from app.config import settings

class GradingEngine:
    def __init__(self, standards_filepath: Path = None):
        self.standards_filepath = standards_filepath or settings.STANDARDS_FILE
        self.standards = self._load_standards()

    def _load_standards(self) -> Dict[str, Any]:
        """Loads grading rules JSON config."""
        if not self.standards_filepath.exists():
            raise FileNotFoundError(f"Grading standards file not found at {self.standards_filepath}")
        with open(self.standards_filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def reload_standards(self):
        """Reloads grading rules from disk."""
        self.standards = self._load_standards()

    def evaluate_onions(
        self,
        onions: List[OnionInstance],
        min_defect_confidence: float = 0.70
    ) -> List[OnionInstance]:
        """
        Evaluates each onion against Grade A and URS deterministic rules.
        Attaches grade, explicit failure reasons, and structured checks table.
        """
        grade_a_rules = self.standards.get("grade_a", {})
        urs_rules = self.standards.get("urs", {})

        for onion in onions:
            self._evaluate_single_onion(
                onion=onion,
                grade_a_rules=grade_a_rules,
                urs_rules=urs_rules,
                min_defect_confidence=min_defect_confidence
            )

        return onions

    def _evaluate_single_onion(
        self,
        onion: OnionInstance,
        grade_a_rules: Dict[str, Any],
        urs_rules: Dict[str, Any],
        min_defect_confidence: float
    ):
        reasons: List[str] = []
        checks: List[OnionCheck] = []

        # Categorize defects into confirmed (>= min_defect_confidence) and potential (< min_defect_confidence)
        confirmed_defects: List[DefectInstance] = []
        potential_defects: List[DefectInstance] = []

        for d in onion.defects:
            if d.confidence >= min_defect_confidence:
                confirmed_defects.append(d)
            else:
                potential_defects.append(d)

        confirmed_classes = [d.defect_class.lower() for d in confirmed_defects]

        # ----------------------------------------------------
        # 1. DIAMETER CHECK
        # ----------------------------------------------------
        dia = onion.diameter_mm
        g_a_min = grade_a_rules.get("min_diameter_mm", 45)
        g_a_max = grade_a_rules.get("max_diameter_mm", 65)
        urs_min = urs_rules.get("min_diameter_mm", 35)
        urs_max = urs_rules.get("max_diameter_mm", 70)

        dia_pass_grade_a = False
        dia_pass_urs = False

        if dia is None:
            dia_str = "Unmeasured (No Coin)"
            checks.append(OnionCheck(
                criterion="Diameter",
                value=dia_str,
                limit=f"{g_a_min}-{g_a_max} mm",
                status="FAIL"
            ))
            reasons.append("Physical size unmeasured (Calibration reference missing in frame)")
        else:
            dia_str = f"{dia:.1f} mm"
            if g_a_min <= dia <= g_a_max:
                dia_pass_grade_a = True
                checks.append(OnionCheck(
                    criterion="Diameter",
                    value=dia_str,
                    limit=f"{g_a_min}-{g_a_max} mm (Grade A)",
                    status="PASS"
                ))
            else:
                checks.append(OnionCheck(
                    criterion="Diameter",
                    value=dia_str,
                    limit=f"{g_a_min}-{g_a_max} mm (Grade A)",
                    status="FAIL"
                ))
                reasons.append(f"Diameter ({dia:.1f} mm) outside Grade A range ({g_a_min}-{g_a_max} mm)")

            if urs_min <= dia <= urs_max:
                dia_pass_urs = True

        # ----------------------------------------------------
        # 2. DEFECT CHECKS
        # ----------------------------------------------------
        # Sprouting
        has_sprouted = "sprouted" in confirmed_classes
        sprouted_val = "Detected" if has_sprouted else "Clean"
        sprouted_status = "FAIL" if has_sprouted else "PASS"
        checks.append(OnionCheck(
            criterion="Sprouting",
            value=sprouted_val,
            limit="Not allowed",
            status=sprouted_status
        ))
        if has_sprouted:
            reasons.append("Sprouting detected — prohibited under Grade A and URS standards")

        # Spoiled / Rot
        has_spoiled = "spoiled" in confirmed_classes
        spoiled_val = "Detected" if has_spoiled else "Clean"
        spoiled_status = "FAIL" if has_spoiled else "PASS"
        checks.append(OnionCheck(
            criterion="Rot / Spoiled",
            value=spoiled_val,
            limit="Not allowed",
            status=spoiled_status
        ))
        if has_spoiled:
            reasons.append("Spoilage/Rot detected — prohibited under Grade A and URS standards")

        # Black Smut
        has_black_smut = "black smut" in confirmed_classes
        smut_val = "Detected" if has_black_smut else "Clean"
        smut_status = "FAIL" if has_black_smut else "PASS"
        checks.append(OnionCheck(
            criterion="Black Smut",
            value=smut_val,
            limit="Not allowed",
            status=smut_status
        ))
        if has_black_smut:
            reasons.append("Black smut disease detected — prohibited under Grade A and URS standards")

        # Double Split
        has_double_split = "double_split" in confirmed_classes
        split_val = "Detected" if has_double_split else "Clean"
        # Allowed in URS, not allowed in Grade A
        split_status_g_a = not has_double_split
        checks.append(OnionCheck(
            criterion="Double Split",
            value=split_val,
            limit="Not allowed in Grade A (Allowed in URS)",
            status="PASS" if split_status_g_a else "FAIL"
        ))
        if has_double_split:
            reasons.append("Double split detected — prohibited in Grade A (acceptable under URS)")

        # Staining
        has_staining = "staining" in confirmed_classes
        if has_staining:
            staining_val = "Staining detected (exact surface % not measurable with bbox model)"
            staining_status = "FAIL"
            reasons.append("Staining detected — exact surface % not measurable with current model (violates Grade A 0% tolerance)")
        else:
            staining_val = "Clean (0%)"
            staining_status = "PASS"

        checks.append(OnionCheck(
            criterion="Surface Staining",
            value=staining_val,
            limit="0% for Grade A (Max 40% URS)",
            status=staining_status
        ))

        # Add notes for potential (low confidence) defects below threshold
        for pd in potential_defects:
            reasons.append(f"Notice: Possible {pd.defect_class} detected (confidence {int(pd.confidence * 100)}% < threshold {int(min_defect_confidence * 100)}%)")

        # ----------------------------------------------------
        # 3. DETERMINISTIC EVALUATION (GRADE A vs URS vs NON_COMPLIANT)
        # ----------------------------------------------------
        # Check Grade A eligibility
        is_grade_a = (
            dia_pass_grade_a and
            not has_sprouted and
            not has_spoiled and
            not has_black_smut and
            not has_double_split and
            not has_staining
        )

        if is_grade_a:
            onion.grade = "GRADE_A"
            onion.reasons = ["Meets all size (45-65mm) and defect-free criteria for Grade A"]
            onion.checks = checks
            return

        # Check URS eligibility
        # URS rules:
        # min_diameter_mm <= dia <= max_diameter_mm (35-70mm)
        # sprouted: not allowed
        # spoiled: not allowed
        # black_smut: not allowed
        # double_split: allowed (true)
        # staining: allowed up to 40% (staining detected is acceptable under URS with warning note)
        is_urs = (
            dia_pass_urs and
            not has_sprouted and
            not has_spoiled and
            not has_black_smut
            # double_split is allowed under URS
            # staining is tolerated under URS
        )

        if is_urs:
            urs_reasons = []
            if not dia_pass_grade_a:
                urs_reasons.append(f"Diameter ({dia:.1f} mm) qualifies for URS range ({urs_min}-{urs_max} mm)")
            if has_double_split:
                urs_reasons.append("Double split present — allowed under URS standards")
            if has_staining:
                urs_reasons.append("Staining present — within URS tolerance limits (max 40%)")
            
            onion.grade = "URS"
            onion.reasons = urs_reasons if urs_reasons else ["Qualifies for Under Sized / Relaxed Specification (URS)"]
            onion.checks = checks
            return

        # Otherwise NON_COMPLIANT
        onion.grade = "NON_COMPLIANT"
        onion.reasons = reasons if reasons else ["Failed size and defect tolerance criteria"]
        onion.checks = checks
