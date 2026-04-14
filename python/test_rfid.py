import time

import serial_io
from config import ALUNOS_REGISTRADOS, SERIAL_BAUD, SERIAL_PORT


def main():
    alunos_por_uid = {}
    for uid, perfil in ALUNOS_REGISTRADOS.items():
        uid_normalizado = serial_io.normalize_uid(uid)
        if uid_normalizado:
            alunos_por_uid[uid_normalizado] = perfil

    ser = serial_io.init_serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
    if ser is None:
        print(serial_io.get_last_status())
        return

    print("Aproxime o cartao RFID. Pressione Ctrl+C para sair.")
    try:
        while True:
            uid = serial_io.read_id(ser)
            if uid:
                perfil = alunos_por_uid.get(uid)
                if perfil:
                    print(f"OK: {uid} -> {perfil['nome']}")
                else:
                    print(f"UID nao cadastrado: {uid}")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nEncerrando teste RFID.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
