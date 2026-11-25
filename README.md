# population-dynamics

Simulation animée de modèles de dynamique des populations (Malthus, Verhulst, Lotka-Volterra, Holling–Tanner) avec curseurs de paramètres.

Pour les modèles proies–prédateurs, un plan de phase (proies, prédateurs) accompagne les courbes : Lotka-Volterra y décrit des boucles qui dépendent du point de départ, Holling–Tanner converge vers un cycle limite unique (ou vers l'équilibre, marqué d'une croix, quand la croissance des prédateurs s dépasse ≈ 0.3).

Holling–Tanner ajoute à Lotka-Volterra :
- des proies logistiques (capacité K, comme Verhulst) ;
- une prédation qui sature (Holling type II : au plus w proies par prédateur) ;
- des prédateurs logistiques dont la capacité dépend des proies (N/h).

## Lancer

```
pip install -r requirements.txt
python main.py
```

## Fichiers

- `modeles.py` : modèles (dérivées, paramètres réglables)
- `solveurs.py` : Euler et Runge-Kutta 4
- `affichage.py` : tracé animé (courbes temporelles et plan de phase)
- `interface.py` : boutons (modèles, pêche, pause, reset) et curseurs
- `main.py` : application

## Tests

```
pytest
```
