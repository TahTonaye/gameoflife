# Game of Life

Le jeu de la vie de Conway : un moteur NumPy vectorisé, une interface
PySide6 cliquable et une animation Matplotlib.

## Les 4 règles

Une cellule est vivante (1) ou morte (0). Chaque cellule regarde ses
8 voisines et toute la grille se met à jour d'un coup :

1. une vivante avec moins de 2 voisines meurt (isolement) ;
2. une vivante avec 2 ou 3 voisines survit ;
3. une vivante avec plus de 3 voisines meurt (surpopulation) ;
4. une morte avec exactement 3 voisines naît.

Les bords sont des murs : une cellule hors de la grille n'existe pas,
un coin a au maximum 3 voisines — pas de wrap-around.

## Installation

```bash
pip install -r requirements.txt
```

## Lancer

```bash
# Interface PySide : grille cliquable, Play/Pause, Step, Random
python main.py

# Animation Matplotlib : le canon de Gosper tire des planeurs
python -m game_of_life.animate

# Un autre motif, une autre taille de grille
python -m game_of_life.animate glider 30

# Les tests du moteur — à lancer en continu
pytest test_engine.py -v
```

## Structure

```
game_of_life/engine.py    le moteur : count_neighbours, step, load_pattern
game_of_life/gui.py       la fenêtre PySide (QTimer + grille de boutons)
game_of_life/animate.py   l'animation Matplotlib (FuncAnimation + set_data)
test_engine.py            17 tests : figures classiques, coins, non-mutation
patterns/*.csv            glider, block, blinker, toad, gosper_gun
main.py                   point d'entrée de l'interface
```

## Comment le moteur marche

`count_neighbours` entoure la grille d'une bordure de zéros (`np.pad`)
puis additionne les 8 versions décalées de la grille : chaque cellule
reçoit le compte de ses voisines sans qu'aucune boucle Python ne
parcoure les cellules. `step` applique ensuite les règles avec deux
masques booléens :

```python
born = (grid == 0) & (n == 3)
survive = (grid == 1) & ((n == 2) | (n == 3))
# tout le reste meurt
```

La mise à jour est simultanée : `step` construit une nouvelle grille
et ne modifie jamais celle qu'il reçoit.
