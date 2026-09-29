import cv2
import numpy as np
from typing import Optional, Dict, Any, Tuple
from app.models import CalibrationResult

class CalibrationService:
    def __init__(self, ref_type: str = "coin", ref_size_mm: float = 23.0):
        self.ref_type = ref_type.lower()
        self.ref_size_mm = ref_size_mm

    def detect_reference_object(
        self,
        image_path: str,
        manual_ppm: Optional[float] = None
    ) -> CalibrationResult:
        """
        Detects calibration reference object (Coin or ArUco marker) in image using OpenCV.
        Calculates pixels_per_mm.
        """
        # If manual override provided
        if manual_ppm and manual_ppm > 0:
            return CalibrationResult(
                detected=True,
                ref_type="manual",
                ref_size_mm=self.ref_size_mm,
                ref_pixel_width=manual_ppm * self.ref_size_mm,
                pixels_per_mm=round(manual_ppm, 4),
                ref_bbox=None,
                message=f"Manual calibration applied: {manual_ppm:.2f} px/mm"
            )

        img = cv2.imread(image_path)
        if img is None:
            return CalibrationResult(
                detected=False,
                ref_type=self.ref_type,
                ref_size_mm=self.ref_size_mm,
                ref_pixel_width=None,
                pixels_per_mm=None,
                ref_bbox=None,
                message="Image file could not be read for calibration."
            )

        if self.ref_type == "aruco":
            res = self._detect_aruco(img)
            if res[0]:
                return res[1]

        # Coin detection (default or fallback)
        res_coin = self._detect_coin(img)
        if res_coin[0]:
            return res_coin[1]

        # If reference object not found
        return CalibrationResult(
            detected=False,
            ref_type=self.ref_type,
            ref_size_mm=self.ref_size_mm,
            ref_pixel_width=None,
            pixels_per_mm=None,
            ref_bbox=None,
            message="Physical size could not be measured. Please include the calibration coin/marker in frame."
        )

    def _detect_coin(self, img: np.ndarray) -> Tuple[bool, CalibrationResult]:
        """Detects circular reference coin using OpenCV HoughCircles & contour circularity."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.medianBlur(gray, 5)

        h, w = gray.shape
        min_radius = int(min(w, h) * 0.015)
        max_radius = int(min(w, h) * 0.15)

        # Hough Circle Transform
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=min_radius * 4,
            param1=50,
            param2=30,
            minRadius=min_radius,
            maxRadius=max_radius
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            best_circle = None
            best_score = -1

            for c in circles[0, :]:
                cx, cy, r = int(c[0]), int(c[1]), int(c[2])
                
                # Check region around circle for contrast / circularity
                pixel_diameter = r * 2.0
                ppm = pixel_diameter / self.ref_size_mm
                
                # Simple score based on radius stability
                score = r
                if score > best_score:
                    best_score = score
                    best_circle = (cx, cy, r, pixel_diameter, ppm)

            if best_circle:
                cx, cy, r, dia_px, ppm = best_circle
                ref_bbox = {
                    "xmin": float(cx - r),
                    "ymin": float(cy - r),
                    "xmax": float(cx + r),
                    "ymax": float(cy + r),
                    "width": float(dia_px),
                    "height": float(dia_px)
                }
                return True, CalibrationResult(
                    detected=True,
                    ref_type="coin",
                    ref_size_mm=self.ref_size_mm,
                    ref_pixel_width=round(dia_px, 2),
                    pixels_per_mm=round(ppm, 4),
                    ref_bbox=ref_bbox,
                    message=f"Calibration Coin detected ({dia_px:.1f}px = {self.ref_size_mm}mm)"
                )

        # Alternative contour circularity check if HoughCircles misses
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < (np.pi * min_radius * min_radius) or area > (np.pi * max_radius * max_radius):
                continue
            perimeter = cv2.arcLength(cnt, True)
            if perimeter <= 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity > 0.85:  # highly circular shape
                (cx, cy), radius = cv2.minEnclosingCircle(cnt)
                dia_px = radius * 2.0
                ppm = dia_px / self.ref_size_mm
                ref_bbox = {
                    "xmin": float(cx - radius),
                    "ymin": float(cy - radius),
                    "xmax": float(cx + radius),
                    "ymax": float(cy + radius),
                    "width": float(dia_px),
                    "height": float(dia_px)
                }
                return True, CalibrationResult(
                    detected=True,
                    ref_type="coin",
                    ref_size_mm=self.ref_size_mm,
                    ref_pixel_width=round(dia_px, 2),
                    pixels_per_mm=round(ppm, 4),
                    ref_bbox=ref_bbox,
                    message=f"Calibration Coin detected ({dia_px:.1f}px = {self.ref_size_mm}mm)"
                )

        return False, CalibrationResult(
            detected=False,
            ref_type="coin",
            ref_size_mm=self.ref_size_mm,
            ref_pixel_width=None,
            pixels_per_mm=None,
            ref_bbox=None,
            message="No calibration coin detected in image."
        )

    def _detect_aruco(self, img: np.ndarray) -> Tuple[bool, CalibrationResult]:
        """Detects ArUco marker in image."""
        try:
            if hasattr(cv2, 'aruco'):
                dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
                parameters = cv2.aruco.DetectorParameters()
                detector = cv2.aruco.ArucoDetector(dictionary, parameters)
                corners, ids, _ = detector.detectMarkers(img)
                if ids is not None and len(corners) > 0:
                    c = corners[0][0]
                    w_px = np.linalg.norm(c[0] - c[1])
                    ppm = w_px / self.ref_size_mm
                    xmin, ymin = np.min(c, axis=0)
                    xmax, ymax = np.max(c, axis=0)
                    ref_bbox = {
                        "xmin": float(xmin), "ymin": float(ymin),
                        "xmax": float(xmax), "ymax": float(ymax),
                        "width": float(xmax - xmin), "height": float(ymax - ymin)
                    }
                    return True, CalibrationResult(
                        detected=True,
                        ref_type="aruco",
                        ref_size_mm=self.ref_size_mm,
                        ref_pixel_width=round(w_px, 2),
                        pixels_per_mm=round(ppm, 4),
                        ref_bbox=ref_bbox,
                        message=f"ArUco Marker detected ({w_px:.1f}px = {self.ref_size_mm}mm)"
                    )
        except Exception as e:
            print(f"[CalibrationService] ArUco error: {e}")
        return False, CalibrationResult(
            detected=False,
            ref_type="aruco",
            ref_size_mm=self.ref_size_mm,
            ref_pixel_width=None,
            pixels_per_mm=None,
            ref_bbox=None,
            message="No ArUco marker detected."
        )
