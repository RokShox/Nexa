import sys
import re
from typing import List, Dict, Tuple
import nexa.scale.data.zaid as zaid
from nexa.data import Isotope, Isotopes, Elements, Abundances
from nexa.globals import CompositionMode
from nexa.material import Constituent


abund: Abundances = Abundances()
isos: Isotopes = Isotopes()
elms: Elements = Elements()

def main():
    # if len(sys.argv) < 2:
    #     print(f"Usage: {sys.argv[0]} <filename>")
    #     sys.exit(1)

    filebase = sys.argv[1]
    zones = 5
    zaid_list = zaid.zaid()

    lf = {'Bgn': 0, 'End': 1}
 
    conc = {}

    # patBgn = r"Nuclide concentrations in atoms/barn-cm for case '1' (#1/2)"
    patBgn = r"Nuclide concentrations in grams for case '2'"
    patEnd = r"------------"

    try:
        regBgn = re.compile(patBgn)
        regEnd = re.compile(patEnd)
    except re.error as e:
        print(f"Invalid regex pattern: {e}")
        sys.exit(1)

    con_by_zone: List[Constituent] = []

    for z in range(0, zones):
        zone = z + 1
        filename = f"{filebase}{zone:02d}z.out"

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                print(f"Processing file: {filename}")
                lookFor = lf['Bgn']
                for line in f:
                    if lookFor == lf['Bgn']:
                        if m := regBgn.search(line):
                            # print(f"Found start marker in file: {filename}")
                            for _ in range(5):
                                next(f, None)

                            con: Constituent = Constituent(f"Decay{zone:02d}z", CompositionMode.Atom)
                            lookFor = lf['End']

                    elif lookFor == lf['End']:
                        if m := regEnd.search(line):
                            # print(f"Found end marker in file: {filename}")
                            con.seal()
                            con_by_zone.append(con)
                            break
                        else:
                            parts = line.split()
                            isotope = parts[0]
                            za = zaid_list.get_zaid(isotope)
                            if za:
                                if not ismissing(za):
                                    concentration = parts[11]
                                    if za not in conc:
                                        conc[za] = [0] * (zones + 2)
                                        conc[za][0] = isotope
                                        conc[za][1] = za
                                    conc[za][z+2] = float(concentration)
                                    con.add(isos[isotope], float(concentration))
                            else:
                                print(f"Unknown isotope '{isotope}' in file: {filename}")
        except FileNotFoundError:
            print(f"File not found: {filename}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)


    with open(f"{filebase}Decay.txt", 'w', encoding='utf-8') as o:
        print(f"found {len(conc)} isotopes\n")
        for za, conc_data in sorted(conc.items()):
            isotope = conc_data[0]
            o.write(f"{isotope}\t{za}\t")
            for z, concentration in enumerate(conc_data[2:]):
                if z < zones - 1:
                    o.write(f"{concentration:.6e}\t")
                else:
                    o.write(f"{concentration:.6e}")
            o.write("\n")

    with open(f"{filebase}DecayCon.txt", 'w', encoding='utf-8') as o:

        for z in range(zones):
            zone = z + 1
            con = con_by_zone[z]
            o.write(f"Zone {zone} Decay Concentrations:\n")
            o.write(con.display(""))
            o.write("\n")

    for z in range(zones):
        zone = z + 1
        con = con_by_zone[z]
        con_isos: Dict[str, Tuple[Isotope, float, float]] = con.isotopes()
        print(f"Zone {zone} Decay Concentrations:")
        print("Isotope\tMass Fraction\tAtom Fraction")        
        for iso_name, (iso, mass_frac, atom_frac) in con_isos.items():
            print(f"{iso_name}\t{iso.zaid:8d}\t{mass_frac:.8e}\t{atom_frac:.8e}")
        print()

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