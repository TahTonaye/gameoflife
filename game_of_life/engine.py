"""Moteur du jeu de la vie de Conway.

Pur NumPy, vectorisé : aucune boucle Python sur les cellules.
Les bords sont des murs : une cellule hors de la grille n'existe pas,
un coin a donc au maximum 3 voisins (pas de wrap-around).
"""

from pathlib import Path

import numpy as np

# Dossier patterns/ à la racine du projet, indépendant du cwd.
PATTERNS_DIR = Path(__file__).resolve().parent.parent / "patterns"


def count_neighbours(grid):
    """Compte les 8 voisins vivants de chaque cellule.

    On entoure la grille d'une bordure de zéros (np.pad), puis on
    additionne les 8 versions décalées de la grille. Grâce à la
    bordure, les cellules du bord n'ont jamais de voisin
    « de l'autre côté » : les murs restent des murs.

    C'est l'équivalent vectorisé d'une double boucle sur les cellules,
    mais tout le travail se fait en C dans NumPy, d'un coup.
    """
    alive = (np.asarray(grid) == 1).astype(int)

    # Bordure de zéros tout autour (mode constant par défaut).
    p = np.pad(alive, 1)

    # Les 8 décalages : chaque tranche a exactement la taille de la
    # grille d'origine et « regarde » dans une des 8 directions.
    return (
        p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:]
        + p[1:-1, :-2] + p[1:-1, 2:]
        + p[2:, :-2] + p[2:, 1:-1] + p[2:, 2:]
    )


def step(grid):
    """Calcule la génération suivante en appliquant les 4 règles.

    1. vivante avec moins de 2 voisines  -> meurt (isolement)
    2. vivante avec 2 ou 3 voisines      -> survit
    3. vivante avec plus de 3 voisines   -> meurt (surpopulation)
    4. morte avec exactement 3 voisines  -> naît

    Toutes les cellules sont mises à jour simultanément : on compte
    les voisins sur la grille reçue, puis on construit une NOUVELLE
    grille. L'entrée n'est jamais modifiée — sans cela, une cellule
    déjà mise à jour fausserait le compte de voisins de la suivante.
    """
    grid = np.asarray(grid)
    n = count_neighbours(grid)

    born = (grid == 0) & (n == 3)
    survive = (grid == 1) & ((n == 2) | (n == 3))
    # Tout le reste meurt : règles 1 et 3.

    new_grid = np.zeros_like(grid)
    new_grid[born | survive] = 1
    return new_grid


def load_pattern(name):
    """Charge un motif CSV depuis patterns/ (ex : "glider" ou "glider.csv").

    ndmin=2 garantit une matrice même pour un motif d'une seule ligne
    comme le blinker.
    """
    if not name.endswith(".csv"):
        name += ".csv"
    return np.loadtxt(PATTERNS_DIR / name, delimiter=",", dtype=int, ndmin=2)


def place(board, pattern, top=0, left=0):
    """Pose un motif sur une grille et renvoie une COPIE de celle-ci.

    Le motif doit tenir dans la grille à la position demandée —
    sinon NumPy lèvera une erreur, ce qui est voulu : pas d'écrasement
    silencieux.
    """
    board = np.asarray(board).copy()
    h, w = pattern.shape
    board[top:top + h, left:left + w] = pattern
    return board
