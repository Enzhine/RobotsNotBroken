import pathlib

# Types
Int2D = tuple[int, int]
Int2DZero = (0, 0)

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
