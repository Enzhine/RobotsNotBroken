import pathlib

# Types
Int2D = tuple[int, int]

# Path
__BASE = pathlib.Path(__file__).parent.parent.parent
APPLICATION_DIR = __BASE / "python"
APPLICATION_DIR_PATH = APPLICATION_DIR.resolve()
SOURCES_DIR = __BASE / "sources"
SOURCES_DIR_PATH = SOURCES_DIR.resolve()


# funcs
def get_or(_dict: dict, key: str, value):
    try:
        return _dict[key]
    except KeyError:
        return value
