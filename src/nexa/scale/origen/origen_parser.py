import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Self, Tuple


class LookFor(Enum):
    """Enumeration for parsing state."""

    CASE = 1
    CASE_HEAD = 10
    CASE_TITLE = 11
    CASE_UNITS = 12
    CASE_STEP = 13
    CONC = 2
    CONC_HEAD = 20
    CONC_TITLE = 21
    CONC_CUTOFF = 22
    CONC_TIME = 23
    CONC_ISO = 24
    CONC_TOTALS = 25
    END = 3


class NuclideType(Enum):
    """Enumeration for different nuclide types in ORIGEN output."""

    LIGHT_ELEMENTS = "light elements"
    ACTINIDES = "actinides"
    FISSION_PRODUCTS = "fission products"
    TOTAL = "total"

    @classmethod
    def parse(cls, type_str: str) -> Self:
        """Convert string to NuclideType enum."""
        type_str_lower = type_str.lower()
        for member in cls:
            if type_str_lower == member.value:
                return member
        raise ValueError(f"Unknown nuclide type: {type_str}")


class OrigenConcentrationUnits(Enum):
    """Enumeration for units used in ORIGEN concentration tables."""

    GRAMS = ("grams", "g")
    MOLES = ("moles", "mol")
    ATOMS_PER_BARN_CM = ("atoms/barn-cm", "a/b-cm")
    CURIES = ("curies", "Ci")
    BECQUERELS = ("becquerels", "Bq")
    ATOMS_PPM = ("atom fraction * 10^6", "ppm")
    WEIGHT_PPM = ("weight fraction * 10^6", "ppm")
    WATTS = ("watts", "W")
    G_WATTS = ("gamma watts", "W")
    M3_AIR = ("m3 air", "m3")
    M3_WATER = ("m3 water", "m3")

    @classmethod
    def parse(cls, unit_str: str) -> Self:
        """Convert string to OrigenConcentrationUnits enum."""
        unit_str_lower = unit_str.lower()
        for member in cls:
            if unit_str_lower == member.value[0]:
                return member
        raise ValueError(f"Unknown concentration unit: {unit_str}")


class OrigenTimeUnits(Enum):
    """Enumeration for time units used in ORIGEN output."""

    SECONDS = ("s", 1.0)
    MINUTES = ("min", 60.0)
    HOURS = ("hr", 3600.0)
    DAYS = ("d", 86400.0)
    YEARS = ("y", 365.25 * 86400.0)

    @classmethod
    def parse(cls, unit_str: str) -> Self:
        """Convert string to OrigenTimeUnits enum."""
        unit_str_lower = unit_str.lower()
        for member in cls:
            if unit_str_lower == member.value[0]:
                return member
        raise ValueError(f"Unknown time unit: {unit_str}")


@dataclass
class NuclideConcentrationTable:
    """Data class representing a complete nuclide concentration table from ORIGEN output."""

    nuclide_type: NuclideType
    case_id: str  # e.g., "2"
    case_index: int  # e.g., 2
    total_cases: int  # e.g., 2
    time_steps: List[float] = field(default_factory=list)
    concentrations: Dict[str, List[float]] = field(
        default_factory=dict
    )  # isotope -> concentrations
    time_units: Optional[OrigenTimeUnits] = None  # (unit, conversion_factor)
    conc_units: Optional[OrigenConcentrationUnits] = None  # (name, abbrev)
    cutoff: Optional[Tuple[str, int, float]] = None  # (type, step, value)
    totals: List[float] = field(default_factory=list)  # totals for each time step

    def __str__(self):
        return (
            f"  NuclideConcentrationTable for case '{self.case_id}' (#{self.case_index}/{self.total_cases}) "
            f"of type {self.nuclide_type.value} with units {self.conc_units.value[0] if self.conc_units is not None else 'Unknown'}:\n"
            f"    Time Steps: {self.time_steps} {self.time_units.value[0] if self.time_units is not None else 'Unknown'}\n"
            f"    Number of Isotopes: {len(self.concentrations)}\n"
            f"    Cutoff: {self.cutoff}\n"
            f"    Totals: {self.totals}\n"
        )

    @property
    def case_info(self) -> str:
        """Returns formatted case information string."""
        return f"'{self.case_id}' (#{self.case_index}/{self.total_cases})"


@dataclass
class OrigenConcentrationData:
    """Data class representing complete ORIGEN concentration output for a case."""

    case_id: str
    case_index: int
    total_cases: int # This is redundant but the data is in each table
    time_units: Optional[OrigenTimeUnits] = None  # (unit, conversion_factor)
    conc_units: Optional[OrigenConcentrationUnits] = None  # (name, abbrev)
    cutoff: Optional[Tuple[str, int, float]] = None  # (type, step, value)
    light_elements: Optional[NuclideConcentrationTable] = None
    actinides: Optional[NuclideConcentrationTable] = None
    fission_products: Optional[NuclideConcentrationTable] = None
    total: Optional[NuclideConcentrationTable] = None

    def __str__(self):
        return (
            f"OrigenConcentrationData for case '{self.case_id}' (#{self.case_index}/{self.total_cases}) "
            f"with units {self.conc_units.value[0] if self.conc_units is not None else 'Unknown'}:\n"
            f"  Light Elements:\n{self.light_elements if self.light_elements is not None else 'None'}\n"
            f"  Actinides:\n{self.actinides if self.actinides is not None else 'None'}\n"
            f"  Fission Products:\n{self.fission_products if self.fission_products is not None else 'None'}\n"
            f"  Total:\n{self.total if self.total is not None else 'None'}\n"
        )

    def nuclide_table(self, nuclide_type: NuclideType) -> Optional[NuclideConcentrationTable]:
        """Get the nuclide concentration table for the specified nuclide type."""

        if nuclide_type == NuclideType.LIGHT_ELEMENTS:
            return self.light_elements
        elif nuclide_type == NuclideType.ACTINIDES:
            return self.actinides
        elif nuclide_type == NuclideType.FISSION_PRODUCTS:
            return self.fission_products
        elif nuclide_type == NuclideType.TOTAL:
            return self.total
        else:
            raise ValueError(f"Unknown nuclide type: {nuclide_type}")

        return None

    def set_nuclide_table(
        self, nuclide_type: NuclideType, table: NuclideConcentrationTable
    ) -> None:
        """Set the nuclide concentration table for the specified nuclide type."""

        if nuclide_type == NuclideType.LIGHT_ELEMENTS:
            self.light_elements = table
        elif nuclide_type == NuclideType.ACTINIDES:
            self.actinides = table
        elif nuclide_type == NuclideType.FISSION_PRODUCTS:
            self.fission_products = table
        elif nuclide_type == NuclideType.TOTAL:
            self.total = table
        else:
            raise ValueError(f"Unknown nuclide type: {nuclide_type}")
        return None


@dataclass
class CaseStep:
    """Data class representing a time step in a case."""

    step_number: int
    t0: float
    t1: float
    dt_s: float  # delta t in seconds
    t_s: float
    flux: float
    fluence: float
    power_mw: float
    energy_mwd: float
    time_units: Optional[OrigenTimeUnits] = None

    def __str__(self):
        return (
            f"Step {self.step_number}: t0={self.t0}, t1={self.t1}, dt_s={self.dt_s}, "
            f"t_s={self.t_s}, flux={self.flux}, fluence={self.fluence}, power_mw={self.power_mw}, "
            f"energy_mwd={self.energy_mwd}, time_units={self.time_units.value[0] if self.time_units is not None else 'Unknown'}"
        )


@dataclass
class CaseOverview:
    """Data class representing overview information for a case."""

    case_id: str
    case_index: int
    total_cases: int
    title: str = ""
    time_units: Optional[OrigenTimeUnits] = None
    # Do not use an index into steps as an index into concentrations table, as the latter includes t=0
    # index i into steps corresponds to step i+1 since it is zero-based
    # concentrations at the end of index i into steps are at index i+1 in concentrations
    # concentrations at the beginning of index i into steps are at index i in concentrations
    # maybe to use step number as index into steps (i.e., 1-based)
    # Better to use time_steps in NuclideConcentrationTable for finding appropriate concentration
    steps: List[CaseStep] = field(default_factory=list)
    concentrations: List[OrigenConcentrationData] = field(default_factory=list)

    def __str__(self):
        return f"Case '{self.case_id}' (#{self.case_index}/{self.total_cases}): {self.title}"

    def concentration_data_by_units(
        self, conc_units: OrigenConcentrationUnits
    ) -> Optional[OrigenConcentrationData]:
        """Get the concentration data for the specified concentration units."""

        for conc_data in self.concentrations:
            if conc_data.conc_units == conc_units:
                return conc_data
        return None

class OrigenParser:
    """Parser for ORIGEN nuclide concentration tables."""

    def __init__(self):
        self.current_case: Optional[CaseOverview] = None
        self.current_data: Optional[OrigenConcentrationData] = None
        self.current_table: Optional[NuclideConcentrationTable] = None

    def safe_float(self, value_str: str) -> float:
        """Convert string to float, handling missing 'E' in scientific notation."""

        if re.search(r"[+-][\d]{3}$", value_str):
            value_str = value_str[:-4] + "E" + value_str[-4:]
        return float(value_str)


    def parse_lines(self, lines: List[str]) -> List[CaseOverview]:
        """
        Parse lines from ORIGEN output containing nuclide concentration tables.

        Args:
            lines: List of strings from ORIGEN output file

        Returns:
            List[CaseOverview] with parsed data
        """

        self.cases: List[CaseOverview] = []
        self.current_case = None
        self.current_data = None
        self.current_table = None
        lf: LookFor = LookFor.CASE
        lfCase: LookFor = LookFor.CASE_HEAD
        lfConc: LookFor

        for line in lines:
            # Preserve leading spaces for matching
            line = line.rstrip()
            if not line:
                continue

            if lf == LookFor.CASE:
                if lfCase == LookFor.CASE_HEAD:
                    case_match = re.match(
                        r"^=\s+History overview for case '(\w+)' \(#(\d+)/(\d+)\)\s+=$", line
                    )
                    if case_match:
                        case_id = case_match.group(1)
                        case_index = int(case_match.group(2))
                        total_cases = int(case_match.group(3))
                        self.current_case = CaseOverview(
                            case_id=case_id,
                            case_index=case_index,
                            total_cases=total_cases,
                        )
                        lfCase = LookFor.CASE_TITLE
                    continue

                if lfCase == LookFor.CASE_TITLE:
                    # title_match = re.match(r"^=   (.+)\s+=$", line)
                    # if title_match:
                        # title = title_match.group(1)
                        # self.current_case.title = title
                        # print(f"Processing case: {title} '{case_id}' (#{case_index}/{total_cases})")
                        # lfCase = LookFor.CASE_UNITS
                    # else:
                    #     # Expected title line
                    #     raise ValueError(f"Invalid case title line format: {line}")
                    title = line[1:-1].strip()
                    self.current_case.title = title
                    print(f"Processing case: {title} '{case_id}' (#{case_index}/{total_cases})")
                    lfCase = LookFor.CASE_UNITS
                    continue

                if lfCase == LookFor.CASE_UNITS:
                    time_units_match = re.match(r"^\s+\(-\)\s+\((\w+)\)\s+", line)
                    if time_units_match:
                        time_units = OrigenTimeUnits.parse(time_units_match.group(1))
                        self.current_case.time_units = time_units
                        lfCase = LookFor.CASE_STEP
                    continue

                if lfCase == LookFor.CASE_STEP:
                    # Expecting case step lines
                    step_match = re.match(r"^\s+(\d+)\s+", line)
                    if step_match:
                        parts = line.split()
                        if len(parts) == 9:
                            step_number = int(parts[0])
                            t0 = float(parts[1])
                            t1 = float(parts[2])
                            dt_s = float(parts[3])
                            t_s = float(parts[4])
                            flux = float(parts[5])
                            fluence = float(parts[6])
                            power_mw = float(parts[7])
                            energy_mwd = float(parts[8])
                            step = CaseStep(
                                step_number=step_number,
                                t0=t0,
                                t1=t1,
                                dt_s=dt_s,
                                t_s=t_s,
                                flux=flux,
                                fluence=fluence,
                                power_mw=power_mw,
                                energy_mwd=energy_mwd,
                                time_units=self.current_case.time_units,
                            )
                            self.current_case.steps.append(step)
                        else:
                            raise ValueError(f"Invalid case step line format: {line}")
                    else:
                        # End of case steps
                        lf = LookFor.CONC
                        lfConc = LookFor.CONC_HEAD
                        if self.current_case is not None:
                            self.cases.append(self.current_case)
                    continue

            if lf == LookFor.CONC:
                if lfConc == LookFor.CONC_HEAD:
                    # Check for last table in this case
                    if re.match(r"^=\s+Overall neutron balance", line) or re.match(
                        r"^=\s+Absolute fission rates", line
                    ):
                        # Finalize last data
                        if self.current_case is not None and self.current_data is not None:
                            self.current_case.concentrations.append(self.current_data)
                            self.current_data = None
                            self.current_case = None
                        lf = LookFor.CASE
                        lfCase = LookFor.CASE_HEAD
                        continue

                    # Check for sublib table header
                    sublib_match = re.match(
                        r"^=+\s+Nuclide concentrations in ([\w\s/-]+),\s+([\w\s]+)\s+for case '(\w+)' \(#(\d+)/(\d+)\)\s+=",
                        line,
                    )
                    # Check for total table header
                    total_match = re.match(
                        r"^=+\s+Nuclide concentrations in ([\w\s/-]+) for case '(\w+)' \(#(\d+)/(\d+)\)\s+=",
                        line,
                    )
                    if sublib_match or total_match:
                        if sublib_match:
                            units = OrigenConcentrationUnits.parse(sublib_match.group(1))
                            nuclide_type = NuclideType.parse(sublib_match.group(2))
                            case_id = sublib_match.group(3)
                            case_index = int(sublib_match.group(4))
                            total_cases = int(sublib_match.group(5))
                        elif total_match:
                            units = OrigenConcentrationUnits.parse(total_match.group(1))
                            nuclide_type = NuclideType.parse("total")
                            case_id = total_match.group(2)
                            case_index = int(total_match.group(3))
                            total_cases = int(total_match.group(4))

                        if self.current_data is None:
                            self.current_data = OrigenConcentrationData(
                                case_id=case_id,
                                case_index=case_index,
                                total_cases=total_cases,
                                conc_units=units,
                            )
                        elif self.current_data.conc_units != units:
                            # This table has different units than previous tables for this case
                            # Finalize previous data
                            self.current_case.concentrations.append(self.current_data)
                            # Start new data
                            self.current_data = OrigenConcentrationData(
                                case_id=case_id,
                                case_index=case_index,
                                total_cases=total_cases,
                                conc_units=units,
                            )

                        # Start new table
                        self.current_table = NuclideConcentrationTable(
                            nuclide_type=nuclide_type,
                            case_id=case_id,
                            case_index=case_index,
                            total_cases=total_cases,
                            conc_units=units,
                        )

                        # Next line is case title
                        lfConc = LookFor.CONC_TITLE
                    continue

                if lfConc == LookFor.CONC_TITLE:
                    # Expecting title line
                    # title_match = re.match(r"^=\s+(\w+(?:\s+\w+)*)\s+=$", line)
                    # if title_match:
                    #     title = title_match.group(1)
                    #     # Currently not storing title in table, but could be added if needed
                    #     if title != self.current_case.title:
                    #         raise ValueError(
                    #             f"Warning: Concentration table title '{title}' does not match case title '{self.current_case.title}'"
                    #         )
                    #     lfConc = LookFor.CONC_CUTOFF
                    # else:
                    #     raise ValueError(f"Invalid concentration case title line format: {line}")
                    title = line[1:-1].strip()
                    if title != self.current_case.title:
                        raise ValueError(
                            f"Warning: Concentration table title '{title}' does not match case title '{self.current_case.title}'"
                        )
                    lfConc = LookFor.CONC_CUTOFF
                    continue

                if lfConc == LookFor.CONC_CUTOFF:
                    # Expecting cutoff line
                    cutoff_match = re.match(
                        r"^\s+\((absolute|relative) cutoff;\s(integral|concentration).*>\s+([\d.Ee+-]+)",
                        line,
                    )
                    if cutoff_match:
                        cutoff_type = cutoff_match.group(1)
                        if cutoff_match.group(2) == "integral":
                            cutoff_step = -1
                        else:
                            # Note re.match starts at beginning of string, use re.search instead
                            step_match = re.search(
                                r"step\s+(\d+)",
                                line,
                            )
                            if step_match:
                                cutoff_step = int(step_match.group(1))
                            else:
                                raise ValueError(f"Invalid cutoff step format: {line}")
                        cutoff_value = float(cutoff_match.group(3))

                        self.current_table.cutoff = (cutoff_type, cutoff_step, cutoff_value)
                        if self.current_data.cutoff is None:
                            self.current_data.cutoff = self.current_table.cutoff
                        elif self.current_data.cutoff != self.current_table.cutoff:
                            raise ValueError(
                                f"Cutoff mismatch between current data {self.current_data.cutoff} and table {self.current_table.cutoff}"
                            )
                        lfConc = LookFor.CONC_TIME
                    continue

                if lfConc == LookFor.CONC_TIME:
                    # Expecting time steps line
                    time_match = re.match(r"^\s+([\d.Ee+-]+)(\w+)", line)
                    if time_match:
                        time_units = OrigenTimeUnits.parse(time_match.group(2))
                        # Extract time values
                        time_values = re.findall(r"([\d.Ee+-]+)", line)
                        self.current_table.time_steps = [float(t) for t in time_values]
                        self.current_table.time_units = time_units
                        if self.current_data.time_units is None:
                            self.current_data.time_units = time_units
                        lfConc = LookFor.CONC_ISO
                    continue

                if lfConc == LookFor.CONC_ISO:
                    # Parse isotope concentration lines
                    if re.match(r"^\s+[a-z]{1,2}-\d+", line, re.IGNORECASE):
                        parts = line.split()
                        isotope = parts[0]
                        # Stupid SCALE sometimes leaves out the "E" in scientific notation if exponent has 3 digits
                        conc_values = [self.safe_float(part) for part in parts[1:]]

                        # Check if number of concentrations matches time steps
                        if len(conc_values) != len(self.current_table.time_steps):
                            raise ValueError(
                                f"Concentration count {len(conc_values)} does not match time step count {len(self.current_table.time_steps)} for isotope {isotope}"
                            )

                        if isotope in self.current_table.concentrations:
                            raise ValueError(
                                f"Duplicate isotope entry '{isotope}' in table for case '{self.current_table.case_id}'"
                            )
                        else:
                            self.current_table.concentrations[isotope] = conc_values

                    else:
                        # End of isotope concentrations
                        lfConc = LookFor.CONC_TOTALS
                    continue

                if lfConc == LookFor.CONC_TOTALS:
                    # Parse totals line
                    if re.match(r"^\s+totals", line):
                        parts = line.split()
                        total_values = [self.safe_float(part) for part in parts[1:]]
                        self.current_table.totals = total_values
                        # Assign table to appropriate field
                        self.current_data.set_nuclide_table(
                            self.current_table.nuclide_type, self.current_table
                        )
                        # Reset for next table
                        self.current_table = None
                        lfConc = LookFor.CONC_HEAD
                    continue

        return self.cases


if __name__ == "__main__":
    import sys

    cases: List[CaseOverview]
    case: CaseOverview

    # Example usage
    # if len(sys.argv) < 2:
    #     print(f"Usage: {sys.argv[0]} <origen_output_file>")
    #     sys.exit(1)
    # filename = sys.argv[1]
    filename = "sample.txt"

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        parser = OrigenParser()
        cases = parser.parse_lines(lines)
        for case in cases:
            print(case)
            for step in case.steps:
                print(f"  {step}")
            for concentration_data in case.concentrations:
                print(f"  {concentration_data}")

    except FileNotFoundError:
        print(f"File not found: {filename}")
        sys.exit(1)
