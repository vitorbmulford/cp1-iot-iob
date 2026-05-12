import time

import database
import serial_io
from config import SERIAL_BAUD, SERIAL_PORT


def main():
    database.init_db()
    if not database.has_students():
        database.seed_default_students()

    ser = serial_io.init_serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
    if ser is None:
        print(serial_io.get_last_status())
        return

    print("Aproxime o cartao RFID. Pressione Ctrl+C para sair.")
    try:
        while True:
            uid = serial_io.read_id(ser)
            if uid:
                aluno = database.get_student_by_uid(uid)
                if aluno:
                    database.record_access(aluno["id"], uid)
                    print(f"OK: {uid} -> {aluno['nome']}")
                else:
                    print(f"UID nao cadastrado: {uid}")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nEncerrando teste RFID.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
