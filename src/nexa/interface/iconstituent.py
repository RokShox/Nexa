"""Interface for Isotope and Constituent.

Whether to implement as Protocol or ABC is discussed here:
https://medium.com/@pouyahallaj/introduction-1616b3a4a637

Implementations:
- Isotope: leaf node (level 0, always sealed). ``constituents()`` returns an
  empty list. ``fraction()`` always returns 0.0. ``demote()`` and ``promote()``
  raise RuntimeError.
- Constituent: composite node. ``a_value``, ``table()``, and ``display()``
  require the instance to be sealed; they raise RuntimeError otherwise.
"""

# Disable name check on IConstituent while it is being defined
from __future__ import annotations

from typing import Optional, Protocol, Self, TextIO

from nexa.globals.enum import CompositionMode


class IConstituent(Protocol):
    """Shared interface for Isotope (leaf) and Constituent (composite) nodes."""

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
        """Get fraction by name and mode.

        Isotope always returns 0.0 (leaf node with no children).
        """
        ...

    @property
    def a_value(self) -> float:
        """Average atomic mass [amu/atom].

        Isotope always returns ``amu``. Constituent requires ``sealed`` to be
        True; raises RuntimeError otherwise.
        """
        ...

    @property
    def mode(self) -> CompositionMode:
        """Composition mode"""
        ...

    def copy(self, new_name: str = "") -> Self:
        """Deep copy the constituent."""
        ...

    def demote(self) -> Self:
        """Demote the constituent to the next lower level.

        Isotope raises RuntimeError (cannot demote a leaf).
        """
        ...

    def promote(self) -> Self:
        """Promote the constituent to the next higher level.

        Isotope raises RuntimeError (cannot promote a leaf).
        """
        ...

    def table(self) -> list[list[str]]:
        """Build a tabular representation of the hierarchy.

        Constituent requires ``sealed`` to be True; raises RuntimeError
        otherwise.
        """
        ...

    def display(
        self, file: Optional[TextIO] = None, to_string: bool = False
    ) -> Optional[str]:
        """Display the tabular representation.

        Constituent requires ``sealed`` to be True; raises RuntimeError
        otherwise. Returns the formatted string when ``to_string`` is True.
        """
        ...
