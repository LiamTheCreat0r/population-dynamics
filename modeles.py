import numpy as np
from abc import ABC, abstractmethod
from solveurs import rungeKutta


class Modele(ABC):

    noms = ("Population",)  # un nom par composante de l'état

    def __init__(self, solveur=rungeKutta, dt=0.1):
        self.solveur = solveur
        self.dt = dt

    @abstractmethod
    def etat_initial(self):
        """Renvoie l'état de départ (np.ndarray 1D)."""

    @abstractmethod
    def derivee(self, t, y):
        """Second membre de y' = f(t, y)."""

    def pas(self, etat):
        """Un pas du solveur : renvoie l'état à t + dt."""
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

    def __init__(self, growth, **kwargs):
        super().__init__(**kwargs)
        self.growth = growth

    def etat_initial(self):
        return np.array([10.0])

    def derivee(self, t, y):
        return self.growth * y


class Verhulst(Modele):

    def __init__(self, growth, capacity, **kwargs):
        super().__init__(**kwargs)
        self.growth = growth
        self.capacity = capacity

    def etat_initial(self):
        return np.array([10.0])

    def derivee(self, t, y):
        return self.growth * y * (1 - y / self.capacity)


class Volterra(Modele):

    noms = ("Proies", "Prédateurs")

    def __init__(
        self,
        growthPrey,
        growthPredator,
        chanceInteractionPrey,
        chanceInteractionPredator,
        dt=0.01,
        **kwargs
    ):
        super().__init__(dt=dt, **kwargs)
        self.growthPrey = growthPrey
        self.growthPredator = growthPredator
        self.chanceInteractionPrey = chanceInteractionPrey
        self.chanceInteractionPredator = chanceInteractionPredator

    def etat_initial(self):
        return np.array([10.0, 5.0])

    def derivee(self, t, y):
        prey, predator = y
        return np.array(
            [
                self.growthPrey * prey - self.chanceInteractionPrey * prey * predator,
                -self.growthPredator * predator
                + self.chanceInteractionPredator * prey * predator,
            ]
        )
