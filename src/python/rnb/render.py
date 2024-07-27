import json
from abc import ABC, abstractmethod
from typing import Generator

import pygame

from .core import SOURCES_DIR, Int2D, Int2DZero

_SPRITES_DIR = SOURCES_DIR / "sprite"
_TILES_DIR = SOURCES_DIR / "tile"


class Rendering(pygame.sprite.Sprite, ABC):
    TILE_EXT = 'json'
    SPRITE_EXT = 'png'

    __SURFACES: dict[str, pygame.surface.Surface] = dict()
    __TILES: dict[str, dict] = dict()

    __KEY_SPRITE = 'sprite'
    __KEY_TYPE = 'type'
    __KEY_DETAILS = 'details'
    __KEY_D_DIRECTION = 'direction'
    __KEY_D_FRAME = 'frame'

    DIRECTION_HORIZONTAL = 'horizontal'
    DIRECTION_VERTICAL = 'vertical'
    TYPE_DUMMY = 'dummy'
    TYPE_DEFAULT = 'default'

    DEFAULT_FRAME: Int2D = (16, 16)
    DEFAULT_DIRECTION: str = DIRECTION_HORIZONTAL

    @staticmethod
    def __dummy_of(tile_name: str):
        return {
            "sprite": f'{tile_name}.{Rendering.SPRITE_EXT}',
            "type": Rendering.TYPE_DUMMY
        }

    @staticmethod
    def load_sprite(sprite_name: str) -> pygame.surface.Surface:
        if sprite_name in Rendering.__SURFACES:
            return Rendering.__SURFACES[sprite_name]
        source_path = (_SPRITES_DIR / sprite_name).resolve()
        surf = pygame.image.load(source_path).convert_alpha()
        # surf.set_colorkey((255, 255, 255), RLEACCEL)
        Rendering.__SURFACES[sprite_name] = surf
        return surf

    @staticmethod
    def load_tile(json_name: str) -> dict:
        if json_name in Rendering.__TILES:
            return Rendering.__TILES[json_name]
        source_path = (_TILES_DIR / json_name).resolve()
        try:
            with open(source_path, mode='r') as f:
                _json = json.load(f)
        except FileNotFoundError:
            _json = Rendering.__dummy_of(source_path.stem)
        Rendering.__TILES[json_name] = _json
        return _json

    def __init__(self, tile_name: str):
        pygame.sprite.Sprite.__init__(self)
        _json = Rendering.load_tile(tile_name)
        sprite_name = _json[Rendering.__KEY_SPRITE]
        surf = Rendering.load_sprite(sprite_name)

        self.visible = True

        self.__origin: pygame.Surface = surf
        self._surf: pygame.Surface = self.__origin.copy()
        self._rect: pygame.Rect = self._surf.get_rect()
        self._type: str = _json[Rendering.__KEY_TYPE]
        self._details = _json.get(Rendering.__KEY_DETAILS, dict())
        if self._type == Rendering.TYPE_DUMMY:
            return
        self._frame_direction: str = self._details.get(Rendering.__KEY_D_DIRECTION, Rendering.DEFAULT_DIRECTION)
        assert self._frame_direction in [Rendering.DIRECTION_HORIZONTAL,Rendering.DIRECTION_VERTICAL]
        arr = self._details.get(Rendering.__KEY_D_FRAME, Rendering.DEFAULT_FRAME)
        self._frame_size: Int2D = (int(arr[0]), int(arr[1]))

        self.__tint: int = 255

    def sub_renders(self) -> Generator['Rendering', None, None]:
        return
        yield

    def surface(self):
        return self._surf

    def bounds(self):
        return self._rect

    def _origin(self):
        return self.__origin

    def tint(self) -> int:
        return self.__tint

    def tint_by(self, _col: int):
        self.__tint = _col
        new = self.__origin.copy()
        new.fill((_col, _col, _col), special_flags=pygame.BLEND_MULT)
        self._surf = new

    @abstractmethod
    def current_frame(self) -> tuple[pygame.Surface, pygame.Rect]:
        raise NotImplementedError

    @abstractmethod
    def tick(self, ms: float):
        raise NotImplementedError


class StaticRendering(Rendering):
    def __init__(self, tile_name: str):
        Rendering.__init__(self, tile_name)
        w, h = self._surf.get_size()
        self.__static = pygame.Rect(Int2DZero, (w, h))
        assert self._type == Rendering.TYPE_DUMMY

    def current_frame(self) -> tuple[pygame.Surface, pygame.Rect]:
        return self._surf, self.__static

    def tick(self, ms: float):
        pass


class DefaultRendering(Rendering):
    __KEY_D_ORDER = 'order'
    __KEY_D_DURATION = 'duration'
    __KEY_D_LOOP = 'loop'

    ORDER_INWARDS = 'inwards'
    ORDER_BACKWARDS = 'backwards'
    LOOP_NONE = None
    LOOP_CYCLING = 'cycling'
    LOOP_FLIPPING = 'flipping'

    DEFAULT_DURATION: int = 2
    DEFAULT_ORDER: str = ORDER_INWARDS
    DEFAULT_LOOP: str = LOOP_NONE

    def __init__(self, tile_name: str):
        Rendering.__init__(self, tile_name)
        assert self._type == Rendering.TYPE_DEFAULT
        self._duration = float(self._details.get(DefaultRendering.__KEY_D_DURATION, DefaultRendering.DEFAULT_DURATION))
        self._order = self._details.get(DefaultRendering.__KEY_D_ORDER, DefaultRendering.DEFAULT_ORDER)
        assert self._order in [DefaultRendering.ORDER_INWARDS, DefaultRendering.ORDER_BACKWARDS]
        self._loop = self._details.get(DefaultRendering.__KEY_D_LOOP, DefaultRendering.DEFAULT_LOOP)
        assert (self._loop is None) or (self._loop in [DefaultRendering.LOOP_NONE, DefaultRendering.LOOP_CYCLING, DefaultRendering.LOOP_FLIPPING])

        self.__alive = True
        self.__ending = self._loop is None
        self.__cycling = self._loop == DefaultRendering.LOOP_CYCLING

        if self._frame_direction == Rendering.DIRECTION_HORIZONTAL:
            self.__frames_steps = self._rect.w // self._frame_size[0]
            self.__range_x = [x for x in range(0, self._rect.w, self._frame_size[0])]
            self.__range_y = [0 for _ in range(self.__frames_steps)]
        elif self._frame_direction == Rendering.DIRECTION_VERTICAL:
            self.__frames_steps = self._rect.h // self._frame_size[1]
            self.__range_x = [0 for _ in range(self.__frames_steps)]
            self.__range_y = [y for y in range(0, self._rect.h, self._frame_size[1])]

        self.__frames_ms: float = self._duration * 1_000 / self.__frames_steps
        self.__frames_lms = 0.0

        if self._order == DefaultRendering.ORDER_INWARDS:
            self.__frames_c = 0
            self.__frames_inwards = True
        elif self._order == DefaultRendering.ORDER_BACKWARDS:
            self.__frames_c = self.__frames_steps - 1
            self.__frames_inwards = False
        assert self.__frames_steps > 1

    def is_ended(self):
        return not self.__alive

    def __update_frames(self):
        if self.__frames_inwards:
            self.__frames_c += 1
            if self.__frames_c == self.__frames_steps:
                if self.__ending:
                    self.__alive = False
                    self.__frames_c = self.__frames_steps - 1
                elif self.__cycling:
                    self.__frames_c = 0
                else:
                    self.__frames_inwards = False
                    self.__frames_c = self.__frames_steps - 2
        else:
            self.__frames_c -= 1
            if self.__frames_c == -1:
                if self.__ending:
                    self.__alive = False
                    self.__frames_c = 0
                elif self.__cycling:
                    self.__frames_c = self.__frames_steps - 1
                else:
                    self.__frames_inwards = True
                    self.__frames_c = 1

    def tick(self, ms: float):
        if not self.__alive:
            return
        self.__frames_lms += ms
        if self.__frames_lms >= self.__frames_ms:
            self.__frames_lms = 0.0
            self.__update_frames()

    def current_frame(self) -> tuple[pygame.Surface, pygame.Rect]:
        return self._surf, pygame.Rect(self.__range_x[self.__frames_c], self.__range_y[self.__frames_c],
                                       self._frame_size[0], self._frame_size[1])
