from abc import ABC

import pygame
from .core import (
    SOURCES_DIR,
    Int2D,
    Int2DZero
)
from .render import Rendering, StaticRendering, DefaultRendering

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

    def world_pos(self) -> Int2D:
        return self.__x, self.__y

    def assign(self, x=None, y=None, z=None):
        if x:
            self.__x = x
        if y:
            self.__y = y
        if z:
            self.__z = z


class MultiBlock:
    @staticmethod
    def structure(obj: Rendering) -> list[Int2D]:
        if isinstance(obj, MultiBlock):
            return obj.__structure
        return [Int2DZero]

    def __init__(self, structure: list[Int2D]):
        self.__structure = structure


class StaticBlock(StaticRendering, WorldPlaced):
    def __init__(self, tile_name: str):
        StaticRendering.__init__(self, tile_name)
        WorldPlaced.__init__(self, 0, 0, 0)


class AnimatedBlock(DefaultRendering, WorldPlaced):
    def __init__(self, tile_name: str):
        DefaultRendering.__init__(self, tile_name)
        WorldPlaced.__init__(self, 0, 0, 0)


class CursorBlock(StaticBlock):
    def __init__(self):
        StaticBlock.__init__(self, 'cursor.json')


class DirtBlock(StaticBlock):
    def __init__(self):
        StaticBlock.__init__(self, "dirt_block.json")


class StoneBlock(StaticBlock):
    def __init__(self):
        StaticBlock.__init__(self, "stone_block.json")


class BgBigBlock(StaticBlock):
    def __init__(self):
        StaticBlock.__init__(self, "bg_bigblock.json")
        x, y = self._rect.size
        self._rect.move_ip(0, -(y * 3 // 4))


class PowerStageMultiblock(AnimatedBlock, MultiBlock):
    def __init__(self):
        # TODO: REPLACE TO EXISTING
        AnimatedBlock.__init__(self, "power_station.json")
        MultiBlock.__init__(self, [(0, 0), (1, 0), (0, 1), (1, 1)])
        x, y = self._rect.size
        self._rect.move_ip(0, -(y * 1 // 2))


class RobotEntity(StaticBlock):
    def __init__(self):
        StaticBlock.__init__(self, "prog_robot.json")


class BasicSpriteGui(pygame.sprite.Sprite):
    def __init__(self, sprite_name: str, pos: Int2D, group: pygame.sprite.Group):
        pygame.sprite.Sprite.__init__(self)
        self.origin_surf = Rendering.load_sprite(sprite_name)
        self.surf = self.origin_surf.copy()
        self.rect = self.surf.get_rect()
        self.rect.move_ip(*pos)
        group.add(self)
