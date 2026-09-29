from typing import List
from app.models import OnionInstance, CalibrationResult

class SizeMeasurementService:
    @staticmethod
    def measure_onions(
        onions: List[OnionInstance],
        calibration: CalibrationResult
    ) -> List[OnionInstance]:
        """
        Calculates physical diameter in millimeters for each onion using calibration pixels_per_mm.
        Sets measurement_method tag to 'bounding_box_estimate'.
        """
        if not calibration.detected or not calibration.pixels_per_mm or calibration.pixels_per_mm <= 0:
            for onion in onions:
                onion.diameter_mm = None
                onion.measurement_method = None
            return onions

        ppm = calibration.pixels_per_mm

        for onion in onions:
            # Use maximum dimension of the bounding box as estimated diameter in pixels
            bbox_dim_px = max(onion.bbox.width, onion.bbox.height)
            diameter_mm = bbox_dim_px / ppm
            
            onion.diameter_px = round(bbox_dim_px, 2)
            onion.diameter_mm = round(diameter_mm, 1)
            onion.measurement_method = "bounding_box_estimate"

        return onions
