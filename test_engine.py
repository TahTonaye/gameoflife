"""Tests du moteur — à lancer en continu : pytest test_engine.py -v

Les figures classiques : un block qui ne bouge jamais, un blinker qui
oscille, un glider qui traverse la grille d'une cellule en diagonale
toutes les 4 générations. Si le glider voyage correctement, les
4 règles sont bonnes et les bords sont des murs.
"""

import numpy as np

from game_of_life.engine import count_neighbours, load_pattern, place, step


def board(shape, cells):
    """Construit une grille avec les cellules vivantes données."""
    b = np.zeros(shape, dtype=int)
    for r, c in cells:
        b[r, c] = 1
    return b


# ------------------------------------------------------------------
# count_neighbours
# ------------------------------------------------------------------

def test_count_neighbours_centre():
    # Grille 3x3 entièrement vivante : le centre voit les 8 autres.
    full = np.ones((3, 3), dtype=int)
    assert count_neighbours(full)[1, 1] == 8


def test_count_neighbours_coins_sont_des_murs():
    # LE test des bords : dans une grille pleine, un coin n'a que
    # 3 voisins. Avec un wrap-around (np.roll), il en aurait 8.
    full = np.ones((3, 3), dtype=int)
    n = count_neighbours(full)
    assert n[0, 0] == 3
    assert n[0, 2] == 3
    assert n[2, 0] == 3
    assert n[2, 2] == 3


def test_count_neighbours_equivaut_a_la_double_boucle():
    # La version vectorisée doit donner exactement le même résultat
    # que la double boucle naïve — c'est elle qu'elle remplace.
    rng = np.random.default_rng(42)
    g = (rng.random((15, 12)) < 0.4).astype(int)

    rows, cols = g.shape
    attendu = np.zeros_like(g)
    for r in range(rows):
        for c in range(cols):
            total = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < rows and 0 <= cc < cols:
                        total += g[rr, cc]
            attendu[r, c] = total

    assert np.array_equal(count_neighbours(g), attendu)


# ------------------------------------------------------------------
# Les 4 règles
# ------------------------------------------------------------------

def test_regle_1_isolement():
    # Deux cellules côte à côte : chacune n'a qu'une voisine -> mort.
    g = board((4, 4), [(1, 1), (1, 2)])
    assert step(g).sum() == 0


def test_regle_2_survie():
    # Dans un block, chaque cellule a exactement 3 voisines -> survie.
    g = board((4, 4), [(1, 1), (1, 2), (2, 1), (2, 2)])
    assert np.array_equal(step(g), g)


def test_regle_3_surpopulation():
    # Un plus : le centre a 4 voisines -> il meurt.
    g = board((5, 5), [(2, 2), (1, 2), (3, 2), (2, 1), (2, 3)])
    assert step(g)[2, 2] == 0


def test_regle_4_naissance():
    # Une cellule morte avec exactement 3 voisines naît.
    g = board((5, 5), [(1, 2), (2, 2), (3, 2)])
    assert step(g)[2, 1] == 1
    assert step(g)[2, 3] == 1


# ------------------------------------------------------------------
# Les figures classiques
# ------------------------------------------------------------------

def test_block_stable():
    g = place(np.zeros((6, 6), dtype=int), load_pattern("block"), 2, 2)
    assert np.array_equal(step(g), g)


def test_block_dans_le_coin_reste_stable():
    # Collé au mur, chaque cellule du block garde ses 3 voisines :
    # les murs ne cassent pas les figures légitimes.
    g = place(np.zeros((5, 5), dtype=int), load_pattern("block"), 0, 0)
    assert np.array_equal(step(g), g)


def test_blinker_oscille_periode_2():
    horizontal = board((5, 5), [(2, 1), (2, 2), (2, 3)])
    vertical = board((5, 5), [(1, 2), (2, 2), (3, 2)])
    assert np.array_equal(step(horizontal), vertical)
    assert np.array_equal(step(vertical), horizontal)


def test_toad_oscille_periode_2():
    g = place(np.zeros((6, 6), dtype=int), load_pattern("toad"), 2, 1)
    g1 = step(g)
    assert not np.array_equal(g1, g)
    assert np.array_equal(step(g1), g)


def test_glider_voyage_en_diagonale():
    # LE test qui compte : une cellule en diagonale toutes les
    # 4 générations. S'il passe, règles et bords sont bons.
    g = place(np.zeros((10, 10), dtype=int), load_pattern("glider"), 1, 1)
    attendu = place(np.zeros((10, 10), dtype=int), load_pattern("glider"), 2, 2)

    for _ in range(4):
        g = step(g)

    assert np.array_equal(g, attendu)


# ------------------------------------------------------------------
# Les bords sont des murs
# ------------------------------------------------------------------

def test_pas_de_wrap_around():
    # Blinker vertical collé au mur gauche. Sans wrap, la génération
    # suivante est exactement {(2,0), (2,1)}. Avec un wrap (np.roll),
    # une cellule naîtrait aussi dans la DERNIÈRE colonne.
    g = board((5, 5), [(1, 0), (2, 0), (3, 0)])
    g1 = step(g)
    assert np.array_equal(g1, board((5, 5), [(2, 0), (2, 1)]))
    assert g1[:, -1].sum() == 0


def test_cellules_isolees_dans_les_coins_meurent():
    g = board((5, 5), [(0, 0), (0, 4), (4, 0), (4, 4)])
    assert step(g).sum() == 0


# ------------------------------------------------------------------
# Discipline de mise à jour
# ------------------------------------------------------------------

def test_step_ne_modifie_pas_l_entree():
    # La mise à jour est simultanée : step lit la grille reçue et
    # construit une NOUVELLE grille. Muter l'entrée fausserait le
    # compte de voisins des cellules suivantes.
    g = board((5, 5), [(2, 1), (2, 2), (2, 3)])
    avant = g.copy()
    step(g)
    assert np.array_equal(g, avant)


# ------------------------------------------------------------------
# Les motifs fournis
# ------------------------------------------------------------------

def test_load_pattern_dimensions_et_populations():
    assert load_pattern("block").shape == (2, 2)
    assert load_pattern("block").sum() == 4

    # ndmin=2 : même un motif d'une seule ligne reste une matrice.
    assert load_pattern("blinker").shape == (1, 3)

    assert load_pattern("glider").shape == (3, 3)
    assert load_pattern("glider").sum() == 5

    assert load_pattern("toad").shape == (2, 4)

    assert load_pattern("gosper_gun").shape == (9, 36)
    assert load_pattern("gosper_gun").sum() == 36


def test_gosper_gun_tire_des_planeurs():
    # Le canon (36 cellules) doit produire des planeurs : après
    # 60 générations la population a grossi, et le canon lui-même
    # est toujours en place (son block gauche est intact).
    g = place(np.zeros((70, 70), dtype=int), load_pattern("gosper_gun"), 1, 1)

    b = g
    for _ in range(60):
        b = step(b)

    assert b.sum() >= 41            # au moins un planeur de plus
    assert b[5:7, 1:3].all()        # le block gauche du canon vit toujours
