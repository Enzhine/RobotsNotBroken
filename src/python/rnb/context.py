from abc import ABC, abstractmethod

import pygame

from .core import enum, mk_enum, Int2D


class EventHandler(ABC):
    @abstractmethod
    def on_event(self, event: pygame.event.Event):
        raise NotImplementedError


class AbstractContext(ABC):
    @abstractmethod
    def notify(self, *state):
        raise NotImplementedError


class AbstractContextListener(ABC):
    @abstractmethod
    def subscribe(self, context: AbstractContext):
        raise NotImplementedError

    @abstractmethod
    def forget(self, context: AbstractContext):
        raise NotImplementedError

    @abstractmethod
    def is_listening(self) -> bool:
        raise NotImplementedError


class WrappedContext(AbstractContext, ABC):
    def __init__(self):
        self._producer: AbstractContextListener | None = None

    @abstractmethod
    def is_primary(self) -> bool:
        raise NotImplementedError

    def listen(self, context: AbstractContextListener):
        self._producer = context
        self._producer.subscribe(self)

    def disconnect(self):
        if self._producer:
            self._producer.forget(self)
            self._producer = None


class MultiContextListener(AbstractContextListener, ABC):
    def __init__(self, *contexts: WrappedContext):
        self.__layers: list[list[WrappedContext]] = []
        self.__current = -1

        for context in contexts:
            self.subscribe(context)

    def current_layer(self):
        return self.__layers[self.__current]

    def __push_layer(self):
        self.__layers.append([])
        self.__current += 1

    def __pop_layer(self):
        self.__layers.pop()
        self.__current -= 1

    def subscribe(self, context: WrappedContext):
        if context.is_primary() or not self.is_listening():
            self.__push_layer()
        self.current_layer().append(context)

    def forget(self, context: WrappedContext):
        if not self.is_listening():
            return
        if context in self.current_layer():
            self.current_layer().remove(context)
            if len(self.current_layer()) == 0:
                self.__pop_layer()

    def is_listening(self) -> bool:
        return self.__current != -1


class GuiContext(WrappedContext, ABC):
    TYPE_LMB: enum = mk_enum()
    TYPE_RMB: enum = mk_enum()
    TYPE_H_ENTER: enum = mk_enum()
    TYPE_H_EXIT: enum = mk_enum()

    @abstractmethod
    def bounds(self) -> pygame.Rect:
        raise NotImplementedError

    @abstractmethod
    def notify(self, pos: Int2D, _type: enum):
        raise NotImplementedError


