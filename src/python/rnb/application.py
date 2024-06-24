import pygame
from .core import (
    Int2D,
    get_or
)


class LayerControl:
    def __init__(self, target_screen):
        self.target_screen = target_screen

        self.background = pygame.sprite.Group()
        self.general = pygame.sprite.Group()
        self.foreground = pygame.sprite.Group()

    def blit_ordered(self):
        # pre layer
        for sprite in self.background:
            self.target_screen.blit(sprite.surf, sprite.rect)
        # main layer
        for sprite in self.general:
            self.target_screen.blit(sprite.surf, sprite.rect)
        # post layer
        for sprite in self.foreground:
            self.target_screen.blit(sprite.surf, sprite.rect)


class LifeCycle:
    def __init__(self, layers: LayerControl, **props):
        self.fps = get_or(props, 'fps', 60)
        self.alive = True

        self.lc = layers
        self.clock = pygame.time.Clock()

    def __cycle_once(self):
        for event in pygame.event.get():
            # end event
            if event.type == pygame.QUIT:
                self.alive = False

        self.lc.blit_ordered()
        pygame.display.flip()
        self.clock.tick(self.fps)

    def start(self):
        while self.alive:
            self.__cycle_once()


class MainApplication:
    def __init__(self, window_rect: Int2D = None):
        # init
        self.pygame_init()

        # screen preparation
        if window_rect:
            self.screen = pygame.display.set_mode(window_rect)
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        # layer init
        self.layers = LayerControl(self.screen)
        self.life_cycle = LifeCycle(self.layers)

    def start(self):
        self.life_cycle.start()

    def pygame_init(self):
        pygame.init()

    def pygame_quit(self):
        pygame.quit()