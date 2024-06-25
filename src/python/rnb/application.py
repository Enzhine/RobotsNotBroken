import pygame
from .core import (
    Int2D,
    Int2DZero,
    get_or,
    is_unscalable,
    mk_enum,
    enum,
)
from .sprites import BasicSpriteBlock


class LayerControl:
    LAYER_BACKGROUND = mk_enum()
    LAYER_GENERAL = mk_enum()
    LAYER_FOREGROUND = mk_enum()

    def __init__(self, target_screen: pygame.surface.Surface):
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

    def update(self, rect: pygame.rect.Rect):
        self.target_screen.fill((0,0,0), rect)


class MapControl:
    def __init__(self, layer_control: LayerControl, grid_block: Int2D):
        if is_unscalable(grid_block):
            raise RuntimeError('Grid block must be scalable!')
        self.layers = layer_control

        self.__grid_sz_x, self.__grid_sz_y = grid_block
        w, h = layer_control.target_screen.get_size()
        self.sz_x, self.sz_y = w // self.__grid_sz_x, h // self.__grid_sz_y
        self.__cache: dict[Int2D, list[pygame.sprite.Sprite | None]] = dict()

    @staticmethod
    def __map_slots(layer: enum = LayerControl.LAYER_BACKGROUND) -> int:
        if layer == LayerControl.LAYER_FOREGROUND:
            return 2
        elif layer == LayerControl.LAYER_GENERAL:
            return 1
        else:
            return 0

    def __try_get(self, pos: Int2D, layer: enum = LayerControl.LAYER_BACKGROUND) -> BasicSpriteBlock | None:
        try:
            slots = self.__cache[pos]
            return slots[MapControl.__map_slots(layer)]
        except KeyError:
            return None

    def __cache_set(self, obj: BasicSpriteBlock, pos: Int2D, layer: enum = LayerControl.LAYER_BACKGROUND):
        try:
            slots = self.__cache[pos]
        except KeyError:
            slots = [None] * 3
            self.__cache[pos] = slots
        slots[MapControl.__map_slots(layer)] = obj

    def __cache_rem(self, pos: Int2D, layer: enum = LayerControl.LAYER_BACKGROUND):
        try:
            slots = self.__cache[pos]
            slots[MapControl.__map_slots(layer)] = None
        except KeyError:
            pass

    def set(self, clazz: type, pos: Int2D = Int2DZero, layer: enum = LayerControl.LAYER_BACKGROUND):
        got = self.__try_get(pos, layer)
        if clazz:
            if got:
                raise RuntimeError
            sprite = clazz()
            if layer == LayerControl.LAYER_FOREGROUND:
                self.layers.foreground.add(sprite)
            elif layer == LayerControl.LAYER_GENERAL:
                self.layers.general.add(sprite)
            else:
                self.layers.background.add(sprite)
            self.to_local_zero(sprite)
            self.move_ip(sprite, *pos)
            # cache
            self.__cache_set(sprite, pos, layer)
        elif got:
            self.__cache_rem(pos, layer)

    def get(self, pos: Int2D = Int2DZero, layer: enum = LayerControl.LAYER_BACKGROUND) -> BasicSpriteBlock | None:
        return self.__try_get(pos, layer)

    def remove(self, pos: Int2D = Int2DZero, layer: enum = LayerControl.LAYER_BACKGROUND) -> bool:
        obj = self.__try_get(pos, layer)
        if obj:
            obj.kill()
            self.layers.update(obj.rect)
            self.__cache_rem(pos, layer)
            return True
        return False

    def move_ip(self, obj: pygame.sprite.Sprite, x=0, y=0):
        obj.rect.move_ip(x * self.__grid_sz_x, y * -self.__grid_sz_y)

    def to_local_zero(self, obj: pygame.sprite.Sprite):
        self.move_ip(obj, 0, -(self.sz_y - 1))

    def local_pos_at(self, abs_pos: Int2D) -> Int2D:
        x, y = abs_pos
        x //= self.__grid_sz_x
        y //= self.__grid_sz_y
        y = self.sz_y - 1 - y
        return x, y


class ProcessControl:
    def __init__(self, layers: LayerControl):
        self.alive = True
        self.map_ctrl = MapControl(layers, (16, 16))

    def __handle(self):
        for event in pygame.event.get():
            # end event
            if event.type == pygame.QUIT:
                self.alive = False
            if event.type == pygame.MOUSEBUTTONUP:
                lpos = self.map_ctrl.local_pos_at(event.pos)
                self.map_ctrl.remove(lpos, LayerControl.LAYER_BACKGROUND)

    def update(self):
        # guard statement
        if not self.alive:
            return
        self.__handle()

    def render_map(self):
        self.map_ctrl.layers.blit_ordered()


class RenderControl:
    def __init__(self, process: ProcessControl, **props):
        self.fps = get_or(props, 'fps', 60)

        self.process = process
        self.clock = pygame.time.Clock()

    def __cycle_once(self):
        # logic
        self.process.update()
        # render
        self.process.render_map()
        # flip
        pygame.display.flip()
        self.clock.tick(self.fps)

    def rescale(self):
        # TODO
        k = 2
        w, h = self.process.layers.target_screen.get_size()
        cx, cy = w//k, h//k
        sub = self.process.layers.target_screen.subsurface((cx - w//k//2, cy - h//k//2), (cx + w//k//2, cy + h//k//2))
        self.process.layers.target_screen.blit(pygame.transform.scale(sub, (w, h)), (0, 0))

    def start(self):
        while self.process.alive:
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
        self.process = ProcessControl(self.layers)
        self.renders = RenderControl(self.process)

    def start(self):
        self.renders.start()
        self.pygame_quit()

    def pygame_init(self):
        pygame.init()

    def pygame_quit(self):
        pygame.quit()