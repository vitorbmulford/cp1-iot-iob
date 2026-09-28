import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


POSE_CONNECTIONS = (
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24),
    (23, 24), (23, 25), (25, 27), (24, 26), (26, 28),
)


def create_detector(model_path):
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
    )
    return vision.PoseLandmarker.create_from_options(options)


def calcular_angulo(a, b, c):
    """Calcula o angulo em graus formado pelos pontos a-b-c, com vertice em b."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    radianos = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angulo = np.abs(radianos * 180.0 / np.pi)
    return 360 - angulo if angulo > 180.0 else angulo


def detect_and_angle(detector, frame, min_confidence=0.6):
    """Detecta pose e angulo do cotovelo mais confiavel para rosca biceps.

    Retorna (angulo, (ombro, cotovelo, pulso), landmarks). O angulo so e
    retornado se os tres landmarks usados tiverem visibilidade e presenca altas.
    """
    if detector is None:
        return None, None, None

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    resultado = detector.detect_for_video(mp_image, int(time.time() * 1000))
    if not resultado.pose_landmarks:
        return None, None, None

    marcos = resultado.pose_landmarks[0]
    h, w, _ = frame.shape
    # Braco esquerdo (11, 13, 15) ou direito (12, 14, 16).
    candidates = ((11, 13, 15), (12, 14, 16))
    indices = max(candidates, key=lambda arm: sum(getattr(marcos[i], "visibility", 0) for i in arm))
    selected = [marcos[i] for i in indices]
    if any(
        getattr(landmark, "visibility", 0) < min_confidence
        or getattr(landmark, "presence", 0) < min_confidence
        for landmark in selected
    ):
        return None, None, marcos

    ombro, cotovelo, pulso = (
        [int(landmark.x * w), int(landmark.y * h)] for landmark in selected
    )
    return calcular_angulo(ombro, cotovelo, pulso), (ombro, cotovelo, pulso), marcos


def draw_pose(frame, landmarks):
    """Desenha landmarks e conexoes essenciais para a demonstracao."""
    if not landmarks:
        return frame
    h, w, _ = frame.shape
    points = [(int(item.x * w), int(item.y * h)) for item in landmarks]
    for start, end in POSE_CONNECTIONS:
        cv2.line(frame, points[start], points[end], (255, 180, 0), 2)
    for x, y in points:
        cv2.circle(frame, (x, y), 3, (0, 100, 255), -1)
    return frame


def get_wrist_points(landmarks, min_confidence=0.6):
    """Retorna os punhos confiaveis para relacionar o objeto detectado a mao."""
    if not landmarks:
        return []
    # O tamanho do frame nao esta disponivel nos landmarks; os pontos sao
    # convertidos para pixel pelo chamador com base no frame atual.
    return [landmarks[index] for index in (15, 16) if (
        getattr(landmarks[index], "visibility", 0) >= min_confidence
        and getattr(landmarks[index], "presence", 0) >= min_confidence
    )]
