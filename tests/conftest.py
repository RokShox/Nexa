import pytest

from nexa.data import Constituent, abundances
from nexa.data.isotopes import isotopes
from nexa.globals import CompositionMode


def build_fuel() -> Constituent:
    u = Constituent("U", CompositionMode.Mass)
    u.add(isotopes["u-235"], 0.05).add(isotopes["u-238"], 0.95).seal()
    o = abundances["O"]
    pu = Constituent("Pu", CompositionMode.Mass)
    pu.add(isotopes["pu-239"], 0.96).add(isotopes["pu-240"], 0.04).seal()

    uo2 = Constituent("UO2", CompositionMode.Atom)
    uo2.add(u, 1.0).add(o, 2.0).seal()

    puo2 = Constituent("PuO2", CompositionMode.Atom)
    puo2.add(pu, 1.0).add(o.copy("O"), 2.0).seal()

    fuel = Constituent("Fuel", CompositionMode.Atom)
    fuel.add(uo2, 0.5).add(puo2, 0.5).seal()
    return fuel


@pytest.fixture(scope="module")
def fuel() -> Constituent:
    return build_fuel()
