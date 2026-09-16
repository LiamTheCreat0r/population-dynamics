import itertools

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import numpy as np

from modeles import *

croissance = 0.1

POPULATION_INIT = 1000

def data_gen():
    for cnt in itertools.count():
        t = cnt / 10
        yield t, malthus(ydata[-1], croissance)  # last population, from ydata

def init():
    ax.set_ylim(POPULATION_INIT, POPULATION_INIT * 2)
    ax.set_xlim(0, 1)
    del xdata[:]
    xdata.append(0)              # x = time, starts at 0
    del ydata[:]
    ydata.append(POPULATION_INIT)  # y = population, starts at POPULATION_INIT
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
    ymin, ymax = ax.get_ylim()

    if t >= xmax:
        ax.set_xlim(xmin, xdata[-1])
        ax.figure.canvas.draw()
    if ydata[-1] >= ymax:
        ax.set_ylim(POPULATION_INIT, ydata[-1])
        ax.figure.canvas.draw()

    line.set_data(xdata, ydata)

    return line,

# Only save last 100 frames, but run forever
ani = animation.FuncAnimation(fig, run, data_gen, interval=100, init_func=init,
                              save_count=100)
plt.show()