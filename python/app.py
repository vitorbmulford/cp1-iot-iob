import cv2
import time
import mediapipe as mp
import numpy as np
import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

arduino_conectado = True
try:
    ser = serial.Serial('COMx', 9600, timeout=0.1)  # Alterar a porta de acordo com o seu dispositivo
    arduino_conectado = True
    print("Arduino ON - Sistema de Identificacao Pronto!")
except:
    print("Arduino OFF - Apenas modo Convidado disponivel (Tecla 'S')")

model_path = '../assets/pose_landmarker_full.task'
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO
)
detector = vision.PoseLandmarker.create_from_options(options)

fig = plt.figure(figsize=(7, 2.5), dpi=100)
ax = fig.add_subplot(111)
ax.set_facecolor('black')
fig.set_facecolor('black')
canvas = FigureCanvas(fig)

ALUNOS_REGISTRADOS = {
    "4A B9 3B 1B": {"nome": "Lucas", "exercicio": "Rosca Direta", "objetivo": 5},
    "B3 22 A1 0C": {"nome": "Maria", "exercicio": "Rosca Direta", "objetivo": 8}
}

PERFIL_CONVIDADO = {"nome": "Convidado", "exercicio": "Rosca Direta", "objetivo": 3}

estado_app = "AGUARDANDO_ID"
perfil_ativo = None
contador_reps = 0
estagio_exercicio = ""
historico_angulo = []


def calcular_angulo(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radianos = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angulo = np.abs(radianos * 180.0 / np.pi)
    if angulo > 180.0: angulo = 360 - angulo
    return angulo


cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    tecla = cv2.waitKey(1) & 0xFF

    if estado_app == "AGUARDANDO_ID":
        if arduino_conectado and ser.in_waiting > 0:
            id_lido = ser.readline().decode('utf-8').strip()
            if id_lido in ALUNOS_REGISTRADOS:
                perfil_ativo = ALUNOS_REGISTRADOS[id_lido]
                print(f"Aluno Identificado: {perfil_ativo['nome']}")
                historico_angulo, contador_reps, estado_app = [], 0, "TREINO_EM_CURSO"
            else:
                print(f"ID {id_lido} nao cadastrado.")

        if tecla == ord('s'):
            perfil_ativo = PERFIL_CONVIDADO
            print("Iniciando como Aluno Convidado.")
            historico_angulo, contador_reps, estado_app = [], 0, "TREINO_EM_CURSO"

        cv2.putText(frame, "APROXIME O CARTAO OU APERTE 'S' (CONVIDADO)", (30, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    elif estado_app == "TREINO_EM_CURSO":
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        resultado = detector.detect_for_video(mp_image, int(time.time() * 1000))

        if resultado.pose_landmarks:
            marcos = resultado.pose_landmarks[0]
            ombro = [int(marcos[11].x * w), int(marcos[11].y * h)]
            cotovelo = [int(marcos[13].x * w), int(marcos[13].y * h)]
            pulso = [int(marcos[15].x * w), int(marcos[15].y * h)]

            angulo = calcular_angulo(ombro, cotovelo, pulso)


            texto_angulo = f"{int(angulo)} graus"

            cv2.putText(frame, texto_angulo,
                        (cotovelo[0] + 30, cotovelo[1]),  # coordenada calculada
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (255, 255, 255), 2)

            historico_angulo.append(angulo)
            if len(historico_angulo) > 50: historico_angulo.pop(0)

            cv2.line(frame, tuple(ombro), tuple(cotovelo), (255, 255, 255), 2)
            cv2.line(frame, tuple(cotovelo), tuple(pulso), (255, 255, 255), 2)
            for p in [ombro, cotovelo, pulso]: cv2.circle(frame, tuple(p), 8, (0, 0, 255), -1)

            # Contagem de Repeticoes
            if angulo > 160: estagio_exercicio = "descida"
            if angulo < 35 and estagio_exercicio == "descida":
                estagio_exercicio = "subida";
                contador_reps += 1

            ax.clear()
            ax.plot(historico_angulo, color='#00FFFF', linewidth=2)
            ax.set_ylim(0, 180)
            ax.set_title("ANGULO EM TEMPO REAL", color='white', fontsize=10)
            canvas.draw()
            grafico_img = cv2.cvtColor(np.asarray(canvas.buffer_rgba()), cv2.COLOR_RGBA2BGR)
            grafico_img = cv2.resize(grafico_img, (w, 200))
            frame = np.vstack((frame, grafico_img))

            # Barra de Status Superior
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 50), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

            status = f"ALUNO: {perfil_ativo['nome']} | REPS: {contador_reps}/{perfil_ativo['objetivo']}"
            cv2.putText(frame, status, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if contador_reps >= perfil_ativo['objetivo']:
                estado_app = "TREINO_CONCLUIDO"

    elif estado_app == "TREINO_CONCLUIDO":
        cv2.putText(frame, "TREINO CONCLUIDO!", (w // 2 - 150, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        cv2.imshow('Academia Inteligente', frame)
        cv2.waitKey(3000)
        estado_app = "AGUARDANDO_ID"

    cv2.imshow('Academia Inteligente', frame)
    if tecla == ord('q'): break

cap.release()
cv2.destroyAllWindows()