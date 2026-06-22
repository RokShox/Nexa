import re
import unittest

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


class TestNormalizePath(unittest.TestCase):
    def test_downward_spacing_and_case(self):
        self.assertEqual(
            Constituent.normalize_path("  Fuel  >  *  >  O  "),
            "fuel > * > o",
        )

    def test_upward_spacing_and_case(self):
        self.assertEqual(
            Constituent.normalize_path("o-16 < O"),
            "o-16 < o",
        )

    def test_mixed_separators_raises(self):
        with self.assertRaises(ValueError):
            Constituent.normalize_path("Fuel > O < o-16")


class TestPathFractions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fuel = build_fuel()

    def test_exact_downward_path(self):
        query = "Fuel > UO2 > O > o-16"
        result = self.fuel.path_fractions(query)
        self.assertEqual(len(result), 1)
        key = "fuel > uo2 > o > o-16"
        self.assertIn(key, result)
        mass, atom = result[key]
        self.assertGreater(mass, 0.0)
        self.assertGreater(atom, 0.0)
        self.assertNotIn("total", result)

    def test_exact_downward_path_noncanonical_query_has_one_entry(self):
        query = "  fuel > uo2 > o > o-16  "
        result = self.fuel.path_fractions(query)
        self.assertEqual(len(result), 1)
        self.assertIn("fuel > uo2 > o > o-16", result)

    def test_wildcard_downward_path_case_insensitive(self):
        query = "Fuel > * > O"
        result = self.fuel.path_fractions(query)
        self.assertIn("fuel > uo2 > o", result)
        self.assertIn("fuel > puo2 > o", result)
        self.assertIn("total", result)

        uo2_mass, uo2_atom = result["fuel > uo2 > o"]
        puo2_mass, puo2_atom = result["fuel > puo2 > o"]
        sum_mass, sum_atom = result["total"]
        self.assertAlmostEqual(sum_mass, uo2_mass + puo2_mass)
        self.assertAlmostEqual(sum_atom, uo2_atom + puo2_atom)

    def test_total_key_is_stable_for_spaced_query(self):
        query = "  Fuel > * > O  "
        result = self.fuel.path_fractions(query)
        self.assertIn("total", result)
        self.assertNotIn(query, result)

    def test_upward_partial_path_case_insensitive(self):
        query = "o-16 < O"
        result = self.fuel.path_fractions(query)
        self.assertIn("fuel > uo2 > o > o-16", result)
        self.assertIn("fuel > puo2 > o > o-16", result)
        self.assertIn("total", result)
        uo2 = result["fuel > uo2 > o > o-16"]
        puo2 = result["fuel > puo2 > o > o-16"]
        self.assertAlmostEqual(result["total"][0], uo2[0] + puo2[0])
        self.assertAlmostEqual(result["total"][1], uo2[1] + puo2[1])

    def test_bare_isotope_sums_branches(self):
        query = "O-16"
        result = self.fuel.path_fractions(query)
        self.assertIn("fuel > uo2 > o > o-16", result)
        self.assertIn("total", result)

    def test_bare_wildcard_all_isotopes(self):
        result = self.fuel.path_fractions("*")
        self.assertIn("total", result)
        self.assertAlmostEqual(result["total"][0], 1.0)
        self.assertAlmostEqual(result["total"][1], 1.0)
        isotope_keys = [key for key in result if key != "total"]
        self.assertGreater(len(isotope_keys), 1)
        total_mass = sum(result[key][0] for key in isotope_keys)
        total_atom = sum(result[key][1] for key in isotope_keys)
        self.assertAlmostEqual(total_mass, 1.0)
        self.assertAlmostEqual(total_atom, 1.0)

    def test_invalid_isotope_segment_returns_empty(self):
        self.assertEqual(self.fuel.path_fractions("not-an-isotope"), {})
        self.assertEqual(self.fuel.path_fractions("not-an-isotope < o"), {})

    def test_downward_path_wrong_root_raises(self):
        with self.assertRaises(ValueError):
            self.fuel.path_fractions("UO2 > O > o-16")

    def test_unsealed_raises(self):
        con = Constituent("Open", CompositionMode.Atom)
        with self.assertRaises(RuntimeError):
            con.path_fractions("Open")

    def test_normalize_path_matches_resolved_keys(self):
        query = "Fuel > UO2 > O > o-16"
        result = self.fuel.path_fractions(query)
        self.assertIn(Constituent.normalize_path(query), result)

    def test_display_path_fractions_headers_and_format(self):
        result = self.fuel.path_fractions("Fuel > * > O")
        output = self.fuel.display_path_fractions(result, to_string=True)
        assert output is not None
        self.assertIn("Path", output)
        self.assertIn("Mass Fraction", output)
        self.assertIn("Atom Fraction", output)
        for key, (mass, atom) in result.items():
            self.assertIn(key, output)
            self.assertIn(f"{mass:.8e}", output)
            self.assertIn(f"{atom:.8e}", output)

    def test_display_path_fractions_column_alignment(self):
        result = self.fuel.path_fractions("Fuel > * > O")
        output = self.fuel.display_path_fractions(result, to_string=True)
        assert output is not None
        lines = output.rstrip("\n").split("\n")
        self.assertGreaterEqual(len(lines), 2)

        def find_numeric_columns(line: str) -> tuple[int, int]:
            matches = list(re.finditer(r"\d\.\d{8}e[+-]\d{2}", line))
            self.assertEqual(len(matches), 2, msg=line)
            return matches[0].start(), matches[1].start()

        first_mass_col, first_atom_col = find_numeric_columns(lines[1])
        for line in lines[2:]:
            mass_col, atom_col = find_numeric_columns(line)
            self.assertEqual(mass_col, first_mass_col)
            self.assertEqual(atom_col, first_atom_col)

    def test_display_path_fractions_empty_dict(self):
        output = self.fuel.display_path_fractions({}, to_string=True)
        assert output is not None
        lines = output.rstrip("\n").split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("Path", lines[0])
        self.assertIn("Mass Fraction", lines[0])
        self.assertIn("Atom Fraction", lines[0])


if __name__ == "__main__":
    unittest.main()
