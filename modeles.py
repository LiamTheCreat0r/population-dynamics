import numpy as np
from abc import ABC, abstractmethod
from solveurs import rungeKutta


class Modele(ABC):

    noms = ("Population",)  # un nom par composante de l'état

    # Paramètres réglables : (clé, libellé, minimum, maximum, valeur par défaut)
    PARAMETRES = ()

    def __init__(self, solveur=rungeKutta, dt=0.1, **valeurs):
        self.solveur = solveur
        self.dt = dt
        # Valeurs courantes, modifiables à chaud (lues à chaque pas)
        self.params = {cle: defaut for cle, _, _, _, defaut in self.PARAMETRES}
        self.params.update(valeurs)

    def definir(self, cle, valeur):
        """Change un paramètre ; le prochain pas de calcul l'utilise."""
        self.params[cle] = valeur

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

    PARAMETRES = (("croissance", "Croissance", 0.0, 3.0, 1.01),)

    def etat_initial(self):
        return np.array([10.0])

    def derivee(self, t, y):
        return self.params["croissance"] * y


class Verhulst(Modele):

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

    noms = ("Proies", "Prédateurs")

    PARAMETRES = (
        ("croissance_proies", "Croissance des proies", 0.0, 3.0, 1.0),
        ("predation", "Croissance des proies", 0.0, 0.3, 0.1),
        ("mortalite_predateurs", "γ  Mortalité des prédateurs", 0.0, 3.0, 1.5),
        ("conversion", "δ  Gain des prédateurs par rencontre", 0.0, 0.3, 0.075),
    )

    def __init__(self, dt=0.01, **kwargs):
        super().__init__(dt=dt, **kwargs)

    def etat_initial(self):
        return np.array([10.0, 5.0])

    def derivee(self, t, y):
        p = self.params
        proies, predateurs = y
        return np.array(
            [
                p["croissance_proies"] * proies - p["predation"] * proies * predateurs,
                -p["mortalite_predateurs"] * predateurs
                + p["conversion"] * proies * predateurs,
            ]
        )
