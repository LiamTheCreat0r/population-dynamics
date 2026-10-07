import matplotlib.pyplot as plt

COULEURS = ["#2B2F42", "#EF233C"]  # une couleur par série
COULEUR_GRILLE = "#E3E6EC"
COULEUR_AXE = "#8D99AE"
COULEUR_TEXTE = COULEURS[0]

TAILLE_POLICE = 12
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = TAILLE_POLICE


class Graphique:
    """Trace n courbes sur un axe existant, avec axes qui s'étendent seuls."""

    def __init__(self, fig, ax, noms):
        self.fig, self.ax, self.noms = fig, ax, noms
        ax.clear()
        self._style_axes()

        self.lignes = [
            ax.plot([], [], lw=2.5 if i else 2, color=COULEURS[i % len(COULEURS)])[0]
            for i in range(len(noms))
        ]
        # Étiquettes directes seulement s'il y a plusieurs courbes
        self.etiquettes = (
            [
                self._etiquette(n, COULEURS[i % len(COULEURS)])
                for i, n in enumerate(noms)
            ]
            if len(noms) > 1
            else []
        )
        fig.subplots_adjust(bottom=0.22, right=0.85 if self.etiquettes else 0.95)

        self.xdata, self.ydata = [], [[] for _ in noms]

    # --- Interface utilisée par l'application ----------------------------------

    def reinitialiser(self, t, etat):
        self.xdata[:] = [t]
        for serie, valeur in zip(self.ydata, etat):
            serie[:] = [valeur]
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, max(etat) * 2)
        self._maj_artistes(t, etat)

    def ajouter(self, t, etat):
        self.xdata.append(t)
        for serie, valeur in zip(self.ydata, etat):
            serie.append(valeur)

        xmin, xmax = self.ax.get_xlim()
        if t >= xmax:
            self.ax.set_xlim(xmin, t)
        ymin, ymax = self.ax.get_ylim()
        if max(etat) >= ymax:
            self.ax.set_ylim(ymin, max(etat) * 1.1)

        return self._maj_artistes(t, etat)

    def sauvegarder(self, nom_fichier="graphique.png"):
        self.fig.savefig(nom_fichier, dpi=300, bbox_inches="tight")

    # --- Détails internes ------------------------------------------------------

    def _maj_artistes(self, t, etat):
        for ligne, serie in zip(self.lignes, self.ydata):
            ligne.set_data(self.xdata, serie)
        for etiquette, valeur in zip(self.etiquettes, etat):
            etiquette.xy = (t, valeur)
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
            annotation_clip=False,
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
