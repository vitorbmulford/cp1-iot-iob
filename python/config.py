import os

# Paths
ROOT = os.path.dirname(__file__)
MODEL_PATH = os.path.join(ROOT, '..', 'assets', 'pose_landmarker_full.task')
DB_PATH = os.path.join(ROOT, 'smart_gym.sqlite3')

# Serial
# Use None to auto-detect the Arduino port, or set a fixed port such as "COM5".
SERIAL_PORT = "COM5"
SERIAL_BAUD = 9600

# Default data used by seed_db.py and by the app on first run.
ALUNOS_INICIAIS = [
    {"uid": "C2:87:2D:30", "nome": "Lucas", "exercicio": "Agachamento", "repeticoes": 5},
    {"uid": "B3 22 A1 0C", "nome": "Maria", "exercicio": "Agachamento", "repeticoes": 8},
]

# Squat angle thresholds
ANGULO_EM_PE = 160      # Joelho quase reto -> posicao inicial (em pe)
ANGULO_AGACHADO = 120   # Valor maior conta agachamento menos profundo
