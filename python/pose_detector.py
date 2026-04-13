import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


def create_detector(model_path):
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO
    )
    return vision.PoseLandmarker.create_from_options(options)


def calcular_angulo(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radianos = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angulo = np.abs(radianos * 180.0 / np.pi)
    if angulo > 180.0:
        angulo = 360 - angulo
    return angulo


def detect_and_angle(detector, frame):
    """Run detector on a BGR frame. Returns (angle, (ombro,cotovelo,pulso)) or (None, None)."""
    if detector is None:
        return None, None
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    resultado = detector.detect_for_video(mp_image, int(time.time() * 1000))
    if resultado.pose_landmarks:
        marcos = resultado.pose_landmarks[0]
        h, w, _ = frame.shape
        ombro = [int(marcos[11].x * w), int(marcos[11].y * h)]
        cotovelo = [int(marcos[13].x * w), int(marcos[13].y * h)]
        pulso = [int(marcos[15].x * w), int(marcos[15].y * h)]
        angulo = calcular_angulo(ombro, cotovelo, pulso)
        return angulo, (ombro, cotovelo, pulso)
    return None, None

import cv2
import time
