from dataclasses import dataclass, field
from typing import Optional, cast

from nexa.data import Constituent
from nexa.globals import CompositionMode


@dataclass(init=False)
class Material:
    """Data class representing a material."""

    name: str
    composition: Optional[Constituent]

    description: str = ""
    source: str = ""
    _mass_density: Optional[float] = field(
        default=None, init=False, repr=False, compare=False
    )
    _atom_density: Optional[float] = field(
        default=None, init=False, repr=False, compare=False
    )

    def __init__(
        self,
        name: str,
        composition: Optional[Constituent],
        *,
        mass_density: Optional[float] = None,
        atom_density: Optional[float] = None,
        description: str = "",
        source: str = "",
    ) -> None:
        if (mass_density is None) == (atom_density is None):
            raise ValueError(
                "Exactly one of mass_density or atom_density must be provided"
            )

        self.name = name
        self.composition = composition
        self.description = description
        self.source = source
        self._mass_density = mass_density
        self._atom_density = atom_density

    @property
    def mass_density(self) -> Optional[float]:
        if (
            self._mass_density is None
            and self._atom_density is not None
            and self.composition is not None
        ):
            self._mass_density = self.composition.den_from_aden(self._atom_density)
        return self._mass_density

    @mass_density.setter
    def mass_density(self, value: float) -> None:
        self._mass_density = value
        # Invalidate cached atom density so it is recalculated from mass density.
        self._atom_density = None

    @property
    def atom_density(self) -> Optional[float]:
        """Calculate and cache atom density if composition is defined."""
        if (
            self._atom_density is None
            and self._mass_density is not None
            and self.composition is not None
        ):
            self._atom_density = self.composition.aden_from_den(self._mass_density)
        return self._atom_density

    @atom_density.setter
    def atom_density(self, value: float) -> None:
        self._atom_density = value
        # Invalidate cached mass density so it is recalculated from atom density.
        self._mass_density = None

    def display(self) -> str:
        assert self.composition is not None
        return (
            f"{self.name} {self.mass_density:.3f} g/cm^3 {self.atom_density:.5e} a/b-cm:\n"
            + cast(str, self.composition.display(to_string=True))
            + "\n"
        )

    @staticmethod
    def _composition_level(mat: "Material") -> int:
        if mat.composition is None or mat.composition.level is None:
            return 0
        return mat.composition.level

    @staticmethod
    def _required_mass_density(mat: "Material") -> float:
        den = mat.mass_density
        if den is None:
            raise ValueError(
                f"Mass density is undefined for material '{mat.name}' because composition is not set"
            )
        return den

    @staticmethod
    def _required_atom_density(mat: "Material") -> float:
        den = mat.atom_density
        if den is None:
            raise ValueError(
                f"Atom density is undefined for material '{mat.name}' because composition is not set"
            )
        return den

    @classmethod
    def create(
        cls,
        name: str,
        composition: Optional[Constituent],
        *,
        mass_density: Optional[float] = None,
        atom_density: Optional[float] = None,
        description: str = "",
        source: str = "",
    ) -> "Material":
        """Factory method"""
        return cls(
            name=name,
            composition=composition,
            mass_density=mass_density,
            atom_density=atom_density,
            description=description,
            source=source,
        )

    @classmethod
    def mix_mat_by_mass(
        cls,
        name: str,
        mats: list["Material"],
        masses: list[float],
        *,
        mass_density: Optional[float] = None,
        description: str = "",
        source: str = "",
    ) -> "Material":
        """Mix a set of materials by mass fractions to produce a new material."""

        if len(mats) != len(masses):
            raise ValueError("Number of materials and masses must match")

        total_mass = sum(masses)
        if total_mass == 0.0:
            raise ValueError("Total mass of mixture is zero")

        # compute mass fractions
        mass_fracs = [m / total_mass for m in masses]

        # compute nominal density
        nominal_density = 1.0 / sum(
            mf / cls._required_mass_density(m) for m, mf in zip(mats, mass_fracs)
        )
        mass_density = nominal_density if mass_density is None else mass_density

        # Sort materials by composition level in descending order so that lower level constituents are promoted to higher levels in the resulting composition
        sorted_pairs = sorted(
            zip(mats, mass_fracs),
            key=lambda x: cls._composition_level(x[0]),
            reverse=True,
        )

        # Create composition
        mode = CompositionMode.Mass
        con: Constituent = Constituent(name=name, mode=mode)
        for mat, mf in sorted_pairs:
            if mat.composition is None:
                raise ValueError(
                    f"Cannot mix material '{mat.name}' because composition is not set"
                )
            con.add(mat.composition, mf)
        con.seal()

        return cls.create(
            name=name,
            composition=con,
            mass_density=mass_density,
            description=description,
            source=source,
        )

    @classmethod
    def mix_mat_by_atom(
        cls,
        name: str,
        mats: list["Material"],
        atoms: list[float],
        *,
        atom_density: Optional[float] = None,
        description: str = "",
        source: str = "",
    ) -> "Material":
        """Mix a set of materials by atom fractions to produce a new material."""

        if len(mats) != len(atoms):
            raise ValueError("Number of materials and atoms must match")

        total_atoms = sum(atoms)
        if total_atoms == 0.0:
            raise ValueError("Total atoms of mixture is zero")

        # compute atom fractions
        atom_fracs = [a / total_atoms for a in atoms]

        # compute nominal atom density
        nominal_atom_density = sum(
            cls._required_atom_density(m) * af for m, af in zip(mats, atom_fracs)
        )
        atom_density = nominal_atom_density if atom_density is None else atom_density

        # Sort materials by composition level in descending order so that lower level constituents are promoted to higher levels in the resulting composition
        sorted_pairs = sorted(
            zip(mats, atom_fracs),
            key=lambda x: cls._composition_level(x[0]),
            reverse=True,
        )

        # Create composition
        mode = CompositionMode.Atom
        con: Constituent = Constituent(name=name, mode=mode)
        for mat, af in sorted_pairs:
            if mat.composition is None:
                raise ValueError(
                    f"Cannot mix material '{mat.name}' because composition is not set"
                )
            con.add(mat.composition, af)
        con.seal()

        return cls.create(
            name=name,
            composition=con,
            atom_density=atom_density,
            description=description,
            source=source,
        )
