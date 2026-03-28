"""Interface for Isotope and Constituent

Whether to implement as Protocol ot ABC discussed here:
https://medium.com/@pouyahallaj/introduction-1616b3a4a637

"""

# Disbale name check on IConstituent while it is being defined
from __future__ import annotations

from typing import List, Optional, Protocol, Self, TextIO

from nexa.globals.enum import CompositionMode


# Interface for Isotope and Constituent
class IConstituent(Protocol):
    """Interface for Isotope and Constituent"""

    @property
    def name(self) -> str:
        """Constituent name"""
        ...

    @property
    def level(self) -> Optional[int]:
        """Constituent level"""
        ...

    @property
    def sealed(self) -> bool:
        """Constituent sealed"""
        ...

    def constituents(self) -> list[IConstituent]:
        """Get list of constituents"""
        ...

    def fraction(self, name: str, mode: CompositionMode) -> float:
        """Get fraction by name and mode"""
        ...

    @property
    def a_value(self) -> float:
        """Constituent a value"""
        ...

    @property
    def mode(self) -> CompositionMode:
        """Composition mode"""
        ...

    def copy(self, new_name: str = "") -> Self:
        """Deep copy the isotope."""
        ...

    def demote(self) -> Self:
        """Demote the constituent to the next lower level."""
        ...

    def promote(self) -> Self:
        """Promote the constituent to the next higher level."""
        ...

    def table(self) -> List[List[str]]: ...

    def display(self, file: Optional[TextIO] = None, to_string: bool = False) -> Optional[str]: ...
