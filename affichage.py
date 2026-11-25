from bisect import bisect_left

import matplotlib.pyplot as plt

COULEURS = ["#2B2F42", "#EF233C"]  # une couleur par série
COULEUR_GRILLE = "#E3E6EC"
COULEUR_AXE = "#8D99AE"

TAILLE_POLICE = 12
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = TAILLE_POLICE


def _style_axes(ax, xlabel, ylabel):
    """Style commun : seul l'axe du bas est tracé, grille horizontale légère."""
    for cote in ("top", "right", "left"):
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(COULEUR_AXE)
    ax.xaxis.set_ticks_position("bottom")
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", color=COULEUR_AXE)
    ax.grid(axis="y", color=COULEUR_GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def _oublier_avant(debut, temps, *series):
    """Supprime (en place) les points antérieurs à `debut` : le coût d'une
    image reste constant quelle que soit la durée de la simulation."""
    expires = bisect_left(temps, debut)
    del temps[:expires]
    for serie in series:
        del serie[:expires]


def _agrandir(get_lim, set_lim, valeur):
    """Agrandit un axe (avec 10 % de marge) si `valeur` dépasse son maximum."""
    vmin, vmax = get_lim()
    if valeur >= vmax:
        set_lim(vmin, valeur * 1.1)


class Graphique:
    """Trace une courbe par composante de l'état en fonction du temps,
    à partir du point (t0, etat0).

    L'axe des temps glisse pour montrer les `fenetre` dernières unités ;
    l'axe des populations ne fait que s'agrandir.
    """

    def __init__(self, ax, noms, t0, etat0, fenetre):
        self.ax = ax
        self.fenetre = fenetre
        ax.clear()
        _style_axes(ax, "Temps", "Population")

        self.lignes = []
        self.etiquettes = []
        for i, nom in enumerate(noms):
            couleur = COULEURS[i % len(COULEURS)]
            epaisseur = 2 if i == 0 else 2.5
            self.lignes.append(ax.plot([], [], lw=epaisseur, color=couleur)[0])
            # Étiquette au bout de la courbe, seulement s'il y en a plusieurs
            if len(noms) > 1:
                self.etiquettes.append(self._etiquette(nom, couleur))

        self.xdata = [t0]
        self.ydata = [[valeur] for valeur in etat0]
        ax.set_xlim(0, 1)
        ax.set_ylim(0, max(etat0) * 2)
        self._maj_artistes(t0, etat0)

    def ajouter(self, t, etat):
        """Ajoute un point et renvoie les artistes à redessiner."""
        self.xdata.append(t)
        for serie, valeur in zip(self.ydata, etat):
            serie.append(valeur)

        debut = t - self.fenetre
        _oublier_avant(debut, self.xdata, *self.ydata)

        # x : on suit le temps une fois le bord droit atteint
        if t >= self.ax.get_xlim()[1]:
            self.ax.set_xlim(max(0.0, debut), t)
        _agrandir(self.ax.get_ylim, self.ax.set_ylim, max(etat))

        return self._maj_artistes(t, etat)

    # --- Détails internes ------------------------------------------------------

    def _maj_artistes(self, t, etat):
        for ligne, serie in zip(self.lignes, self.ydata):
            ligne.set_data(self.xdata, serie)
        for etiquette, valeur in zip(self.etiquettes, etat):
            etiquette.xy = (t, valeur)  # l'étiquette suit le dernier point
        return (*self.lignes, *self.etiquettes)

    def _etiquette(self, texte, couleur):
        return self.ax.annotate(
            texte,
            xy=(0, 0),
            xytext=(8, 0),
            textcoords="offset points",
            color=couleur,
            fontweight="bold",
            ha="left",
            va="center",
            annotation_clip=False,  # reste visible hors de la zone du graphique
        )


class PlanDePhase:
    """Trajectoire d'un modèle à deux populations dans le plan (N, P).

    On garde les `fenetre` dernières unités de temps (comme `Graphique`) :
    une spirale qui s'enroule vers une boucle fixe signale un cycle limite,
    une spirale qui converge vers la croix un équilibre stable.
    Les axes partent de 0 et ne font que s'agrandir.
    """

    def __init__(self, ax, noms, t0, etat0, fenetre):
        self.ax = ax
        self.fenetre = fenetre
        ax.clear()
        _style_axes(ax, noms[0], noms[1])
        ax.set_title("Plan de phase", loc="left", fontsize=TAILLE_POLICE, color=COULEUR_AXE)

        self.trajectoire = ax.plot([], [], lw=1.5, color=COULEURS[0])[0]
        self.point = ax.plot([], [], "o", ms=7, color=COULEURS[1])[0]
        self.croix = ax.plot(
            [], [], "x", ms=10, mew=2.5, color=COULEUR_AXE, label="Équilibre"
        )[0]
        ax.legend(loc="upper right", frameon=False, fontsize=10)

        self.temps = [t0]
        self.n = [etat0[0]]
        self.p = [etat0[1]]
        ax.set_xlim(0, etat0[0] * 2)
        ax.set_ylim(0, etat0[1] * 2)
        self._maj_artistes(None)

    def ajouter(self, t, etat, equilibre):
        """Ajoute un point ; `equilibre` = (N*, P*) ou None. Renvoie les artistes."""
        self.temps.append(t)
        self.n.append(etat[0])
        self.p.append(etat[1])
        _oublier_avant(t - self.fenetre, self.temps, self.n, self.p)

        _agrandir(self.ax.get_xlim, self.ax.set_xlim, etat[0])
        _agrandir(self.ax.get_ylim, self.ax.set_ylim, etat[1])
        return self._maj_artistes(equilibre)

    def _maj_artistes(self, equilibre):
        self.trajectoire.set_data(self.n, self.p)
        self.point.set_data([self.n[-1]], [self.p[-1]])
        if equilibre is None:
            self.croix.set_data([], [])
        else:
            self.croix.set_data([equilibre[0]], [equilibre[1]])
        return self.trajectoire, self.point, self.croix
