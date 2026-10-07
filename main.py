import matplotlib.pyplot as plt
import matplotlib.animation as animation

from modeles import Malthus, Verhulst, Volterra
from affichage import Graphique
from interface import Controles


class Application:

    MODELES = {
        "Malthus": lambda: Malthus(1.01),
        "Verhulst": lambda: Verhulst(1.2, 1000),
        "Volterra": lambda: Volterra(1.0, 1.5, 0.1, 0.075),
    }

    def __init__(self, depart="Volterra"):
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.nom = depart
        self.en_pause = False
        self.ani = None  # créé après le premier chargement

        self.controles = Controles(
            self.fig,
            self.MODELES,
            on_modele=self.charger,
            on_reset=lambda: self.charger(self.nom),
            on_pause=self.basculer_pause,
        )
        self.charger(depart)

        self.ani = animation.FuncAnimation(
            self.fig,
            self._maj,
            frames=self._frames,
            interval=10,
            cache_frame_data=False,
        )

    # --- Actions déclenchées par les boutons -----------------------------------

    def charger(self, nom):
        """Crée le modèle `nom` et un graphique vierge (sert aussi de reset)."""
        self.nom = nom
        modele = self.MODELES[nom]()
        self.graphique = Graphique(self.fig, self.ax, modele.noms)
        self.flux = modele.flux()
        self.graphique.reinitialiser(*next(self.flux))
        self.controles.marquer_actif(nom)
        self._definir_pause(False)  # un nouveau modèle repart en lecture

    def basculer_pause(self):
        self._definir_pause(not self.en_pause)

    def _definir_pause(self, pause):
        self.en_pause = pause
        self.controles.afficher_pause(pause)
        if self.ani is not None:
            if pause:
                self.ani.pause()
            else:
                self.ani.resume()
        self.fig.canvas.draw_idle()

    # --- Animation -------------------------------------------------------------

    @staticmethod
    def _frames():
        while True:
            yield None

    def _maj(self, _frame):
        return self.graphique.ajouter(*next(self.flux))


app = Application()
plt.show()
