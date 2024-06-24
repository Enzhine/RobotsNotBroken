from rnb.application import MainApplication
from rnb.sprites import DirtBlock


def main():
    res = (600, 500)
    app = MainApplication(res)
    app.layers.background.add(DirtBlock())
    app.start()


if __name__ == '__main__':
    main()
