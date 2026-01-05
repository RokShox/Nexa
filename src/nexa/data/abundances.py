from pathlib import Path
from typing import Dict

from ruamel.yaml import YAML

from nexa.globals import CompositionMode
from nexa.material import Constituent


class Abundances(dict):
    """Class to store natural abundances.

    Implements a singleton pattern.
    Imports Isotopes singleton so beware import loops.
    Subclasses dict to represent a Dict[str, Constituent] where:
        key: str - element symbol (normalized to lower case)
        value: Constituent - Constituent instance with the isotopes and their abundances
    """

    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern"""
        if not hasattr(cls, "instance"):
            # cls.instance = super(Abundances, cls).__new__(cls)
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        """Initialize the Abundances.

        For each element, create a level 1 Constituent instance with the isotopes and their
        abundances.
        Overrides dict methods that change values to prevent changes.
        """
        from nexa.data import Isotopes

        if not self._initialized:
            self._initialized = True
            self._isos = Isotopes()
            print("initializing Abundances")
            p = Path(__file__).resolve().parent.parent / "resources" / "tblNatIso.yaml"
            yaml = YAML()
            raw_dict: Dict[str, Dict[str, float]] = yaml.load(p)

            # Store instances
            for elm_sym, iso_dict in raw_dict.items():
                elm_sym = self.__normalize_key(elm_sym)
                elm_con = Constituent(elm_sym, CompositionMode.Atom)

                for iso_sym, afrac in iso_dict.items():
                    # iso_sym = Isotopes._normalize_key(iso_sym)
                    iso_con = self._isos[iso_sym]
                    elm_con.add(iso_con, float(afrac))
                elm_con.seal()

                super().__setitem__(self.__normalize_key(elm_sym), elm_con)

    def __getitem__(self, key: str) -> Constituent:
        try:
            return super().__getitem__(self.__normalize_key(key))
        except KeyError:
            return None

    # no setting
    def __setitem__(self, key: str, value: Constituent):
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
