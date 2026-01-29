from typing import List, Self, Tuple
from copy import deepcopy
from nexa.globals.enum import CompositionMode


class Isotope:
    """Class to store isotope data.

    Data maintained as read-only properties.
    Implements IConstituent interface.

    symbol: str - isotope symbol
    zaid: int - zaid
    amu: float - atomic mass units
    z: int - atomic number
    a: int - mass number
    """
    _SZAID = 0
    _ZAID = 1
    _S = 2
    _Z = 3
    _A = 4
    _AMU = 5
    # (szaid, mcnp_zaid, s, z, a, amu)
    _iso_data: Tuple[int, int, int, int, int, float] = ()
    _symbol: str = ""

    def __init__(self, symbol: str, iso_data: Tuple[int, int, int, int, int, float]) -> None:
        """All initialization is done in the constructor.  No updates are allowed."""
        self._symbol: str = symbol
        self._iso_data: Tuple[int, int, int, int, int, float] = iso_data

    def __str__(self):
        return f"symbol({self.symbol}) z({self.z}) a({self.a}) szaid({self.szaid}) amu({self.amu})"

    def __repr__(self):
        return f"symbol({self.symbol}) z({self.z}) a({self.a}) szaid({self.szaid}) amu({self.amu})"

    # region Properties
    # define readonly properties to disallow changes
    @property
    def symbol(self) -> str:
        """Isotope symbol (read only)."""
        return self._symbol

    @property
    def szaid(self) -> int:
        """Isotope SZA id (read only)."""
        return self._iso_data[self._SZAID]

    @property
    def zaid(self) -> int:
        """Isotope ZA id (read only)."""
        return self._iso_data[self._ZAID]

    @property
    def amu(self) -> float:
        """Isotope atomic mass [amu] (read only)."""
        return self._iso_data[self._AMU]

    @property
    def element(self) -> str:
        """Element symbol (read only)."""
        return self._symbol.split("-")[0]

    @property
    def s(self) -> int:
        """Metastable state (read only)."""
        return self._iso_data[self._S]

    @property
    def z(self) -> int:
        """Atomic number (read only)."""
        return self._iso_data[self._Z]

    @property
    def a(self) -> int:
        """Mass number (read only)."""
        return self._iso_data[self._A]

    @property
    def za(self) -> int:
        """z*1000 + a (read only). excludes s, not the same as zaid"""
        return self._iso_data[self._Z] * 1000 + self._iso_data[self._A]

    @property
    def is_metastable(self) -> bool:
        """Is isotope metastable? (read only)."""
        return self._iso_data[self._S] > 0

    # endregion

    # region Implement IConstituent
    @property
    def name(self) -> str:
        """Constituent name"""
        return self.symbol

    @property
    def level(self) -> int:
        """Constituent level"""
        return 0

    @property
    def sealed(self) -> bool:
        """Constituent sealed"""
        return True

    @property
    def a_value(self) -> float:
        """Constituent a value"""
        return self.amu

    @property
    def mode(self) -> CompositionMode:
        """Composition mode"""
        return None

    def copy(self, new_name: str = None) -> Self:
        """Deep copy the isotope.

        Cannot change the name but parameter is provided for compatibility with IConstituent.
        """
        if new_name is not None:
            raise ValueError("Cannot change the name of an isotope.")
        iso: Isotope = deepcopy(self)
        return iso

    def table(self) -> List[List[str | float]]:
        tbl = []
        tbl.append([])
        tbl[0] = []
        tbl[0].append(f"{self.name}")
        tbl[0].append(self.a_value)
        return tbl

    def display(self, f) -> None:
        tbl = self.table()
        for row in tbl:
            f.write("\t".join([(f"{col}" if type(col) is str else f"{col:8e}") for col in row]))
            f.write("\n")

    # endregion
