import matplotlib.pyplot as plt
import matplotlib.animation as animation

from modeles import *

# modele = Malthus(1.01)

modele = Verhulst(1.2, 1000)

# modele = Volterra(
#     1.0,
#     1.5,
#     0.1,
#     0.075,
# )

ani = animation.FuncAnimation(
    modele.fig,
    modele.run,
    modele.data_gen,
    interval=10,
    init_func=modele.init,
    save_count=100,
)

plt.show()
