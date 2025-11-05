from nexa.mcnp.output import Table220Parser, SummaryNuclideData, SummaryTotals, SummaryInventory


def test_table220_parser():
    pass


if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1burnup summary table summed over all materials                                                         print table 220",
        "",
        " nuclides with atom fractions below 1.000E-10 for a material are zeroed and deleted from print tables after t=0",
        "",
        " nuclide data are sorted by increasing zaid summed over all materials volume  2.3748E+05 (cm**3)",
        "",
        " actinide inventory for sum of materials at end of step  0, time 0.000E+00 (days), power 1.000E+00 (MW)",
        "",
        "  no. zaid     mass      activity   sp. act.  atom den.   atom fr.   mass fr.",
        "               (gm)        (Ci)     (Ci/gm)    (a/b-cm)",
        "   1  90230  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00",
        "   2  90231  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00",
        "   3  90232  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00",
        "     totals  2.191E+06  0.000E+00  0.000E+00  2.335E-02  3.333E-01  8.814E-01",
        "",
        " actinide inventory for sum of materials at end of step  1, time 4.000E+00 (days), power 1.000E+00 (MW)",
        "",
        "  no. zaid     mass      activity   sp. act.  atom den.   atom fr.   mass fr.",
        "               (gm)        (Ci)     (Ci/gm)    (a/b-cm)",
        "   1  92234  1.025E+03  6.374E+00  6.217E-03  1.111E-05  1.585E-04  4.124E-04",
        "   2  92235  1.084E+05  2.344E-01  2.161E-06  1.170E-03  1.670E-02  4.363E-02",
        "   3  92236  3.281E+01  2.122E-03  6.467E-05  3.524E-07  5.030E-06  1.320E-05",
        "     totals  2.191E+06  6.192E+05  2.826E-01  2.335E-02  3.333E-01  8.814E-01"
    ]
    
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
