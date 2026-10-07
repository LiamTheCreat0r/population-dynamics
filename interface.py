from matplotlib.widgets import Button, Slider

from affichage import COULEURS, COULEUR_GRILLE, COULEUR_AXE

# Colonne de gauche : x de départ et largeur (en fraction de la figure)
GAUCHE, LARGEUR = 0.03, 0.27
HAUT_BOUTON, PAS_BOUTON = 0.055, 0.07
HAUT_SLIDER, PAS_SLIDER = 0.03, 0.095


class Controles:
    """Panneau de gauche, en trois sections :
    Modèles (un bouton par modèle), Paramètres (un curseur par paramètre
    du modèle courant) et Simulation (Pause / Reset).

    Elle ne fait que déclencher les fonctions reçues (callbacks) et refléter
    l'état qu'on lui indique ; la logique reste dans l'application.
    """

    def __init__(self, fig, noms_modeles, on_modele, on_reset, on_pause, on_parametre):
        self.fig = fig
        self.noms_modeles = list(noms_modeles)
        self.on_parametre = on_parametre
        self.boutons = {}
        self.sliders = []
        self._axes_sliders = []

        # --- Section « Modèles » ---
        self._titre("Modèles", 0.94)
        bas = 0.94 - 0.03 - HAUT_BOUTON
        for nom in self.noms_modeles:
            self.boutons[nom] = self._bouton(
                nom, GAUCHE, bas, LARGEUR, lambda _e, n=nom: on_modele(n)
            )
            bas -= PAS_BOUTON
        bas += PAS_BOUTON  # position du dernier bouton

        # --- Section « Paramètres » (les curseurs sont créés à la demande) ---
        self._y_titre_params = bas - 0.06
        self._titre("Paramètres", self._y_titre_params)
        self._y_premier_slider = self._y_titre_params - 0.10

        # --- Section « Simulation » ---
        self._titre("Simulation", 0.14)
        demi = (LARGEUR - 0.02) / 2
        self.boutons["Pause"] = self._bouton(
            "Pause", GAUCHE, 0.04, demi, lambda _e: on_pause()
        )
        self.boutons["Reset"] = self._bouton(
            "Reset", GAUCHE + demi + 0.02, 0.04, demi, lambda _e: on_reset()
        )

    # --- Construction ----------------------------------------------------------

    def _titre(self, texte, y):
        self.fig.text(
            GAUCHE,
            y,
            texte.upper(),
            fontsize=10,
            fontweight="bold",
            color=COULEUR_AXE,
            va="center",
        )

    def _bouton(self, texte, x, y, largeur, action):
        bouton = Button(self.fig.add_axes([x, y, largeur, HAUT_BOUTON]), texte)
        bouton.on_clicked(action)
        return bouton  # la référence doit être gardée, sinon il est ramassé

    # --- Mise à jour depuis l'application -------------------------------------

    def marquer_actif(self, nom_actif):
        """Met en évidence le bouton du modèle en cours."""
        for nom in self.noms_modeles:
            actif = nom == nom_actif
            b = self.boutons[nom]
            b.color = COULEURS[0] if actif else COULEUR_GRILLE
            b.ax.set_facecolor(b.color)
            b.label.set_color("white" if actif else COULEURS[0])

    def afficher_pause(self, en_pause):
        """Adapte le libellé du bouton Pause."""
        self.boutons["Pause"].label.set_text("Reprendre" if en_pause else "Pause")

    def afficher_parametres(self, parametres, valeurs):
        """Remplace les curseurs par ceux du modèle courant.

        `parametres` : tuples (clé, libellé, min, max, défaut) ;
        `valeurs` : dictionnaire des valeurs actuelles.
        """
        for slider in self.sliders:
            slider.disconnect_events()
        for ax in self._axes_sliders:
            ax.remove()
        self.sliders, self._axes_sliders = [], []

        y = self._y_premier_slider
        for cle, libelle, vmin, vmax, _defaut in parametres:
            ax = self.fig.add_axes([GAUCHE, y, 0.19, HAUT_SLIDER])
            ax.set_title(libelle, loc="left", fontsize=10, color=COULEURS[0])
            slider = Slider(
                ax,
                "",
                vmin,
                vmax,
                valinit=valeurs[cle],
                valfmt="%.3g",
                color=COULEURS[1],
            )
            slider.on_changed(lambda v, c=cle: self.on_parametre(c, v))
            self.sliders.append(slider)
            self._axes_sliders.append(ax)
            y -= PAS_SLIDER
