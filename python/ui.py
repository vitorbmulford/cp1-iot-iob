import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import cv2


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
