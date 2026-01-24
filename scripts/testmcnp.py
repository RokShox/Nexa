from nexa.mcnp.output import Table220Parser, SummaryNuclideData, SummaryTotals, SummaryInventory, MCNPOutputParser
from pathlib import Path


def test_table220_parser():
    pass


if __name__ == "__main__":
   
    with open('tbl220.txt', 'r') as f:
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

    step: int = 6
    inv: SummaryInventory = parser.get_inventory_at_step(step)

    if inv:
        print(f"Found inventory for step {step}:")
        print(f"  Actinide nuclides: {len(inv.actinide_nuclides)}")
        print(f"  Non-actinide nuclides: {len(inv.nonactinide_nuclides)}")
    else:
        print(f"No inventory found for step {step}.")
