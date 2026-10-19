import os

# Paths
ROOT = os.path.dirname(__file__)
MODEL_PATH = os.path.join(ROOT, '..', 'assets', 'pose_landmarker_full.task')
DB_PATH = os.path.join(ROOT, 'smart_gym.sqlite3')

# Serial
# Use None to auto-detect the Arduino port, or set a fixed port such as "COM5".
SERIAL_PORT = os.getenv("SMARTGYM_SERIAL_PORT") or None
SERIAL_BAUD = 9600

# Demonstracao sem leitor fisico: na tela de login, pressione L na janela da webcam.
SIMULATED_RFID_UID = "C2:87:2D:30"

# Default data used by seed_db.py and by the app on first run.
ALUNOS_INICIAIS = [
    {"uid": "C2:87:2D:30", "nome": "Lucas", "exercicio": "Rosca Biceps", "repeticoes": 5},
    {"uid": "B3 22 A1 0C", "nome": "Maria", "exercicio": "Rosca Biceps", "repeticoes": 8},
]

# Rosca biceps: angulo ombro-cotovelo-pulso.
ANGULO_BRACO_ESTENDIDO = 160  # Braco quase reto: inicio e fim.
ANGULO_BRACO_FLEXIONADO = 45  # Cotovelo fechado: contracao confirmada.
POSE_MIN_CONFIDENCE = 0.60

# YOLO / equipamento. O modelo COCO pre-treinado e baixado pelo Ultralytics
# na primeira execucao, caso ainda nao exista no cache local.
YOLO_MODEL = os.path.join(ROOT, "yolov8s-worldv2.pt")
YOLO_CONFIDENCE = 0.15  # Objetos pequenos ou parcialmente ocultos na mao.
YOLO_IMAGE_SIZE = int(os.getenv("SMARTGYM_YOLO_IMAGE_SIZE", "640"))
YOLO_TARGET_CLASSES = ("dumbbell", "weight", "bottle", "water bottle", "cell phone", "mobile phone", "cup", "remote control", "book")
# Classes abertas procuradas pelo YOLO-World somente perto dos punhos.
HAND_OBJECT_MAX_DISTANCE = 55  # Margem pequena entre punho e caixa do objeto.
HAND_OBJECT_CROP_RADIUS = 180  # Regiao analisada ao redor de cada punho.
# Somente classes portateis proximas ao punho sao tratadas como halter.
YOLO_DETECTION_WINDOW = 4
YOLO_REQUIRED_HITS = 2
YOLO_HOLDER_LOCK_SECONDS = 3.0  # Mantem o halter valido durante falhas breves.
