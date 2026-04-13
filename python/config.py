import os

# Paths
ROOT = os.path.dirname(__file__)
MODEL_PATH = os.path.join(ROOT, '..', 'assets', 'pose_landmarker_full.task')

# Registered students (RFID -> profile)
ALUNOS_REGISTRADOS = {
    "4A B9 3B 1B": {"nome": "Lucas", "exercicio": "Rosca Direta", "objetivo": 5},
    "B3 22 A1 0C": {"nome": "Maria", "exercicio": "Rosca Direta", "objetivo": 8}
}

PERFIL_CONVIDADO = {"nome": "Convidado", "exercicio": "Rosca Direta", "objetivo": 3}
