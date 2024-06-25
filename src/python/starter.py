import pygame
import random
from rnb.application import MainApplication
from rnb.sprites import DirtBlock, StoneBlock


def main():
    app = MainApplication()
    for x in range(0, 10):
        for y in range(0, 10):
            clazz = DirtBlock if random.random() < 0.5 else StoneBlock
            app.process.map_ctrl.set(clazz, pos=(x, y))
    app.start()


if __name__ == '__main__':
    main()
