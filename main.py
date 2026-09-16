import itertools

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from modeles import Malthus

growth = 1.05

fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.grid()

modele = Malthus(ax, line)

def data_gen():
    for cnt in itertools.count():
        t = cnt / 10
        yield t, modele.generation(modele.ydata[-1], growth)

ani = animation.FuncAnimation(fig, modele.run, data_gen, interval=100,
                              init_func=modele.init, save_count=100)
plt.show()