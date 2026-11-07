# population-dynamics

Simulation animée de modèles de dynamique des populations (Malthus, Verhulst, Lotka-Volterra) avec curseurs de paramètres.

## Lancer

```
pip install -r requirements.txt
python main.py
```

## Fichiers

- `modeles.py` : modèles (dérivées, paramètres réglables)
- `solveurs.py` : Euler et Runge-Kutta 4
- `affichage.py` : tracé animé
- `interface.py` : boutons (modèles, pêche, pause, reset) et curseurs
- `main.py` : application

## Tests

```
pytest
```
