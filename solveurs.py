import numpy as np


def _grille(y0, tmax, h):
    """Alloue les temps t et le tableau y (avec y[0] = y0)."""
    n = int(round(tmax / h))
    t = h * np.arange(n + 1)
    y = np.empty((n + 1,) + np.shape(y0))
    y[0] = y0
    return t, y


def euler(f, y0, tmax, h):
    """Résout y' = f(t, y) par la méthode d'Euler. Renvoie (t, y)."""
    t, y = _grille(y0, tmax, h)
    n = len(t) - 1
    for k in range(n):
        y[k + 1] = y[k] + h * f(t[k], y[k])
    return t, y


def runge_kutta(f, y0, tmax, h):
    """Résout y' = f(t, y) par la méthode RK4. Renvoie (t, y)."""
    t, y = _grille(y0, tmax, h)
    n = len(t) - 1
    for k in range(n):
        k1 = f(t[k], y[k])
        k2 = f(t[k] + h / 2, y[k] + h / 2 * k1)
        k3 = f(t[k] + h / 2, y[k] + h / 2 * k2)
        k4 = f(t[k] + h, y[k] + h * k3)
        y[k + 1] = y[k] + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return t, y
