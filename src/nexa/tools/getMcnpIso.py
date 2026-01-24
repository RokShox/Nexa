import sys
import os
from pathlib import Path
from typing import Dict, List
from nexa.mcnp.output import MCNPOutputParser
from nexa.mcnp.output.table210 import Table210Parser, NeutronicsData, MaterialBurnupData, NuclideInventoryData, InventoryTotals, MaterialInventory
from nexa.mcnp.output.table220 import Table220Parser, SummaryNuclideData, SummaryTotals, SummaryInventory
from nexa.data import Isotopes, Isotope, Elements, Abundances, LibEndf81
from nexa.globals import CompositionMode
from nexa.material import Constituent
from nexa.mcnp.input.cardM import MaterialCard

if __name__ == "__main__":
   
    abund: Abundances = Abundances()
    isos: Isotopes = Isotopes()
    elms: Elements = Elements()

    # run_dir = Path(r'D:\Projects\Ampera\Run\v1.0')
    run_dir = Path(r'D:\Projects\DeepFission\Run\v1.1')
    os.chdir(run_dir)

    out_name = sys.argv[1] if len(sys.argv) > 1 else print ("Usage: getMcnpIso.py <output_name>") & sys.exit(1)
    if not out_name.endswith('o'):
        out_name += 'o'
    case_name = out_name[:-1]

    with open(out_name, 'r') as f:
        sample_lines =  [line.rstrip('\n') for line in f]

    parser = Table220Parser()
    inventories = parser.parse_lines(sample_lines)
    
    print(f"Found {len(inventories)} summary inventories:")
    for inv in inventories:
        print(f"  Step {inv.step}: {len(inv.actinide_nuclides)} actinides, {len(inv.nonactinide_nuclides)} non-actinides")
        if inv.actinide_totals:
            print(f"    Actinide total mass: {inv.actinide_totals.mass_gm:.2e} gm")
        if inv.nonactinide_totals:
            print(f"    Non-actinide total mass: {inv.nonactinide_totals.mass_gm:.2e} gm")
    
    print(f"\nAvailable steps: {parser.get_all_steps()}")

    step: int = len(inventories) - 1
    inv: SummaryInventory = parser.get_inventory_at_step(step)

    if inv:
        print(f"Found inventory for step {step}:")
        print(f"  Actinide nuclides: {len(inv.actinide_nuclides)}")
        print(f"  Non-actinide nuclides: {len(inv.nonactinide_nuclides)}")
    else:
        print(f"No inventory found for step {step}.")

    nper: int = 5
    actual_step: int = 10
    with open(f"{case_name}BurnAvg{actual_step:02d}.txt", 'w', encoding='utf-8') as o:
        for i, nuclide in enumerate(inv.actinide_nuclides):
                print(f"{nuclide.zaid}={nuclide.atom_density_a_b_cm:.6e}", end='\n' if (i + 1) % nper == 0 else ' ', file=o)
        print("", file=o)
        for i, nuclide in enumerate(inv.nonactinide_nuclides):
                print(f"{nuclide.zaid}={nuclide.atom_density_a_b_cm:.6e}", end='\n' if (i + 1) % nper == 0 else ' ', file=o)
        print("", file=o)



    # con: Constituent = Constituent(name=f"{case_name}BurnMat{step:02d}", mode=CompositionMode.Atom)
    # for nuclide in inv.actinide_nuclides:
    #     iso: Isotope = isos.iso_by_zaid(nuclide.zaid)
    #     if iso:
    #         con.add(iso, nuclide.atom_density_a_b_cm)

    # for nuclide in inv.nonactinide_nuclides:
    #     iso: Isotope = isos.iso_by_zaid(nuclide.zaid)
    #     if iso:
    #         con.add(iso, nuclide.atom_density_a_b_cm)

    # con.seal()
    # print(f"\nConstituent for burnup material at step {step}:")
    # con.display()

    # mat_card: MaterialCard = MaterialCard(mat_id=1001, constituent=con)
    # print(f"\nMaterial Card for burnup material at step {step}:")
    # print(mat_card.to_string())


    # Table210Parser

    parser210 = Table210Parser()
    neutronics_data, material_burnup_data, material_inventories = parser210.parse_lines(sample_lines)
    # d: Dict = parser210.to_dict()
    print(f"\nNeutronics Data:\n{neutronics_data[-1]}")
    
    # print(f"\nMaterial Burnup Data for Material 101 at last step:")
    # mat1_burnup_list: List[MaterialBurnupData] = material_burnup_data.get(101, [])
    # if mat1_burnup_list:
    #     print(mat1_burnup_list[-1])

    # mat_inv_list = material_inventories.get(101, [])
    # if mat_inv_list:
    #     print(f"\nMaterial Inventory for Material 101 at step -1:")
    #     print(mat_inv_list[-1])

    # last_step = neutronics_data[-1].step
    last_step = 10
    with open(f"{case_name}BurnMat{last_step:02d}.txt", 'w', encoding='utf-8') as o:
        for mat_id, inv_list in material_inventories.items():
            inv: MaterialInventory = inv_list[-1]
            con_burn: Constituent = Constituent(name=f"{case_name}Mat{mat_id:03d}Burn", mode=CompositionMode.Atom)
            for nuclide in inv.actinide_nuclides:
                iso: Isotope = isos.iso_by_zaid(nuclide.zaid)
                if not LibEndf81.is_missing_zaid(iso.zaid):
                    con_burn.add(iso, nuclide.atom_fraction)
            for nuclide in inv.nonactinide_nuclides:
                iso: Isotope = isos.iso_by_zaid(nuclide.zaid)
                if not LibEndf81.is_missing_zaid(iso.zaid):
                    con_burn.add(iso, nuclide.atom_fraction)
            con_burn.seal()
            print(f"\nConstituent for burnup material {mat_id} at last step:")
            con_burn.display() 

            mat_card_burn: MaterialCard = MaterialCard(mat_id=mat_id, constituent=con_burn)
            mat_card_burn.set_library("NLIB", "11c")
            aden = inv.actinide_totals.atom_density_a_b_cm + inv.nonactinide_totals.atom_density_a_b_cm
            print(f"c    Material Card for burnup material {mat_id} at step {last_step} aden={aden:10.6e}:", file=o)
            print(mat_card_burn.to_string(), file=o)

