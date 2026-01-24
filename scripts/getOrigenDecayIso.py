import os
import re
import sys
import code
from typing import Dict, List, Tuple
from pathlib import Path

import nexa.scale.data.zaid as zaid
from nexa.data import Abundances, Elements, Isotope, Isotopes, LibEndf80, LibEndf81
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

    # run_dir = Path(r'D:\Projects\Ampera\Src\v1.0')
    run_dir = Path(r'D:\Projects\DeepFission\Src')
    os.chdir(run_dir)

    out_name = sys.argv[1] if len(sys.argv) > 1 else print ("Usage: getDecayIso.py <output_name>") & sys.exit(1)
    case_name = Path(out_name).stem
    
    filebase = sys.argv[1]
    zaid_list = zaid.zaid()

    try:
        with open(out_name, "r", encoding="utf-8") as f:
            print(f"Processing file: {out_name}")
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File not found: {out_name}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    parser = OrigenParser()
    cases = parser.parse_lines(lines) # List[CaseOverview]

    case: CaseOverview = cases[0]
    conc_data: OrigenConcentrationData = case.concentrations[1] # concentrations is List[OrigenConcentrationData]

    nuclide_table: NuclideConcentrationTable = conc_data.nuclide_table(NuclideType.TOTAL)
    concentrations = nuclide_table.concentrations # Dict[str, List[float]]
 
    # con: Constituent = Constituent(f"{case_name}Decay", CompositionMode.Atom)
    # for isotope, concentration in concentrations.items():
    #     za = zaid_list.get_zaid(isotope)
    #     if za:
    #         if not LibEndf81.is_missing_zaid(za):
    #             con.add(isos[isotope], concentration[-1])
    #     else:
    #         print(f"Unknown isotope '{isotope}' in file: {out_name}")
    # con.seal()


    # with open(f"{case_name}DecayCon.txt", "w", encoding="utf-8") as o:
    #     con_isos: Dict[str, Tuple[Isotope, float, float]] = con.isotopes()
    #     o.write(f"Case {case_name} Decay Concentrations:\n")
    #     o.write(f"{'Isotope':6} {'ZAID':>6} {'Mass Fraction':>13} {'Atom Fraction':>13}\n")
    #     for iso_name, (iso, mass_frac, atom_frac) in con_isos.items():
    #         o.write(f"{iso_name:6} {iso.zaid:>6d} {mass_frac:>.6e} {atom_frac:>.6e}\n")
    #     o.write("\n")



    """Run repl loop."""
    code.interact(local=locals())

if __name__ == "__main__":
    main()
