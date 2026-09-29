from typing import List, Dict, Tuple
from app.models import RoboflowPrediction, OnionInstance, DefectInstance, BoundingBox
from app.config import settings

class OnionAssociationService:
    @staticmethod
    def compute_iou(box1: BoundingBox, box2: BoundingBox) -> float:
        """Computes Intersection over Union (IoU) between two bounding boxes."""
        x_left = max(box1.xmin, box2.xmin)
        y_top = max(box1.ymin, box2.ymin)
        x_right = min(box1.xmax, box2.xmax)
        y_bottom = min(box1.ymax, box2.ymax)

        if x_right <= x_left or y_bottom <= y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (box1.xmax - box1.xmin) * (box1.ymax - box1.ymin)
        box2_area = (box2.xmax - box2.xmin) * (box2.ymax - box2.ymin)
        
        union_area = box1_area + box2_area - intersection_area
        if union_area <= 0:
            return 0.0

        return intersection_area / union_area

    @staticmethod
    def compute_containment(defect_box: BoundingBox, onion_box: BoundingBox) -> float:
        """Computes fraction of defect bounding box area that lies inside onion bounding box."""
        x_left = max(defect_box.xmin, onion_box.xmin)
        y_top = max(defect_box.ymin, onion_box.ymin)
        x_right = min(defect_box.xmax, onion_box.xmax)
        y_bottom = min(defect_box.ymax, onion_box.ymax)

        if x_right <= x_left or y_bottom <= y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        defect_area = (defect_box.xmax - defect_box.xmin) * (defect_box.ymax - defect_box.ymin)
        if defect_area <= 0:
            return 0.0

        return intersection_area / defect_area

    @staticmethod
    def is_center_inside(defect_box: BoundingBox, onion_box: BoundingBox) -> bool:
        """Returns True if the center point of defect box is inside onion box."""
        return (onion_box.xmin <= defect_box.x <= onion_box.xmax) and \
               (onion_box.ymin <= defect_box.y <= onion_box.ymax)

    def associate_instances(
        self,
        predictions: List[RoboflowPrediction],
        min_defect_confidence: float = 0.70,
        min_onion_confidence: float = 0.30
    ) -> Tuple[List[OnionInstance], List[RoboflowPrediction]]:
        """
        Groups detections into OnionInstance objects and associates defects to individual onions.
        Returns:
            - List of OnionInstance objects
            - List of unassociated/unclassified predictions (if any)
        """
        onion_predictions: List[RoboflowPrediction] = []
        defect_predictions: List[RoboflowPrediction] = []
        unassociated: List[RoboflowPrediction] = []

        # Separate onions from non-onion defects
        for pred in predictions:
            if pred.class_name.lower() == settings.ONION_CLASS_NAME.lower():
                if pred.confidence >= min_onion_confidence:
                    onion_predictions.append(pred)
            else:
                defect_predictions.append(pred)

        # Create OnionInstance for each detected onion box
        onions: List[OnionInstance] = []
        for idx, pred in enumerate(onion_predictions, start=1):
            bbox = BoundingBox(
                x=pred.x,
                y=pred.y,
                width=pred.width,
                height=pred.height,
                xmin=pred.xmin,
                ymin=pred.ymin,
                xmax=pred.xmax,
                ymax=pred.ymax
            )
            # Estimate pixel diameter as max of width and height of bbox
            diameter_px = max(pred.width, pred.height)
            
            onions.append(OnionInstance(
                id=f"onion_{idx:03d}",
                bbox=bbox,
                confidence=pred.confidence,
                defects=[],
                diameter_px=round(diameter_px, 2),
                diameter_mm=None,
                measurement_method=None,
                grade=None,
                reasons=[],
                checks=[]
            ))

        if not onions:
            return [], defect_predictions

        # Associate defects to onions based on IoU, containment, and center point inclusion
        for defect in defect_predictions:
            defect_bbox = BoundingBox(
                x=defect.x,
                y=defect.y,
                width=defect.width,
                height=defect.height,
                xmin=defect.xmin,
                ymin=defect.ymin,
                xmax=defect.xmax,
                ymax=defect.ymax
            )

            best_onion_idx = -1
            best_score = -1.0

            for idx, onion in enumerate(onions):
                iou = self.compute_iou(defect_bbox, onion.bbox)
                containment = self.compute_containment(defect_bbox, onion.bbox)
                center_in = self.is_center_inside(defect_bbox, onion.bbox)

                # Composite match score
                score = (0.5 * containment) + (0.3 * iou) + (0.5 if center_in else 0.0)

                if score > best_score:
                    best_score = score
                    best_onion_idx = idx

            # If match score > 0.05, associate defect with best matching onion
            if best_onion_idx >= 0 and best_score > 0.05:
                is_confirmed = defect.confidence >= min_defect_confidence
                status_text = (
                    f"{defect.class_name} ({int(defect.confidence * 100)}%)"
                    if is_confirmed
                    else f"Possible {defect.class_name} ({int(defect.confidence * 100)}%)"
                )

                defect_instance = DefectInstance(
                    defect_class=defect.class_name,
                    confidence=defect.confidence,
                    bbox=defect_bbox,
                    is_confirmed=is_confirmed,
                    status_text=status_text
                )
                onions[best_onion_idx].defects.append(defect_instance)
            else:
                unassociated.append(defect)

        return onions, unassociated
