import re
from collections import UserDict
from importlib.resources import files
from typing import Any

from ruamel.yaml import YAML  # type: ignore

from .isotope import Isotope, IsotopeData


def _normalize_key(key: str):
    nkey: str = key.strip().lower().replace(" ", "")
    nkey = re.sub(r"([a-z]+)(\d+)(m?)", r"\1-\2\3", nkey)
    return nkey


class _ReadOnlyIsotopes(UserDict[str, Isotope]):
    """Immutable class to store isotopes

    Loaded at module level. Do not instantiate.

    key: str - isotope symbol
    value: Isotope - isotope instance
    """

    def __init__(self, data: dict[str, Isotope]) -> None:
        super().__init__()
        # Initialize without calling update, which is overridden to be read-only
        self.data = dict(data)

    # Override __getitem__ to normalize keys and provide better error messages
    def __getitem__(self, key: str) -> Isotope:
        key = _normalize_key(key)
        # Example: provide a default value if key is missing (like defaultdict)
        if key in self:
            return super().__getitem__(key)
        else:
            raise KeyError(f"No isotope found with symbol '{key}'")

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


def _load_isotopes() -> dict[str, Isotope]:
    resource = files("nexa.resources") / "tblSCALENuclideMass.yaml"
    yaml = YAML()
    raw_dict: dict[str, list] = yaml.load(resource)
    d: dict[str, Isotope] = {}
    # Store Isotope instances
    for key, value in raw_dict.items():
        sym = _normalize_key(value[0])
        value[0] = sym  # ensure symbol normalized
        iso: Isotope = Isotope(IsotopeData(*value))
        if sym in d:
            raise ValueError(f"Duplicate isotope symbol: {sym}")
        d[sym] = iso
    return d


isotopes: _ReadOnlyIsotopes = _ReadOnlyIsotopes(_load_isotopes())


# These helpers will have to be imported explicitly
def iso_by_symbol(symbol: str) -> Isotope:
    normalized_symbol = _normalize_key(symbol)
    if normalized_symbol in isotopes:
        return isotopes[normalized_symbol]
    else:
        raise ValueError(f"No isotope found with symbol {symbol}")


def iso_by_szaid(szaid: int) -> Isotope:
    for iso in isotopes.values():
        if iso.szaid == szaid:
            return iso
    raise ValueError(f"No isotope found with SZAID {szaid}")


def iso_by_zaid(zaid: int) -> Isotope:
    for iso in isotopes.values():
        if iso.zaid == zaid:
            return iso
    raise ValueError(f"No isotope found with ZAID {zaid}")


def iso_by_s(s: int) -> list[Isotope]:
    iso_list = [iso for iso in isotopes.values() if iso.s == s]
    iso_list.sort(key=lambda x: x.za * 10 + x.s)
    return iso_list


def iso_by_z(z: int) -> list[Isotope]:
    iso_list = [iso for iso in isotopes.values() if iso.z == z]
    iso_list.sort(key=lambda x: x.za * 10 + x.s)
    return iso_list


def iso_by_a(a: int) -> list[Isotope]:
    iso_list = [iso for iso in isotopes.values() if iso.a == a]
    iso_list.sort(key=lambda x: x.za * 10 + x.s)
    return iso_list


def iso_by_element(element: str) -> list[Isotope]:
    normalized_element = element.strip().lower()
    iso_list = [iso for iso in isotopes.values() if iso.element == normalized_element]
    # ensure metastable iso listed after ground state iso
    iso_list.sort(key=lambda x: x.za * 10 + x.s)
    return iso_list


def szaid_to_zaid(szaid: int) -> int:
    iso = iso_by_szaid(szaid)
    if iso:
        return iso.zaid
    raise ValueError(f"No isotope found with SZAID {szaid}")


def zaid_to_szaid(zaid: int) -> int:
    iso = iso_by_zaid(zaid)
    if iso:
        return iso.szaid
    raise ValueError(f"No isotope found with ZAID {zaid}")


def zaid_to_symbol(zaid: int) -> str:
    iso = iso_by_zaid(zaid)
    if iso:
        return iso.symbol
    raise ValueError(f"No isotope found with ZAID {zaid}")


def szaid_to_symbol(szaid: int) -> str:
    iso = iso_by_szaid(szaid)
    if iso:
        return iso.symbol
    raise ValueError(f"No isotope found with SZAID {szaid}")
