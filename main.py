import matplotlib.pyplot as plt
import matplotlib.animation as animation

from modeles import Malthus, Verhulst, Volterra
from affichage import Graphique
from interface import Controles


class Application:

    # Les valeurs par défaut sont dans chaque classe (PARAMETRES)
    MODELES = {
        "Malthus": Malthus,
        "Verhulst": Verhulst,
        "Volterra": Volterra,
    }

    def __init__(self, depart="Volterra"):
        self.fig, self.ax = plt.subplots(figsize=(10, 5.5))
        self.nom = depart
        self.modele = None
        self.en_pause = False
        self.ani = None  # créé après le premier chargement

        self.controles = Controles(
            self.fig,
            self.MODELES,
            on_modele=self.charger,
            on_reset=lambda: self.charger(self.nom),
            on_pause=self.basculer_pause,
            on_parametre=self.changer_parametre,
        )
        self.charger(depart)

        self.ani = animation.FuncAnimation(
            self.fig,
            self._maj,
            frames=self._frames,
            interval=16,
            cache_frame_data=False,
        )

    # --- Actions déclenchées par les contrôles ---------------------------------

    def charger(self, nom):
        """Crée le modèle `nom` avec ses valeurs par défaut (sert aussi de reset)."""
        self.nom = nom
        self.modele = self.MODELES[nom]()
        self.graphique = Graphique(self.fig, self.ax, self.modele.noms)
        self.flux = self.modele.flux()
        self.graphique.reinitialiser(*next(self.flux))
        self.controles.marquer_actif(nom)
        self.controles.afficher_parametres(self.modele.PARAMETRES, self.modele.params)
        self._definir_pause(False)

    def changer_parametre(self, cle, valeur):
        """La simulation continue : le modèle relit ses paramètres à chaque pas."""
        self.modele.definir(cle, valeur)

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
