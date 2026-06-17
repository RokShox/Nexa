from collections import UserDict
from importlib.resources import files
from typing import Any

from ruamel.yaml import YAML  # type: ignore

from nexa.data import Element


def _normalize_key(key: str):
    return key.strip().lower()


class _ReadOnlyElements(UserDict[str, Element]):
    """Immutable class to store elemental constituents

    Loaded at module level. Do not instantiate.

    key: str - element symbol
    value: Element - Element instance with the isotopes and their abundances
    """

    def __init__(self, data: dict[str, Element]) -> None:
        # Initialize without calling update, which is overridden to be read-only
        self.data = dict(data)

    # Override __getitem__ to normalize keys and provide better error messages
    def __getitem__(self, key: str) -> Element:
        key = _normalize_key(key)
        if key in self:
            return super().__getitem__(key)
        else:
            raise KeyError(f"No elemental constituent found with symbol '{key}'")

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            key = _normalize_key(key)
        return super().__contains__(key)

    # Override methods that would modify the dictionary to prevent changes
    def __setitem__(self, key: Any, value: Any) -> None:
        raise TypeError(f"{self.__class__.__name__} is read-only")

    def __delitem__(self, key: Any) -> None:
        raise TypeError(f"{self.__class__.__name__} is read-only")

    def update(self, other: Any = None, /, **kwargs: Any) -> None:
        raise TypeError(f"{self.__class__.__name__} is read-only")

    def pop(self, key: Any, default: Any = None) -> Any:
        raise TypeError(f"{self.__class__.__name__} is read-only")

    def popitem(self) -> tuple[Any, Any]:
        raise TypeError(f"{self.__class__.__name__} is read-only")

    def clear(self) -> None:
        raise TypeError(f"{self.__class__.__name__} is read-only")

    def setdefault(self, key: Any, default: Any = None) -> Any:
        raise TypeError(f"{self.__class__.__name__} is read-only")


def _load_elements() -> dict[str, Element]:
    """Initialize the Elements.

    For each element, create an Element instance.
    Initialized from a yaml file generating a Dict[str, List] where:
        key: str - element symbol (normalized to lower case)
        value: List - [name, z, zaid, amu]

    Element atomic mass data should not be used except for approximate calculations.
    Use a Constituent mass instead.
    """
    print("initializing Elements")
    resource = files("nexa.resources") / "tblElmNames.yaml"
    yaml = YAML()
    raw_dict: dict[str, list] = yaml.load(resource)
    d: dict[str, Element] = {}
    # Store element name, z, amu
    for key, value in raw_dict.items():
        sym = _normalize_key(key)
        elm = Element(sym, value[0], value[1], value[3])
        if sym in d:
            raise ValueError(f"Duplicate element symbol: {sym}")
        d[sym] = elm
    return d


elements: _ReadOnlyElements = _ReadOnlyElements(_load_elements())


def zaid_of_elm(elm: str) -> int:
    """Get ZA id by element symbol."""
    return elements[_normalize_key(elm)].zaid


def amu_of_elm(elm: str) -> float:
    """Get atomic mass by element symbol."""
    return elements[_normalize_key(elm)].amu


def z_of_elm(elm: str) -> int:
    """Get atomic number by element symbol."""
    return elements[_normalize_key(elm)].z


def elm_by_zaid(zaid: int) -> Element:
    """Get Element by ZA id."""
    for elm in elements.values():
        if elm.zaid == zaid:
            return elm
    raise ValueError(f"No element found with ZAID {zaid}")


def elm_by_z(z: int) -> Element:
    """Get Element by atomic number."""
    for elm in elements.values():
        if elm.z == z:
            return elm
    raise ValueError(f"No element found with atomic number {z}")


def elm_by_name(name: str) -> Element:
    """Get Element by name (normalized)."""
    nname: str = _normalize_key(name)
    for elm in elements.values():
        if elm.name == nname:
            return elm
    raise ValueError(f"No element found with name {name}")
