import re
import time

import serial
from serial.tools import list_ports


UID_PATTERN = re.compile(r'([0-9A-Fa-f]{2}(?:[:\-\s][0-9A-Fa-f]{2}){3,})')
ARDUINO_PORT_HINTS = ('arduino', 'ch340', 'usb serial', 'usb-serial', 'cp210', 'ftdi')
LAST_STATUS = "Serial ainda nao inicializada"


def normalize_uid(uid):
    partes = re.findall(r'[0-9A-Fa-f]{2}', uid or '')
    if not partes:
        return None
    return ':'.join(parte.upper() for parte in partes)


def extract_uid(linha):
    match = UID_PATTERN.search(linha or '')
    if not match:
        return None
    return normalize_uid(match.group(1))


def list_available_ports():
    return list(list_ports.comports())


def find_serial_port(preferred_port=None):
    ports = list_available_ports()
    if ports:
        descricao = ', '.join(f'{porta.device} ({porta.description})' for porta in ports)
        print(f"Portas seriais encontradas: {descricao}")
    else:
        print("Nenhuma porta serial encontrada.")
        return None

    if preferred_port:
        for porta in ports:
            if porta.device.upper() == preferred_port.upper():
                return porta.device
        print(f"Porta configurada {preferred_port} nao encontrada.")

    for porta in ports:
        texto = f'{porta.description} {porta.manufacturer} {porta.hwid}'.lower()
        if any(dica in texto for dica in ARDUINO_PORT_HINTS):
            return porta.device

    return None


def init_serial(port=None, baud=9600, timeout=0.1):
    global LAST_STATUS

    selected_port = find_serial_port(port)
    if not selected_port:
        LAST_STATUS = "Arduino OFF - porta serial nao encontrada"
        print("Arduino OFF - Configure SERIAL_PORT em config.py e feche o Monitor Serial da Arduino IDE.")
        return None

    try:
        ser = serial.Serial(selected_port, baud, timeout=timeout)
        time.sleep(2)
        LAST_STATUS = f"Arduino ON em {selected_port}"
        print(f"{LAST_STATUS} - Sistema de Identificacao Pronto!")
        return ser
    except serial.SerialException as erro:
        LAST_STATUS = f"Arduino OFF em {selected_port}: porta ocupada"
        print(f"Arduino OFF em {selected_port}: {erro}")
        print("Feche o Monitor Serial/Arduino IDE se ele estiver aberto e rode o Python de novo.")
    except Exception as erro:
        LAST_STATUS = f"Arduino OFF em {selected_port}: {erro}"
        print(f"Arduino OFF em {selected_port}: {erro}")
    return None


def get_last_status():
    return LAST_STATUS


def read_id(ser):
    if ser is None:
        return None
    try:
        while ser.in_waiting > 0:
            linha = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"[DEBUG serial] recebido: '{linha}'")
            uid = extract_uid(linha)
            if uid:
                print(f"[DEBUG serial] UID extraido: {uid}")
                return uid
    except Exception as erro:
        print(f"[DEBUG serial] erro na leitura: {erro}")
        return None
    return None
