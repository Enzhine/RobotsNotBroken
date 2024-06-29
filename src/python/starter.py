from rnb.application import MainApplication
from rnb.world import DefaultWorldGenerator


def main():
    wg = DefaultWorldGenerator(5, 6, 12, 5, seed=1243)
    app = MainApplication(world_gen=wg)
    app.process.rescaler.force_scale(3)
    app.start()


if __name__ == '__main__':
    main()
