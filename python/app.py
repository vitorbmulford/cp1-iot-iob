import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import time

import cv2
import numpy as np

from config import (
    ANGULO_BRACO_ESTENDIDO,
    ANGULO_BRACO_FLEXIONADO,
    MODEL_PATH,
    POSE_MIN_CONFIDENCE,
    SERIAL_BAUD,
    SERIAL_PORT,
    SIMULATED_RFID_UID,
    HAND_OBJECT_MAX_DISTANCE,
    HAND_OBJECT_CROP_RADIUS,
    YOLO_TARGET_CLASSES,
    YOLO_CONFIDENCE,
    YOLO_IMAGE_SIZE,
    YOLO_DETECTION_WINDOW,
    YOLO_HOLDER_LOCK_SECONDS,
    YOLO_MODEL,
    YOLO_REQUIRED_HITS,
)
import database
import serial_io
import pose_detector
import ui
from equipment_detector import EquipmentDetector
from exercise_counter import BicepCurlCounter
from mqtt_config import MQTTConfig
from mqtt_publisher import StationPublisher
from station_events import StationSession


def main():
    database.init_db()
    database.migrate_exercise_to_bicep_curl()
    if not database.has_students():
        database.seed_default_students()

    ser = serial_io.init_serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
    pose = pose_detector.create_detector(MODEL_PATH)
    equipment = EquipmentDetector(
        YOLO_MODEL, YOLO_CONFIDENCE, YOLO_TARGET_CLASSES, HAND_OBJECT_MAX_DISTANCE, HAND_OBJECT_CROP_RADIUS,
        YOLO_DETECTION_WINDOW, YOLO_REQUIRED_HITS, YOLO_HOLDER_LOCK_SECONDS,
        image_size=YOLO_IMAGE_SIZE,
    )
    counter = BicepCurlCounter(ANGULO_BRACO_ESTENDIDO, ANGULO_BRACO_FLEXIONADO)

    estado_app = "AGUARDANDO_ID"
    perfil_ativo = None
    contador_reps = 0
    historico_angulo = []
    ultimo_status_rfid = "RFID: aguardando leitura"
    ultima_tentativa_serial = time.time()
    if ser is None:
        ultimo_status_rfid = f"RFID: {serial_io.get_last_status()}"

    camera_backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
    cap = cv2.VideoCapture(0, camera_backend)
    plot = ui.AnglePlot()
    dashboard = ui.TrainingDashboard()
    mqtt_config = MQTTConfig()
    publisher = StationPublisher(mqtt_config)
    session = StationSession(mqtt_config.station_id, publisher.publish)
    session.publish("status", session.status())
    publisher.start()

    try:
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
                if tecla == ord("l"):
                    id_lido = SIMULATED_RFID_UID
                    ultimo_status_rfid = f"RFID simulado: {id_lido}"
                if id_lido:
                    aluno = database.get_student_by_uid(id_lido)
                    if aluno:
                        database.record_access(aluno["id"], id_lido)
                        session.login(aluno)
                        perfil_ativo = aluno
                        ultimo_status_rfid = f"RFID: {id_lido} -> {perfil_ativo['nome']}"
                        print(f"Aluno Identificado: {perfil_ativo['nome']}")
                        historico_angulo, contador_reps = [], 0
                        counter.reset()
                        equipment.reset()
                        estado_app = "PRONTA_PARA_USO"
                    else:
                        ultimo_status_rfid = f"RFID: {id_lido} nao cadastrado"
                        print(f"ID {id_lido} nao cadastrado.")

                cv2.putText(frame, "CARTAO RFID OU TECLA L", (30, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(frame, ultimo_status_rfid, (30, h // 2 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            elif estado_app in ("PRONTA_PARA_USO", "TREINO_EM_CURSO"):
                # YOLO e MediaPipe processam o mesmo frame, cada um com sua funcao.
                angulo, pontos, landmarks = pose_detector.detect_and_angle(
                    pose, frame, POSE_MIN_CONFIDENCE,
                )
                pose_detector.draw_pose(frame, landmarks)
                hand_points = [
                    (int(wrist.x * w), int(wrist.y * h))
                    for wrist in pose_detector.get_wrist_points(landmarks, POSE_MIN_CONFIDENCE)
                ]
                equipamento_detectado = equipment.detect(frame, hand_points)
                pose_confiavel = angulo is not None and pontos is not None

                if pose_confiavel:
                    estado_app = "TREINO_EM_CURSO"
                    historico_angulo.append(angulo)
                    if len(historico_angulo) > 50:
                        historico_angulo.pop(0)
                    ombro, cotovelo, pulso = pontos
                    cv2.putText(frame, f"{int(angulo)} graus", (cotovelo[0] + 20, cotovelo[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.line(frame, tuple(ombro), tuple(cotovelo), (255, 255, 255), 2)
                    cv2.line(frame, tuple(cotovelo), tuple(pulso), (255, 255, 255), 2)

                if counter.update(angulo, pose_confiavel, equipamento_detectado):
                    contador_reps += 1

                status_equipamento = "HALTER DETECTADO" if equipamento_detectado else "AGUARDANDO HALTER - CONTAGEM BLOQUEADA"
                estado_contagem = counter.state if equipamento_detectado else "Contagem bloqueada"
                cv2.putText(frame, status_equipamento, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0) if equipamento_detectado else (0, 0, 255), 2)
                cv2.putText(frame, f"FASE: {estado_contagem}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)

                grafico_img = plot.render(historico_angulo, w)
                frame = np.vstack((frame, grafico_img))
                status = (
                    f"ALUNO: {perfil_ativo['nome']} | {perfil_ativo['exercicio'].upper()}: "
                    f"{contador_reps}/{perfil_ativo['repeticoes']}"
                )
                frame = ui.draw_status_bar(frame, status)
                status_painel = "Treino Ativo" if pose_confiavel else "Pronta para Uso"
                dashboard.update_state(
                    status_painel, perfil_ativo, contador_reps, ultimo_status_rfid,
                    equipamento_detectado,
                )

                if contador_reps >= perfil_ativo["repeticoes"]:
                    session.complete_series(contador_reps)
                    estado_app = "TREINO_CONCLUIDO"

            elif estado_app == "TREINO_CONCLUIDO":
                dashboard.update_state("Treino Concluido", perfil_ativo, contador_reps, ultimo_status_rfid, True)
                cv2.putText(frame, "TREINO CONCLUIDO!", (w // 2 - 150, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                cv2.imshow("Academia Inteligente", frame)
                cv2.waitKey(3000)
                session.logout()
                estado_app, perfil_ativo, contador_reps, historico_angulo = "AGUARDANDO_ID", None, 0, []
                counter.reset()
                equipment.reset()

            cv2.imshow("Academia Inteligente", frame)
            if tecla == ord("q"):
                break

    finally:
        session.logout()
        cap.release()
        cv2.destroyAllWindows()
        dashboard.close()
        if ser is not None:
            ser.close()
        publisher.stop()


if __name__ == "__main__":
    main()
