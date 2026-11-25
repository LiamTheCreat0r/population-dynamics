import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox

from modeles import Malthus, Verhulst, Volterra, HollingTanner
from affichage import Graphique, PlanDePhase
from interface import Controles, TAILLE_FIGURE, VITESSE_DEFAUT

POPULATION_MAX = 1e300

# Animation : vitesse ×1 = IMAGES_PAR_SECONDE pas de calcul par seconde réelle
IMAGES_PAR_SECONDE = 60
DELAI_MS = 16  # pause entre la fin d'une image et le début de la suivante
DUREE_IMAGE_MAX = 0.1  # s ; au-delà (fenêtre déplacée…), on ne rattrape pas le retard

# Position des graphiques [gauche, bas, largeur, hauteur] (fraction de la figure) ;
# la colonne de gauche est réservée aux contrôles
POSITION_TEMPS_SEUL = [0.29, 0.12, 0.67, 0.83]
POSITION_TEMPS = [0.29, 0.12, 0.33, 0.83]  # place à droite pour les étiquettes
POSITION_PHASE = [0.73, 0.12, 0.25, 0.80]
# Zone redessinée à chaque image (graphiques, graduations, étiquettes comprises),
# en fraction de la figure : tout ce qui est à droite de la colonne de contrôles
ZONE_GRAPHIQUES = [[0.24, 0.0], [1.0, 1.0]]


class Application:

    # Les valeurs par défaut sont dans chaque classe (PARAMETRES)
    MODELES = {
        "Malthus": Malthus,
        "Verhulst": Verhulst,
        "Volterra": Volterra,
        "Holling-Tanner": HollingTanner,
    }

    def __init__(self, depart="Volterra"):
        self.fig = plt.figure(figsize=TAILLE_FIGURE)
        self.ax_temps = self.fig.add_axes(POSITION_TEMPS_SEUL)
        self.ax_phase = self.fig.add_axes(POSITION_PHASE)

        # Blitting : les graphiques sont « animés », donc exclus des dessins
        # complets de la figure. Après chaque dessin complet, on mémorise le fond
        # de leur zone ; chaque image se contente ensuite de restaurer ce fond,
        # de redessiner les deux graphiques et de recopier cette zone à l'écran.
        # Les contrôles ne sont redessinés que lorsqu'ils changent.
        for ax in (self.ax_temps, self.ax_phase):
            ax.set_animated(True)
        self._fond = None
        self.fig.canvas.mpl_connect("draw_event", self._apres_dessin_complet)
        self.nom = depart
        self.en_pause = False
        self.vitesse = VITESSE_DEFAUT
        self._pas_en_attente = 0.0  # fraction de pas reportée à l'image suivante
        self._derniere_image = None  # instant (s) de l'image précédente
        self._image_prevue = False
        self.timer = None  # créé après le premier chargement

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

        # Minuteur à un coup, relancé à la fin de chaque image : si le dessin est
        # lent, la cadence baisse mais la fenêtre reste réactive (un minuteur
        # périodique empilerait les images et gèlerait la fenêtre sur macOS).
        self.timer = self.fig.canvas.new_timer(interval=DELAI_MS)
        self.timer.single_shot = True
        self.timer.add_callback(self._image)
        self._programmer_image()

    # --- Actions déclenchées par les contrôles ---------------------------------

    def charger(self, nom):
        """Crée le modèle `nom` avec ses valeurs par défaut (sert aussi de reset)."""
        self.nom = nom
        self.modele = self.MODELES[nom]()
        self.flux = self.modele.flux()
        t0, etat0 = next(self.flux)
        noms, fenetre = self.modele.noms, self.modele.FENETRE
        self.graphique = Graphique(self.ax_temps, noms, t0, etat0, fenetre)

        # Plan de phase seulement pour les modèles à deux populations
        deux_populations = len(noms) == 2
        self.ax_phase.set_visible(deux_populations)
        self.ax_temps.set_position(POSITION_TEMPS if deux_populations else POSITION_TEMPS_SEUL)
        self.plan = (
            PlanDePhase(self.ax_phase, noms, t0, etat0, fenetre) if deux_populations else None
        )
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
        self.modele.params[cle] = valeur

    def changer_vitesse(self, valeur):
        self.vitesse = valeur

    def basculer_pause(self):
        self._definir_pause(not self.en_pause)

    def _definir_pause(self, pause):
        self.en_pause = pause
        self.controles.afficher_pause(pause)
        if pause:
            self._annuler_image()
        else:
            self._derniere_image = None  # la durée de la pause ne compte pas
            self._programmer_image()
        self.fig.canvas.draw_idle()

    # --- Animation -------------------------------------------------------------

    def _programmer_image(self):
        """Prévoit la prochaine image, sauf en pause ou si elle est déjà prévue
        (relancer un minuteur actif en créerait un second sur macOS)."""
        if self.timer is not None and not self.en_pause and not self._image_prevue:
            self._image_prevue = True
            self.timer.start()

    def _annuler_image(self):
        if self.timer is not None:
            self.timer.stop()
        self._image_prevue = False

    def _image(self):
        """Une image : avance la simulation, dessine, puis prévoit la suivante."""
        self._image_prevue = False
        maintenant = time.perf_counter()
        if self._derniere_image is None:
            duree = 1 / IMAGES_PAR_SECONDE
        else:
            duree = min(maintenant - self._derniere_image, DUREE_IMAGE_MAX)
        self._derniere_image = maintenant
        self._avancer(duree)
        self._dessiner_graphiques()  # synchrone : l'image est finie au retour
        self._programmer_image()

    def _zone(self):
        """Zone des graphiques, en pixels."""
        return Bbox(ZONE_GRAPHIQUES).transformed(self.fig.transFigure)

    def _apres_dessin_complet(self, _event):
        """Après un dessin complet (démarrage, curseur, bouton, redimensionnement…) :
        mémorise le fond de la zone des graphiques, puis dessine ces derniers.

        Lors d'un enregistrement (bouton Save), la figure est dessinée à une autre
        résolution : on y dessine les graphiques mais on garde le fond de l'écran.
        """
        if not self.fig.canvas.is_saving():
            self._fond = self.fig.canvas.copy_from_bbox(self._zone())
        self._dessiner_axes()

    def _dessiner_axes(self):
        for ax in (self.ax_temps, self.ax_phase):
            self.fig.draw_artist(ax)  # rien n'est dessiné si l'axe est masqué

    def _dessiner_graphiques(self):
        """Redessine seulement la zone des graphiques."""
        canvas = self.fig.canvas
        if self._fond is None:  # pas encore de dessin complet
            canvas.draw()  # appelle _apres_dessin_complet
            return
        canvas.restore_region(self._fond)
        self._dessiner_axes()
        canvas.blit(self._zone())

    def _avancer(self, duree):
        """Avance de `vitesse × IMAGES_PAR_SECONDE` pas par seconde réelle écoulée
        (`duree`), en cumulant les fractions de pas : la vitesse ne dépend donc
        pas de la cadence d'affichage.

        Ex. à 60 images/s : vitesse 0.25 → un pas toutes les 4 images ;
        vitesse 2.5 → 2 ou 3 pas par image.
        """
        self._pas_en_attente += self.vitesse * duree * IMAGES_PAR_SECONDE
        nb_pas = int(self._pas_en_attente)
        self._pas_en_attente -= nb_pas
        for _ in range(nb_pas):
            t, etat = next(self.flux)
            # Valeur non finie ou trop grande : le graphique ne peut plus suivre
            if not np.all(np.isfinite(etat)) or np.max(etat) > POPULATION_MAX:
                self._definir_pause(True)
                break
            self.graphique.ajouter(t, etat)
            if self.plan is not None:
                self.plan.ajouter(t, etat, self.modele.equilibre())


if __name__ == "__main__":
    Application()
    plt.show()
