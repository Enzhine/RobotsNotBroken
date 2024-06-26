import pygame
from .core import Int2D
from abc import ABC, abstractmethod
from math import log, floor, ceil


class EventHandler(ABC):
    @abstractmethod
    def on_event(self, event: pygame.event.Event):
        raise NotImplementedError


class RescaleInputHandler(EventHandler):
    def __init__(self, k=1.1, max_k=4):
        self.scale = 1
        self.__steps = 0
        self.__k = k
        self.__max_k = floor(log(max_k, k))

    @staticmethod
    def __is_vertical(event: pygame.event.Event):
        return event.y > 0

    def on_event(self, event):
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
        self.scale = 1.1 ** self.__steps


class TranslateInputHandler(EventHandler):
    def __init__(self, rescaler: RescaleInputHandler, sizes: Int2D):
        self.__rescaler = rescaler
        self.__prev = None
        self.__sizes = sizes
        self.delta = [0, 0]

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
        dx, dy = self.delta[0], self.delta[1]
        sx, sy = ceil(w / 2 - w / k / 2 + x / k - dx), ceil(h / 2 - h / k / 2 + y / k - dy)
        return sx, sy

    def __delta(self, now):
        return now[0] - self.__prev[0], now[1] - self.__prev[1]

    def __plus(self, delta):
        self.delta[0] = self.delta[0] + delta[0]
        self.delta[1] = self.delta[1] + delta[1]

    @staticmethod
    def is_lmb(event: pygame.event.Event):
        return event.button == 1

    @staticmethod
    def is_rmb(event: pygame.event.Event):
        return event.button == 3

    def on_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and TranslateInputHandler.is_rmb(event):
            self.__prev = self.__map_scaled(event.pos)
            return
        elif event.type == pygame.MOUSEBUTTONUP:
            self.__prev = None
            return
        elif event.type == pygame.MOUSEMOTION:
            if not self.__prev:
                return
            l_pos = self.__map_scaled(event.pos)
            self.__plus(self.__delta(l_pos))
            self.__prev = l_pos
