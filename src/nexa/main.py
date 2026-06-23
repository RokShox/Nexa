from nexa.data import Constituent, Isotope, abundances, elements
from nexa.data.isotopes import iso_by_a, iso_by_element, iso_by_symbol, iso_by_z, isotopes
from nexa.globals import CompositionMode


def main():
    print(f"am242: {isotopes['am242']}")
    print(f"am-242 zaid: {isotopes['am-242'].zaid}")
    print(f"am-242 amu: {isotopes['am-242'].amu}")
    print(f"am242 zaid: {isotopes['am242'].zaid}")
    print(f"am242m zaid: {isotopes['am242m'].zaid}")
    print(f"c zaid: {isotopes['c-12'].zaid}")
    print(f"c12: {isotopes['c12']}")

    sym: str = "U235"
    iso: Isotope = iso_by_symbol(sym)
    print(f"iso: {iso}")
    print(f"{iso = }")

    print("\n".join([f"{iso.symbol}" for iso in iso_by_element("Co")]))
    print("\n".join([f"{iso.symbol}" for iso in iso_by_a(242)]))
    print("\n".join([f"{iso.symbol}" for iso in iso_by_z(95)]))

    print(f"element: {iso.element}")

    print(f"am: {elements['am']}")
    print(f"Am: {elements['Am']}")

    conH: Constituent = Constituent("H", CompositionMode.Atom)
    conH.add(isotopes["h-1"], 0.99).add(isotopes["h-2"], 0.01).seal()
    print(f"{conH = }")

    conO: Constituent = Constituent("O", CompositionMode.Mass)
    conO.add(isotopes["o-16"], 0.99).add(isotopes["o-17"], 0.01).seal()
    print(f"{conO = }")

    conH2O: Constituent = Constituent("H2O", CompositionMode.Atom)
    conH2O.add(conH, 0.667).add(conO, 0.333).seal()
    print(f"{conH2O = }")

    con_ta: Constituent = abundances["Ta"]
    con_be: Constituent = abundances["Be"]
    con_tabe = Constituent("TaBe", CompositionMode.Mass)
    con_tabe.add(con_ta, 0.5).add(con_be, 0.5).seal()
    print(f"{con_tabe = }")

    con_na: Constituent = abundances["Na"]
    con_cl: Constituent = abundances["Cl"]
    con_nacl = Constituent("NaCl", CompositionMode.Atom)
    con_nacl.add(con_na, 1.0).add(con_cl, 1.0).seal()
    print(f"{con_nacl = }")

    conMat: Constituent = Constituent("Mix", CompositionMode.Mass)
    conMat.add(con_tabe, 0.5).add(con_nacl, 0.5).seal()

    con_c: Constituent = abundances["C"]
    con_h: Constituent = abundances["H"]
    con_n: Constituent = abundances["N"]
    con_acryl: Constituent = Constituent("Acrylonitrile", CompositionMode.Atom)
    con_acryl.add(con_c, 3.0 / 7.0).add(con_h, 3.0 / 7.0).add(con_n, 1.0 / 7.0).seal()
    con_butad: Constituent = Constituent("Butadiene", CompositionMode.Atom)
    con_butad.add(con_c, 0.4).add(con_h, 0.6).seal()
    con_rubber: Constituent = Constituent("Nitrile Rubber", CompositionMode.Mass)
    con_rubber.add(con_acryl, 0.5).add(con_butad, 0.5).seal()

    # memo = {}
    # con_clone = deepcopy(con_rubber, memo)

    con_test = Constituent("Test", CompositionMode.Mass)
    # con_test.add(con_rubber, 0.5).add(con_butad, 0.5).seal()
    con_test.add(con_butad, 0.5).add(con_rubber, 0.5).seal()

    # con_rubber.promote().display(sys.stdout)
    # con_rubber.display(sys.stdout)
    # con_rubber.demote().display(sys.stdout)
    # con_rubber.demote().demote().display(sys.stdout)

    cl = abundances["cl"]
    na = abundances["na"]
    salt = Constituent("salt", CompositionMode.Atom)
    salt.add(na, 1).add(cl, 1).seal()
    salt.display()

    cl = abundances["cl"]
    k = abundances["k"]
    kcl = Constituent("kcl", CompositionMode.Atom)
    kcl.add(k, 1).add(cl, 1).seal()
    kcl.display()

    sn = abundances["sn"]
    cu = abundances["cu"]
    bronze = Constituent("bronze", CompositionMode.Mass)
    bronze.add(cu, 0.88).add(sn, 0.12).seal()
    bronze.display()
    bronze.flatten().display()

    salty_bronze = Constituent("salty_bronze", CompositionMode.Mass)
    salty_bronze.add(salt, 0.1).add(bronze, 0.9).seal()
    salty_bronze.display()
    salty_bronze.demote().display()

    salty_bronze_ta = Constituent("salty_bronze_ta", CompositionMode.Mass)
    salty_bronze_ta.add(salty_bronze, 0.99).add(abundances["ta"], 0.9).seal()
    salty_bronze_ta.display()

    ss316h = Constituent("ss316h", CompositionMode.Mass)
    (
        ss316h.add(abundances["c"], 0.00070)
        .add(abundances["cr"], 0.17000)
        .add(abundances["fe"], 0.65605)
        .add(abundances["mn"], 0.02000)
        .add(abundances["mo"], 0.02500)
        .add(abundances["ni"], 0.12000)
        .add(abundances["p"], 0.00045)
        .add(abundances["s"], 0.00030)
        .add(abundances["si"], 0.00750)
        .seal()
    )
    ss316h.display()

    # Set path to the output file to display constituents to a file.
    # p = Path("/Temp/mat.txt")
    # with p.open(mode="w") as f:
    #     con_test.display(f)
    #     con_test.flatten().display(f)
    #     salt.display(f)
    #     bronze.display(f)

    # print(ss316h.isotopes())

    query: str = "ss316h > c"
    result = ss316h.path_fractions(query)
    print(f"{query} = {result}")


def main_cli():
    """Run repl loop."""
    import code

    code.interact(local=globals())


if __name__ == "__main__":
    main()
