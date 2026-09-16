from abc import ABC, abstractmethod

from abc import ABC, abstractmethod


class Modele(ABC):

    POPULATION_INIT = 10

    def __init__(self, ax, line):
        self.ax = ax
        self.line = line
        self.xdata = []
        self.ydata = []

    @abstractmethod
    def generation(self, *args):
        """Calcule l'etat suivant a partir de l'etat courant."""

    def init(self):
        self.ax.set_ylim(self.POPULATION_INIT, self.POPULATION_INIT * 2)
        self.ax.set_xlim(0, 1)
        self.xdata.clear()
        self.xdata.append(0)
        self.ydata.clear()
        self.ydata.append(self.POPULATION_INIT)
        self.line.set_data(self.xdata, self.ydata)
        return self.line

    def run(self, data):
        t, y = data
        self.xdata.append(t)
        self.ydata.append(y)

        xmin, xmax = self.ax.get_xlim()
        if t >= xmax:
            self.ax.set_xlim(xmin, self.xdata[-1])
            self.ax.figure.canvas.draw()

        ymin, ymax = self.ax.get_ylim()
        if y >= ymax:
            self.ax.set_ylim(ymin, self.ydata[-1])
            self.ax.figure.canvas.draw()

        self.line.set_data(self.xdata, self.ydata)
        return self.line


class Malthus(Modele):

    def generation(self, population, growth):
        return population * growth

def verhulst(population, growth, environnementCapacity):
    return population + population*growth*(1-population/environnementCapacity)
    
def volterra(populationPrey, populationPredator,growthPrey,growthPredator,chanceInteractionPrey,chanceInteractionPredtor):
    preyEvolution = growthPrey*populationPrey - chanceInteractionPrey*populationPrey*populationPredator
    predatorEvolution = -growthPredator*populationPredator + chanceInteractionPredtor*populationPrey*populationPredator