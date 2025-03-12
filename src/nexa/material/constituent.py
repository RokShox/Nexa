import re
import sys
from typing import List, Dict, Self
from copy import deepcopy

# from ruamel.yaml import YAML

from nexa.interface import IConstituent
from nexa.globals import CompositionMode


class Constituent:
    """Class to store constituent data.

    Level is inferred from the first added child.

    Child constituents are deep-copied to prevent changes to the original.

    Child fractions are normalized during sealing so atom stoichiometry or relative masses may be
    entered.

    Once sealed, the mass/atom fraction assigned to a child cannot be changed else it would affect
    the parent hierarchy.
    If event handlers could be attached to children, then parents could sense changes in children
    and update accordingly.
    See the Observer pattern described here
    https://gpttutorpro.com/how-to-create-and-handle-events-in-python/#google_vignette
    https://refactoring.guru/design-patterns/observer/python/example

    """

    # region dunders
    def __init__(self, name: str, mode: CompositionMode = CompositionMode.Atom):
        self._name: str = name
        self._level: int = None
        self._sealed: bool = False
        self._composition: Dict[str, List[IConstituent, float, float]] = {}
        self._a_value: float = 0.0
        self._mode: CompositionMode = mode

    def __str__(self):
        return " ".join(
            [
                f"name({self.name}):",
                f"level({self.level})",
                f"a({(self.a_value if self.sealed else 0.0):.4f})",
                f"sealed({self.sealed})",
            ]
        )

    def __repr__(self):
        return " ".join(
            [
                f"name({self.name}):",
                f"level({self.level})",
                f"a({(self.a_value if self.sealed else 0.0):.4f})",
                f"sealed({self.sealed})",
            ]
        )

    # endregion

    # region properties
    @property
    def name(self) -> str:
        """Constituent name"""
        return self._name

    @name.setter
    def name(self, name: str):
        """Constituent name"""
        if self._sealed:
            raise AttributeError("Cannot change sealed attribute")
        self._name = name

    @property
    def level(self) -> int:
        """Constituent level"""
        return self._level

    @property
    def sealed(self) -> bool:
        """Constituent sealed"""
        return self._sealed

    @property
    def a_value(self) -> float:
        """Constituent a value"""
        if not self.sealed:
            raise RuntimeError("Constituent not sealed")

        return self._a_value

    @property
    def mode(self) -> CompositionMode:
        """Composition mode"""
        return self._mode

    # endregion

    # region private methods
    def _calculate_other_fraction(self):
        """Calculate the other fractions"""
        if self.mode == CompositionMode.Atom:
            for c in self._composition.values():
                c[CompositionMode.Mass] = c[CompositionMode.Atom] * c[0].a_value / self.a_value
        else:
            for c in self._composition.values():
                c[CompositionMode.Atom] = c[CompositionMode.Mass] * self.a_value / c[0].a_value

    def _normalize(self, mode: CompositionMode):
        """Normalize the mode fractions"""

        total = sum([c[mode] for c in self._composition.values()])
        for c in self._composition.values():
            c[mode] /= total

    # endregion

    # region public methods
    def seal(self) -> None:
        """Seal the constituent"""
        if self.sealed:
            raise RuntimeError("Constituent already sealed")

        self._sealed = True

        # Normalize the fractions
        self._normalize(self.mode)

        # Calculate the a value
        if self.mode == CompositionMode.Atom:
            self._a_value = sum(
                [c[0].a_value * c[CompositionMode.Atom] for c in self._composition.values()]
            )
        else:
            self._a_value = 1.0 / sum(
                [c[CompositionMode.Mass] / c[0].a_value for c in self._composition.values()]
            )

        self._calculate_other_fraction()

    def add(self, constituent: IConstituent, fraction: float) -> Self:
        """Add a constituent"""
        if self.sealed:
            raise RuntimeError("Constituent sealed")
        if constituent.name in self._composition:
            raise RuntimeError(f"Constituent {constituent.name} already exists")
        if fraction <= 0.0:
            raise ValueError(f"Fraction {fraction} must be between >0")
        if self.level and constituent.level != self.level - 1:
            # raise ValueError(
            #     f"Constituent level {constituent.level} must be {self.level - 1}"
            # )
            if constituent.level > self.level - 1:
                while constituent.level != self.level - 1:
                    constituent = constituent.demote()
                    # print(f"Demoting {constituent.name}")
            elif constituent.level < self.level - 1:
                while constituent.level != self.level - 1:
                    constituent = constituent.promote()
                    # print(f"Promoting {constituent.name}")

        if self.level is None:
            self._level = constituent.level + 1

        if self.mode == CompositionMode.Atom:
            self._composition[constituent.name] = [constituent, 0.0, fraction]
        else:
            self._composition[constituent.name] = [constituent, fraction, 0.0]

        return self

    def mass_fraction(self, name: str) -> float:
        """Get mass fraction by name"""
        if name not in self._composition:
            raise ValueError(f"Constituent {name} not found")
        return self._composition[name][CompositionMode.Mass]

    def atom_fraction(self, name: str) -> float:
        """Get atom fraction by name"""
        if name not in self._composition:
            raise ValueError(f"Constituent {name} not found")
        return self._composition[name][CompositionMode.Atom]

    def fraction(self, name: str, mode: CompositionMode) -> float:
        """Get fraction by name and mode"""
        if name not in self._composition:
            raise ValueError(f"Constituent {name} not found")
        return self._composition[name][mode]

    def constituents(self) -> List[IConstituent]:
        """Get list of constituents"""
        return [value[0] for value in self._composition.values()]

    def constituent(self, name: str) -> IConstituent:
        """Get constituent by name"""
        if name not in self._composition:
            raise ValueError(f"Constituent {name} not found")
        return self._composition[name][0]

    def copy(self, new_name: str = None) -> IConstituent:
        """Deep copy the constituent.

        The copy is temporarily unsealed to change the name if necessary.
        """
        con: IConstituent = deepcopy(self)
        if new_name is not None:
            con._sealed = False
            con._name = new_name
            con.seal()
        return con

    def promote(self) -> IConstituent:
        """Promote the constituent"""
        if not self.sealed:
            raise RuntimeError("Constituent must be sealed")

        con: Constituent = Constituent(self.name, self.mode)
        con.add(self, 1.0)
        con.seal()
        return con

    def demote(self) -> IConstituent:
        """Demote the constituent"""
        if not self.sealed:
            raise RuntimeError("Constituent must be sealed")
        if self.level < 2:
            raise RuntimeError("Constituent level must be greater than 1")

        con_demoted: Constituent = Constituent(self.name, self.mode)
        isos = {}

        # For each child, add the grandchildren as children of the demoted constituent
        # If current level == 2, then the grandchildren are Isotopes.
        # These must be combined across children uniquely.
        if self.level == 2:
            for child in self.constituents():
                child_frac = self.fraction(child.name, self.mode)
                for gchild in child.constituents():
                    gchild_frac = child.fraction(gchild.name, self.mode) * child_frac
                    # Keep a dictionary of unique isotopes
                    try:
                        isos[gchild.name][1] += gchild_frac
                    except KeyError:
                        isos[gchild.name] = [gchild.copy(), gchild_frac]

            # total = sum([value[1] for value in isos.values()])
            # print(f"in demote: {total = }")
            for key, value in isos.items():
                con_demoted.add(value[0], value[1])

        else:
            for child in self.constituents():
                child_frac = self.fraction(child.name, self.mode)
                for gchild in child.constituents():
                    gchild_frac = child.fraction(gchild.name, self.mode) * child_frac
                    # Copy the grandchild and add it to the demoted constituent with a new name
                    new_name = f"{child.name}_{gchild.name}"
                    new_gchild = gchild.copy(new_name)
                    con_demoted.add(new_gchild, gchild_frac)

        con_demoted.seal()
        return con_demoted

    def flatten(self) -> IConstituent:
        if not self.sealed:
            raise RuntimeError("Constituent not sealed")

        con_flattened: IConstituent = self
        while con_flattened.level > 1:
            con_flattened = con_flattened.demote()

        return con_flattened

    # endregion

    # region view methods
    def table(self) -> List[List[str | float]]:
        if not self.sealed:
            raise RuntimeError("Constituent not sealed")

        tbl = []

        if self._level == 0:
            tbl.append([])
            tbl[0] = []
            tbl[0].append(f"{self.name}")
            tbl[0].append(self.a_value)
            return tbl

        else:
            for child in self.constituents():
                child_tbl = child.table()

                mfrac = self.mass_fraction(child.name)
                afrac = self.atom_fraction(child.name)
                oav = self._level + 1
                omf = oav + 1 + 2 * (self._level - 1)
                oaf = omf + 1

                if self._level == 1:
                    for i in range(len(child_tbl)):
                        child_tbl[i].insert(0, "")
                        child_tbl[i].append(mfrac)
                        child_tbl[i].append(afrac)
                        tbl.append(child_tbl[i])

                else:
                    for i in range(len(child_tbl)):
                        child_tbl[i].insert(0, "")
                        child_tbl[i].append(mfrac * child_tbl[i][omf - 2])
                        child_tbl[i].append(afrac * child_tbl[i][oaf - 2])
                        tbl.append(child_tbl[i])

            self_tbl = ["" for i in range(oaf + 1)]
            self_tbl[0] = f"{self.name}"
            self_tbl[oav] = self.a_value
            self_tbl[omf] = sum(
                [self._composition[key][CompositionMode.Mass] for key in self._composition]
            )
            self_tbl[oaf] = sum(
                [self._composition[key][CompositionMode.Atom] for key in self._composition]
            )
            tbl.append(self_tbl)
            return tbl

    def display(self, f=None) -> None:
        tbl = self.table()

        if f is None:
            f = sys.stdout

        # Ugly hack
        min_sep = 3
        min_sym = len(f"Level {self.level}")
        spad = [
            max(max([len(row[self.level - i]) for row in tbl]), min_sym) + min_sep
            for i in range(self.level + 1)
        ]
        eprec = 3
        epad = eprec + 6 + min_sep
        fprec = 4
        fpad = fprec + 4 + min_sep
        if f.name == "<stdout>":
            # Header line 1
            # symbols
            f.write(f"{'Constituent':<{sum(spad)}}")

            # a value
            f.write(f"{'Avg Mass':>{fpad}}")

            # fractions
            for i in range(self.level):
                lev = f"Fraction in Level {i+1}"
                f.write(f"{lev:>{2*epad}}")
            f.write("\n")

            # Header line 2
            # symbols
            for i in range(self.level, 0, -1):
                lev = f"Level {i}"
                f.write(f"{lev:<{spad[i]}}")
            f.write(f"{'Isotope':<{spad[0]}}")

            # a value
            f.write(f"{'[amu/atom]':>{fpad}}")

            # fractions
            [f.write(f"{'Mass':>{epad}}{'Atom':>{epad}}") for i in range(self.level)]
            f.write("\n")
        else:
            # Header line 1
            # symbols
            f.write("Constituent\t")
            [f.write("\t") for i in range(self.level - 1, 0, -1)]
            f.write("\t")

            # a value
            f.write("Avg Mass\t")

            # fractions
            [f.write(f"Fraction in Level {i+1}\t\t") for i in range(self.level)]
            f.write("\n")

            # Header line 2
            # symbols
            [f.write(f"Level {i}\t") for i in range(self.level, 0, -1)]
            f.write("Isotope\t")

            # a value
            f.write("[amu/atom]\t")

            # fractions
            [f.write("Mass\tAtom\t") for i in range(self.level)]
            f.write("\n")

        for row in tbl:
            if f.name == "<stdout>":
                # symbols
                f.write(
                    "".join([f"{row[i]:<{spad[self.level - i]}}" for i in range(self.level + 1)])
                )

                # a value
                f.write(
                    "".join(
                        [
                            (f"{col:>{fpad}}" if type(col) is str else f"{col:>{fpad}.{fprec}f}")
                            for col in [row[self.level + 1]]
                        ]
                    )
                )

                # fractions
                f.write(
                    "".join(
                        [
                            (f"{col:>{epad}}" if type(col) is str else f"{col:>{epad}.{eprec}e}")
                            for col in row[self.level + 2 :]
                        ]
                    )
                )
                f.write("\n")
            else:
                f.write("\t".join([(f"{col}" if type(col) is str else f"{col:8e}") for col in row]))
                f.write("\n")
        f.write("\n")

    # endregion

    # region serialization
    # Need to support serialization
    # def dump(self, yaml: YAML):
    #     '''Dump the constituent data'''
    #     return yaml.dump(self._composition)

    # def load(self, yaml: YAML, p: str):
    #     '''Load the constituent data'''
    #     raw_dict: Dict[str, List] = yaml.load(p)
    #     for key, value in raw_dict.items():
    #         self.add(Isotope(key, value[0], value[1]), value[2])
    # endregion
