"""Interface for Isotope and Constituent

Whether to implement as Protocol ot ABC discussed here:
https://medium.com/@pouyahallaj/introduction-1616b3a4a637

"""

from typing import Protocol, List, Self

from nexa.globals.enum import CompositionMode


# Interface for Isotope and Constituent
class IConstituent(Protocol):
    """Interface for Isotope and Constituent"""

    @property
    def name(self) -> str:
        """Constituent name"""
        pass

    @property
    def level(self) -> int:
        """Constituent level"""
        pass

    @property
    def is_sealed(self) -> bool:
        """Constituent sealed"""
        pass

    @property
    def a_value(self) -> float:
        """Constituent a value"""
        pass

    @property
    def mode(self) -> CompositionMode:
        """Composition mode"""
        pass

    def copy(self, new_name: str = None) -> Self:
        """Deep copy the isotope."""
        pass

    def table(self) -> List[List[str | float]]:
        pass

    def display(self, f) -> None:
        pass
