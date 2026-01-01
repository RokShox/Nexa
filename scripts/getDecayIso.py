import re
import sys
from typing import Dict, List, Tuple

import nexa.scale.data.zaid as zaid
from nexa.data import Abundances, Elements, Isotope, Isotopes
from nexa.globals import CompositionMode
from nexa.material import Constituent
from nexa.scale.origen.origen_parser import (
    CaseOverview,
    NuclideConcentrationTable,
    NuclideType,
    OrigenConcentrationData,
    OrigenParser,
)

abund: Abundances = Abundances()
isos: Isotopes = Isotopes()
elms: Elements = Elements()


def main():
    """Parse Origen outputs for current burn step"""

    filebase = sys.argv[1]
    zones = 5
    zaid_list = zaid.zaid()

    con_by_zone: List[Constituent] = []

    for z in range(0, zones):
        zone = z + 1
        filename = f"{filebase}{zone:02d}z.out"

        try:
            with open(filename, "r", encoding="utf-8") as f:
                print(f"Processing file: {filename}")
                lines = f.readlines()
        except FileNotFoundError:
            print(f"File not found: {filename}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)

        parser = OrigenParser()
        cases = parser.parse_lines(lines)
        case: CaseOverview = cases[1]
        # print(case)
        conc_data: OrigenConcentrationData = case.concentrations[1]
        # print(conc_data)
        nuclide_table: NuclideConcentrationTable = conc_data.nuclide_table(NuclideType.TOTAL)
        # print(nuclide_table)
        concentrations = nuclide_table.concentrations
        con: Constituent = Constituent(f"Decay{zone:02d}z", CompositionMode.Atom)

        for isotope, concentration in concentrations.items():
            za = zaid_list.get_zaid(isotope)
            if za:
                if not ismissing(za):
                    con.add(isos[isotope], concentration[-1])
            else:
                print(f"Unknown isotope '{isotope}' in file: {filename}")
        con.seal()
        con_by_zone.append(con)

    with open(f"{filebase}DecayCon.txt", "w", encoding="utf-8") as o:
        # for z in range(zones):
        #     zone = z + 1
        #     con = con_by_zone[z]
        #     o.write(f"Zone {zone} Decay Concentrations:\n")
        #     o.write(con.display(""))
        #     o.write("\n")

        for z in range(zones):
            zone = z + 1
            con = con_by_zone[z]
            con_isos: Dict[str, Tuple[Isotope, float, float]] = con.isotopes()
            o.write(f"Zone {zone} Decay Concentrations:\n")
            o.write(f"{'Isotope':6} {'ZAID':>6} {'Mass Fraction':>13} {'Atom Fraction':>13}\n")
            for iso_name, (iso, mass_frac, atom_frac) in con_isos.items():
                o.write(f"{iso_name:6} {iso.zaid:>6d} {mass_frac:>.6e} {atom_frac:>.6e}\n")
            o.write("\n")


def ismissing(za):
    missing = [
        4010,
        38091,
        38092,
        39092,
        39093,
        40097,
        51127,
        52529,
        57141,
        59145,
    ]

    if za in missing:
        return True
    else:
        return False


if __name__ == "__main__":
    main()
