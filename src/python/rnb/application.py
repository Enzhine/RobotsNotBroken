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
from .handlers import (
    RescaleInputHandler,
    TranslateInputHandler
)
from math import ceil


class LayerControl:
    LAYER_BACKGROUND = mk_enum()
    LAYER_GENERAL = mk_enum()
    LAYER_FOREGROUND = mk_enum()

    def __init__(self, target_screen: pygame.surface.Surface):
        self.target_screen = target_screen
        self.pre_target = pygame.Surface(self.target_screen.get_size())

        self.background = pygame.sprite.Group()
        self.general = pygame.sprite.Group()
        self.foreground = pygame.sprite.Group()

    def blit_ordered(self):
        # pre layer
        for sprite in self.background:
            self.pre_target.blit(sprite.surf, sprite.rect)
        # main layer
        for sprite in self.general:
            self.pre_target.blit(sprite.surf, sprite.rect)
        # post layer
        for sprite in self.foreground:
            self.pre_target.blit(sprite.surf, sprite.rect)

    def final_render(self, screen):
        self.target_screen.blit(screen, (0, 0))

    def update(self, rect: pygame.rect.Rect):
        self.pre_target.fill((0, 0, 0), rect)


class MapControl:
    def __init__(self, layer_control: LayerControl, grid_block: Int2D):
        if is_unscalable(grid_block):
            raise RuntimeError('Grid block must be scalable!')
        self.layers = layer_control

        self.__grid_sz_x, self.__grid_sz_y = grid_block
        w, h = layer_control.target_screen.get_size()
        self.sz_x, self.sz_y = ceil(w / self.__grid_sz_x), ceil(h // self.__grid_sz_y)
        self.__cache = [[[None] * 3 for _ in range(self.sz_y)] for _ in range(self.sz_x)]

    @staticmethod
    def __map_z(layer: enum) -> int:
        if layer == LayerControl.LAYER_FOREGROUND:
            return 2
        elif layer == LayerControl.LAYER_GENERAL:
            return 1
        else:
            return 0

    def __map_layer(self, layer: enum) -> pygame.sprite.Group:
        if layer == LayerControl.LAYER_FOREGROUND:
            return self.layers.foreground
        elif layer == LayerControl.LAYER_GENERAL:
            return self.layers.general
        else:
            return self.layers.background

    def __cache_get(self, pos: Int2D, layer: enum = LayerControl.LAYER_BACKGROUND) -> BasicSpriteBlock | None:
        x, y = pos
        z = MapControl.__map_z(layer)
        return self.__cache[x][y][z]

    def __cache_set(self, obj: BasicSpriteBlock | None, pos: Int2D, layer: enum = LayerControl.LAYER_BACKGROUND):
        x, y = pos
        z = MapControl.__map_z(layer)
        self.__cache[x][y][z] = obj

    def set(self, clazz: type, pos: Int2D = Int2DZero, layer: enum = LayerControl.LAYER_BACKGROUND):
        got = self.__cache_get(pos, layer)
        if clazz:
            if got:
                raise RuntimeError
            sprite = clazz()

            ground = self.__map_layer(layer)
            ground.add(sprite)

            self.to_local_zero(sprite)
            self.move_ip(sprite, *pos)
            # cache
            self.__cache_set(sprite, pos, layer)
        elif got:
            self.rem(pos, layer)

    def get(self, pos: Int2D = Int2DZero, layer: enum = LayerControl.LAYER_BACKGROUND) -> BasicSpriteBlock | None:
        return self.__cache_get(pos, layer)

    def rem(self, pos: Int2D = Int2DZero, layer: enum = LayerControl.LAYER_BACKGROUND) -> bool:
        obj = self.__cache_get(pos, layer)
        if obj:
            obj.kill()
            self.layers.update(obj.rect)
            self.__cache_set(None, pos, layer)
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
        self.steps = 0

        self.rescaler = RescaleInputHandler()
        self.translator = TranslateInputHandler(self.rescaler, self.map_ctrl.layers.target_screen.get_size())

    def rescaled(self) -> pygame.surface.Surface:
        k = self.rescaler.scale
        w, h = self.map_ctrl.layers.target_screen.get_size()
        sw, sh = ceil(w/k), ceil(h/k)
        cx, cy = ceil(w/2), ceil(h/2)
        dx, dy = self.translator.delta[0], self.translator.delta[1]
        sub = self.map_ctrl.layers.pre_target.subsurface((cx - sw//2 - dx, cy - sh//2 - dy), (sw, sh))
        return pygame.transform.scale(sub, (w, h))

    def __handle_quit(self, event: pygame.event.Event):
        if event.type != pygame.QUIT:
            return
        self.alive = False

    def __handle(self):
        for event in pygame.event.get():
            # events
            self.__handle_quit(event)
            self.rescaler.on_event(event)
            self.translator.on_event(event)
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    lpos = self.map_ctrl.local_pos_at(self.translator.map_scaled(event.pos))
                    self.map_ctrl.rem(lpos, LayerControl.LAYER_BACKGROUND)

    def update(self):
        # guard statement
        if not self.alive:
            return
        self.__handle()

    def render_map(self):
        self.map_ctrl.layers.blit_ordered()
        self.map_ctrl.layers.target_screen.fill((0, 0, 0))
        self.map_ctrl.layers.final_render(self.rescaled())


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