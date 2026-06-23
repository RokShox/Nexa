from dataclasses import dataclass, field
from typing import Optional, cast

from nexa.data import Constituent
from nexa.globals import CompositionMode
from nexa.interface import IConstituent


@dataclass(init=False)
class Material:
    """Data class representing a material."""

    name: str
    composition: Optional[Constituent]

    description: str = ""
    source: str = ""
    _mass_density: Optional[float] = field(default=None, init=False, repr=False, compare=False)
    _atom_density: Optional[float] = field(default=None, init=False, repr=False, compare=False)

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
            raise ValueError("Exactly one of mass_density or atom_density must be provided")

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

        constituents: list[IConstituent] = []
        for mat in mats:
            if mat.composition is None:
                raise ValueError(f"Cannot mix material '{mat.name}' because composition is not set")
            constituents.append(mat.composition)

        con = Constituent.from_constituents(
            name=name,
            mode=CompositionMode.Mass,
            constituents=constituents,
            fractions=mass_fracs,
        )

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

        constituents: list[IConstituent] = []
        for mat in mats:
            if mat.composition is None:
                raise ValueError(f"Cannot mix material '{mat.name}' because composition is not set")
            constituents.append(mat.composition)

        con = Constituent.from_constituents(
            name=name,
            mode=CompositionMode.Atom,
            constituents=constituents,
            fractions=atom_fracs,
        )

        return cls.create(
            name=name,
            composition=con,
            atom_density=atom_density,
            description=description,
            source=source,
        )

    @classmethod
    def mix_mat_by_volume(
        cls,
        name: str,
        mats: list["Material"],
        volumes: list[float],
        *,
        mass_density: Optional[float] = None,
        description: str = "",
        source: str = "",
    ) -> "Material":
        """Mix a set of materials by volume fractions to produce a new material."""

        if len(mats) != len(volumes):
            raise ValueError("Number of materials and volumes must match")

        total_volume = sum(volumes)
        if total_volume == 0.0:
            raise ValueError("Total volume of mixture is zero")

        # compute volume fractions
        volume_fracs = [v / total_volume for v in volumes]

        # compute mass fractions
        mass_fracs: list[float] = []
        for m, vf in zip(mats, volume_fracs):
            den: float = cls._required_mass_density(m)
            mass_fracs.append(vf * den)
        nominal_mass_density = sum(mass_fracs)
        mass_fracs = [mf / nominal_mass_density for mf in mass_fracs]

        # override nominal mass density if mass density is provided
        mass_density = nominal_mass_density if mass_density is None else mass_density

        constituents: list[IConstituent] = []
        for mat in mats:
            if mat.composition is None:
                raise ValueError(f"Cannot mix material '{mat.name}' because composition is not set")
            constituents.append(mat.composition)

        con = Constituent.from_constituents(
            name=name,
            mode=CompositionMode.Mass,
            constituents=constituents,
            fractions=mass_fracs,
        )

        return cls.create(
            name=name,
            composition=con,
            mass_density=mass_density,
            description=description,
            source=source,
        )
