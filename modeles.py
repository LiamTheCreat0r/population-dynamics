import itertools
from abc import ABC, abstractmethod
from solveurs import *

import matplotlib.pyplot as plt

# --- Style global (inspiré de "Making pretty plots") ---------------------------

# Palette : bleu nuit pour les proies, rouge vif pour les prédateurs (mis en avant)
COULEUR_PROIES = "#2B2F42"
COULEUR_PREDATEURS = "#EF233C"
COULEUR_GRILLE = "#E3E6EC"
COULEUR_AXE = "#8D99AE"

# Polices : taille unique et lisible, sans empattement
TAILLE_POLICE = 12
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = TAILLE_POLICE
plt.rcParams["axes.labelsize"] = TAILLE_POLICE
plt.rcParams["xtick.labelsize"] = TAILLE_POLICE
plt.rcParams["ytick.labelsize"] = TAILLE_POLICE


class Modele(ABC):

    POPULATION_INIT = 10

    def __init__(self, solveur=rungeKutta, dt=0.1):
        self.solveur = solveur
        self.dt = dt
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        (self.line,) = self.ax.plot([], [], lw=2, color=COULEUR_PROIES)
        self._style_axes()
        self.xdata = []
        self.ydata = []

    @abstractmethod
    def derivee(self, t, y):
        """Second membre de l'équation différentielle y' = f(t, y)."""

    def generation(self, etat):
        """Un pas du solveur : renvoie l'état à t + dt."""
        _, y = self.solveur(self.derivee, etat, self.dt, self.dt)
        return y[-1]

    def _style_axes(self):
        """Épure le graphique : pas de cadre, grille discrète, axes nommés."""
        # On retire le cadre (haut, droite, gauche) : seul l'axe du bas reste
        for cote in ("top", "right", "left"):
            self.ax.spines[cote].set_visible(False)
        self.ax.spines["bottom"].set_color(COULEUR_AXE)

        # Graduations uniquement en bas ; la grille horizontale guide l'oeil
        self.ax.xaxis.set_ticks_position("bottom")
        self.ax.tick_params(axis="y", length=0)
        self.ax.tick_params(axis="x", color=COULEUR_AXE)
        self.ax.grid(axis="y", color=COULEUR_GRILLE, linewidth=0.8)
        self.ax.set_axisbelow(True)  # la grille passe derrière les courbes

        self.ax.set_xlabel("Temps")
        self.ax.set_ylabel("Population")

    def sauvegarder(self, nom_fichier="graphique.png"):
        """Enregistre le graphique en haute résolution (300 DPI)."""
        self.fig.savefig(nom_fichier, dpi=300, bbox_inches="tight")

    def init(self):
        self.ax.set_ylim(self.POPULATION_INIT, self.POPULATION_INIT * 2)
        self.ax.set_xlim(0, 1)
        self.xdata.clear()
        self.xdata.append(0)
        self.ydata.clear()
        self.ydata.append(self.POPULATION_INIT)
        self.line.set_data(self.xdata, self.ydata)
        return self.line

    def run(self, data):
        t, y = data
        self.xdata.append(t)
        self.ydata.append(y)

        xmin, xmax = self.ax.get_xlim()
        if t >= xmax:
            self.ax.set_xlim(xmin, self.xdata[-1])
            self.ax.figure.canvas.draw()

        ymin, ymax = self.ax.get_ylim()
        if y >= ymax:
            self.ax.set_ylim(ymin, self.ydata[-1])
            self.ax.figure.canvas.draw()

        self.line.set_data(self.xdata, self.ydata)
        return self.line

    def data_gen(self):
        for cnt in itertools.count(1):
            yield cnt * self.dt, self.generation(self.ydata[-1])


class Malthus(Modele):

    growth: float

    def __init__(self, growth, **kwargs):
        super().__init__(**kwargs)
        self.growth = growth

    def derivee(self, t, y):
        return self.growth * y


class Verhulst(Modele):

    growth: float
    environnementCapacity: float

    def __init__(self, growth, environnementCapacity, **kwargs):
        super().__init__(**kwargs)
        self.growth = growth
        self.environnementCapacity = environnementCapacity

    def derivee(self, t, y):
        return self.growth * y * (1 - y / self.environnementCapacity)


class Volterra(Modele):
    """Modèle proie-prédateur : un seul graphique avec une courbe par population."""

    # Population initiale de prédateurs (les proies utilisent POPULATION_INIT)
    PREDATOR_INIT = 5

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

        # Paramètres du modèle
        self.growthPrey = growthPrey
        self.growthPredator = growthPredator
        self.chanceInteractionPrey = chanceInteractionPrey
        self.chanceInteractionPredator = chanceInteractionPredator
        self.dt = dt  # pas de temps de l'intégration d'Euler

        # Courbe des prédateurs sur le même axe (self.line = courbe des proies)
        (self.line_pred,) = self.ax.plot([], [], lw=2.5, color=COULEUR_PREDATEURS)

        # Étiquettes directes au bout des courbes, à la place de la légende
        self.label_proies = self._etiquette("Proies", COULEUR_PROIES)
        self.label_pred = self._etiquette("Prédateurs", COULEUR_PREDATEURS)

        # On laisse de la place à droite pour les étiquettes
        self.fig.subplots_adjust(right=0.85)

        # Historique des prédateurs (xdata et ydata sont déjà créés par Modele)
        self.ydata_pred = []

    def derivee(self, t, y):
        prey, predator = y
        return np.array(
            [
                self.growthPrey * prey - self.chanceInteractionPrey * prey * predator,
                -self.growthPredator * predator
                + self.chanceInteractionPredator * prey * predator,
            ]
        )

    def data_gen(self):
        etat = np.array([self.POPULATION_INIT, self.PREDATOR_INIT], dtype=float)
        t = 0
        while True:
            t += self.dt
            etat = self.generation(etat)
            yield t, etat[0], etat[1]

    def _etiquette(self, texte, couleur):
        """Crée une étiquette colorée, décalée de 8 points à droite de son point."""
        return self.ax.annotate(
            texte,
            xy=(0, 0),
            xytext=(8, 0),
            textcoords="offset points",
            color=couleur,
            fontweight="bold",
            ha="left",
            va="center",
            annotation_clip=False,  # reste visible même hors de l'axe
        )

    def generation(self, populationPrey, populationPredator):
        """Calcule un pas d'Euler du système de Lotka-Volterra."""
        # Variation des proies : elles se reproduisent, mais sont mangées
        # lors des rencontres avec les prédateurs
        dPrey = (
            self.growthPrey * populationPrey
            - self.chanceInteractionPrey * populationPrey * populationPredator
        )
        # Variation des prédateurs : ils meurent naturellement, mais se
        # reproduisent en mangeant des proies
        dPredator = (
            -self.growthPredator * populationPredator
            + self.chanceInteractionPredator * populationPrey * populationPredator
        )
        # Nouvel état = ancien état + pas de temps * variation
        return (
            populationPrey + self.dt * dPrey,
            populationPredator + self.dt * dPredator,
        )

    def data_gen(self):
        """Générateur pour FuncAnimation : produit (t, proies, prédateurs)."""
        t = 0
        prey, predator = self.POPULATION_INIT, self.PREDATOR_INIT
        while True:
            t += self.dt
            prey, predator = self.generation(prey, predator)
            yield t, prey, predator

    def init(self):
        """Initialise l'animation : bornes des axes et points de départ."""
        self.ax.set_xlim(0, 1)
        # L'axe y doit pouvoir contenir les deux populations
        self.ax.set_ylim(0, max(self.POPULATION_INIT, self.PREDATOR_INIT) * 2)

        # Réinitialisation des historiques avec l'état initial
        self.xdata[:] = [0]
        self.ydata[:] = [self.POPULATION_INIT]
        self.ydata_pred[:] = [self.PREDATOR_INIT]

        self.line.set_data(self.xdata, self.ydata)
        self.line_pred.set_data(self.xdata, self.ydata_pred)

        # Les étiquettes repartent du point initial de chaque courbe
        self.label_proies.xy = (0, self.POPULATION_INIT)
        self.label_pred.xy = (0, self.PREDATOR_INIT)
        return self.line, self.line_pred, self.label_proies, self.label_pred

    def run(self, data):
        """Ajoute un point pour chaque population et ajuste les axes."""
        t, prey, predator = data
        self.xdata.append(t)
        self.ydata.append(prey)
        self.ydata_pred.append(predator)

        # Si le temps dépasse l'axe des x, on l'étend
        xmin, xmax = self.ax.get_xlim()
        if t >= xmax:
            self.ax.set_xlim(xmin, t)
            self.fig.canvas.draw()

        # Si l'une des deux populations dépasse l'axe des y, on l'étend
        ymin, ymax = self.ax.get_ylim()
        ymax_data = max(prey, predator)
        if ymax_data >= ymax:
            self.ax.set_ylim(ymin, ymax_data * 1.1)
            self.fig.canvas.draw()

        self.line.set_data(self.xdata, self.ydata)
        self.line_pred.set_data(self.xdata, self.ydata_pred)

        # Les étiquettes suivent le bout de chaque courbe
        self.label_proies.xy = (t, prey)
        self.label_pred.xy = (t, predator)
        return self.line, self.line_pred, self.label_proies, self.label_pred
