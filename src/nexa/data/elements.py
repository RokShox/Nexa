from ruamel.yaml import YAML

from pathlib import Path
from typing import List, Dict

from nexa.data import Element


class Elements(dict):
    """Class to store elements.

    Implements a singleton pattern.
    Disallows methods that change values.
    Subclasses dict to represent a Dict[str, Element] where:
    key: str - element symbol
    value: Element - Element instance
    """

    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern"""
        if not hasattr(cls, "instance"):
            # cls.instance = super(Elements, cls).__new__(cls)
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        """Initialize the Elements.

        For each element, create an Element instance.
        Initialized from a yaml file generating a Dict[str, List] where:
            key: str - element symbol (normalized to lower case)
            value: List - [name, z, zaid, amu]

        Element atomic mass data should not be used except for approximate calculations.
        Use a Constituent mass instead.
        """
        if not self._initialized:
            self._initialized = True
            print("initializing Elements")
            p = Path(__file__).resolve().parent.parent / "resources" / "tblElmNames.yaml"
            yaml = YAML()
            raw_dict: Dict[str, List] = yaml.load(p)
            # Store Isotope instances
            for key, value in raw_dict.items():
                sym = self.__normalize_key(key)
                elm = Element(sym, value[0], value[1], value[3])
                super().__setitem__(self.__normalize_key(key), elm)

    def __getitem__(self, key: str) -> Element:
        try:
            return super().__getitem__(self.__normalize_key(key))
        except KeyError:
            return None

    # no setting
    def __setitem__(self, key: str, value: Element):
        raise RuntimeError("Setting not allowed")

    # no deletion
    def __delitem__(self):
        raise RuntimeError("Deletion not allowed")

    # no update
    def update(self, d: dict):
        raise RuntimeError("Update not allowed")

    # no pop
    def pop(self, s=None):
        raise RuntimeError("Deletion not allowed")

    # no popitem
    def popitem(self, s=None):
        raise RuntimeError("Deletion not allowed")

    # no setdefault
    def setdefault(self, key, value):
        raise RuntimeError("Setting not allowed")

    def __normalize_key(self, key: str):
        return key.strip().lower()

    def zaid(self, elm: str) -> int:
        """Get ZA id by element symbol."""
        return self[self.__normalize_key(elm)].zaid

    def amu(self, elm: str) -> float:
        """Get atomic mass by element symbol."""
        return self[self.__normalize_key(elm)].amu

    def z(self, elm: str) -> int:
        """Get atomic number by element symbol."""
        return self[self.__normalize_key(elm)].z

    def elm_by_zaid(self, zaid: int) -> Element:
        """Get Element by ZA id."""
        for elm in self.values():
            if elm.zaid == zaid:
                return elm
        return None

    def elm_by_z(self, z: int) -> Element:
        """Get Element by atomic number."""
        for elm in self.values():
            if elm.z == z:
                return elm
        return None

    def elm_by_name(self, name: str) -> Element:
        """Get Element by name (normalized)."""
        nname: str = self.__normalize_key(name)
        for elm in self.values():
            if elm.name == nname:
                return elm
        return None
