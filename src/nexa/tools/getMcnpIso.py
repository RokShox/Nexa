import sys
import os
from pathlib import Path
import argparse

from nexa.globals import CompositionMode
from nexa.data import Isotope, elements, abundances, LibEndf81
from nexa.data.isotopes import isotopes, iso_by_zaid, iso_by_szaid
from nexa.material import Constituent
from nexa.mcnp.output import MCNPOutputParser
from nexa.mcnp.output.table210 import Table210Parser, NeutronicsData, MaterialBurnupData, NuclideInventoryData, InventoryTotals, MaterialInventory
from nexa.mcnp.output.table220 import Table220Parser, SummaryNuclideData, SummaryTotals, SummaryInventory
from nexa.mcnp.input.cardM import MaterialCard

def main():
   
    parser = argparse.ArgumentParser(prog="getMcnpIso", description="Parse Mcnp burn output files for isotope concentrations.")
    parser.add_argument("file", metavar="FILE", type=str, help="Path to the Mcnp output file to parse")
    args = parser.parse_args()

    out_name: str = args.file
    if not out_name.endswith('o'):
        out_name += 'o'
    case_name: str = out_name[:-1]

    with open(out_name, 'r') as f:
        lines: list[str] =  [line.rstrip('\n') for line in f]

    # class SummaryInventory:
    #     """Data class representing complete summary inventory for all materials at a specific step."""
    #     step: int
    #     time_days: float
    #     power_mw: float
    #     total_volume_cm3: float
    #     actinide_nuclides: dict[str,SummaryNuclideData] = field(default_factory=dict)
    #     actinide_totals: SummaryTotals | None = None
    #     nonactinide_nuclides: dict[str,SummaryNuclideData] = field(default_factory=dict)
    #     nonactinide_totals: SummaryTotals | None = None

    # class SummaryNuclideData:
    #     """Data class representing summary nuclide inventory data for all materials."""
    #     symbol: str
    #     number: int
    #     zaid: int
    #     mass_gm: float
    #     activity_ci: float
    #     spec_activity_ci_gm: float
    #     atom_density_a_b_cm: float
    #     atom_fraction: float
    #     mass_fraction: float

    # class SummaryTotals:
    #     """Data class representing summary totals for all materials."""
    #     mass_gm: float
    #     activity_ci: float
    #     spec_activity_ci_gm: float
    #     atom_density_a_b_cm: float
    #     atom_fraction: float
    #     mass_fraction: float

    parser = Table220Parser()
    inventories: list[SummaryInventory] = parser.parse_lines(lines)
    summary: SummaryInventory

    print(f"Found {len(inventories)} summary inventories:")
    for summary in inventories:
        print(f"  Step {summary.step}: Time {summary.time_days} [d] Power {summary.power_mw} [MW]  Total Volume {summary.total_volume_cm3:.4e} [cm3]")
        actinides = summary.nuclides_by_type("actinide")
        nonactinides = summary.nuclides_by_type("nonactinide")
        if actinides:
            print(f"    U-233 total mass: {actinides['u-233'].mass_gm:.2e} [g]")
            print(f"    Pa-233 total mass: {actinides['pa-233'].mass_gm:.2e} [g]")
        # if inv.nonactinide_totals:
        #     print(f"    Non-actinide total mass: {inv.nonactinide_totals.mass_gm:.2e} gm")
    sys.exit(0) 

    print(f"\nAvailable steps: {parser.get_all_steps()}")

    step: int = len(inventories) - 1
    summary: SummaryInventory = parser.get_inventory_at_step(step)

    if summary:
        print(f"Found inventory for step {step}:")
        print(f"  Actinide nuclides: {len(summary.actinide_nuclides)}")
        print(f"  Non-actinide nuclides: {len(summary.nonactinide_nuclides)}")
    else:
        print(f"No inventory found for step {step}.")

    nper: int = 5
    actual_step: int = 10
    with open(f"{case_name}BurnAvg{actual_step:02d}.txt", 'w', encoding='utf-8') as o:
        for i, nuclide in enumerate(summary.actinide_nuclides):
                print(f"{nuclide.zaid}={nuclide.atom_density_a_b_cm:.6e}", end='\n' if (i + 1) % nper == 0 else ' ', file=o)
        print("", file=o)
        for i, nuclide in enumerate(summary.nonactinide_nuclides):
                print(f"{nuclide.zaid}={nuclide.atom_density_a_b_cm:.6e}", end='\n' if (i + 1) % nper == 0 else ' ', file=o)
        print("", file=o)



    # con: Constituent = Constituent(name=f"{case_name}BurnMat{step:02d}", mode=CompositionMode.Atom)
    # for nuclide in summary.actinide_nuclides:
    #     iso: Isotope = iso_by_zaid(nuclide.zaid)
    #     if iso:
    #         con.add(iso, nuclide.atom_density_a_b_cm)

    # for nuclide in summary.nonactinide_nuclides:
    #     iso: Isotope = iso_by_zaid(nuclide.zaid)
    #     if iso:
    #         con.add(iso, nuclide.atom_density_a_b_cm)

    # con.seal()
    # print(f"\nConstituent for burnup material at step {step}:")
    # con.display()

    # mat_card: MaterialCard = MaterialCard(mat_id=1001, constituent=con)
    # print(f"\nMaterial Card for burnup material at step {step}:")
    # print(mat_card.to_string())


    # Table210Parser

    # class NeutronicsData:
    #     """Data class representing neutronics and burnup data for a step."""
    #     step: int
    #     duration_days: float
    #     time_days: float
    #     power_mw: float
    #     keff: float
    #     flux: float
    #     ave_nu: float
    #     ave_q: float
    #     burnup_gwd_mtu: float
    #     source_nts_sec: float

    # class MaterialBurnupData:
    #     """Data class representing individual material burnup data for a step."""
    #     step: int
    #     duration_days: float
    #     time_days: float
    #     power_fraction: float
    #     burnup_gwd_mtu: float

    # class MaterialInventory:
    #     """Data class representing complete inventory for a material at a specific step."""
    #     material_id: int
    #     step: int
    #     time_days: float
    #     power_mw: float
    #     volume_cm3: float
    #     actinide_nuclides: list[NuclideInventoryData] = field(default_factory=list)
    #     actinide_totals: InventoryTotals | None = None
    #     nonactinide_nuclides: list[NuclideInventoryData] = field(default_factory=list)
    #     nonactinide_totals: InventoryTotals | None = None

    parser210 = Table210Parser()
    # tuple[list[NeutronicsData], dict[int, list[MaterialBurnupData]], dict[int, list[MaterialInventory]]]
    #   list[NeutronicsData] indexed by step
    #   dict[int, list[MaterialBurnupData]] keyed by material_id, indexed by step
    #   dict[int, list[MaterialInventory]] keyed by material_id, indexed by step
    neutronics_data, material_burnup_data, material_inventories = parser210.parse_lines(lines)
    
    # d: dict = parser210.to_dict()
    print(f"\nNeutronics Data:\n{neutronics_data[-1]}")
    
    # print(f"\nMaterial Burnup Data for Material 101 at last step:")
    # mat1_burnup_list: list[MaterialBurnupData] = material_burnup_data.get(101, [])
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
                iso: Isotope = iso_by_zaid(nuclide.zaid)
                if not LibEndf81.is_missing_zaid(iso.zaid):
                    con_burn.add(iso, nuclide.atom_fraction)
            for nuclide in inv.nonactinide_nuclides:
                iso: Isotope = iso_by_zaid(nuclide.zaid)
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

if __name__ == "__main__":
    main()