"""Animation Matplotlib : FuncAnimation + set_data.

La démo du canon de Gosper, qui tire des planeurs pour toujours :
    python -m game_of_life.animate
Un autre motif et une autre taille de grille :
    python -m game_of_life.animate glider 30
"""

import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from game_of_life.engine import load_pattern, place, step


def build_board(name, size):
    """Grille size x size avec le motif posé près du coin haut-gauche.

    Poser le motif en haut à gauche laisse toute la place aux
    planeurs du canon, qui voyagent vers le bas à droite.
    """
    pattern = load_pattern(name)
    return place(np.zeros((size, size), dtype=int), pattern, top=1, left=1)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    name = argv[0] if len(argv) > 0 else "gosper_gun"
    size = int(argv[1]) if len(argv) > 1 else 60

    board = build_board(name, size)

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xticks([])
    ax.set_yticks([])

    # L'artiste est créé UNE seule fois ; ensuite on ne fait que
    # remplacer ses données avec set_data — jamais de nouvel imshow.
    im = ax.imshow(board, cmap="binary", vmin=0, vmax=1, interpolation="nearest")

    state = {"board": board, "gen": 0}

    def update(_frame):
        state["board"] = step(state["board"])
        state["gen"] += 1
        im.set_data(state["board"])
        ax.set_title(
            f"{name} — génération {state['gen']} — "
            f"{int(state['board'].sum())} vivantes"
        )
        return (im,)

    # Garder une référence à l'animation est obligatoire : sans elle,
    # le ramasse-miettes l'arrête immédiatement.
    anim = FuncAnimation(fig, update, interval=80, cache_frame_data=False)
    plt.show()
    return anim


if __name__ == "__main__":
    main()
