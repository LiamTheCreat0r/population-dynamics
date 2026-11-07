import numpy as np
import pytest

from modeles import Malthus, Verhulst, Volterra
from solveurs import euler, runge_kutta

R, N0, TMAX = 1.0, 10.0, 2.0


def erreur_malthus(solveur, h):
    """Erreur max |N_k - N(t_k)| sur Malthus (solution exacte N0·e^(rt))."""
    t, y = solveur(lambda t, y: R * y, np.array([N0]), TMAX, h)
    return np.max(np.abs(y[:, 0] - N0 * np.exp(R * t)))


@pytest.mark.parametrize("solveur", [euler, runge_kutta])
def test_malthus_proche_solution_exacte(solveur):
    assert erreur_malthus(solveur, 0.001) < 0.1


@pytest.mark.parametrize(
    "solveur, ratio", [(euler, 2), (runge_kutta, 16)]
)
def test_ordre_de_convergence(solveur, ratio):
    """Diviser h par 2 divise l'erreur par ~2 (Euler) ou ~16 (RK4)."""
    mesure = erreur_malthus(solveur, 0.02) / erreur_malthus(solveur, 0.01)
    assert mesure == pytest.approx(ratio, rel=0.15)


def test_rk4_plus_precis_qu_euler():
    assert erreur_malthus(runge_kutta, 0.1) < erreur_malthus(euler, 0.1)


@pytest.mark.parametrize("solveur", [euler, runge_kutta])
def test_systeme_vectoriel_oscillateur(solveur):
    """x'' = -x : (x, v) = (cos t, -sin t)."""
    f = lambda t, y: np.array([y[1], -y[0]])
    t, y = solveur(f, np.array([1.0, 0.0]), 1.0, 0.001)
    assert y[-1] == pytest.approx([np.cos(1.0), -np.sin(1.0)], abs=2e-3)


def test_equilibre_verhulst():
    m = Verhulst()
    assert m.derivee(0, np.array([0.0]))[0] == 0
    assert m.derivee(0, np.array([m.params["capacite"]]))[0] == pytest.approx(0)


def test_equilibre_volterra():
    m = Volterra()
    p = m.params
    eq = np.array([p["mortalite_predateurs"] / p["conversion"],
                   p["croissance_proies"] / p["predation"]])
    assert m.derivee(0, eq) == pytest.approx([0, 0])
    assert m.derivee(0, np.zeros(2)) == pytest.approx([0, 0])


def test_peche_equilibre_decale():
    """Avec pêche, l'équilibre est ((c+q)/d, (a-q)/b)."""
    m = Volterra()
    m.peche = True
    p = m.params
    q = p["effort_peche"]
    eq = np.array([(p["mortalite_predateurs"] + q) / p["conversion"],
                   (p["croissance_proies"] - q) / p["predation"]])
    assert m.derivee(0, eq) == pytest.approx([0, 0])


def test_peche_coupee_sans_effet():
    m = Volterra()
    y = np.array([10.0, 5.0])
    sans = m.derivee(0, y)
    m.peche = True
    assert not np.allclose(sans, m.derivee(0, y))


def test_modele_generique_flux():
    """Le flux avance de dt à chaque pas, quel que soit le modèle."""
    flux = Malthus().flux()
    t0, _ = next(flux)
    t1, _ = next(flux)
    assert t1 - t0 == pytest.approx(Malthus.DT)
