from abc import ABC, abstractmethod

import pygame

from .context import WrappedContext, SmartContext
from .core import Int2D, Int2DZero, get_or, is_unscalable, mk_enum, enum, dist, sum2d, sub2d
from .blocks import MultiBlock, CursorBlock, WorldPlaced
from .render import Rendering, TickingRendering
from .handlers import RescaleInputHandler, TranslateInputHandler, GuiContextListener, TestGui
from math import ceil, floor


class LayerControl:
    LAYER_BACKGROUND = mk_enum()
    LAYER_GENERAL = mk_enum()
    LAYER_FOREGROUND = mk_enum()

    def __init__(self, bg_depth: float, fg_depth: float):
        self.__bg_depth = bg_depth
        self.__fg_depth = fg_depth
        self.background = pygame.sprite.Group()
        self.general = pygame.sprite.Group()
        self.foreground = pygame.sprite.Group()

        self.gui = pygame.sprite.Group()

    def by_depth(self, offset: Int2D, layer: enum):
        if layer == self.LAYER_GENERAL:
            return offset
        elif layer == self.LAYER_FOREGROUND:
            return offset[0] * self.__fg_depth, offset[1] * self.__fg_depth
        elif layer == self.LAYER_BACKGROUND:
            return offset[0] * self.__bg_depth, offset[1] * self.__bg_depth
        raise RuntimeError('Not existing layer!')

    def map_layer(self, layer: enum) -> pygame.sprite.Group:
        if layer == LayerControl.LAYER_FOREGROUND:
            return self.foreground
        elif layer == LayerControl.LAYER_GENERAL:
            return self.general
        else:
            return self.background


class LightMap:
    def __init__(self, light_level: int, sizes: Int2D, base: int = None):
        self.__w, self.__h = sizes
        self.__mx = light_level
        if base is None:
            base = self.__mx
        self.__lmp = [[base for _ in range(self.__h)] for _ in range(self.__w)]

    def update_light(self, pos: Int2D, level: float) -> int:
        x, y = pos
        now = floor(level * self.__mx)
        self.__lmp[x][y] += now
        return self.get_light(pos)

    def get_max(self):
        return self.__mx

    def get_light(self, pos: Int2D) -> int:
        x, y = pos
        return min(self.__lmp[x][y], self.__mx)


class MapControl:
    def __init__(self, layer_control: LayerControl, grid_block: Int2D, screen_size: Int2D):
        if is_unscalable(grid_block):
            raise RuntimeError('Grid block must be scalable!')
        self.layers = layer_control

        self.__grid_sz_x, self.__grid_sz_y = grid_block
        w, h = screen_size
        self.__sz_x, self.__sz_y = ceil(w / self.__grid_sz_x), ceil(h // self.__grid_sz_y)
        self.__cache = [[[None] * 3 for _ in range(self.__sz_y)] for _ in range(self.__sz_x)]

        self.light_map = LightMap(255, self.map_size(), base=0)
        self.light_ctrl = LightControl(self)

    def map_size(self):
        return self.__sz_x, self.__sz_y

    @staticmethod
    def __map_z(layer: enum) -> int:
        if layer == LayerControl.LAYER_FOREGROUND:
            return 2
        elif layer == LayerControl.LAYER_GENERAL:
            return 1
        else:
            return 0

    def __cache_get(self, pos: Int2D, layer: enum = LayerControl.LAYER_BACKGROUND) -> Rendering | None:
        x, y = pos
        z = MapControl.__map_z(layer)
        return self.__cache[x][y][z]

    def __cache_set(self, obj: Rendering | None, pos: Int2D, layer: enum = LayerControl.LAYER_BACKGROUND):
        x, y = pos
        z = MapControl.__map_z(layer)
        self.__cache[x][y][z] = obj
        if obj:
            obj.assign(x, y, z)

    def set_silently(self, sprite: Rendering, pos: Int2D, layer: enum = LayerControl.LAYER_BACKGROUND):
        ground = self.layers.map_layer(layer)
        ground.add(sprite)
        self.to_local_zero(sprite)
        self.move_ip(sprite, *pos)

    def set(self, clazz: type, pos: Int2D = Int2DZero, layer: enum = LayerControl.LAYER_BACKGROUND):
        got = self.__cache_get(pos, layer)
        if clazz:
            if got:
                raise RuntimeError
            sprite = clazz()

            ground = self.layers.map_layer(layer)
            ground.add(sprite)

            self.to_local_zero(sprite)
            self.move_ip(sprite, *pos)
            self.__sync_light(sprite, pos)
            # cache
            for spos in MultiBlock.structure(sprite):
                x, y = pos[0] + spos[0], pos[1] + spos[1]
                self.__cache_set(sprite, (x, y), layer)
        elif got:
            self.rem(pos, layer)

    def get(self, pos: Int2D = Int2DZero, layer: enum = LayerControl.LAYER_BACKGROUND) -> Rendering | None:
        return self.__cache_get(pos, layer)

    def rem(self, pos: Int2D = Int2DZero, layer: enum = LayerControl.LAYER_BACKGROUND) -> bool:
        obj = self.__cache_get(pos, layer)
        if obj:
            obj.kill()
            for spos in MultiBlock.structure(obj):
                x, y = pos[0] + spos[0], pos[1] + spos[1]
                self.__cache_set(None, (x, y), layer)
            return True
        return False

    def __sync_light(self, obj, pos: Int2D):
        obj.tint_by(self.light_map.get_light(pos))

    def update_light(self, pos: Int2D, level: float):
        self.light_map.update_light(pos, level)
        obj = self.get(pos, LayerControl.LAYER_GENERAL)
        if obj:
            self.__sync_light(obj, pos)

    def move_ip(self, sprite: Rendering, x=0, y=0):
        sprite.bounds().move_ip(x * self.__grid_sz_x, y * -self.__grid_sz_y)

    def global_to(self, x=0, y=0):
        return x * self.__grid_sz_x, y * -self.__grid_sz_y

    def global_zero(self) -> Int2D:
        return 0, (self.__sz_y - 1) * self.__grid_sz_y

    def to_local_zero(self, obj: Rendering):
        self.move_ip(obj, 0, -(self.__sz_y - 1))

    def local_pos_at(self, abs_pos: Int2D) -> Int2D:
        x, y = abs_pos
        x //= self.__grid_sz_x
        y //= self.__grid_sz_y
        y = self.__sz_y - 1 - y
        return x, y


class LightControl:
    def __init__(self, map_ctrl: MapControl):
        self.__map_ctrl = map_ctrl

    @staticmethod
    def __spherical(radius: int, offset: Int2D = Int2DZero) -> set:
        s = set()
        x, y = offset
        co = (x + 0.5, y + 0.5)
        for _x in range(x - radius, x + radius + 1):
            for _y in range(y - radius, y + radius + 1):
                c = (_x + 0.5, _y + 0.5)
                d = dist(co, c)
                if d <= radius:
                    s.add((_x, _y, floor(d)))
        return s

    def brighten(self, pos: Int2D, radius: int, level: float = 1):
        for *_pos, l in LightControl.__spherical(radius, pos):
            _level = (1 - l / radius) * level
            self.__map_ctrl.update_light(_pos, _level)


class GameCursorInputHandler(SmartContext):

    def __init__(self, th: TranslateInputHandler, map_ctrl: MapControl):
        SmartContext.__init__(self)
        self.__mc = map_ctrl
        self.__th = th
        self.__last = Int2DZero

        self.cursor = CursorBlock()

    def priority(self) -> int:
        return 10

    def notify(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self.__last = self.__th.map_scaled(event.pos)

    def map_pos(self) -> Int2D:
        return self.__mc.local_pos_at(self.__last)

    def draw_pos(self) -> Int2D:
        map_pos = self.map_pos()
        return sum2d(self.__mc.global_zero(), self.__mc.global_to(*map_pos))

    def state_changed(self, state: enum):
        if state == WrappedContext.CTXT_UNF:
            self.__last = Int2DZero


class ProcessControl:
    def __init__(self, dest: pygame.surface.Surface, layer_ctrl: LayerControl):
        self.__dest = dest
        self.__layer_ctrl = layer_ctrl

        self.alive = True
        self.map_ctrl = MapControl(self.__layer_ctrl, (16, 16), self.__dest.get_size())

        self.ctxt_listener = GuiContextListener()
        self.rescaler = RescaleInputHandler()
        self.rescaler.listen(self.ctxt_listener)
        self.translator = TranslateInputHandler(self.rescaler, self.__dest.get_size())
        self.translator.listen(self.ctxt_listener)
        self.cursor_ctrl = GameCursorInputHandler(self.translator, self.map_ctrl)
        self.cursor_ctrl.listen(self.ctxt_listener)

    def __handle_quit(self, event: pygame.event.Event):
        if event.type != pygame.QUIT:
            return
        self.alive = False

    def __handle(self):
        for event in pygame.event.get():
            # events
            self.__handle_quit(event)
            self.ctxt_listener.on_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    TestGui(self.__layer_ctrl.gui, self.__dest).listen(self.ctxt_listener, push=True)
                # pos = self.cursor_ctrl.map_pos(self.map_ctrl)
                # if event.button == 1:
                #     self.map_ctrl.light_ctrl.brighten(pos, 5)

    def update(self):
        # guard statement
        if not self.alive:
            return
        self.__handle()


class RenderControl:
    def __init__(self, dest: pygame.surface.Surface, process: ProcessControl, **props):
        self.__dest = dest
        self.__pre_dest = pygame.surface.Surface(self.__dest.get_size()).convert_alpha()
        self.fps = get_or(props, 'fps', 60)

        self.process = process
        self.clock = pygame.time.Clock()
        self.__dms = 0.0

        self.__front = pygame.font.Font(None, 36)

    def __cycle_once(self):
        # logic
        self.process.update()
        # render
        self.__render_map()
        # flip
        pygame.display.flip()
        self.__dms = self.clock.tick(self.fps)

    def start(self):
        while self.process.alive:
            self.__cycle_once()

    def __rescaled_view(self) -> tuple[Int2D, Int2D]:
        k = self.process.rescaler.scale
        w, h = self.__dest.get_size()
        sw, sh = ceil(w / k), ceil(h / k)
        cx, cy = ceil(w / 2), ceil(h / 2)
        return (cx - sw // 2, cy - sh // 2), (sw, sh)

    def __rescaled(self) -> pygame.surface.Surface:
        w, h = self.__dest.get_size()
        sub = self.__pre_dest.subsurface(*self.__rescaled_view())
        return pygame.transform.scale(sub, (w, h))

    def __layers(self):
        return self.process.map_ctrl.layers

    def __map_ctrl(self):
        return self.process.map_ctrl

    def __blit_layer(self, layer, dms: float):
        dest_layer = self.__layers().map_layer(layer)
        delta = self.process.translator.delta()
        view = pygame.Rect(*self.__rescaled_view())
        for sprite in dest_layer:
            sprite: Rendering
            if hasattr(sprite, 'tick'):
                sprite.tick(dms)
            if not sprite.visible:
                continue
            pos = sprite.bounds().move(self.__layers().by_depth(delta, layer))
            if not pos.colliderect(view):
                continue
            surf, area = sprite.current_frame()
            self.__pre_dest.blit(surf, dest=pos, area=area)

    def __blit_ordered(self, dms: float):
        self.__blit_layer(LayerControl.LAYER_BACKGROUND, dms)
        self.__blit_layer(LayerControl.LAYER_GENERAL, dms)
        self.__blit_layer(LayerControl.LAYER_FOREGROUND, dms)

    def __blit_cursor(self):
        sprite = self.process.cursor_ctrl.cursor
        to = sum2d(self.process.cursor_ctrl.draw_pos(), self.process.translator.delta())
        target = sprite.bounds().move(to)
        self.__pre_dest.blit(sprite.surface(), target)

    def __blit_gui(self):
        for sprite in self.__layers().gui:
            self.__dest.blit(sprite.surf, sprite.rect)

    def __render_map(self):
        self.__pre_dest.fill((0, 0, 0))
        self.__blit_ordered(self.__dms)
        self.__blit_cursor()
        self.__dest.blit(self.__rescaled(), (0, 0))
        self.__blit_gui()
        self.__dest.blit(self.__front.render(f'{self.clock.get_fps():.2f}', False, (255, 255, 255)), Int2DZero)


class WorldGenerator(ABC):
    @abstractmethod
    def generate(self, map_ctrl: MapControl):
        raise NotImplementedError


class MainApplication:
    def __init__(self, window_rect: Int2D = None, world_gen: WorldGenerator = None):
        # init
        self.pygame_init()

        # screen preparation
        if window_rect:
            self.screen = pygame.display.set_mode(window_rect)
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        # layer init
        self.layers = LayerControl(0.8, 1.2)
        self.process = ProcessControl(self.screen, self.layers)
        self.renders = RenderControl(self.screen, self.process)

        # world gen
        self.__step_world_gen(world_gen)

    def __step_world_gen(self, world_gen: WorldGenerator):
        if world_gen:
            print('World generation...')
            world_gen.generate(self.process.map_ctrl)
            print('Generate completed.')
        else:
            print('No world generator was provided. Skipping...')

    def start(self):
        self.renders.start()
        self.pygame_quit()

    def pygame_init(self):
        pygame.init()

    def pygame_quit(self):
        pygame.quit()
