import sys
import numpy as np

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QSizePolicy
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap


def step(world):
    """
    Calcule la génération suivante du Game of Life.
    0 = mort
    1 = vivant
    """
    alive = (world == 1).astype(int)

    p = np.pad(alive, 1, mode="constant", constant_values=0)
    neighbours = (
        p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:] +
        p[1:-1, :-2] +               p[1:-1, 2:] +
        p[2:, :-2] +  p[2:, 1:-1] +  p[2:, 2:]
    )

    survive = (world == 1) & ((neighbours == 2) | (neighbours == 3))
    born = (world == 0) & (neighbours == 3)

    new_world = np.zeros_like(world)
    new_world[survive | born] = 1

    # Les murs restent des murs.
    new_world[world == 2] = 2

    return new_world


class GameOfLifeWindow(QWidget):
    """
    0 = cellule morte
    1 = cellule vivante
    2 = mur
    """

    CMAP = ListedColormap([
        "#1e1e1e",  # 0 mort
        "#2ecc71",  # 1 vivant
        "#5b6b85",  # 2 mur
    ])

    def __init__(self, size=30):
        super().__init__()

        self.size = size
        self.generation = 0
        self.brush = 2  # par défaut : on peint des murs

        self.setWindowTitle("Game of Life + Matplotlib")

        # Monde logique : 0 mort, 1 vivant, 2 mur
        self.world = np.zeros((self.size, self.size), dtype=int)

        # Barre de statut
        self.status = QLabel("Generation: 0 | Alive: 0 | Left click = wall | Right click = erase")

        # Boutons de contrôle
        self.play_btn = QPushButton("Play")
        self.step_btn = QPushButton("Step")
        self.reset_btn = QPushButton("Reset")
        self.clear_btn = QPushButton("Clear")
        self.random_btn = QPushButton("Random")

        self.play_btn.clicked.connect(self.toggle_play)
        self.step_btn.clicked.connect(self.one_step)
        self.reset_btn.clicked.connect(self.reset_world)
        self.clear_btn.clicked.connect(self.clear_world)
        self.random_btn.clicked.connect(self.random_world)

        controls = QHBoxLayout()
        controls.addWidget(self.play_btn)
        controls.addWidget(self.step_btn)
        controls.addWidget(self.random_btn)
        controls.addWidget(self.clear_btn)
        controls.addWidget(self.reset_btn)

        # Figure Matplotlib construite à la main, comme demandé dans le cours
        self.fig = Figure(figsize=(6, 6))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)

        # Le canvas doit pouvoir grandir dans la fenêtre
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Image artist : créée UNE seule fois
        self.im = self.ax.imshow(
            self.world,
            cmap=self.CMAP,
            vmin=0,
            vmax=2,
            interpolation="nearest"
        )

        self.ax.set_title("Game of Life")
        self.ax.axis("off")

        # Fait remplir le canvas proprement
        self.ax.set_position([0, 0, 1, 1])

        # Colorbar ajoutée à la figure, pas à l'axe
        self.fig.colorbar(self.im, ax=self.ax, label="State")
        self.fig.tight_layout()

        # Événements Matplotlib
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_drag)

        # Timer Qt : dans Qt on utilise QTimer, pas FuncAnimation
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        # Layout principal
        layout = QVBoxLayout()
        layout.addLayout(controls, stretch=0)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.status, stretch=0)
        self.setLayout(layout)

        self.reset_world()

    def reset_world(self):
        """Réinitialise la grille avec un glider au centre."""
        self.timer.stop()
        self.play_btn.setText("Play")
        self.generation = 0
        self.world[:] = 0

        mid = self.size // 2
        pattern = [
            (mid - 1, mid),
            (mid, mid + 1),
            (mid + 1, mid - 1),
            (mid + 1, mid),
            (mid + 1, mid + 1),
        ]

        for r, c in pattern:
            if 0 <= r < self.size and 0 <= c < self.size:
                self.world[r, c] = 1

        self.redraw("Grille réinitialisée avec un glider.")

    def clear_world(self):
        """Vide toute la grille."""
        self.timer.stop()
        self.play_btn.setText("Play")
        self.generation = 0
        self.world[:] = 0
        self.redraw("Grille vidée.")

    def random_world(self):
        """Génère un monde aléatoire."""
        self.timer.stop()
        self.play_btn.setText("Play")
        self.generation = 0

        # 25% de cellules vivantes environ
        self.world = (np.random.rand(self.size, self.size) < 0.25).astype(int)
        self.redraw("Grille aléatoire générée.")

    def toggle_play(self):
        """Lance ou met en pause la simulation."""
        if self.timer.isActive():
            self.timer.stop()
            self.play_btn.setText("Play")
            self.redraw("Simulation en pause.")
        else:
            self.timer.start(200)
            self.play_btn.setText("Pause")
            self.redraw("Simulation lancée.")

    def one_step(self):
        """Avance d'une génération si la simulation est en pause."""
        if self.timer.isActive():
            self.redraw("Pause d'abord la simulation pour faire un step manuel.")
            return
        self.tick()

    def tick(self):
        """Fait avancer le moteur puis met à jour l'image Matplotlib."""
        new_world = step(self.world)

        if np.array_equal(new_world, self.world):
            self.timer.stop()
            self.play_btn.setText("Play")
            self.world = new_world
            self.redraw("État stable atteint.")
            return

        self.world = new_world
        self.generation += 1
        self.redraw("Nouvelle génération calculée.")

    def on_press(self, event):
        """
        Clic sur l'image Matplotlib.
        Clic gauche = mur
        Clic droit = gomme (cellule morte)
        """
        if event.inaxes is None:
            return

        if self.timer.isActive():
            self.redraw("Pause la simulation pour dessiner.")
            return

        self.brush = 0 if event.button == 3 else 2
        self.paint(event)

    def on_drag(self, event):
        """
        Drag sur l'image Matplotlib.
        On ne peint que si un bouton est maintenu.
        """
        if event.button is None:
            return
        if event.inaxes is None:
            return
        if self.timer.isActive():
            return

        self.brush = 0 if event.button == 3 else 2
        self.paint(event)

    def paint(self, event):
        """
        Convertit le clic en cellule de la grille
        et peint un petit bloc 3x3 pour éviter les trous pendant le drag.
        """
        if event.xdata is None or event.ydata is None:
            return

        col = int(round(event.xdata))
        row = int(round(event.ydata))

        if not (0 <= row < self.size and 0 <= col < self.size):
            return

        r0, r1 = max(0, row - 1), min(self.size, row + 2)
        c0, c1 = max(0, col - 1), min(self.size, col + 2)

        block = self.world[r0:r1, c0:c1]

        if self.brush == 2:
            # On dessine des murs, mais on ne transforme pas une cellule vivante en mur
            block[block != 1] = 2
            msg = f"Mur peint autour de ({row}, {col})"
        else:
            # Gomme : remet à mort, mais n'efface pas les cellules vivantes
            block[block != 1] = 0
            msg = f"Gomme autour de ({row}, {col})"

        self.world[r0:r1, c0:c1] = block
        self.redraw(msg)

    def redraw(self, message=None):
        """
        Met à jour l'artiste Matplotlib déjà créé,
        puis demande au canvas de se repeindre.
        """
        alive = int((self.world == 1).sum())

        self.im.set_data(self.world)
        self.canvas.draw_idle()

        if message is None:
            self.status.setText(
                f"Generation: {self.generation} | Alive: {alive} | Left click = wall | Right click = erase"
            )
        else:
            self.status.setText(
                f"Generation: {self.generation} | Alive: {alive} | {message}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = GameOfLifeWindow(size=30)
    w.resize(900, 800)
    w.show()
    sys.exit(app.exec())