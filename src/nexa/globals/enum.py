from enum import IntEnum


# Enum for composition mode
class CompositionMode(IntEnum):
    """Enum for composition mode

    Used as int index into constituent tuple
    """

    Mass = 1
    Atom = 2
