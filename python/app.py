import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import time
import numpy as np

from config import ALUNOS_REGISTRADOS, PERFIL_CONVIDADO, MODEL_PATH
import serial_io
import pose_detector
import ui


def main():
    ser = serial_io.init_serial('COMx', 9600, timeout=0.1)
    detector = pose_detector.create_detector(MODEL_PATH)

    estado_app = "AGUARDANDO_ID"
    perfil_ativo = None
    contador_reps = 0
    estagio_exercicio = ""
    historico_angulo = []

    cap = cv2.VideoCapture(0)
    plot = ui.AnglePlot()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        tecla = cv2.waitKey(1) & 0xFF

        if estado_app == "AGUARDANDO_ID":
            id_lido = serial_io.read_id(ser)
            if id_lido:
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
            angulo, pontos = pose_detector.detect_and_angle(detector, frame)
            if angulo is not None and pontos is not None:
                ombro, cotovelo, pulso = pontos
                texto_angulo = f"{int(angulo)} graus"
                cv2.putText(frame, texto_angulo, (cotovelo[0] + 30, cotovelo[1]),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                historico_angulo.append(angulo)
                if len(historico_angulo) > 50:
                    historico_angulo.pop(0)

                cv2.line(frame, tuple(ombro), tuple(cotovelo), (255, 255, 255), 2)
                cv2.line(frame, tuple(cotovelo), tuple(pulso), (255, 255, 255), 2)
                for p in [ombro, cotovelo, pulso]:
                    cv2.circle(frame, tuple(p), 8, (0, 0, 255), -1)

                # Contagem de Repeticoes
                if angulo > 160:
                    estagio_exercicio = "descida"
                if angulo < 35 and estagio_exercicio == "descida":
                    estagio_exercicio = "subida"
                    contador_reps += 1

                grafico_img = plot.render(historico_angulo, w)
                frame = np.vstack((frame, grafico_img))

                status = f"ALUNO: {perfil_ativo['nome']} | REPS: {contador_reps}/{perfil_ativo['objetivo']}"
                frame = ui.draw_status_bar(frame, status)

                if contador_reps >= perfil_ativo['objetivo']:
                    estado_app = "TREINO_CONCLUIDO"

        elif estado_app == "TREINO_CONCLUIDO":
            cv2.putText(frame, "TREINO CONCLUIDO!", (w // 2 - 150, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.imshow('Academia Inteligente', frame)
            cv2.waitKey(3000)
            estado_app = "AGUARDANDO_ID"

        cv2.imshow('Academia Inteligente', frame)
        if tecla == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
