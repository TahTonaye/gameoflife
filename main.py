import sys
import numpy as np

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QGridLayout, QVBoxLayout, QHBoxLayout, QLabel
)

# La logique du jeu vit dans le moteur : l'interface ne fait
# qu'afficher l'état et déclencher les générations.
from game_of_life.engine import step


class GameOfLife(QWidget):
    def __init__(self, size=20):
        super().__init__()

        # Taille de la grille.
        self.size = size

        # Numéro de génération affiché dans la barre de statut.
        self.generation = 0

        # Booléen pratique pour savoir si la simulation tourne.
        self.running = False

        self.setWindowTitle("Game of Life")

        # État logique du monde :
        # True = cellule vivante, False = cellule morte
        self.world = np.zeros((size, size), dtype=bool)

        # Barre de statut pour afficher les infos de la simulation.
        self.status = QLabel("Generation: 0 | Alive: 0")

        # Boutons de contrôle.
        self.play_btn = QPushButton("Play")
        self.step_btn = QPushButton("Step")
        self.reset_btn = QPushButton("Reset")
        self.clear_btn = QPushButton("Clear")
        self.random_btn = QPushButton("Random")

        # Connexion des boutons à leurs méthodes.
        self.play_btn.clicked.connect(self.toggle_play)
        self.step_btn.clicked.connect(self.one_step)
        self.reset_btn.clicked.connect(self.reset_world)
        self.clear_btn.clicked.connect(self.clear_world)
        self.random_btn.clicked.connect(self.random_world)

        # Barre horizontale du haut : statut + boutons.
        bar = QHBoxLayout()
        bar.addWidget(self.status)
        bar.addStretch()
        bar.addWidget(self.play_btn)
        bar.addWidget(self.step_btn)
        bar.addWidget(self.random_btn)
        bar.addWidget(self.clear_btn)
        bar.addWidget(self.reset_btn)

        # Grille visuelle des cellules.
        self.grid = QGridLayout()
        self.grid.setSpacing(2)

        # Stockage des boutons dans une liste de listes
        # pour pouvoir les retrouver facilement avec [r][c].
        self.buttons = []

        for r in range(self.size):
            row = []
            for c in range(self.size):
                b = QPushButton("")
                b.setFixedSize(24, 24)

                # Closure fix :
                # chaque bouton garde sa propre valeur de r et c.
                b.clicked.connect(lambda _=False, r=r, c=c: self.on_click(r, c))

                self.grid.addWidget(b, r, c)
                row.append(b)
            self.buttons.append(row)

        # Layout principal vertical :
        # barre de contrôle au-dessus, grille en dessous.
        outer = QVBoxLayout()
        outer.addLayout(bar)
        outer.addLayout(self.grid)
        self.setLayout(outer)

        # Timer Qt :
        # toutes les X millisecondes, il appelle self.tick().
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        # Charge un motif initial au démarrage.
        self.reset_world()

    def reset_world(self):
        """Réinitialise la grille avec un petit motif de départ."""
        self.timer.stop()
        self.running = False
        self.play_btn.setText("Play")
        self.generation = 0

        # Vide entièrement la grille.
        self.world[:] = False

        # Petit motif classique de départ : un glider au centre.
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
                self.world[r, c] = True

        self.redraw(message="Grille réinitialisée avec un glider.")

    def clear_world(self):
        """Vide complètement la grille."""
        self.timer.stop()
        self.running = False
        self.play_btn.setText("Play")
        self.generation = 0
        self.world[:] = False
        self.redraw(message="Grille vidée.")

    def random_world(self):
        """Crée une grille aléatoire."""
        self.timer.stop()
        self.running = False
        self.play_btn.setText("Play")
        self.generation = 0

        # Environ 28% de cellules vivantes au départ.
        self.world = np.random.rand(self.size, self.size) < 0.28
        self.redraw(message="Grille aléatoire générée.")

    def on_click(self, r, c):
        """
        Inverse l'état d'une cellule quand on clique dessus.
        On bloque l'édition pendant que la simulation tourne.
        """
        if self.running:
            self.redraw(message="Pause la simulation pour modifier la grille.")
            return

        # Toggle : vivant devient mort, mort devient vivant.
        self.world[r, c] = not self.world[r, c]

        state = "vivante" if self.world[r, c] else "morte"
        self.redraw(message=f"Cellule ({r}, {c}) -> {state}")

    def toggle_play(self):
        """Lance ou met en pause la simulation."""
        if self.timer.isActive():
            self.timer.stop()
            self.running = False
            self.play_btn.setText("Play")
            self.redraw(message="Simulation en pause.")
        else:
            self.timer.start(250)
            self.running = True
            self.play_btn.setText("Pause")
            self.redraw(message="Simulation lancée.")

    def one_step(self):
        """Avance d'une seule génération si la simulation est en pause."""
        if self.running:
            self.redraw(message="Impossible : la simulation tourne déjà.")
            return

        self.tick()

    def tick(self):
        """
        Fait avancer la simulation d'une génération.
        Cette méthode est appelée :
        - soit par le bouton Step
        - soit automatiquement par le QTimer
        """
        new_world = step(self.world)

        # Si la nouvelle grille est identique à l'ancienne,
        # le système est stable : plus aucun changement.
        if np.array_equal(new_world, self.world):
            self.timer.stop()
            self.running = False
            self.play_btn.setText("Play")
            self.world = new_world
            self.redraw(message="État stable atteint.")
            return

        # Sinon on applique la nouvelle génération.
        self.world = new_world
        self.generation += 1
        self.redraw(message="Nouvelle génération calculée.")

    def redraw(self, message=None):
        """
        Met à jour l'affichage à partir de self.world.
        Le monde logique est dans NumPy,
        les boutons ne sont qu'une vue de cet état.
        """
        alive = int(self.world.sum())

        for r in range(self.size):
            for c in range(self.size):
                b = self.buttons[r][c]

                if self.world[r, c]:
                    # Cellule vivante : verte
                    b.setText("")
                    b.setStyleSheet(
                        "background-color: #2ecc71; border: 1px solid #1f1f1f;"
                    )
                else:
                    # Cellule morte : sombre
                    b.setText("")
                    b.setStyleSheet(
                        "background-color: #1e1e1e; border: 1px solid #3a3a3a;"
                    )

        # Mise à jour de la barre de statut.
        if message is None:
            self.status.setText(f"Generation: {self.generation} | Alive: {alive}")
        else:
            self.status.setText(
                f"Generation: {self.generation} | Alive: {alive} | {message}"
            )


if __name__ == "__main__":
    # Application Qt : une seule par programme.
    app = QApplication(sys.argv)

    # Création et affichage de la fenêtre.
    w = GameOfLife(size=20)
    w.show()

    # Lancement de la boucle d'événements Qt.
    sys.exit(app.exec())