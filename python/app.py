import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import time
import numpy as np

from config import (MODEL_PATH, ANGULO_EM_PE, ANGULO_AGACHADO,
                    SERIAL_PORT, SERIAL_BAUD)
import database
import serial_io
import pose_detector
import ui


def main():
    database.init_db()
    if not database.has_students():
        database.seed_default_students()
    ser = serial_io.init_serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
    detector = pose_detector.create_detector(MODEL_PATH)

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
    dashboard = ui.TrainingDashboard()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        tecla = cv2.waitKey(1) & 0xFF

        if estado_app == "AGUARDANDO_ID":
            dashboard.update_state("Aguardando Login", mensagem_rfid=ultimo_status_rfid)
            if ser is None and time.time() - ultima_tentativa_serial > 2:
                ultima_tentativa_serial = time.time()
                ser = serial_io.init_serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
                ultimo_status_rfid = f"RFID: {serial_io.get_last_status()}"

            id_lido = serial_io.read_id(ser)
            if id_lido:
                aluno = database.get_student_by_uid(id_lido)
                if aluno:
                    database.record_access(aluno["id"], id_lido)
                    perfil_ativo = aluno
                    ultimo_status_rfid = f"RFID: {id_lido} -> {perfil_ativo['nome']}"
                    print(f"Aluno Identificado: {perfil_ativo['nome']}")
                    historico_angulo, contador_reps = [], 0
                    estagio_exercicio = ""
                    estado_app = "PRONTA_PARA_USO"
                    dashboard.update_state(
                        "Pronta para Uso",
                        perfil_ativo,
                        contador_reps,
                        ultimo_status_rfid,
                    )
                else:
                    ultimo_status_rfid = f"RFID: {id_lido} nao cadastrado"
                    print(f"ID {id_lido} nao cadastrado.")

            cv2.putText(frame, "APROXIME O CARTAO", (30, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, ultimo_status_rfid, (30, h // 2 + 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        elif estado_app in ("PRONTA_PARA_USO", "TREINO_EM_CURSO"):
            angulo, pontos = pose_detector.detect_and_angle(detector, frame)
            status_painel = "Pronta para Uso" if estado_app == "PRONTA_PARA_USO" else "Treino Ativo"

            if angulo is not None and pontos is not None:
                estado_app = "TREINO_EM_CURSO"
                status_painel = "Treino Ativo"
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

                status = (
                    f"ALUNO: {perfil_ativo['nome']} | "
                    f"{perfil_ativo['exercicio'].upper()}: "
                    f"{contador_reps}/{perfil_ativo['repeticoes']}"
                )
                frame = ui.draw_status_bar(frame, status)
            else:
                status = (
                    f"ALUNO: {perfil_ativo['nome']} | "
                    f"AGUARDANDO POSE | {contador_reps}/{perfil_ativo['repeticoes']}"
                )
                frame = ui.draw_status_bar(frame, status)

            dashboard.update_state(status_painel, perfil_ativo, contador_reps, ultimo_status_rfid)

            if contador_reps >= perfil_ativo['repeticoes']:
                estado_app = "TREINO_CONCLUIDO"

        elif estado_app == "TREINO_CONCLUIDO":
            dashboard.update_state("Treino Concluido", perfil_ativo, contador_reps, ultimo_status_rfid)
            cv2.putText(frame, "TREINO CONCLUIDO!", (w // 2 - 150, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.imshow('Academia Inteligente', frame)
            cv2.waitKey(3000)
            estado_app = "AGUARDANDO_ID"
            perfil_ativo = None
            contador_reps = 0
            historico_angulo = []

        cv2.imshow('Academia Inteligente', frame)
        if tecla == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    dashboard.close()


if __name__ == '__main__':
    main()
