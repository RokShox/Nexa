from collections import UserDict
from importlib.resources import files
from typing import Any

from ruamel.yaml import YAML  # type: ignore

from nexa.data.isotopes import isotopes
from nexa.globals import CompositionMode
from nexa.material import Constituent


# Hide helper function
def _normalize_key(key: str):
    return key.strip().lower()


class _ReadOnlyAbundances(UserDict[str, Constituent]):
    """Immutable class to store elemental abundances

    Loaded at module level. Do not instantiate.

    key: str - element symbol
    value: Constituent - Constituent instance with the isotopes and their abundances
    """

    def __init__(self, data: dict[str, Constituent]) -> None:
        # Initialize without calling update, which is overridden to be read-only
        self.data = dict(data)

    # Override __getitem__ to normalize keys and provide better error messages
    def __getitem__(self, key: str) -> Constituent:
        key = _normalize_key(key)
        if key in self:
            return super().__getitem__(key)
        else:
            raise KeyError(f"No elemental constituent found with symbol '{key}'")

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


def _load_abundances() -> dict[str, Constituent]:
    """Initialize the Abundances.

    For each element, create a level 1 Constituent instance with the isotopes and their
    abundances.
    Overrides dict methods that change values to prevent changes.
    """

    print("initializing Abundances")
    resource = files("nexa.resources") / "tblNatIso.yaml"
    yaml = YAML()
    raw_dict: dict[str, dict[str, float]] = yaml.load(resource)
    d: dict[str, Constituent] = {}
    # Store instances
    for elm_sym, iso_dict in raw_dict.items():
        elm_sym = _normalize_key(elm_sym)
        elm_con = Constituent(elm_sym, CompositionMode.Atom)

        for iso_sym, afrac in iso_dict.items():
            iso_con = isotopes[iso_sym]
            elm_con.add(iso_con, float(afrac))
        elm_con.seal()
        if elm_sym in d:
            raise ValueError(f"Duplicate element symbol: {elm_sym}")
        d[elm_sym] = elm_con
    return d


abundances: _ReadOnlyAbundances = _ReadOnlyAbundances(_load_abundances())
