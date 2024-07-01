from math import floor

from .application import (
    WorldGenerator,
    MapControl, LayerControl
)
from .core import (
    Int2D,
    mul2d,
    Int2DZero,
    sub2d, sum2d, manh_dist
)
import random as r

from .blocks import (
    BgBigBlock,
    DirtBlock,
    StoneBlock,
    PowerStageMultiblock
)


def rand_int2d(rand: r.Random = r):
    temp = [-1, 0, 1]
    return rand.choice(temp), rand.choice(temp)


def rand_float2d(rand: r.Random = r):
    temp = [-1, 1]
    sx = rand.choice(temp)
    sy = rand.choice(temp)
    return sx * rand.random(), sy * rand.random()


def rand_jump(dist: int, offset=Int2DZero, rand: r.Random = r):
    j = mul2d(rand_float2d(rand), dist)
    return floor(j[0]) + offset[0], floor(j[1]) + offset[1]


def middle(_from: Int2D, to: Int2D):
    dist = sub2d(to, _from)
    return _from[0] + dist[0] // 2, _from[1] + dist[1] // 2


class DefaultWorldGenerator(WorldGenerator):
    def __init__(self, caves: int, cave_len: int, cave_sep: int, repeat=1, seed=None):
        if seed is None:
            seed = r.random()
        self.__r = r.Random(seed)
        self.caves = caves
        self.cave_len = cave_len
        self.cave_sep = cave_sep
        self.repeat = repeat

    def __trace(self, _from: Int2D, to: Int2D) -> set[Int2D]:
        _trace = set()

        lpos: Int2D = _from
        ldist = manh_dist(_from, to)
        last = list()
        while ldist != 0:
            while (step := rand_int2d(self.__r)) in last:
                continue
            _lpos = sum2d(lpos, step)
            _ldist = manh_dist(_lpos, to)
            if _ldist < ldist:
                ldist = _ldist
                lpos = _lpos
                last.clear()
            else:
                last.append(step)
            _trace.add(_lpos)
        return _trace

    def __cave(self, _from: Int2D, to=None) -> tuple[Int2D, set[Int2D]]:
        if not to:
            to = rand_jump(self.cave_len, offset=_from, rand=self.__r)
        _set = self.__trace(_from, to)
        return to, _set

    def generate(self, map_ctrl: MapControl):
        # caves
        sets = set()

        w, h = map_ctrl.map_size()
        cx, cy = w // 2, h // 2
        l, _r = (cx - self.cave_len // 2, cy), (cx + self.cave_len // 2, cy)

        to, s = self.__cave(l, to=_r)
        mid = middle(l, to)
        sets |= s
        for _ in range(self.caves):
            for _ in range(self.repeat):
                l = rand_jump(self.cave_sep, offset=mid, rand=self.__r)
                to, s = self.__cave(l)
                sets |= s
            mid = middle(l, to)
        # bg
        for x in range(0, w, 4):
            for y in range(0, h, 4):
                map_ctrl.set_silently(BgBigBlock(), pos=(x, y), layer=LayerControl.LAYER_BACKGROUND)
        # blocks
        sets -= {(cx - 1, cy - 1), (cx, cy - 1), (cx + 1, cy - 1), (cx + 2, cy - 1)}
        for x in range(0, w):
            for y in range(0, h):
                if (x, y) in sets:
                    continue
                clazz = DirtBlock if self.__r.random() < 0.8 else StoneBlock
                map_ctrl.set(clazz, pos=(x, y), layer=LayerControl.LAYER_GENERAL)
        # prepared
        center = (cx, cy)
        map_ctrl.set(PowerStageMultiblock, pos=center, layer=LayerControl.LAYER_GENERAL)
        map_ctrl.light_ctrl.brighten(center, 5)
