import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import time
import numpy as np

from config import (ALUNOS_REGISTRADOS, PERFIL_CONVIDADO, MODEL_PATH,
                    ANGULO_EM_PE, ANGULO_AGACHADO, SERIAL_PORT, SERIAL_BAUD)
import serial_io
import pose_detector
import ui


def main():
    ser = serial_io.init_serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
    detector = pose_detector.create_detector(MODEL_PATH)
    alunos_por_uid = {}
    for uid, perfil in ALUNOS_REGISTRADOS.items():
        uid_normalizado = serial_io.normalize_uid(uid)
        if uid_normalizado:
            alunos_por_uid[uid_normalizado] = perfil

    estado_app = "AGUARDANDO_ID"
    perfil_ativo = None
    contador_reps = 0
    estagio_exercicio = ""
    historico_angulo = []
    ultimo_status_rfid = "RFID: aguardando leitura"
    ultima_tentativa_serial = time.time()
    if ser is None:
        ultimo_status_rfid = f"RFID: {serial_io.get_last_status()}"

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
            if ser is None and time.time() - ultima_tentativa_serial > 2:
                ultima_tentativa_serial = time.time()
                ser = serial_io.init_serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
                ultimo_status_rfid = f"RFID: {serial_io.get_last_status()}"

            id_lido = serial_io.read_id(ser)
            if id_lido:
                if id_lido in alunos_por_uid:
                    perfil_ativo = alunos_por_uid[id_lido]
                    ultimo_status_rfid = f"RFID: {id_lido} -> {perfil_ativo['nome']}"
                    print(f"Aluno Identificado: {perfil_ativo['nome']}")
                    historico_angulo, contador_reps, estado_app = [], 0, "TREINO_EM_CURSO"
                else:
                    ultimo_status_rfid = f"RFID: {id_lido} nao cadastrado"
                    print(f"ID {id_lido} nao cadastrado.")

            if tecla == ord('s'):
                perfil_ativo = PERFIL_CONVIDADO
                print("Iniciando como Aluno Convidado.")
                historico_angulo, contador_reps, estado_app = [], 0, "TREINO_EM_CURSO"

            cv2.putText(frame, "APROXIME O CARTAO", (30, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, ultimo_status_rfid, (30, h // 2 + 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        elif estado_app == "TREINO_EM_CURSO":
            angulo, pontos = pose_detector.detect_and_angle(detector, frame)

            if angulo is not None and pontos is not None:
                quadril, joelho, tornozelo = pontos

                # Exibe o angulo proximo ao joelho
                texto_angulo = f"{int(angulo)} graus"
                cv2.putText(frame, texto_angulo, (joelho[0] + 20, joelho[1]),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                historico_angulo.append(angulo)
                if len(historico_angulo) > 50:
                    historico_angulo.pop(0)

                # Desenha os segmentos quadril-joelho e joelho-tornozelo
                cv2.line(frame, tuple(quadril), tuple(joelho), (255, 255, 255), 2)
                cv2.line(frame, tuple(joelho), tuple(tornozelo), (255, 255, 255), 2)
                for p in [quadril, joelho, tornozelo]:
                    cv2.circle(frame, tuple(p), 8, (0, 0, 255), -1)

                # Contagem de repeticoes do agachamento
                # Em pe: joelho reto (angulo alto) -> agachado: joelho dobrado (angulo baixo)
                if angulo > ANGULO_EM_PE:
                    estagio_exercicio = "em_pe"
                if angulo < ANGULO_AGACHADO and estagio_exercicio == "em_pe":
                    estagio_exercicio = "agachado"
                    contador_reps += 1

                grafico_img = plot.render(historico_angulo, w)
                frame = np.vstack((frame, grafico_img))

                status = f"ALUNO: {perfil_ativo['nome']} | AGACHAMENTOS: {contador_reps}/{perfil_ativo['objetivo']}"
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
