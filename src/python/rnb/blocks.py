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

    def __repr__(self):
        return self.__class__.__name__


class AnimatedBlock(DefaultRendering, WorldPlaced):
    def __init__(self, tile_name: str):
        DefaultRendering.__init__(self, tile_name)
        WorldPlaced.__init__(self, 0, 0, 0)

    def __repr__(self):
        return self.__class__.__name__


class SubRendering:
    def __init__(self):
        self._sub_renders = pygame.sprite.Group()

    def sub_renders(self) -> list[Rendering]:
        return self._sub_renders


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


class PowerStationMultiblock(Rendering, MultiBlock, WorldPlaced, SubRendering):
    def __init__(self):
        Rendering.__init__(self, "power_station.json")
        WorldPlaced.__init__(self, 0, 0, 0)
        MultiBlock.__init__(self, [(0, 0), (1, 0), (0, 1), (1, 1)])
        SubRendering.__init__(self)

        x, y = self._rect.size
        self._rect.move_ip(0, -(y * 1 // 2))

        self.state_open = False
        self.__state_open_render: DefaultRendering | None = None

    def __repr__(self):
        return f'{self.__class__.__name__};{self.state_open=}'

    def _apply_state(self, state: Rendering):
        _surf, _area = state.current_frame()
        self.surface().blit(_surf, dest=self._rect_delta(state), area=_area)

    def set_open(self):
        if not self.state_open:
            if self.__state_open_render:
                self.__state_open_render.kill()
            self.__state_open_render = DefaultRendering('power_station_door_open.json')
            self.__state_open_render.bounds().move_ip(self.__state_open_render._rect_delta(self, (0, self.bounds().h // 2)))
            self.__state_open_render.tint_by(self.tint())

            self.sub_renders().add(self.__state_open_render)
            self.state_open = True

    def set_closed(self):
        if self.state_open:
            if self.__state_open_render:
                self.__state_open_render.kill()
            self.__state_open_render = DefaultRendering('power_station_door_close.json')
            self.__state_open_render.bounds().move_ip(self.__state_open_render._rect_delta(self, (0, self.bounds().h // 2)))
            self.__state_open_render.tint_by(self.tint())

            self.sub_renders().add(self.__state_open_render)
            self.state_open = False

    def current_frame(self) -> tuple[pygame.Surface, pygame.Rect]:
        return self._surf, self._surf.get_rect()

    def tick(self, ms: float):
        if self.__state_open_render:
            if self.__state_open_render.is_ended():
                self._apply_state(self.__state_open_render)
                self.__state_open_render.kill()
                self.__state_open_render = None
            else:
                self.__state_open_render.tick(ms)


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
