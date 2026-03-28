import sys
from copy import deepcopy
from io import StringIO
from typing import NamedTuple, Optional, Self, TextIO, cast

from nexa.globals.enum import CompositionMode
from nexa.interface import IConstituent

IsotopeData = NamedTuple(
    "IsotopeData",
    [
        ("symbol", str),
        ("szaid", int),
        ("zaid", int),
        ("s", int),
        ("z", int),
        ("a", int),
        ("amu", float),
    ],
)


class Isotope(IConstituent):
    """Class to store isotope data.

    Data maintained as read-only properties.
    Implements IConstituent interface.

    symbol: str - isotope symbol
    szaid: int - szaid
    zaid: int - MCNP zaid
    s: int - metastable state
    z: int - atomic number
    a: int - mass number
    amu: float - atomic mass units
    """

    # (symbol, szaid, mcnp_zaid, s, z, a, amu)
    _iso_data: IsotopeData

    def __init__(self, iso_data: IsotopeData) -> None:
        """All initialization is done in the constructor.  No updates are allowed."""
        self._iso_data = iso_data

    def __str__(self):
        return f"symbol({self.symbol}) z({self.z}) a({self.a}) szaid({self.szaid}) amu({self.amu})"

    def __repr__(self):
        return f"symbol({self.symbol}) z({self.z}) a({self.a}) szaid({self.szaid}) amu({self.amu})"

    # region Properties
    # define readonly properties to disallow changes
    @property
    def symbol(self) -> str:
        """Isotope symbol (read only)."""
        return self._iso_data.symbol

    @property
    def szaid(self) -> int:
        """Isotope SZA id (read only)."""
        return self._iso_data.szaid

    @property
    def zaid(self) -> int:
        """Isotope ZA id (read only)."""
        return self._iso_data.zaid

    @property
    def amu(self) -> float:
        """Isotope atomic mass [amu] (read only)."""
        return self._iso_data.amu

    @property
    def element(self) -> str:
        """Element symbol (read only)."""
        return self._iso_data.symbol.split("-")[0]

    @property
    def s(self) -> int:
        """Metastable state (read only)."""
        return self._iso_data.s

    @property
    def z(self) -> int:
        """Atomic number (read only)."""
        return self._iso_data.z

    @property
    def a(self) -> int:
        """Mass number (read only)."""
        return self._iso_data.a

    @property
    def za(self) -> int:
        """z*1000 + a (read only). excludes s, not the same as zaid"""
        return self._iso_data.z * 1000 + self._iso_data.a

    @property
    def is_metastable(self) -> bool:
        """Is isotope metastable? (read only)."""
        return self._iso_data.s > 0

    # endregion

    # region Implement IConstituent
    def constituents(self) -> list[IConstituent]:
        """Isotope has no constituents, return empty list."""
        return []

    def fraction(self, name: str, mode: CompositionMode) -> float:
        """Get fraction by name and mode"""
        return 0.0

    @property
    def name(self) -> str:
        """Constituent name"""
        return self.symbol

    @property
    def level(self) -> Optional[int]:
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
        return CompositionMode.Atom

    def copy(self, new_name: str = "") -> Self:
        """Deep copy the isotope.

        Cannot change the name but parameter is provided for compatibility with IConstituent.
        """
        if new_name:
            raise ValueError("Cannot change the name of an isotope.")
        iso: Isotope = deepcopy(self)
        return iso

    def demote(self) -> Self:
        raise RuntimeError("Cannot demote an isotope.")

    def promote(self) -> Self:
        raise RuntimeError("Cannot promote an isotope.")

    def table(self) -> list[list[str]]:
        tbl = []
        tbl.append([])
        tbl[0] = []
        tbl[0].append(f"{self.name}")
        tbl[0].append(f"{self.a_value:.6e}")
        return tbl

    def display(self, file: Optional[TextIO] = None, to_string: bool = False) -> Optional[str]:
        # Handle output destination
        if to_string:
            output_file = StringIO()
        elif file is None:
            output_file = sys.stdout
        else:
            output_file = file

        tbl = self.table()
        for row in tbl:
            output_file.write(
                "\t".join([(f"{col}" if type(col) is str else f"{col:6e}") for col in row])
            )
            output_file.write("\n")

        if to_string:
            return cast(StringIO, output_file).getvalue()

    # endregion
