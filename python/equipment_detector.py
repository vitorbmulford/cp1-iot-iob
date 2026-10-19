"""Detecta objetos COCO segurados na mao e os trata como halter."""

from collections import deque
import time

import cv2
from ultralytics import YOLO


class EquipmentDetector:
    def __init__(
        self, model_path, confidence, target_classes, max_hand_distance,
        crop_radius, window_size, required_hits, lock_seconds, image_size=640,
    ):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.model.set_classes(list(target_classes))
        self.target_classes = set(target_classes)
        self.max_hand_distance = max_hand_distance
        self.crop_radius = crop_radius
        self.required_hits = required_hits
        self.lock_seconds = lock_seconds
        self.image_size = image_size
        self.history = deque(maxlen=window_size)
        self.present = False
        self.last_held_at = None

    def reset(self):
        self.history.clear()
        self.present = False
        self.last_held_at = None

    def _is_held(self, box, hand_points):
        x1, y1, x2, y2 = box
        for hand_x, hand_y in hand_points:
            nearest_x = min(max(hand_x, x1), x2)
            nearest_y = min(max(hand_y, y1), y2)
            if (hand_x - nearest_x) ** 2 + (hand_y - nearest_y) ** 2 <= self.max_hand_distance ** 2:
                return True
        return False

    def _detect_near_hands(self, frame, hand_points):
        """Executa YOLO em recortes dos punhos, ampliando objetos pequenos."""
        height, width = frame.shape[:2]
        candidates = []
        for hand_x, hand_y in hand_points:
            x1 = max(0, hand_x - self.crop_radius)
            y1 = max(0, hand_y - self.crop_radius)
            x2 = min(width, hand_x + self.crop_radius)
            y2 = min(height, hand_y + self.crop_radius)
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            # O imgsz alto amplia a garrafa/celular no recorte antes da inferencia.
            result = self.model(crop, imgsz=self.image_size, conf=self.confidence, verbose=False)[0]
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls[0])
                if result.names[class_id] not in self.target_classes:
                    continue
                left, top, right, bottom = map(int, box.xyxy[0].tolist())
                coords = (left + x1, top + y1, right + x1, bottom + y1)
                if self._is_held(coords, [(hand_x, hand_y)]):
                    candidates.append((coords, float(box.conf[0]), result.names[class_id]))
        return candidates

    def detect(self, frame, hand_points):
        """Confirma e mantem o halter bloqueado durante perdas temporarias do YOLO."""
        held_boxes = self._detect_near_hands(frame, hand_points)
        now = time.monotonic()
        self.history.append(bool(held_boxes))
        if held_boxes:
            self.last_held_at = now

        if not self.present and sum(self.history) >= self.required_hits:
            self.present = True
        elif self.present and (self.last_held_at is None or now - self.last_held_at > self.lock_seconds):
            self.present = False
            self.history.clear()

        for (x1, y1, x2, y2), confidence, label in held_boxes:
            color = (0, 255, 0) if self.present else (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame, f"HALTER: {label} {confidence:.0%}", (x1, max(25, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
            )
        return self.present
