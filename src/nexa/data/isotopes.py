from ruamel.yaml import YAML

from pathlib import Path
import re

from nexa.data import Isotope


class Isotopes(dict):
    """Class to store isotopes

    key: str - isotope symbol
    value: Isotope - isotope instance
    """

    type ISODATA = tuple[str, int, int, int, int, int, float]
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
            p = Path(__file__).resolve().parent.parent / "resources" / "tblSCALENuclideMass.yaml"
            yaml = YAML()
            raw_dict: dict[str, list] = yaml.load(p)
            # Store Isotope instances
            for key, value in raw_dict.items():
                sym = self.__normalize_key(value[0])
                value[0] = sym  # ensure symbol normalized
                iso_data = Isotope(tuple(value))
                super().__setitem__(sym, iso_data)

    def __getitem__(self, key: str) -> Isotope:
        try:
            return super().__getitem__(self.__normalize_key(key))
        except KeyError:
            return None

    # no setting
    def __setitem__(self, key: str, value: Isotope):
        raise RuntimeError("Setting not allowed")

    # no deletion
    def __delitem__(self, key: str):
        raise RuntimeError("Deletion not allowed")

    # no update
    def update(self, d: dict):
        raise RuntimeError("Update not allowed")

    # no pop
    def pop(self, key: str = None):
        raise RuntimeError("Deletion not allowed")

    # no popitem
    def popitem(self, key: str = None):
        raise RuntimeError("Deletion not allowed")

    # no setdefault
    def setdefault(self, key, value):
        raise RuntimeError("Setting not allowed")

    def __normalize_key(self, key: str):
        nkey: str = key.lower().replace(" ", "")
        nkey = re.sub(r"([a-z]+)(\d+)(m?)", r"\1-\2\3", nkey)
        return nkey

    def szaid(self, iso: str) -> int:
        return self[self.__normalize_key(iso)].szaid

    def zaid(self, iso: str) -> int:
        return self[self.__normalize_key(iso)].zaid

    def amu(self, iso: str) -> float:
        return self[self.__normalize_key(iso)].amu

    def s(self, iso: str) -> int:
        return self[self.__normalize_key(iso)].s

    def z(self, iso: str) -> int:
        return self[self.__normalize_key(iso)].z

    def a(self, iso: str) -> int:
        return self[self.__normalize_key(iso)].a

    def iso_by_szaid(self, szaid: int) -> Isotope | None:
        for iso in self.values():
            if iso.szaid == szaid:
                return iso
        return None

    def iso_by_zaid(self, zaid: int) -> Isotope | None:
        for iso in self.values():
            if iso.zaid == zaid:
                return iso
        return None

    def iso_by_s(self, s: int) -> list[Isotope]:
        iso_list = [iso for iso in self.values() if iso.s == s]
        iso_list.sort(key=lambda x: x.za * 10 + x.s)
        return iso_list

    def iso_by_z(self, z: int) -> list[Isotope]:
        iso_list = [iso for iso in self.values() if iso.z == z]
        iso_list.sort(key=lambda x: x.za * 10 + x.s)
        return iso_list

    def iso_by_a(self, a: int) -> list[Isotope]:
        iso_list = [iso for iso in self.values() if iso.a == a]
        iso_list.sort(key=lambda x: x.za * 10 + x.s)
        return iso_list

    def iso_by_element(self, element: str) -> list[Isotope]:
        normalized_element = element.lower()
        iso_list = [iso for iso in self.values() if iso.element() == normalized_element]
        # ensure metastable iso listed after ground state iso
        iso_list.sort(key=lambda x: x.za * 10 + x.s)
        return iso_list

    def szaid_to_zaid(self, szaid: int) -> int | None:
        iso = self.iso_by_szaid(szaid)
        if iso:
            return iso.zaid
        return None
    
    def zaid_to_szaid(self, zaid: int) -> int | None:
        iso = self.iso_by_zaid(zaid)
        if iso:
            return iso.szaid
        return None
    
    def zaid_to_symbol(self, zaid: int) -> str | None:
        iso = self.iso_by_zaid(zaid)
        if iso:
            return iso.symbol
        return None
    
    def szaid_to_symbol(self, szaid: int) -> str | None:
        iso = self.iso_by_szaid(szaid)
        if iso:
            return iso.symbol
        return None