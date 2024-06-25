import pygame
from pygame.locals import RLEACCEL
from .core import SOURCES_DIR

_SPRITES_DIR = SOURCES_DIR / "sprite"


class BasicSpriteBlock(pygame.sprite.Sprite):
    def __init__(self, sprite_name: str):
        super(BasicSpriteBlock, self).__init__()
        self.source_path = (_SPRITES_DIR / sprite_name).resolve()
        self.surf = pygame.image.load(self.source_path).convert()
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.rect = self.surf.get_rect()


class DirtBlock(BasicSpriteBlock):
    def __init__(self):
        super(DirtBlock, self).__init__("dirt_block.png")


class StoneBlock(BasicSpriteBlock):
    def __init__(self):
        super(StoneBlock, self).__init__("stone_block.png")
