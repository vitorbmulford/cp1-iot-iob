import os

# Paths
ROOT = os.path.dirname(__file__)
MODEL_PATH = os.path.join(ROOT, '..', 'assets', 'pose_landmarker_full.task')

# Serial
# Use None to auto-detect the Arduino port, or set a fixed port such as "COM5".
SERIAL_PORT = None
SERIAL_BAUD = 9600

# Registered students (RFID -> profile)
ALUNOS_REGISTRADOS = {
    "00:A9:39:26": {"nome": "Lucas", "exercicio": "Agachamento", "objetivo": 5},
    "B3 22 A1 0C": {"nome": "Maria", "exercicio": "Agachamento", "objetivo": 8}
}

PERFIL_CONVIDADO = {"nome": "Convidado", "exercicio": "Agachamento", "objetivo": 3}

# Squat angle thresholds
ANGULO_EM_PE = 160      # Joelho quase reto -> posicao inicial (em pe)
ANGULO_AGACHADO = 90    # Joelho dobrado ~90 graus -> posicao de agachamento
