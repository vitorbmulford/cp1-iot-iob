import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
import time


def create_detector(model_path):
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO
    )
    return vision.PoseLandmarker.create_from_options(options)


def calcular_angulo(a, b, c):
    """Calcula o angulo em graus formado pelos pontos a-b-c, com vertice em b."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    radianos = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angulo = np.abs(radianos * 180.0 / np.pi)
    if angulo > 180.0:
        angulo = 360 - angulo
    return angulo


def detect_and_angle(detector, frame):
    """
    Detecta pose no frame e retorna o angulo do joelho para agachamento.
    Usa quadril (23), joelho (25) e tornozelo (27) do lado esquerdo.
    Retorna (angulo, (quadril, joelho, tornozelo)) ou (None, None).
    """
    if detector is None:
        return None, None

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    resultado = detector.detect_for_video(mp_image, int(time.time() * 1000))

    if resultado.pose_landmarks:
        marcos = resultado.pose_landmarks[0]
        h, w, _ = frame.shape

        # Landmarks do agachamento: quadril (23), joelho (25), tornozelo (27) — lado esquerdo
        quadril   = [int(marcos[23].x * w), int(marcos[23].y * h)]
        joelho    = [int(marcos[25].x * w), int(marcos[25].y * h)]
        tornozelo = [int(marcos[27].x * w), int(marcos[27].y * h)]

        angulo = calcular_angulo(quadril, joelho, tornozelo)
        return angulo, (quadril, joelho, tornozelo)

    return None, None