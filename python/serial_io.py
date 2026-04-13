import serial

def init_serial(port='COMx', baud=9600, timeout=0.1):
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
        print("Arduino ON - Sistema de Identificacao Pronto!")
        return ser
    except Exception:
        print("Arduino OFF - Apenas modo Convidado disponivel (Tecla 'S')")
        return None


def read_id(ser):
    if ser is None:
        return None
    try:
        if ser.in_waiting > 0:
            return ser.readline().decode('utf-8').strip()
    except Exception:
        return None
    return None
