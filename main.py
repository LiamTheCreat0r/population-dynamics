import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button

from modeles import Malthus, Verhulst, Volterra
from affichage import Graphique, COULEURS, COULEUR_GRILLE


class Application:

    # Les modèles ne connaissent plus fig/ax : de simples constructeurs suffisent
    MODELES = {
        "Malthus": lambda: Malthus(1.01),
        "Verhulst": lambda: Verhulst(1.2, 1000),
        "Volterra": lambda: Volterra(1.0, 1.5, 0.1, 0.075),
    }

    def __init__(self, depart="Volterra"):
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.nom = depart
        self._creer_boutons()
        self.charger(depart)

        self.ani = animation.FuncAnimation(
            self.fig,
            self._maj,
            frames=self._frames,
            interval=10,
            cache_frame_data=False,
        )

    def _creer_boutons(self):
        self.boutons = {}
        largeur, ecart, x = 0.18, 0.02, 0.1
        for nom in [*self.MODELES, "Reset"]:
            bouton = Button(self.fig.add_axes([x, 0.04, largeur, 0.08]), nom)
            if nom == "Reset":
                bouton.on_clicked(lambda _e: self.charger(self.nom))
            else:
                bouton.on_clicked(lambda _e, n=nom: self.charger(n))
            self.boutons[nom] = bouton
            x += largeur + ecart

    def _colorer_boutons(self):
        for nom in self.MODELES:
            actif = nom == self.nom
            b = self.boutons[nom]
            b.color = COULEURS[0] if actif else COULEUR_GRILLE
            b.ax.set_facecolor(b.color)
            b.label.set_color("white" if actif else COULEURS[0])

    def charger(self, nom):
        """Crée le modèle `nom` et un graphique vierge (sert aussi de reset)."""
        self.nom = nom
        modele = self.MODELES[nom]()
        self.graphique = Graphique(self.fig, self.ax, modele.noms)
        self.flux = modele.flux()
        self.graphique.reinitialiser(*next(self.flux))
        self._colorer_boutons()
        self.fig.canvas.draw_idle()

    @staticmethod
    def _frames():
        while True:
            yield None

    def _maj(self, _frame):
        return self.graphique.ajouter(*next(self.flux))


app = Application()
plt.show()
