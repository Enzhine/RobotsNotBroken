import pathlib

# Types
Int2D = tuple[int, int]
Int2DRef = list[int]
Int2DZero = (0, 0)
Float2D = tuple[float, float]
Float2DRef = list[float]

Color = tuple[int, int, int]
ColorBlack: Color = (0, 0, 0)
ColorWhite: Color = (255, 255, 255)

# Path
__BASE = pathlib.Path(__file__).parent.parent.parent
APPLICATION_DIR = __BASE / "python"
APPLICATION_DIR_PATH = APPLICATION_DIR.resolve()
SOURCES_DIR = __BASE / "sources"
SOURCES_DIR_PATH = SOURCES_DIR.resolve()

# Fake enum
enum = int


class __enum__:
    c = 0


def mk_enum() -> enum:
    c = __enum__.c
    __enum__.c += 1
    return c


# funcs
def get_or(_dict: dict, key: str, value):
    try:
        return _dict[key]
    except KeyError:
        return value


def is_unscalable(point: tuple) -> bool:
    return any(align == 0 for align in point)


def sum2d(a: Int2D, b: Int2D) -> Int2D:
    return a[0] + b[0], a[1] + b[1]


def sub2d(a: Int2D, b: Int2D) -> Int2D:
    return a[0] - b[0], a[1] - b[1]


def sum2dref(a: Int2DRef, b: Int2DRef | Int2D):
    a[0] = a[0] + b[0]
    a[1] = a[1] + b[1]


def mul2d(a: Int2D | Float2D, val) -> Float2D:
    return a[0] * val, a[1] * val


def mul2dref(a: Int2DRef | Float2DRef, val):
    a[0] = a[0] * val
    a[1] = a[1] * val


def manh_dist(_from: Int2D | Float2D, to: Int2D | Float2D) -> int | float:
    dx, dy = sub2d(to, _from)
    return abs(dx) + abs(dy)


def dist(_from: Int2D | Float2D, to: Int2D | Float2D) -> int | float:
    dx, dy = sub2d(to, _from)
    return (dx**2 + dy**2) ** 0.5
