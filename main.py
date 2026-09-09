import itertools

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import numpy as np

from modeles import *

croissance = 0.001

POPULATION_INIT = 1

def data_gen():
    for cnt in itertools.count():
        t = cnt / 10
        yield t, malthus(xdata[-1], croissance)

def init():
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlim(0, 1)
    del xdata[:]
    xdata.append(POPULATION_INIT)
    del ydata[:]
    ydata.append(0)
    line.set_data(xdata, ydata)
    return line,

fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.grid()
xdata, ydata = [], []


def run(data):
    # update the data
    t, y = data
    xdata.append(t)
    ydata.append(y)
    xmin, xmax = ax.get_xlim()

    if t >= xmax:
        ax.set_xlim(xmin, 2*xmax)
        ax.figure.canvas.draw()
    line.set_data(xdata, ydata)

    return line,

# Only save last 100 frames, but run forever
ani = animation.FuncAnimation(fig, run, data_gen, interval=100, init_func=init,
                              save_count=100)
plt.show()