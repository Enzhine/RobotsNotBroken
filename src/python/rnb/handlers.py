from abc import ABC, abstractmethod

import pygame

from .core import Int2D, Int2DZero, sum2dref, sub2d, sum2d, enum
from .context import MultiContextListener, GuiContext, EventHandler, WrappedContext
from math import log, floor, ceil

from .sprites import BasicSpriteGui


class GuiContextListener(MultiContextListener, EventHandler):
    def __init__(self):
        super().__init__()
        self.__prev: Int2D = Int2DZero

    def on_event(self, event: pygame.event.Event):
        if not self.is_listening():
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if TranslateInputHandler.is_lmb(event):
                _type = GuiContext.TYPE_LMB
            else:
                _type = GuiContext.TYPE_RMB
            for context in self.current_layer():
                if isinstance(context, GuiContext):
                    if context.bounds().collidepoint(event.pos):
                        context.notify(event.pos, _type)
                else:
                    context: WrappedContext
                    context.notify(event)
        elif event.type == pygame.MOUSEMOTION:
            for context in self.current_layer():
                if isinstance(context, GuiContext):
                    before = context.bounds().collidepoint(self.__prev)
                    now = context.bounds().collidepoint(event.pos)
                    if not before and now:
                        context.notify(event.pos, GuiContext.TYPE_H_ENTER)
                    elif before and not now:
                        context.notify(event.pos, GuiContext.TYPE_H_EXIT)
                else:
                    context: WrappedContext
                    context.notify(event)
            self.__prev = event.pos
        else:
            for context in self.current_layer():
                if not isinstance(context, GuiContext):
                    context: WrappedContext
                    context.notify(event)


class EventContext(WrappedContext, ABC):
    def is_primary(self) -> bool:
        return False

    @abstractmethod
    def notify(self, event: pygame.event.Event):
        raise NotImplementedError


class RescaleInputHandler(EventContext):
    def __init__(self, k=1.1, max_k=4):
        self.scale = 1
        self.__steps = 0
        self.__k = k
        self.__max_k = floor(log(max_k, k))

    def __update_scale(self):
        self.scale = 1.1 ** self.__steps

    def force_scale(self, scale: float):
        self.__steps = floor(log(scale, self.__k))
        self.__update_scale()

    @staticmethod
    def __is_vertical(event: pygame.event.Event):
        return event.y > 0

    def notify(self, event: pygame.event.Event):
        if event.type != pygame.MOUSEWHEEL:
            return
        # input
        if RescaleInputHandler.__is_vertical(event):
            self.__steps += 1
        else:
            self.__steps -= 1
        # validate
        if self.__steps < 0:
            self.__steps = 0
        elif self.__steps > self.__max_k:
            self.__steps = self.__max_k
        # rescale
        self.__update_scale()


class TranslateInputHandler(EventContext):
    def __init__(self, rescaler: RescaleInputHandler, screen_size: Int2D):
        self.__rescaler = rescaler
        self.__prev = None
        self.__sizes = screen_size
        self.__delta = [0, 0]

        self.__last = Int2DZero

    def last_pos(self):
        return self.__last

    def delta(self) -> Int2D:
        return tuple(self.__delta)

    def __map_scaled(self, pos: Int2D) -> Int2D:
        k = self.__rescaler.scale
        x, y = pos
        w, h = self.__sizes
        sx, sy = ceil(w / 2 - w / k / 2 + x / k), ceil(h / 2 - h / k / 2 + y / k)
        return sx, sy

    def map_scaled(self, pos: Int2D) -> Int2D:
        k = self.__rescaler.scale
        x, y = pos
        w, h = self.__sizes
        dx, dy = self.__delta[0], self.__delta[1]
        sx, sy = ceil(w / 2 - w / k / 2 + x / k - dx), ceil(h / 2 - h / k / 2 + y / k - dy)
        return sx, sy

    @staticmethod
    def is_lmb(event: pygame.event.Event):
        return event.button == 1

    @staticmethod
    def is_rmb(event: pygame.event.Event):
        return event.button == 3

    def notify(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and TranslateInputHandler.is_rmb(event):
            self.__prev = self.__map_scaled(event.pos)
            return
        elif event.type == pygame.MOUSEBUTTONUP:
            self.__prev = None
            return
        elif event.type == pygame.MOUSEMOTION:
            l_pos = self.__map_scaled(event.pos)
            self.__last = l_pos
            if not self.__prev:
                return
            sum2dref(self.__delta, sub2d(l_pos, self.__prev))
            self.__prev = l_pos


class TestGui(BasicSpriteGui, GuiContext):
    def __init__(self, group: pygame.sprite.Group, target: pygame.surface.Surface):
        w, h = target.get_size()
        BasicSpriteGui.__init__(self, "prog_robot.png", (w // 2, h // 2), group)

    def notify(self, pos: Int2D, _type: enum):
        if _type == GuiContext.TYPE_RMB:
            self.disconnect()
            self.kill()

    def is_primary(self) -> bool:
        return True

    def bounds(self) -> pygame.Rect:
        return self.rect
