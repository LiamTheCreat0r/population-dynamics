import numpy as np
from abc import ABC, abstractmethod
from solveurs import runge_kutta


class Modele(ABC):
    """Modèle de population y' = f(t, y), simulé pas à pas.

    Les paramètres sont relus à chaque pas : on peut les modifier
    (dans `params`) pendant la simulation.
    """

    noms = ("Population",)  # un nom par composante de l'état

    # Paramètres réglables : (clé, libellé, minimum, maximum, valeur par défaut)
    PARAMETRES = ()

    DT = 0.1  # pas de temps par défaut

    PECHE_POSSIBLE = False  # le modèle accepte-t-il un effort de pêche ?

    def __init__(self, solveur=runge_kutta, dt=None, **valeurs):
        self.solveur = solveur
        self.dt = dt or self.DT
        self.params = {cle: defaut for cle, _, _, _, defaut in self.PARAMETRES}
        self.params.update(valeurs)
        self.peche = False  # pêche active ou non

    @abstractmethod
    def etat_initial(self):
        """Renvoie l'état de départ (np.ndarray 1D)."""

    @abstractmethod
    def derivee(self, t, y):
        """Second membre de y' = f(t, y)."""

    def pas(self, etat):
        """Renvoie l'état à t + dt.

        Le solveur est appelé sur un seul pas (durée = pas = dt) ;
        on garde le dernier point calculé.
        """
        _, y = self.solveur(self.derivee, etat, self.dt, self.dt)
        return y[-1]

    def flux(self):
        """Générateur infini de (t, état)."""
        t, etat = 0.0, self.etat_initial()
        yield t, etat
        while True:
            etat = self.pas(etat)
            t += self.dt
            yield t, etat


class Malthus(Modele):
    """Croissance exponentielle : N' = r·N."""

    PARAMETRES = (("croissance", "Croissance", 0.0, 3.0, 1.01),)

    def etat_initial(self):
        return np.array([10.0])

    def derivee(self, t, y):
        return self.params["croissance"] * y


class Verhulst(Modele):
    """Croissance logistique : N' = r·N·(1 − N/K), K = capacité du milieu."""

    PARAMETRES = (
        ("croissance", "Croissance", 0.0, 3.0, 1.2),
        ("capacite", "Capacité du milieu", 100.0, 5000.0, 1000.0),
    )

    def etat_initial(self):
        return np.array([10.0])

    def derivee(self, t, y):
        p = self.params
        return p["croissance"] * y * (1 - y / p["capacite"])


class Volterra(Modele):
    """Proies N et prédateurs P (Lotka-Volterra), avec pêche optionnelle :

        N' =  α·N − β·N·P − q·N
        P' = −γ·P + δ·N·P − q·P

    q est l'effort de pêche (0 quand la pêche est coupée).
    """

    noms = ("Proies", "Prédateurs")

    DT = 0.01

    PECHE_POSSIBLE = True

    PARAMETRES = (
        ("croissance_proies", "α  Croissance des proies", 0.0, 3.0, 1.0),
        ("predation", "β  Prédation", 0.0, 0.3, 0.1),
        ("mortalite_predateurs", "γ  Mortalité des prédateurs", 0.0, 3.0, 1.5),
        ("conversion", "δ  Gain des prédateurs par rencontre", 0.0, 0.3, 0.075),
        ("effort_peche", "q  Effort de pêche", 0.0, 3.0, 0.3),
    )

    def etat_initial(self):
        return np.array([10.0, 5.0])

    def derivee(self, t, y):
        p = self.params
        proies, predateurs = y
        q = p["effort_peche"] if self.peche else 0.0
        rencontres = proies * predateurs
        return np.array(
            [
                p["croissance_proies"] * proies - p["predation"] * rencontres - q * proies,
                -p["mortalite_predateurs"] * predateurs
                + p["conversion"] * rencontres
                - q * predateurs,
            ]
        )
