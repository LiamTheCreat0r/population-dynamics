import matplotlib.pyplot as plt
import matplotlib.animation as animation

from matplotlib.widgets import Button
from modeles import *


class Application:

    # Nom du bouton -> fonction qui construit le modèle (sur la figure partagée)
    MODELES = {
        "Malthus": lambda fig, ax: Malthus(1.01, fig=fig, ax=ax),
        "Verhulst": lambda fig, ax: Verhulst(1.2, 1000, fig=fig, ax=ax),
        "Volterra": lambda fig, ax: Volterra(1.0, 1.5, 0.1, 0.075, fig=fig, ax=ax),
    }

    def __init__(self):
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.nom = "Volterra"
        self.modele = None
        self.gen = None

        self._creer_boutons()
        self.charger(self.nom)

        self.ani = animation.FuncAnimation(
            self.fig,
            self._maj,
            frames=self._frames,
            interval=10,
            cache_frame_data=False,
        )

    # --- Boutons ---------------------------------------------------------------

    def _creer_boutons(self):
        self.boutons = {}  # on garde les références, sinon les boutons sont ramassés
        noms = list(self.MODELES) + ["Reset"]
        largeur, ecart, x = 0.18, 0.02, 0.1
        for nom in noms:
            ax_btn = self.fig.add_axes([x, 0.04, largeur, 0.08])
            bouton = Button(ax_btn, nom)
            if nom == "Reset":
                bouton.on_clicked(lambda _event: self.charger(self.nom))
            else:
                bouton.on_clicked(lambda _event, n=nom: self.charger(n))
            self.boutons[nom] = bouton
            x += largeur + ecart

    def _colorer_boutons(self):
        for nom in self.MODELES:
            actif = nom == self.nom
            couleur = COULEUR_PROIES if actif else COULEUR_GRILLE
            b = self.boutons[nom]
            b.color = couleur
            b.ax.set_facecolor(couleur)
            b.label.set_color("white" if actif else COULEUR_PROIES)

    # --- Gestion du modèle -----------------------------------------------------

    def charger(self, nom):
        """Construit (ou reconstruit = reset) le modèle `nom` et repart de zéro."""
        self.nom = nom
        self.modele = self.MODELES[nom](self.fig, self.ax)
        self.modele.init()
        self.gen = self.modele.data_gen()
        self._colorer_boutons()
        self.fig.canvas.draw_idle()

    # --- Animation -------------------------------------------------------------

    @staticmethod
    def _frames():
        while True:  # flux infini : les données viennent du modèle courant
            yield None

    def _maj(self, _frame):
        return self.modele.run(next(self.gen))


app = Application()
plt.show()
