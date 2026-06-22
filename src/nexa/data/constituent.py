from __future__ import annotations

import sys
from copy import deepcopy
from io import StringIO
from typing import Literal, NamedTuple, Optional, Self, TextIO, cast

# from ruamel.yaml import YAML
from nexa.data.isotope import Isotope
from nexa.globals import CompositionMode
from nexa.interface import IConstituent

CompositionEntry = NamedTuple(
    "CompositionEntry",
    [("constituent", IConstituent), ("mass", float), ("atom", float)],
)


class Constituent(IConstituent):
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

    # Exact value, see https://physics.nist.gov/cgi-bin/cuu/Value?na
    avogadro: float = 6.02214076e-01

    # region dunders
    def __init__(self, name: str, mode: CompositionMode = CompositionMode.Atom):
        self._name: str = name
        self._level: Optional[int] = None
        self._sealed: bool = False
        self._composition: dict[str, CompositionEntry] = {}
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
    def level(self) -> Optional[int]:
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
        c: IConstituent
        mass: float
        atom: float

        if self.mode == CompositionMode.Atom:
            for key, item in self._composition.items():
                c = item.constituent
                atom = item.atom
                mass = atom * c.a_value / self.a_value
                self._composition[key] = item._replace(mass=mass)
        else:
            for key, item in self._composition.items():
                c = item.constituent
                mass = item.mass
                atom = mass * self.a_value / c.a_value
                self._composition[key] = item._replace(atom=atom)

    def _normalize(self, mode: CompositionMode):
        """Normalize the mode fractions"""
        if mode == CompositionMode.Mass:
            total = sum(item.mass for item in self._composition.values())
            for key, item in self._composition.items():
                self._composition[key] = item._replace(mass=item.mass / total)
        elif mode == CompositionMode.Atom:
            total = sum(item.atom for item in self._composition.values())
            for key, item in self._composition.items():
                self._composition[key] = item._replace(atom=item.atom / total)

    # endregion

    # region public methods
    @classmethod
    def from_constituents(
        cls,
        name: str,
        mode: CompositionMode,
        constituents: list[IConstituent],
        fractions: list[float],
    ) -> Constituent:
        """Create a sealed constituent from a list of child constituents.

        Children are added in descending level order so that lower-level constituents are
        promoted rather than demoted when levels differ.

        Fractions are relative weights in the given ``mode`` (atom or mass stoichiometry) and
        are normalized during sealing.
        """
        if not constituents:
            raise ValueError("At least one constituent is required")
        if len(fractions) != len(constituents):
            raise ValueError("Number of constituents and fractions must match")

        sorted_pairs = sorted(
            zip(constituents, fractions),
            key=lambda pair: pair[0].level or 0,
            reverse=True,
        )

        con = cls(name, mode)
        for constituent, fraction in sorted_pairs:
            con.add(constituent, fraction)
        con.seal()
        return con

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
                [item.constituent.a_value * item.atom for item in self._composition.values()]
            )
        else:
            self._a_value = 1.0 / sum(
                [item.mass / item.constituent.a_value for item in self._composition.values()]
            )

        self._calculate_other_fraction()

    def unseal(self) -> None:
        """Unseal the constituent"""
        if not self.sealed:
            raise RuntimeError("Constituent not sealed")
        self._sealed = False

    def add(self, constituent: IConstituent, fraction: float) -> Self:
        """Add a constituent"""
        if self.sealed:
            raise RuntimeError("Constituent sealed")
        if constituent.name in self._composition:
            raise RuntimeError(f"Constituent {constituent.name} already exists")
        if fraction < 0.0:
            raise ValueError(f"Fraction {fraction} must be >= 0")
        if self.level is not None:
            assert constituent.level is not None
            if constituent.level != self.level - 1:
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

        else:
            assert constituent.level is not None
            self._level = constituent.level + 1

        if self.mode == CompositionMode.Atom:
            self._composition[constituent.name] = CompositionEntry(constituent, 0.0, fraction)
        else:
            self._composition[constituent.name] = CompositionEntry(constituent, fraction, 0.0)

        return self

    def mass_fraction(self, name: str) -> float:
        """Get mass fraction by name"""
        if name not in self._composition:
            raise ValueError(f"Constituent {name} not found")
        return self._composition[name].mass

    def atom_fraction(self, name: str) -> float:
        """Get atom fraction by name"""
        if name not in self._composition:
            raise ValueError(f"Constituent {name} not found")
        return self._composition[name].atom

    def fraction(self, name: str, mode: CompositionMode) -> float:
        """Get fraction by name and mode"""
        if name not in self._composition:
            raise ValueError(f"Constituent {name} not found")
        if mode == CompositionMode.Mass:
            return self._composition[name].mass
        elif mode == CompositionMode.Atom:
            return self._composition[name].atom
        else:
            raise ValueError(f"Invalid composition mode: {mode}")

    def constituents(self) -> list[IConstituent]:
        """Get list of constituents"""
        return [item.constituent for item in self._composition.values()]

    def constituent(self, name: str) -> IConstituent:
        """Get constituent by name"""
        if name not in self._composition:
            raise ValueError(f"Constituent {name} not found")
        return self._composition[name].constituent

    def isotopes(self) -> dict[str, tuple[Isotope, float, float]]:
        """Get isotopes dictionary"""
        con: Constituent = self
        if self.level != 1:
            con = self.flatten()

        isos: dict[str, tuple[Isotope, float, float]] = {}
        for iso in con.constituents():
            iso_frac_mass = con.mass_fraction(iso.name)
            iso_frac_atom = con.atom_fraction(iso.name)
            isos[iso.name] = (cast(Isotope, iso.copy()), iso_frac_mass, iso_frac_atom)

        return isos

    def copy(self, new_name: str = "") -> Constituent:
        """Deep copy the constituent.

        The copy is temporarily unsealed to change the name if necessary.
        """
        con: Constituent = deepcopy(self)
        if new_name:
            con.unseal()
            con._name = new_name
            con.seal()
        return con

    def promote(self) -> Constituent:
        """Promote the constituent"""
        if not self.sealed:
            raise RuntimeError("Constituent must be sealed")

        con: Constituent = Constituent(self.name, self.mode)
        con.add(self, 1.0)
        con.seal()
        return con

    def demote(self) -> Constituent:
        """Demote the constituent"""
        if not self.sealed:
            raise RuntimeError("Constituent must be sealed")

        assert self.level is not None
        if self.level < 2:
            return self

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

    def flatten(self) -> Constituent:
        if not self.sealed:
            raise RuntimeError("Constituent not sealed")

        con_flattened: Constituent = self
        assert con_flattened.level is not None
        while con_flattened.level > 1:
            con_flattened = con_flattened.demote()
            assert con_flattened.level is not None

        return con_flattened

    def den_from_aden(self, aden: float) -> float:
        """Calculate density from atom density"""
        if not self.sealed:
            raise RuntimeError("Constituent not sealed")
        assert self.level is not None
        if self.level < 1:
            raise RuntimeError(
                "Constituent must be level 1 or higher to calculate density from atom density"
            )
        return aden * self.a_value / self.avogadro

    def aden_from_den(self, den: float) -> float:
        """Calculate atom density from density"""
        if not self.sealed:
            raise RuntimeError("Constituent not sealed")
        assert self.level is not None
        if self.level < 1:
            raise RuntimeError(
                "Constituent must be level 1 or higher to calculate atom density from density"
            )
        return den * self.avogadro / self.a_value

    @staticmethod
    def normalize_path(path: str) -> str:
        """Return canonical path string with trimmed edges and single spaces around separators."""
        stripped = path.strip()
        if not stripped:
            raise ValueError("Path must not be empty")
        if ">" in stripped and "<" in stripped:
            raise ValueError("Path cannot mix '>' and '<' separators")
        if ">" in stripped:
            parts = [part.strip().lower() for part in stripped.split(">")]
            return " > ".join(parts)
        if "<" in stripped:
            parts = [part.strip().lower() for part in stripped.split("<")]
            return " < ".join(parts)
        return stripped.lower()

    def path_fractions(self, path: str) -> dict[str, tuple[float, float]]:
        """Resolve mass and atom fractions for constituent(s) identified by a path string.

        Paths may use downward ``>`` traversal from ``self.name``, upward ``<`` traversal from an
        isotope, or a single isotope name / ``*`` shorthand. Spaces around separators are not
        significant for parsing.

        Returns a dict mapping path strings to ``(mass_frac, atom_frac)`` relative to ``self``.
        Resolved branch keys use canonical downward form (``" > "`` separators) with segment
        names folded to lowercase. Segment matching is case-insensitive. When the query contains
        ``*`` or matches multiple branches, an additional entry is included whose key is the
        verbatim ``path`` argument and whose value is the weighted sum across resolved entries.

        Examples::

            fuel.path_fractions("Fuel > UO2 > O > o-16")
            fuel.path_fractions("Fuel > * > O")
            fuel.path_fractions("o-16 < O")
            fuel.path_fractions("o-16")
            fuel.path_fractions("*")
        """
        if not self.sealed:
            raise RuntimeError("Constituent not sealed")

        direction, segments = self._parse_fraction_path(path)
        if direction == "down":
            if segments[0].lower() != self.name.lower():
                raise ValueError(
                    f"Downward path must start with '{self.name}', got '{segments[0]}'"
                )
            results = self._resolve_down(segments)
        elif direction == "up":
            results = self._resolve_up(segments)
        else:
            results = self._resolve_single_token(segments[0])

        self._add_query_sum(results, path)
        return results

    # endregion

    # region path fraction helpers
    PathDirection = Literal["down", "up", "single"]

    @staticmethod
    def _parse_fraction_path(path: str) -> tuple[PathDirection, list[str]]:
        stripped = path.strip()
        if not stripped:
            raise ValueError("Path must not be empty")
        has_down = ">" in stripped
        has_up = "<" in stripped
        if has_down and has_up:
            raise ValueError("Path cannot mix '>' and '<' separators")
        if has_down:
            segments = [part.strip() for part in stripped.split(">")]
            return "down", segments
        if has_up:
            segments = [part.strip() for part in stripped.split("<")]
            return "up", segments
        return "single", [stripped]

    @staticmethod
    def _canonical_path(parts: list[str]) -> str:
        return " > ".join(part.lower() for part in parts)

    def _record_path_fraction(
        self,
        results: dict[str, tuple[float, float]],
        parts: list[str],
        mass_acc: float,
        atom_acc: float,
    ) -> None:
        key = self._canonical_path(parts)
        if key in results:
            existing_mass, existing_atom = results[key]
            results[key] = (existing_mass + mass_acc, existing_atom + atom_acc)
        else:
            results[key] = (mass_acc, atom_acc)

    def _matching_children(self, node: Constituent, token: str) -> list[IConstituent]:
        if token == "*":
            return node.constituents()
        token_fold = token.lower()
        return [child for child in node.constituents() if child.name.lower() == token_fold]

    def _enumerate_paths(self) -> list[tuple[list[str], float, float, IConstituent]]:
        entries: list[tuple[list[str], float, float, IConstituent]] = []

        def walk(
            node: IConstituent,
            parts: list[str],
            mass_acc: float,
            atom_acc: float,
        ) -> None:
            entries.append((parts, mass_acc, atom_acc, node))
            if node.level == 0:
                return
            parent = cast(Constituent, node)
            for child in parent.constituents():
                child_mass = mass_acc * parent.mass_fraction(child.name)
                child_atom = atom_acc * parent.atom_fraction(child.name)
                walk(child, parts + [child.name], child_mass, child_atom)

        walk(self, [self.name], 1.0, 1.0)
        return entries

    @staticmethod
    def _suffix_matches(path_parts: list[str], pattern: list[str]) -> bool:
        if len(pattern) > len(path_parts):
            return False
        suffix = path_parts[-len(pattern) :]
        for index, token in enumerate(pattern):
            path_token = suffix[-(index + 1)]
            if token == "*":
                continue
            if token.lower() != path_token.lower():
                return False
        return True

    def _resolve_down(self, segments: list[str]) -> dict[str, tuple[float, float]]:
        results: dict[str, tuple[float, float]] = {}

        if len(segments) == 1:
            results[self._canonical_path([self.name])] = (1.0, 1.0)
            return results

        def descend(
            node: Constituent,
            index: int,
            parts: list[str],
            mass_acc: float,
            atom_acc: float,
        ) -> None:
            token = segments[index]
            is_last = index == len(segments) - 1
            children = self._matching_children(node, token)
            if not children:
                return

            for child in children:
                child_mass = mass_acc * node.mass_fraction(child.name)
                child_atom = atom_acc * node.atom_fraction(child.name)
                child_parts = parts + [child.name]
                if is_last:
                    self._record_path_fraction(results, child_parts, child_mass, child_atom)
                elif child.level != 0:
                    descend(
                        cast(Constituent, child),
                        index + 1,
                        child_parts,
                        child_mass,
                        child_atom,
                    )

        descend(self, 1, [self.name], 1.0, 1.0)
        return results

    def _resolve_up(self, segments: list[str]) -> dict[str, tuple[float, float]]:
        results: dict[str, tuple[float, float]] = {}
        for path_parts, mass_acc, atom_acc, node in self._enumerate_paths():
            if node.level != 0:
                continue
            if node.name.lower() != segments[0].lower():
                continue
            if self._suffix_matches(path_parts, segments):
                self._record_path_fraction(results, path_parts, mass_acc, atom_acc)
        return results

    def _resolve_single_token(self, token: str) -> dict[str, tuple[float, float]]:
        if token == "*":
            results: dict[str, tuple[float, float]] = {}
            for path_parts, mass_acc, atom_acc, node in self._enumerate_paths():
                if node.level == 0:
                    self._record_path_fraction(results, path_parts, mass_acc, atom_acc)
            return results
        return self._resolve_up([token])

    @staticmethod
    def _add_query_sum(results: dict[str, tuple[float, float]], query_path: str) -> None:
        if not results:
            if "*" in query_path:
                results[query_path] = (0.0, 0.0)
            return

        add_sum = "*" in query_path or len(results) > 1
        if not add_sum:
            return

        total_mass = sum(mass for mass, _atom in results.values())
        total_atom = sum(atom for _mass, atom in results.values())
        results[query_path] = (total_mass, total_atom)

    # endregion

    # region view methods
    def table(self) -> list[list[str]]:
        if not self.sealed:
            raise RuntimeError("Constituent not sealed")

        tbl = []

        if self._level == 0:
            tbl.append([])
            tbl[0] = []
            tbl[0].append(f"{self.name}")
            tbl[0].append(f"{self.a_value:.6e}")
            return tbl

        else:
            assert self._level is not None
            oav: int = self._level + 1
            omf: int = oav + 1 + 2 * (self._level - 1)
            oaf: int = omf + 1

            for child in self.constituents():
                child_tbl = child.table()

                mfrac: float = self.mass_fraction(child.name)
                afrac: float = self.atom_fraction(child.name)

                if self._level == 1:
                    for i in range(len(child_tbl)):
                        child_tbl[i].insert(0, "")
                        child_tbl[i].append(f"{mfrac:.6e}")
                        child_tbl[i].append(f"{afrac:.6e}")
                        tbl.append(child_tbl[i])

                else:
                    for i in range(len(child_tbl)):
                        child_tbl[i].insert(0, "")
                        child_tbl[i].append(f"{mfrac * float(child_tbl[i][omf - 2]):.6e}")
                        child_tbl[i].append(f"{afrac * float(child_tbl[i][oaf - 2]):.6e}")
                        tbl.append(child_tbl[i])

            self_tbl = ["" for i in range(oaf + 1)]
            self_tbl[0] = f"{self.name}"
            self_tbl[oav] = f"{self.a_value:.6e}"
            self_tbl[omf] = f"{sum([self._composition[key].mass for key in self._composition]):.6e}"
            self_tbl[oaf] = f"{sum([self._composition[key].atom for key in self._composition]):.6e}"
            tbl.append(self_tbl)
            return tbl

    def display(self, file: Optional[TextIO] = None, to_string: bool = False) -> Optional[str]:
        tbl = self.table()
        # Shut up Pylance
        assert self.level is not None
        # Handle output destination
        if to_string:
            output_file = StringIO()
        elif file is None:
            output_file = sys.stdout
        else:
            output_file = file

        # Ugly hack
        min_sep = 3
        min_sym = len(f"Level {self.level}")
        spad = [
            max(max([len(row[self.level - i]) for row in tbl]), min_sym) + min_sep
            for i in range(self.level + 1)
        ]
        eprec = 6
        epad = eprec + 6 + min_sep
        fprec = 6
        fpad = fprec + 4 + min_sep
        if to_string or output_file.name == "<stdout>":
            # Header line 1
            # symbols
            output_file.write(f"{'Constituent':<{sum(spad)}}")

            # a value
            output_file.write(f"{'Avg Mass':>{fpad}}")

            # fractions
            for i in range(self.level):
                lev = f"Fraction in Level {i + 1}"
                output_file.write(f"{lev:>{2 * epad}}")
            output_file.write("\n")

            # Header line 2
            # symbols
            for i in range(self.level, 0, -1):
                lev = f"Level {i}"
                output_file.write(f"{lev:<{spad[i]}}")
            output_file.write(f"{'Isotope':<{spad[0]}}")

            # a value
            output_file.write(f"{'[amu/atom]':>{fpad}}")

            # fractions
            [output_file.write(f"{'Mass':>{epad}}{'Atom':>{epad}}") for i in range(self.level)]
            output_file.write("\n")
        else:
            # Header line 1
            # symbols
            output_file.write("Constituent\t")
            [output_file.write("\t") for i in range(self.level - 1, 0, -1)]
            output_file.write("\t")

            # a value
            output_file.write("Avg Mass\t")

            # fractions
            [output_file.write(f"Fraction in Level {i + 1}\t\t") for i in range(self.level)]
            output_file.write("\n")

            # Header line 2
            # symbols
            [output_file.write(f"Level {i}\t") for i in range(self.level, 0, -1)]
            output_file.write("Isotope\t")

            # a value
            output_file.write("[amu/atom]\t")

            # fractions
            [output_file.write("Mass\tAtom\t") for i in range(self.level)]
            output_file.write("\n")

        for row in tbl:
            if to_string or output_file.name == "<stdout>":
                # symbols
                output_file.write(
                    "".join([f"{row[i]:<{spad[self.level - i]}}" for i in range(self.level + 1)])
                )

                # a value
                output_file.write(
                    "".join(
                        [
                            (f"{col:>{fpad}}" if type(col) is str else f"{col:>{fpad}.{fprec}f}")
                            for col in [row[self.level + 1]]
                        ]
                    )
                )

                # fractions
                output_file.write(
                    "".join(
                        [
                            (f"{col:>{epad}}" if type(col) is str else f"{col:>{epad}.{eprec}e}")
                            for col in row[self.level + 2 :]
                        ]
                    )
                )
                output_file.write("\n")
            else:
                output_file.write(
                    "\t".join([(f"{col}" if type(col) is str else f"{col:6e}") for col in row])
                )
                output_file.write("\n")
        output_file.write("\n")

        if to_string:
            return cast(StringIO, output_file).getvalue()

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
