import matplotlib.pyplot as plt
import matplotlib.animation as animation

from modeles import Malthus, Verhulst, Volterra
from affichage import Graphique
from interface import Controles, VITESSE_DEFAUT

POPULATION_MAX = 1e300


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
        self.en_pause = False
        self.vitesse = VITESSE_DEFAUT
        self._pas_en_attente = 0.0  # fraction de pas reportée à l'image suivante
        self.ani = None  # créé après le premier chargement

        self.controles = Controles(
            self.fig,
            self.MODELES,
            on_modele=self.charger,
            on_reset=lambda: self.charger(self.nom),
            on_pause=self.basculer_pause,
            on_peche=self.basculer_peche,
            on_parametre=self.changer_parametre,
            on_vitesse=self.changer_vitesse,
        )
        self.charger(depart)

        self.ani = animation.FuncAnimation(
            self.fig,
            self._maj,
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
        self.controles.afficher_peche(self.modele.PECHE_POSSIBLE, self.modele.peche)
        self._definir_pause(False)

    def basculer_peche(self):
        """Active ou coupe la pêche ; la simulation continue."""
        self.modele.peche = not self.modele.peche
        self.controles.afficher_peche(self.modele.PECHE_POSSIBLE, self.modele.peche)
        self.fig.canvas.draw_idle()

    def changer_parametre(self, cle, valeur):
        """La simulation continue : le modèle relit ses paramètres à chaque pas."""
        self.modele.definir(cle, valeur)

    def changer_vitesse(self, valeur):
        self.vitesse = valeur

    def basculer_pause(self):
        self._definir_pause(not self.en_pause)

    def _definir_pause(self, pause):
        changement = pause != self.en_pause
        self.en_pause = pause
        self.controles.afficher_pause(pause)
        # Relancer un timer déjà actif en créerait un second sur macOS
        if self.ani is not None and changement:
            if pause:
                self.ani.pause()
            else:
                self.ani.resume()
        self.fig.canvas.draw_idle()

    # --- Animation -------------------------------------------------------------

    def _maj(self, _frame):
        """Avance de `vitesse` pas par image, en cumulant les fractions de pas."""
        self._pas_en_attente += self.vitesse
        nb_pas = int(self._pas_en_attente)
        self._pas_en_attente -= nb_pas
        artistes = ()
        for _ in range(nb_pas):
            t, etat = next(self.flux)
            if max(etat) > POPULATION_MAX:  # au-delà, le graphique ne peut plus suivre
                self._definir_pause(True)
                break
            artistes = self.graphique.ajouter(t, etat)
        return artistes


if __name__ == "__main__":
    Application()
    plt.show()
