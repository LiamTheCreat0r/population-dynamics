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

    FENETRE = 10.0  # durée visible sur les graphiques (unités de temps)

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

    def equilibre(self):
        """Équilibre intérieur (toutes populations > 0) pour les paramètres
        actuels, ou None s'il n'y en a pas (ou s'il n'est pas affiché)."""
        return None

    def effort(self):
        """Effort de pêche effectif : q si la pêche est active, sinon 0."""
        return self.params.get("effort_peche", 0.0) if self.peche else 0.0

    SOUS_PAS_MAX = 1024  # nombre maximal de sous-pas pour franchir un pas dt

    def pas(self, etat):
        """Renvoie l'état à t + dt.

        En temps normal, le solveur fait un seul pas de durée dt. Si le résultat
        est absurde (population négative ou non finie), l'équation est trop
        raide pour ce pas — par ex. Holling–Tanner quand les proies tendent
        vers 0 — et on recommence avec 2, 4, 8… sous-pas plus courts.
        Une population ne pouvant pas être négative, on la borne à 0.
        """
        n = 1
        while True:
            _, y = self.solveur(self.derivee, etat, self.dt, self.dt / n)
            suivant = y[-1]
            valide = np.all(np.isfinite(suivant)) and np.min(suivant) >= 0
            if valide or n >= self.SOUS_PAS_MAX:
                return np.maximum(suivant, 0.0)
            n *= 2

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
        q = self.effort()
        rencontres = proies * predateurs
        return np.array(
            [
                p["croissance_proies"] * proies
                - p["predation"] * rencontres
                - q * proies,
                -p["mortalite_predateurs"] * predateurs
                + p["conversion"] * rencontres
                - q * predateurs,
            ]
        )

    def equilibre(self):
        """N* = (γ + q)/δ, P* = (α − q)/β."""
        p = self.params
        q = self.effort()
        if p["conversion"] == 0 or p["predation"] == 0:
            return None
        n = (p["mortalite_predateurs"] + q) / p["conversion"]
        m = (p["croissance_proies"] - q) / p["predation"]
        return np.array([n, m]) if n > 0 and m > 0 else None


class HollingTanner(Modele):
    """Proies N et prédateurs P (Holling–Tanner), avec pêche optionnelle :

        N' = r·N·(1 − N/K) − w·N·P/(D + N) − q·N
        P' = s·P·(1 − h·P/N)               − q·P

    - proies logistiques, de capacité K (comme Verhulst) ;
    - prédation de Holling type II : un prédateur mange au plus w proies
      par unité de temps, D = densité de proies donnant la moitié de ce maximum ;
    - prédateurs logistiques, de capacité N/h (h proies pour nourrir un prédateur).

    Avec les valeurs par défaut, l'équilibre est instable et les trajectoires
    convergent vers un cycle limite ; pour s ≳ 0.3 l'équilibre devient stable.
    """

    noms = ("Proies", "Prédateurs")

    DT = 0.05

    FENETRE = 60.0  # un cycle dure ~21 : on en voit environ trois

    PECHE_POSSIBLE = True

    PARAMETRES = (
        ("croissance_proies", "r  Croissance des proies", 0.0, 3.0, 1.0),
        ("capacite", "K  Capacité du milieu", 20.0, 500.0, 100.0),
        ("predation_max", "w  Prédation maximale", 0.0, 3.0, 1.0),
        ("demi_saturation", "D  Demi-saturation", 1.0, 50.0, 10.0),
        ("croissance_predateurs", "s  Croissance des prédateurs", 0.0, 1.0, 0.2),
        ("proies_par_predateur", "h  Proies par prédateur", 0.1, 3.0, 1.0),
        ("effort_peche", "q  Effort de pêche", 0.0, 1.0, 0.1),
    )

    def etat_initial(self):
        return np.array([10.0, 5.0])

    def derivee(self, t, y):
        p = self.params
        proies, predateurs = y
        q = self.effort()
        consommation = p["predation_max"] * proies / (p["demi_saturation"] + proies)
        return np.array(
            [
                p["croissance_proies"] * proies * (1 - proies / p["capacite"])
                - consommation * predateurs
                - q * proies,
                # max(…) : évite la division par zéro si les proies s'éteignent
                p["croissance_predateurs"]
                * predateurs
                * (1 - p["proies_par_predateur"] * predateurs / max(proies, 1e-9))
                - q * predateurs,
            ]
        )

    def equilibre(self):
        """P' = 0 donne P = (s − q)·N/(s·h). En reportant dans N' = 0, avec
        c = w·(s − q)/(s·h) : (r − q − r·N/K)·(D + N) = c·N, du second degré en N."""
        p = self.params
        r, k, d = p["croissance_proies"], p["capacite"], p["demi_saturation"]
        s, h = p["croissance_predateurs"], p["proies_par_predateur"]
        q = self.effort()
        if s <= q:  # les prédateurs ne peuvent pas se maintenir
            return None
        c = p["predation_max"] * (s - q) / (s * h)
        racines = np.roots([-r / k, r - q - r * d / k - c, (r - q) * d])
        positives = [x.real for x in racines if abs(x.imag) < 1e-12 and x.real > 0]
        if not positives:
            return None
        n = max(positives)
        return np.array([n, (s - q) * n / (s * h)])
