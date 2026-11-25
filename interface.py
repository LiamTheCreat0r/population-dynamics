from matplotlib.colors import to_rgb
from matplotlib.widgets import Button, Slider

from affichage import COULEURS, COULEUR_GRILLE, COULEUR_AXE

TAILLE_FIGURE = (13, 6.5)  # pouces

# Colonne de gauche : x de départ et largeur (en fraction de la figure)
GAUCHE, LARGEUR = 0.023, 0.21
ECART = 0.015  # écart horizontal entre deux boutons voisins
HAUT_BOUTON, PAS_BOUTON = 0.047, 0.06
HAUT_SLIDER, PAS_SLIDER_MAX = 0.025, 0.07
LARGEUR_SLIDER = 0.15
BAS_SLIDERS = 0.25  # les curseurs restent au-dessus de la section Simulation
VITESSE_MIN, VITESSE_MAX, VITESSE_DEFAUT = 0.1, 10.0, 1.0  # pas de calcul par image
ECLAIRCISSEMENT_SURVOL = 0.2  # part de blanc mélangée à la couleur au survol


def styler(bouton, actif, couleur_active):
    """Bouton actif : fond `couleur_active` et texte blanc ; sinon fond gris clair.
    Au survol, le fond devient un peu plus clair."""
    fond = couleur_active if actif else COULEUR_GRILLE
    bouton.color = fond
    bouton.hovercolor = tuple(c + (1 - c) * ECLAIRCISSEMENT_SURVOL for c in to_rgb(fond))
    bouton.ax.set_facecolor(fond)
    bouton.label.set_color("white" if actif else COULEURS[0])


class Controles:
    """Panneau de gauche, en trois sections :
    Modèles (un bouton par modèle), Paramètres (un curseur par paramètre
    du modèle courant) et Simulation (Pêche / Vitesse / Pause / Reset).

    Elle ne fait que déclencher les fonctions reçues (callbacks) et refléter
    l'état qu'on lui indique ; la logique reste dans l'application.
    """

    def __init__(
        self,
        fig,
        noms_modeles,
        on_modele,
        on_reset,
        on_pause,
        on_peche,
        on_parametre,
        on_vitesse,
    ):
        self.fig = fig
        self.noms_modeles = list(noms_modeles)
        self.on_parametre = on_parametre
        self.boutons = {}
        self.sliders = []

        demi = (LARGEUR - ECART) / 2
        x_droite = GAUCHE + demi + ECART

        # --- Section « Modèles » : grille de deux colonnes ---
        self._titre("Modèles", 0.95)
        haut = 0.95 - 0.03 - HAUT_BOUTON
        for i, nom in enumerate(self.noms_modeles):
            x = GAUCHE if i % 2 == 0 else x_droite
            bas = haut - (i // 2) * PAS_BOUTON
            self.boutons[nom] = self._bouton(
                nom, x, bas, demi, lambda _e, n=nom: on_modele(n)
            )

        # --- Section « Paramètres » (les curseurs sont créés à la demande) ---
        y_titre = bas - 0.05
        self._titre("Paramètres", y_titre)
        self._y_premier_slider = y_titre - 0.085

        # --- Section « Simulation » : grille 2 × 2 ---
        self._titre("Simulation", 0.20)
        self.boutons["Pêche"] = self._bouton(
            "Pêche", GAUCHE, 0.11, demi, lambda _e: on_peche()
        )
        self.slider_vitesse = self._slider(
            x_droite, 0.115, 0.06, "Vitesse",
            VITESSE_MIN, VITESSE_MAX, VITESSE_DEFAUT, "×%.1f", on_vitesse,
        )
        self.boutons["Pause"] = self._bouton(
            "Pause", GAUCHE, 0.04, demi, lambda _e: on_pause()
        )
        self.boutons["Reset"] = self._bouton(
            "Reset", x_droite, 0.04, demi, lambda _e: on_reset()
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
        bouton.label.set_fontsize(11)
        bouton.on_clicked(action)
        return bouton  # la référence doit être gardée, sinon il est ramassé

    def _slider(self, x, y, largeur, libelle, vmin, vmax, valinit, valfmt, action):
        """Curseur avec son libellé au-dessus ; `action(valeur)` à chaque changement."""
        ax = self.fig.add_axes([x, y, largeur, HAUT_SLIDER])
        ax.set_title(libelle, loc="left", fontsize=10, color=COULEURS[0])
        slider = Slider(
            ax, "", vmin, vmax, valinit=valinit, valfmt=valfmt, color=COULEURS[1]
        )
        slider.on_changed(action)
        return slider  # même remarque que pour les boutons

    # --- Mise à jour depuis l'application -------------------------------------

    def marquer_actif(self, nom_actif):
        """Met en évidence le bouton du modèle en cours."""
        for nom in self.noms_modeles:
            styler(self.boutons[nom], nom == nom_actif, COULEURS[0])

    def afficher_pause(self, en_pause):
        """Adapte le libellé du bouton Pause."""
        self.boutons["Pause"].label.set_text("Reprendre" if en_pause else "Pause")

    def afficher_peche(self, possible, active):
        """Montre le bouton Pêche (si le modèle la gère) et son état."""
        b = self.boutons["Pêche"]
        b.ax.set_visible(possible)
        b.active = possible  # un bouton caché ne doit pas réagir aux clics
        styler(b, active, COULEURS[1])
        b.label.set_text("Pêche : active" if active else "Pêche")

    def afficher_parametres(self, parametres, valeurs):
        """Remplace les curseurs par ceux du modèle courant.

        `parametres` : tuples (clé, libellé, min, max, défaut) ;
        `valeurs` : dictionnaire des valeurs actuelles.
        """
        for slider in self.sliders:
            slider.disconnect_events()
            slider.ax.remove()

        self.sliders = []
        y = self._y_premier_slider
        # Espacement resserré si les curseurs ne tiennent pas tous
        place = self._y_premier_slider - BAS_SLIDERS
        pas = min(PAS_SLIDER_MAX, place / max(1, len(parametres) - 1))
        for cle, libelle, vmin, vmax, _defaut in parametres:
            self.sliders.append(
                self._slider(
                    GAUCHE, y, LARGEUR_SLIDER, libelle, vmin, vmax, valeurs[cle],
                    "%.3g", lambda v, c=cle: self.on_parametre(c, v),
                )
            )
            y -= pas
