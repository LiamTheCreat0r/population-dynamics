from matplotlib.widgets import Button

from affichage import COULEURS, COULEUR_GRILLE


class Controles:
    """Barre de boutons : un par modèle, plus Reset et Pause.

    Elle ne fait que déclencher les fonctions reçues (callbacks) et refléter
    l'état qu'on lui indique ; la logique reste dans l'application.
    """

    def __init__(self, fig, noms_modeles, on_modele, on_reset, on_pause):
        self.fig = fig
        self.noms_modeles = list(noms_modeles)
        self.boutons = {}

        actions = {
            **{nom: (lambda _e, n=nom: on_modele(n)) for nom in self.noms_modeles},
            "Reset": lambda _e: on_reset(),
            "Pause": lambda _e: on_pause(),
        }

        largeur, ecart, x = 0.15, 0.02, 0.06
        for nom, action in actions.items():
            bouton = Button(fig.add_axes([x, 0.04, largeur, 0.08]), nom)
            bouton.on_clicked(action)
            self.boutons[nom] = bouton  # références gardées : sinon ramassés
            x += largeur + ecart

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
