import pygame
from pygame.locals import RLEACCEL
from .core import (
    SOURCES_DIR,
    Int2D,
    Int2DZero,
    Color, ColorBlack, ColorWhite
)

_SPRITES_DIR = SOURCES_DIR / "sprite"


class WorldPlaced:
    def __init__(self, x, y, layer):
        self.__x = x
        self.__y = y
        self.__z = layer

    def x(self):
        return self.__x

    def y(self):
        return self.__y

    def z(self):
        return self.__z

    def world_pos(self):
        return self.__x, self.__y

    def assign(self, x=None, y=None, z=None):
        if x:
            self.__x = x
        if y:
            self.__y = y
        if z:
            self.__z = z


class BasicSpriteBlock(pygame.sprite.Sprite, WorldPlaced):
    __SURFACES: dict[str, pygame.surface.Surface] = dict()

    @staticmethod
    def load_source(sprite_name: str) -> pygame.surface.Surface:
        if sprite_name in BasicSpriteBlock.__SURFACES:
            return BasicSpriteBlock.__SURFACES[sprite_name]
        source_path = (_SPRITES_DIR / sprite_name).resolve()
        surf = pygame.image.load(source_path).convert_alpha()
        #surf.set_colorkey((255, 255, 255), RLEACCEL)
        BasicSpriteBlock.__SURFACES[sprite_name] = surf
        return surf

    def __init__(self, sprite_name: str):
        pygame.sprite.Sprite.__init__(self)
        WorldPlaced.__init__(self, 0, 0, 0)
        self.origin_surf = BasicSpriteBlock.load_source(sprite_name)
        self.surf = self.origin_surf.copy()
        self.rect = self.surf.get_rect()
        self.tint_col = ColorWhite

        self.visible = True

    def is_tint_visible(self):
        return self.tint_col != ColorBlack

    def tint(self, color: Color):
        self.tint_col = color
        self.surf = self.origin_surf.copy()
        self.surf.fill(color, special_flags=pygame.BLEND_MULT)


class CursorBlock(pygame.sprite.Sprite, WorldPlaced):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        WorldPlaced.__init__(self, 0, 0, 0)
        self.origin_surf = BasicSpriteBlock.load_source('cursor.png')
        self.surf = self.origin_surf.copy()
        self.rect = self.surf.get_rect()


class MultiBlock:
    @staticmethod
    def structure(obj: BasicSpriteBlock) -> list[Int2D]:
        if isinstance(obj, MultiBlock):
            return obj.__structure
        return [Int2DZero]

    def __init__(self, structure: list[Int2D]):
        self.__structure = structure


class DirtBlock(BasicSpriteBlock):
    def __init__(self):
        super(DirtBlock, self).__init__("dirt_block.png")


class StoneBlock(BasicSpriteBlock):
    def __init__(self):
        super(StoneBlock, self).__init__("stone_block.png")


class BgBigBlock(BasicSpriteBlock):
    def __init__(self):
        super(BgBigBlock, self).__init__("bg_bigblock.png")
        x, y = self.rect.size
        self.rect.move_ip(0, -(y * 3 // 4))


class PowerStageMultiblock(BasicSpriteBlock, MultiBlock):
    def __init__(self):
        super(PowerStageMultiblock, self).__init__("powerstage_multiblock.png")
        MultiBlock.__init__(self, [(0, 0), (1, 0), (0, 1), (1, 1)])
        x, y = self.rect.size
        self.rect.move_ip(0, -(y * 2 // 4))


class RobotEntity(BasicSpriteBlock):
    def __init__(self):
        super(RobotEntity, self).__init__("prog_robot.png")
