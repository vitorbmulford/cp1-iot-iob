import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import cv2
import tkinter as tk
from tkinter import TclError


class AnglePlot:
    def __init__(self, width=7, height=2.5, dpi=100):
        self.fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('black')
        self.fig.set_facecolor('black')
        self.canvas = FigureCanvas(self.fig)

    def render(self, history, target_width):
        self.ax.clear()
        self.ax.plot(history, color='#00FFFF', linewidth=2)
        self.ax.set_ylim(0, 180)
        self.ax.set_title("ANGULO EM TEMPO REAL", color='white', fontsize=10)
        self.canvas.draw()
        grafico_img = cv2.cvtColor(np.asarray(self.canvas.buffer_rgba()), cv2.COLOR_RGBA2BGR)
        grafico_img = cv2.resize(grafico_img, (target_width, 200))
        return grafico_img


def draw_status_bar(frame, text):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 50), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.putText(frame, text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return frame


class TrainingDashboard:
    STATUS_COLORS = {
        "Aguardando Login": "#f59e0b",
        "Pronta para Uso": "#22c55e",
        "Treino Ativo": "#2563eb",
        "Treino Concluido": "#16a34a",
    }

    def __init__(self):
        self.closed = False
        self.root = tk.Tk()
        self.root.title("Smart Gym - Estacao de Treino")
        self.root.geometry("520x360")
        self.root.minsize(480, 320)
        self.root.configure(bg="#101820")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.status_var = tk.StringVar(value="Aguardando Login")
        self.welcome_var = tk.StringVar(value="Aproxime a tag/cartao RFID")
        self.exercise_var = tk.StringVar(value="Exercicio: -")
        self.reps_target_var = tk.StringVar(value="Repeticoes previstas: -")
        self.counter_var = tk.StringVar(value="Executadas: 0/0")
        self.rfid_var = tk.StringVar(value="RFID: aguardando leitura")

        self._build()

    def _build(self):
        container = tk.Frame(self.root, bg="#101820", padx=24, pady=24)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Smart Gym",
            bg="#101820",
            fg="#f8fafc",
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        self.status_label = tk.Label(
            container,
            textvariable=self.status_var,
            bg=self.STATUS_COLORS["Aguardando Login"],
            fg="#ffffff",
            font=("Segoe UI", 16, "bold"),
            padx=16,
            pady=10,
        )
        self.status_label.pack(fill="x", pady=(18, 16))

        tk.Label(
            container,
            textvariable=self.welcome_var,
            bg="#101820",
            fg="#ffffff",
            font=("Segoe UI", 18, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        for var in (self.exercise_var, self.reps_target_var, self.counter_var):
            tk.Label(
                container,
                textvariable=var,
                bg="#101820",
                fg="#dbeafe",
                font=("Segoe UI", 13),
                anchor="w",
            ).pack(fill="x", pady=4)

        tk.Label(
            container,
            textvariable=self.rfid_var,
            bg="#101820",
            fg="#94a3b8",
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(fill="x", side="bottom", pady=(18, 0))

    def update_state(self, status, aluno=None, contador=0, mensagem_rfid=""):
        if self.closed:
            return

        try:
            self.status_var.set(status)
            self.status_label.configure(bg=self.STATUS_COLORS.get(status, "#475569"))

            if aluno:
                nome = aluno["nome"]
                exercicio = aluno["exercicio"]
                repeticoes = aluno["repeticoes"]
                self.welcome_var.set(f"Bem-vindo(a), {nome}")
                self.exercise_var.set(f"Exercicio atual: {exercicio}")
                self.reps_target_var.set(f"Repeticoes previstas: {repeticoes}")
                self.counter_var.set(f"Executadas: {contador}/{repeticoes}")
            else:
                self.welcome_var.set("Aproxime a tag/cartao RFID")
                self.exercise_var.set("Exercicio atual: -")
                self.reps_target_var.set("Repeticoes previstas: -")
                self.counter_var.set("Executadas: 0/0")

            if mensagem_rfid:
                self.rfid_var.set(mensagem_rfid)

            self.root.update_idletasks()
            self.root.update()
        except TclError:
            self.closed = True

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.root.destroy()
        except TclError:
            pass
