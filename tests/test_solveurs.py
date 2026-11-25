import numpy as np
import pytest

from modeles import HollingTanner, Malthus, Verhulst, Volterra
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


def test_equilibre_volterra_methode():
    m = Volterra()
    p = m.params
    attendu = [p["mortalite_predateurs"] / p["conversion"],
               p["croissance_proies"] / p["predation"]]
    assert m.equilibre() == pytest.approx(attendu)


@pytest.mark.parametrize("peche", [False, True])
def test_equilibre_holling_tanner(peche):
    m = HollingTanner()
    m.peche = peche
    eq = m.equilibre()
    assert eq is not None and min(eq) > 0
    assert m.derivee(0, eq) == pytest.approx([0, 0], abs=1e-9)


def test_holling_tanner_sans_predateurs_tend_vers_capacite():
    """Sans prédateurs, les proies suivent Verhulst : (K, 0) est un équilibre."""
    m = HollingTanner()
    assert m.derivee(0, np.array([m.params["capacite"], 0.0])) == pytest.approx([0, 0])


def amplitude_proies(modele, etat0, tmax=300.0, t_regime=200.0):
    """(min, max) des proies une fois le régime permanent atteint."""
    t, y = runge_kutta(modele.derivee, np.array(etat0), tmax, 0.05)
    proies = y[t > t_regime, 0]
    return proies.min(), proies.max()


def test_cycle_limite_holling_tanner():
    """Deux départs différents mènent à la même oscillation (cycle limite)."""
    m = HollingTanner()
    a = amplitude_proies(m, [10.0, 5.0])
    b = amplitude_proies(m, [80.0, 40.0])
    assert a == pytest.approx(b, abs=1.0)
    assert a[1] - a[0] > 10  # il oscille vraiment


def test_holling_tanner_equilibre_stable_si_s_grand():
    """Au-delà de la bifurcation de Hopf (s ≈ 0.3), les oscillations s'éteignent."""
    m = HollingTanner(croissance_predateurs=0.5)
    bas, haut = amplitude_proies(m, [10.0, 5.0])
    assert haut - bas < 0.1
    assert haut == pytest.approx(m.equilibre()[0], abs=0.1)


def test_volterra_cycles_dependent_du_depart():
    """Contraste : chez Volterra, l'amplitude dépend de la condition initiale."""
    m = Volterra()
    a = amplitude_proies(m, [10.0, 5.0], tmax=30.0, t_regime=10.0)
    b = amplitude_proies(m, [15.0, 8.0], tmax=30.0, t_regime=10.0)
    assert abs((a[1] - a[0]) - (b[1] - b[0])) > 5


def test_holling_tanner_reste_fini_et_positif():
    """Réglage où les proies frôlent 0 : sans sous-pas, RK4 divergeait (NaN)."""
    m = HollingTanner(
        croissance_proies=1.65, capacite=349.0, predation_max=1.17,
        demi_saturation=2.69, croissance_predateurs=0.34,
        proies_par_predateur=0.16, effort_peche=0.5,
    )
    flux = m.flux()
    for _ in range(6000):
        _, etat = next(flux)
        assert np.all(np.isfinite(etat)) and np.min(etat) >= 0


def test_pas_inchange_en_regime_normal():
    """Sans difficulté numérique, pas() fait un seul pas RK4 de durée dt."""
    m = Volterra()
    y0 = m.etat_initial()
    _, attendu = runge_kutta(m.derivee, y0, m.dt, m.dt)
    assert np.array_equal(m.pas(y0), attendu[-1])
