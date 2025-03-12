from pathlib import Path
import sys

from nexa.data import Isotopes, Elements, Abundances
from nexa.globals import CompositionMode
from nexa.material import Constituent

abund: Abundances = Abundances()
isos: Isotopes = Isotopes()
elms: Elements = Elements()


def main():
    # print(f"am242: {isos['am242']}")
    # print(f"am-242 zaid: {isos.zaid('am-242')}")
    # print(f"am-242 amu: {isos.amu('am-242')}")
    # print(f"am242 zaid: {isos.zaid('am242')}")
    # print(f"am242m zaid: {isos.zaid('am242m')}")
    # print(f"c zaid: {isos.zaid('c')}")
    # print(f"c12: {isos['c12']}")

    # sym: str = "U235"
    # iso: Isotope = isos[sym]
    # print(f"iso: {iso}")
    # print(f"{iso = }")

    # print("\n".join([f"{iso.symbol}" for iso in isos.iso_by_element("Co")]))
    # print("\n".join([f"{iso.symbol}" for iso in isos.iso_by_a(242)]))
    # print("\n".join([f"{iso.symbol}" for iso in isos.iso_by_z(95)]))

    # print(f"element: {iso.element}")

    # print(f"am: {elms['am']}")
    # print(f"Am: {elms['Am']}")

    # conH: Constituent = Constituent("H", 1, CompositionMode.Atom)
    # conH.add(isos["h-1"], 0.99).add(isos["h-2"], 0.01).seal()
    # print(f"{conH = }")

    # conO: Constituent = Constituent("O", 1, CompositionMode.Mass)
    # conO.add(isos["o-16"], 0.99).add(isos["o-17"], 0.01).seal()
    # print(f"{conO = }")

    # conH2O: Constituent = Constituent("H2O", 2, CompositionMode.Atom)
    # conH2O.add(conH, 0.667).add(conO, 0.333).seal()
    # print(f"{conH2O = }")

    con_ta: Constituent = abund["Ta"]
    con_be: Constituent = abund["be"]
    con_tabe = Constituent("TaBe", CompositionMode.Mass)
    con_tabe.add(con_ta, 0.5).add(con_be, 0.5).seal()
    print(f"{con_tabe = }")

    con_na: Constituent = abund["Na"]
    con_cl: Constituent = abund["Cl"]
    con_nacl = Constituent("NaCl", CompositionMode.Atom)
    con_nacl.add(con_na, 1.0).add(con_cl, 1.0).seal()
    print(f"{con_nacl = }")

    conMat: Constituent = Constituent("Mix", CompositionMode.Mass)
    conMat.add(con_tabe, 0.5).add(con_nacl, 0.5).seal()

    con_c: Constituent = abund["C"]
    con_h: Constituent = abund["H"]
    con_n: Constituent = abund["N"]
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

    cl = abund["cl"]
    na = abund["na"]
    salt = Constituent("salt", CompositionMode.Atom)
    salt.add(na, 1).add(cl, 1).seal()
    salt.display()

    sn = abund["sn"]
    cu = abund["cu"]
    bronze = Constituent("bronze", CompositionMode.Mass)
    bronze.add(cu, 0.88).add(sn, 0.12).seal()
    bronze.display()
    bronze.flatten().display()

    salty_bronze = Constituent("salty_bronze", CompositionMode.Mass)
    salty_bronze.add(salt, 0.1).add(bronze, 0.9).seal()
    salty_bronze.display()
    salty_bronze.demote().display()

    salty_bronze_ta = Constituent("salty_bronze_ta", CompositionMode.Mass)
    salty_bronze_ta.add(salty_bronze, 0.99).add(abund["ta"], 0.9).seal()
    salty_bronze_ta.display()

    ss316h = Constituent("ss316h", CompositionMode.Mass)
    (
        ss316h.add(abund["c"], 0.00070)
        .add(abund["cr"], 0.17000)
        .add(abund["fe"], 0.65605)
        .add(abund["mn"], 0.02000)
        .add(abund["mo"], 0.02500)
        .add(abund["ni"], 0.12000)
        .add(abund["p"], 0.00045)
        .add(abund["s"], 0.00030)
        .add(abund["si"], 0.00750)
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


def main_cli():
    """Run repl loop."""
    import code

    code.interact(local=globals())


if __name__ == "__main__":
    main()
