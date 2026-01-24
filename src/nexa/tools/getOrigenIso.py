import os
import re
import sys
import code
from typing import Dict, List, Tuple
from pathlib import Path
import argparse

import nexa.scale.data.zaid as zaid
from nexa.data import Abundances, Elements, Isotope, Isotopes, LibEndf80, LibEndf81
from nexa.globals import CompositionMode
from nexa.material import Constituent
from nexa.scale.origen.origen_parser import (
    CaseOverview,
    NuclideConcentrationTable,
    NuclideType,
    OrigenConcentrationData,
    OrigenConcentrationUnits,
    OrigenParser,
)
from nexa.mcnp.input.cardM import MaterialCard

abund: Abundances = Abundances()
isos: Isotopes = Isotopes()
elms: Elements = Elements()


def main():
    """Parse Origen outputs for current burn step"""

    parser = argparse.ArgumentParser(prog="getOrigenIso", description="Parse Origen output files for isotope concentrations.")
    parser.add_argument("file", metavar="FILE", type=str, help="Path to the Origen output file to parse")
    parser.add_argument("--tempC", type=float, help="Burn material temperature in deg C", default=600.0)
    args = parser.parse_args()

    out_name = args.file
    case_name = Path(out_name).stem
    
    zaid_list = zaid.zaid()

    reCase: re = re.compile(r'^(?P<series>\w+)(?P<index>\d{2})b(?P<step>\d{2})z(?P<zone>\d{2})d(?P<depl>\d)$')
    match = reCase.match(case_name)
    if match:
        case_series: str = f"{match.group('series')}"
        case_index: int = int(f"{match.group('index')}")
        case_step: int = int(f"{match.group('step')}")
        case_zone: int = int(f"{match.group('zone')}")
        case_depl: int = int(f"{match.group('depl')}")
        next_step: int = case_step if case_depl == 0 else case_step + 1
        next_depl: int = 1 if case_depl == 0 else 0
    else:
        raise ValueError(f"Invalid Origen case name format: {case_name}")

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

    # First case is irradiation
    case: CaseOverview = cases[0]
    conc_data: OrigenConcentrationData = case.concentration_data_by_units(OrigenConcentrationUnits.ATOMS_PER_BARN_CM)
    if conc_data is None:
        raise ValueError(f"No concentration data found for ATOMS_PER_BARN_CM in case: {case.case_id}")

    nuclide_table: NuclideConcentrationTable = conc_data.nuclide_table(NuclideType.TOTAL)
    concentrations = nuclide_table.concentrations # Dict[str, List[float]]
 
    con: Constituent = Constituent(f"{case_name}Iso", CompositionMode.Atom)
    for isotope, concentration in concentrations.items():
        za = zaid_list.get_zaid(isotope)
        if za:
            if not LibEndf81.is_missing_zaid(za):
                # Get the last time step concentration
                con.add(isos[isotope], concentration[-1])
        else:
            print(f"Unknown isotope '{isotope}' with zaid {za} in file: {out_name}")
    con.seal()

    avogadro: float = 0.602214076
    atom_den: float = nuclide_table.totals[-1]
    mass_den: float = atom_den * con.a_value / avogadro
    # No need to print isos from a predictor case in Origen format
    # These isos will be used in the following predictor step 
    if case_depl == 1:
        origen_iso_name = f"{case_series}{case_index:02d}b{next_step:02d}z{case_zone:02d}d{next_depl}Isos"
        with open(f"{origen_iso_name}", "w", encoding="utf-8") as o:
            con_isos: Dict[str, Tuple[Isotope, float, float]] = con.isotopes()
            nper = 4
            line = "    "
            for i, (iso, mass_frac, atom_frac) in enumerate(con_isos.values()):
                line += f"{iso.zaid:6}={atom_frac*atom_den:.6e} "
                if (i+1) % nper == 0 or i == len(con_isos)-1:
                    print(line.rstrip(), file=o)
                    line = "    "
    
    # Write MCNP material cards for each burn zone all to one file
    mcnp_iso_name = f"{case_series}{case_index:02d}b{next_step:02d}d{next_depl}BurnMat"
    with open(f"{mcnp_iso_name}", "a" if case_zone > 1 else "w", encoding="utf-8") as o:
        ext81: str = LibEndf81.ext_by_tempC(args.tempC)
        m = MaterialCard(100+case_zone, con)
        m.set_library("NLIB", ext81)
        print(f"c    Zone {case_zone:d} MassDen {mass_den:10.6e} AtomDen {atom_den:10.6e}", file=o)
        print(m.to_string(), file=o)

    # """Run repl loop."""
    # code.interact(local=locals())

if __name__ == "__main__":
    main()
