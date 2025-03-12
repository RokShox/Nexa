from ruamel.yaml import YAML

from pathlib import Path
from typing import List, Dict
import re

from nexa.data import Isotope


class Isotopes(dict):
    """Class to store isotopes

    key: str - isotope symbol
    value: Isotope - isotope instance
    """

    _initialized: bool = False

    def __new__(cls):
        if not hasattr(cls, "instance"):
            # cls.instance = super(Isotopes, cls).__new__(cls)
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            # print("initializing Isotopes")
            p = Path(__file__).resolve().parent.parent / "resources" / "tblMCNP6NuclideMass.yaml"
            yaml = YAML()
            raw_dict: Dict[str, List] = yaml.load(p)
            # Store Isotope instances
            for key, value in raw_dict.items():
                sym = self.__normalize_key(key)
                iso = Isotope(sym, value[0], value[1])
                super().__setitem__(sym, iso)

    def __getitem__(self, key: str) -> Isotope:
        try:
            return super().__getitem__(self.__normalize_key(key))
        except KeyError:
            return None

    # no setting
    def __setitem__(self, key: str, value: Isotope):
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
        nkey: str = key.lower().replace(" ", "")
        nkey = re.sub(r"([a-z]+)(\d+)(m?)", r"\1-\2\3", nkey)
        return nkey

    def zaid(self, iso: str) -> int:
        return self[self.__normalize_key(iso)].zaid

    def amu(self, iso: str) -> float:
        return self[self.__normalize_key(iso)].amu

    def z(self, iso: str) -> int:
        return self[self.__normalize_key(iso)].z

    def a(self, iso: str) -> int:
        return self[self.__normalize_key(iso)].a

    def iso_by_zaid(self, zaid: int) -> Isotope:
        for iso in self.values():
            if iso.zaid == zaid:
                return iso
        return None

    def iso_by_z(self, z: int) -> List[Isotope]:
        iso_list = [iso for iso in self.values() if iso.z == z]
        iso_list.sort(key=lambda x: x.zaid)
        return iso_list

    def iso_by_a(self, a: int) -> List[Isotope]:
        iso_list = [iso for iso in self.values() if iso.a == a]
        iso_list.sort(key=lambda x: x.z * 1000 + x.zaid % 1000)
        return iso_list

    def iso_by_element(self, element: str) -> List[Isotope]:
        normalized_element = element.lower()
        iso_list = [iso for iso in self.values() if iso.element() == normalized_element]
        # ensure metastable iso listed after ground state iso
        iso_list.sort(key=lambda x: x.a * 1000 + x.zaid % 1000)
        return iso_list
