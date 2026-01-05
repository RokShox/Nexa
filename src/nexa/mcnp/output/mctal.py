import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Self, Tuple

from nexa.mcnp.data import McnpParticleType, McnpParticleTypes, McnpTallyBinEnum
from nexa.util import MultiDimIterator


class LookFor(Enum):
    """Enumeration for parsing state."""

    HEAD = 1
    HEAD_HEADER = 10
    HEAD_TITLE = 11
    HEAD_NTAL = 12
    HEAD_TALLY = 13
    TALLY = 2
    TALLY_HEAD = 20
    TALLY_PARTICLE = 21
    TALLY_FC = 22
    TALLY_BIN = 23
    TALLY_BIN_DATA = 24
    TALLY_VALS = 25
    TALLY_TFC = 26
    KCODE = 3
    END = 4


class DetectorType(Enum):
    """Enumeration for MCNP tally detector types."""

    # tuple: (int mctal value, str description)
    NONE = (0, "none")
    POINT = (1, "point")
    RING = (2, "ring")
    FIP = (3, "pinhole radiograph (FIP)")
    FIR = (4, "transmitted image radiograph (rectangular, FIR)")
    FIC = (5, "transmitted image radiograph (cylindrical, FIC)")

    @classmethod
    def parse(cls, det_type: int) -> Self:
        """Convert integer to DetectorType enum."""

        for member in cls:
            if det_type == member.value[0]:
                return member
        raise ValueError(f"Unknown detector type: {det_type}")


class TallyModifierType(Enum):
    """Enumeration for MCNP tally modifier types."""

    # tuple: (int mctal value, str description)
    NONE = (0, "none")
    ASTERISK = (1, "*")
    PLUS = (2, "+")

    @classmethod
    def parse(cls, mod_type: int) -> Self:
        """Convert integer to TallyModifierType enum."""

        for member in cls:
            if mod_type == member.value[0]:
                return member
        raise ValueError(f"Unknown tally modifier type: {mod_type}")


@dataclass
class MctalTally:
    """Represents an MCNP tally in MCTAL file"""

    tally_num: int = 0
    particles: List[McnpParticleType] = field(default_factory=list)
    detector_type: DetectorType = DetectorType.NONE
    modifier_type: TallyModifierType = TallyModifierType.NONE
    # tuple is (McnpTallyBinEnum, bin count, bin qual, bin data)
    bin: Dict[str, Tuple[Enum, int, str, List[int | float]]] = field(default_factory=dict)
    fc_data: List[str] = field(default_factory=list)
    # tuple is (value, uncertainty)
    vals_data: List[Tuple[float, float]] = field(default_factory=list)
    # tuple is (nps, mean, error, fom)
    tfc_data: List[Tuple[int, float, float, float]] = field(default_factory=list)
    tfc_bin: Tuple[int, int, int, int, int, int, int, int] = field(default_factory=tuple)

    def total_vals(self) -> int:
        """Calculate total number of bins across all bin types."""
        total = 1
        for bin_tuple in self.bin.values():
            total *= bin_tuple[1] if bin_tuple[1] > 0 else 1
        return total

    def value(self, indices: Tuple[int, int, int, int, int, int, int, int]) -> Tuple[float, float]:
        """Get value and uncertainty for given bin indices.

        indices: List of indices corresponding to each bin type in order of bin dict
        """
        if not self.vals_data:
            raise RuntimeError("No VALS data available for this tally")

        if len(indices) != len(self.bin):
            raise ValueError("Number of indices does not match number of bin types")

        # Calculate flat index
        flat_index = 0
        multiplier = 1
        bin_keys = list(self.bin.keys())
        for i in reversed(range(len(bin_keys))):
            bin_key = bin_keys[i]
            bin_tuple = self.bin[bin_key]
            bin_count = 1 if bin_tuple[1] == 0 else bin_tuple[1]
            index = indices[i]
            if index < 0 or index >= bin_count:
                raise IndexError(f"Index {index} out of range for bin {bin_key}")
            flat_index += index * multiplier
            multiplier *= bin_count

        return self.vals_data[flat_index]

    def iterator(self) -> MultiDimIterator:
        """Get MultiDimIterator for iterating over VALS data."""
        sizes = {}
        for bin_key, bin_tuple in self.bin.items():
            sizes[bin_key] = 1 if bin_tuple[1] == 0 else bin_tuple[1]

        return MultiDimIterator(sizes)

    def __str__(self) -> str:
        return (
            f"MctalTally {self.tally_num}:\n"
            f"  Particles: {[p.name for p in self.particles]}\n"
            f"  Detector Type: {self.detector_type.name}\n"
            f"  Modifier Type: {self.modifier_type.name}\n"
            f"  Bins: { {k: (v[1], v[2]) for k, v in self.bin.items()} }\n"
            f"  FC Data Lines: {len(self.fc_data)}\n"
            f"  VALS Data Entries: {len(self.vals_data)}\n"
            f"  TFC Data Entries: {len(self.tfc_data)}\n"
            f"  TFC Bin: {self.tfc_bin}"
        )


@dataclass
class MctalOverview:
    """Represents contents of MCTAL file"""

    case: str = ""
    code_name: str = ""
    version: str = ""
    probid: str = ""
    knod: int = 0
    nps: int = 0
    rnr: int = 0
    title: str = ""
    tally_nums: List[int] = field(default_factory=list)
    tallies: Dict[int, MctalTally] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"MCTAL Overview:\n"
            f"Case: {self.case}\n"
            f"Code Name: {self.code_name}\n"
            f"Version: {self.version}\n"
            f"Problem ID: {self.probid}\n"
            f"Knod: {self.knod}\n"
            f"NPS: {self.nps:7.3e}\n"
            f"RNR: {self.rnr}\n"
            f"Title: {self.title}\n"
            f"Tally Numbers: {self.tally_nums}\n"
            f"Number of Tallies: {len(self.tallies)}"
        )


class MctalParser:
    """Parser for MCNP MCTAL output files."""

    def __init__(self):
        self._current_tally: MctalTally = None

    def parse_lines(self, lines: List[str]) -> MctalOverview:
        """Parse MCNP MCTAL file"""

        lf: LookFor = LookFor.HEAD
        lfHead: LookFor = LookFor.HEAD_HEADER

        for line in lines:
            # don't strip line since leading spaces are important
            if lf == LookFor.HEAD:
                if lfHead == LookFor.HEAD_HEADER:
                    # ex: "mcnp6.mp   6     12/18/25 12:51:58     7        59999293     45587388933"
                    parts = line.split()
                    if len(parts) == 7:
                        self._overview: MctalOverview = MctalOverview(
                            code_name=parts[0],
                            version=parts[1],
                            probid=parts[2] + " " + parts[3],
                            knod=int(parts[4]),
                            nps=int(parts[5]),
                            rnr=int(parts[6]),
                        )
                    else:
                        raise RuntimeError("Invalid MCTAL header")
                    lfHead = LookFor.HEAD_TITLE
                    continue

                if lfHead == LookFor.HEAD_TITLE:
                    # ex: " Ampera-X Analysis "
                    self._overview.title = line.strip()
                    lfHead = LookFor.HEAD_NTAL
                    continue

                if lfHead == LookFor.HEAD_NTAL:
                    # ex: "ntal     4"
                    parts = line.split()
                    # npert not handled yet
                    if len(parts) == 2:
                        ntal = int(parts[1])
                        npert = 0
                    elif len(parts) == 4:
                        ntal = int(parts[1])
                        npert = int(parts[3])
                    else:
                        raise RuntimeError("Invalid MCTAL NTAL line")
                    lfHead = LookFor.HEAD_TALLY
                    continue

                if lfHead == LookFor.HEAD_TALLY:
                    # ex: "    1    4   14   24"
                    # Read tally numbers
                    tally_nums = []
                    while len(tally_nums) < ntal:
                        parts = line.strip().split()
                        for part in parts:
                            tally_nums.append(int(part))
                        continue
                    if len(tally_nums) == ntal:
                        self._overview.tally_nums = tally_nums
                    else:
                        raise RuntimeError("Invalid MCTAL tally numbers")
                    lf = LookFor.TALLY
                    lfTally: LookFor = LookFor.TALLY_HEAD
                    continue

            if lf == LookFor.TALLY:
                if lfTally == LookFor.TALLY_HEAD:
                    # ex: "tally    1                   -1    0    0"
                    parts = line.split()
                    # TMESH tallies are NYI
                    if parts[0] == "tally" and len(parts) == 5:
                        tally_num = int(parts[1])
                        tally_particle = int(parts[2])
                        tally_det_type = DetectorType.parse(int(parts[3]))
                        tally_modifier = TallyModifierType.parse(int(parts[4]))
                        # Start new tally
                        self._current_tally = MctalTally(
                            tally_num=tally_num,
                            detector_type=tally_det_type,
                            modifier_type=tally_modifier,
                        )
                        # Check if particles can be determined from tally_particle or if on next line
                        if tally_particle > 0:
                            particles: List[McnpParticleType] = []
                            num = tally_particle
                            for i in range(3):
                                if num % 2 == 1:
                                    # some magic here since ipt for n, p, e = i+1
                                    particles.append(McnpParticleTypes.particle_by_ipt(i + 1))
                                num = num // 2
                            self._current_tally.particles = particles
                            lfTally = LookFor.TALLY_FC
                        else:
                            # read the particle string on next line
                            lfTally = LookFor.TALLY_PARTICLE
                    continue

                if lfTally == LookFor.TALLY_PARTICLE:
                    # ex: " 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
                    parts = line.strip().split()
                    if len(parts) == McnpParticleTypes.num_particles:
                        particles: List[McnpParticleType] = []
                        for part in parts:
                            try:
                                ipt = int(part)
                                if ipt > 0:
                                    particle = McnpParticleTypes.particle_by_ipt(ipt)
                                    particles.append(particle)
                            except KeyError:
                                raise RuntimeError(f"Invalid particle IPT in MCTAL tally: {part}")
                            except ValueError:
                                raise RuntimeError(
                                    f"Non-integer particle IPT in MCTAL tally: {part}"
                                )
                    else:
                        raise RuntimeError("Invalid MCTAL tally particle line")

                    self._current_tally.particles = particles
                    lfTally = LookFor.TALLY_FC
                    continue

                if lfTally == LookFor.TALLY_FC:
                    # ex: "     current by zone"
                    if line.startswith("     "):
                        # Process FC line
                        self._current_tally.fc_data.append(line.strip())
                        continue
                    else:
                        lfTally = LookFor.TALLY_BIN
                        # no continue here since we want to re-process this line

                if lfTally == LookFor.TALLY_BIN:
                    # ex: "f        7"
                    # Process bin lines
                    bin_match = re.match(r"([fdusmcet])([tu\s])\s+(\d+)", line)
                    if bin_match:
                        bin_key = bin_match.group(1).upper()
                        bin_type = McnpTallyBinEnum[bin_key]
                        bin_qual = bin_match.group(2).strip()
                        bin_count = int(bin_match.group(3))
                        bin_tuple = (bin_type, bin_count, bin_qual, [])
                    else:
                        raise RuntimeError(f"Invalid MCTAL {bin_key} line")
                    # Need to handle bin F when detector tally since no F data - NYI
                    if bin_count != 0 and McnpTallyBinEnum.has_mctal_data(bin_type):
                        expected = bin_count - 1 if bin_qual == "t" else bin_count
                        lfTally = LookFor.TALLY_BIN_DATA
                    elif bin_type == McnpTallyBinEnum.T:
                        self._current_tally.bin[bin_key] = bin_tuple
                        expected = self._current_tally.total_vals()
                        lfTally = LookFor.TALLY_VALS
                    else:
                        # save current bin_tuple and
                        # keep same lfTally, process next bin since no bin data to read
                        self._current_tally.bin[bin_key] = bin_tuple
                    continue

                if lfTally == LookFor.TALLY_BIN_DATA:
                    # ex: "      1      2      3      4      5      6      7"
                    # Read bin data lines
                    values_read = len(bin_tuple[3])
                    if values_read < expected:
                        parts = line.strip().split()
                        for part in parts:
                            if "." in part or "e" in part.lower():
                                bin_tuple[3].append(float(part))
                            else:
                                bin_tuple[3].append(int(part))
                    values_read = len(bin_tuple[3])
                    if values_read == expected:
                        # Finished reading bin data
                        self._current_tally.bin[bin_key] = bin_tuple
                        if bin_type == McnpTallyBinEnum.T:
                            expected = self._current_tally.total_vals()
                            lfTally = LookFor.TALLY_VALS
                        else:
                            lfTally = LookFor.TALLY_BIN
                    if values_read > expected:
                        raise RuntimeError("Too many bin data values in MCTAL tally")
                    continue

                if lfTally == LookFor.TALLY_VALS:
                    # ex: "vals"
                    if len(self._current_tally.vals_data) == 0 and line.startswith("vals"):
                        continue
                    # ex: "  3.00000E+09 0.5774  9.70000E+10 0.1015  1.34000E+11 0.0877  1.93000E+11 0.0724"
                    if len(self._current_tally.vals_data) < expected:
                        parts = line.strip().split()
                        if len(parts) % 2 != 0:
                            raise RuntimeError("Invalid VALS data line in MCTAL tally")
                        i = 0
                        while i < len(parts):
                            val = float(parts[i])
                            err = float(parts[i + 1]) if (i + 1) < len(parts) else 0.0
                            self._current_tally.vals_data.append((val, err))
                            i += 2
                    if len(self._current_tally.vals_data) == expected:
                        # Finished reading VALS data
                        lfTally = LookFor.TALLY_TFC
                    if len(self._current_tally.vals_data) > expected:
                        raise RuntimeError("Too many VALS data values in MCTAL tally")
                    continue

                if lfTally == LookFor.TALLY_TFC:
                    # ex: "tfc   10       1       1       1       1       1       2     253       1"
                    if line.startswith("tfc"):
                        parts = line.strip().split()
                        if len(parts) == 10 and parts[0] == "tfc":
                            ntfc = int(parts[1])
                            itfc = 0
                            # store tfc bin 0-based
                            self._current_tally.tfc_bin = tuple(int(part) - 1 for part in parts[2:])
                        else:
                            raise RuntimeError("Invalid TFC header line in MCTAL tally")
                    # ex: "       10000000  3.91204E+15  2.50865E-02  4.43250E+01"
                    elif re.match(r"\s*\d+", line):
                        if itfc < ntfc:
                            parts = line.strip().split()
                            if len(parts) != 4:
                                raise RuntimeError("Invalid TFC data line in MCTAL tally")
                            # nps, mean, error, fom
                            self._current_tally.tfc_data.append(
                                tuple(
                                    [
                                        int(parts[0]),
                                        float(parts[1]),
                                        float(parts[2]),
                                        float(parts[3]),
                                    ]
                                )
                            )
                            itfc += 1
                        if itfc == ntfc:
                            # Finished reading TFC data
                            self._overview.tallies[self._current_tally.tally_num] = (
                                self._current_tally
                            )
                            self._current_tally = None
                            lf = LookFor.TALLY
                            lfTally = LookFor.TALLY_HEAD
                    else:
                        raise RuntimeError("Invalid TFC data line in MCTAL tally")
                    continue

                if lfTally == LookFor.KCODE:
                    # NYI
                    continue

        return self._overview


if __name__ == "__main__":

    for file in sys.argv[1:]:
        try:
            with open(file, "r", encoding="utf-8") as f:
                print(f"Processing file: {file}")
                lines = f.readlines()
        except FileNotFoundError:
            print(f"File not found: {file}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)

        parser = MctalParser()
        mctal: MctalOverview = parser.parse_lines(lines)
        mctal.case = file
        print(mctal)
        for tal_num in mctal.tally_nums:
            tal = mctal.tallies.get(tal_num, None)
            if tal:
                print(f"Tally {tal.tally_num} has {len(tal.vals_data)} VALS entries")
                print(f"value at tfc bin {tal.tfc_bin}: {tal.value(tal.tfc_bin)}")

        # 'F', 'D', 'U', 'S', 'M', 'C', 'E', 'T'
        fixed = {"D": 0, "U": 0, "S": 0, "M": 0, "E": 252, "T": 0}
        free = ["C", "F"]
        tal = mctal.tallies.get(1, None)
        print(f"\nTally details:\n{tal}")
        if tal:
            print(f"\nIterating COORDS data for Tally 1 with free params {free} and fixed {fixed}:")
            it = tal.iterator()
            # for coord in it.iter_coords(free, fixed, format="tuple"):
            #     print(f"{coord}: {tal.value(coord)}\n")
            iter_gen = it.iter_coords(free, fixed, format="tuple")
            for c in range(it.sizes["C"]):
                for f in range(it.sizes["F"]):
                    coord = next(iter_gen)
                    print(f"{tal.value(coord)[0]:10.6e} {tal.value(coord)[1]:.4f} ", end="")
                print()

    # print(DetectorType.parse(0))
    # print(DetectorType.parse(1))
    # print(TallyModifierType.parse(2))
