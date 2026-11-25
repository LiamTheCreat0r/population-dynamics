from bisect import bisect_left

import matplotlib.pyplot as plt

COULEURS = ["#2B2F42", "#EF233C"]  # une couleur par série
COULEUR_GRILLE = "#E3E6EC"
COULEUR_AXE = "#8D99AE"

FENETRE = 10.0  # durée visible sur le graphique (unités de temps)

TAILLE_POLICE = 12
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = TAILLE_POLICE


class Graphique:
    """Trace une courbe par composante de l'état, à partir du point (t0, etat0).

    L'axe des temps glisse pour montrer les FENETRE dernières unités ;
    l'axe des populations ne fait que s'agrandir.
    """

    def __init__(self, fig, ax, noms, t0, etat0):
        self.ax = ax
        ax.clear()
        self._style_axes()

        self.lignes = []
        self.etiquettes = []
        for i, nom in enumerate(noms):
            couleur = COULEURS[i % len(COULEURS)]
            epaisseur = 2 if i == 0 else 2.5
            self.lignes.append(ax.plot([], [], lw=epaisseur, color=couleur)[0])
            # Étiquette au bout de la courbe, seulement s'il y en a plusieurs
            if len(noms) > 1:
                self.etiquettes.append(self._etiquette(nom, couleur))

        # La colonne de gauche est réservée aux contrôles ; à droite, la place
        # pour les étiquettes
        fig.subplots_adjust(
            left=0.36,
            bottom=0.12,
            top=0.95,
            right=0.85 if self.etiquettes else 0.95,
        )

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

        # Oublie les points sortis de la fenêtre : le coût d'une image reste constant
        debut = t - FENETRE
        expires = bisect_left(self.xdata, debut)
        del self.xdata[:expires]
        for serie in self.ydata:
            del serie[:expires]

        # x : on suit le temps une fois le bord droit atteint
        if t >= self.ax.get_xlim()[1]:
            self.ax.set_xlim(max(0.0, debut), t)
        # y : on agrandit (avec 10 % de marge) dès qu'une courbe dépasse
        ymin, ymax = self.ax.get_ylim()
        if max(etat) >= ymax:
            self.ax.set_ylim(ymin, max(etat) * 1.1)

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

    def _style_axes(self):
        for cote in ("top", "right", "left"):
            self.ax.spines[cote].set_visible(False)
        self.ax.spines["bottom"].set_color(COULEUR_AXE)
        self.ax.xaxis.set_ticks_position("bottom")
        self.ax.tick_params(axis="y", length=0)
        self.ax.tick_params(axis="x", color=COULEUR_AXE)
        self.ax.grid(axis="y", color=COULEUR_GRILLE, linewidth=0.8)
        self.ax.set_axisbelow(True)
        self.ax.set_xlabel("Temps")
        self.ax.set_ylabel("Population")
