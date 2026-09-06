import re

import pytest

from nexa.data import Constituent
from nexa.globals import CompositionMode


def test_downward_spacing_and_case():
    assert Constituent.normalize_path("  Fuel  >  *  >  O  ") == "fuel > * > o"


def test_upward_spacing_and_case():
    assert Constituent.normalize_path("o-16 < O") == "o-16 < o"


def test_mixed_separators_raises():
    with pytest.raises(ValueError):
        Constituent.normalize_path("Fuel > O < o-16")


def test_exact_downward_path(fuel):
    query = "Fuel > UO2 > O > o-16"
    result = fuel.path_fractions(query)
    assert len(result) == 1
    key = "fuel > uo2 > o > o-16"
    assert key in result
    mass, atom = result[key]
    assert mass > 0.0
    assert atom > 0.0
    assert "total" not in result


def test_exact_downward_path_noncanonical_query_has_one_entry(fuel):
    query = "  fuel > uo2 > o > o-16  "
    result = fuel.path_fractions(query)
    assert len(result) == 1
    assert "fuel > uo2 > o > o-16" in result


def test_wildcard_downward_path_case_insensitive(fuel):
    query = "Fuel > * > O"
    result = fuel.path_fractions(query)
    assert "fuel > uo2 > o" in result
    assert "fuel > puo2 > o" in result
    assert "total" in result

    uo2_mass, uo2_atom = result["fuel > uo2 > o"]
    puo2_mass, puo2_atom = result["fuel > puo2 > o"]
    sum_mass, sum_atom = result["total"]
    assert sum_mass == pytest.approx(uo2_mass + puo2_mass)
    assert sum_atom == pytest.approx(uo2_atom + puo2_atom)


def test_total_key_is_stable_for_spaced_query(fuel):
    query = "  Fuel > * > O  "
    result = fuel.path_fractions(query)
    assert "total" in result
    assert query not in result


def test_upward_partial_path_case_insensitive(fuel):
    query = "o-16 < O"
    result = fuel.path_fractions(query)
    assert "fuel > uo2 > o > o-16" in result
    assert "fuel > puo2 > o > o-16" in result
    assert "total" in result
    uo2 = result["fuel > uo2 > o > o-16"]
    puo2 = result["fuel > puo2 > o > o-16"]
    assert result["total"][0] == pytest.approx(uo2[0] + puo2[0])
    assert result["total"][1] == pytest.approx(uo2[1] + puo2[1])


def test_upward_wildcard_isotope_under_element(fuel):
    query = "* < u"
    result = fuel.path_fractions(query)
    assert "fuel > uo2 > u > u-235" in result
    assert "fuel > uo2 > u > u-238" in result
    assert "fuel > puo2 > pu > pu-239" not in result
    assert "fuel > puo2 > pu > pu-240" not in result
    assert "total" in result
    u235 = result["fuel > uo2 > u > u-235"]
    u238 = result["fuel > uo2 > u > u-238"]
    assert result["total"][0] == pytest.approx(u235[0] + u238[0])
    assert result["total"][1] == pytest.approx(u235[1] + u238[1])


def test_upward_wildcard_isotope_under_element_case_insensitive(fuel):
    result = fuel.path_fractions("* < U")
    assert "fuel > uo2 > u > u-235" in result
    assert "fuel > uo2 > u > u-238" in result
    assert "total" in result


def test_bare_isotope_sums_branches(fuel):
    query = "O-16"
    result = fuel.path_fractions(query)
    assert "fuel > uo2 > o > o-16" in result
    assert "total" in result


def test_bare_wildcard_all_isotopes(fuel):
    result = fuel.path_fractions("*")
    assert "total" in result
    assert result["total"][0] == pytest.approx(1.0)
    assert result["total"][1] == pytest.approx(1.0)
    isotope_keys = [key for key in result if key != "total"]
    assert len(isotope_keys) > 1
    total_mass = sum(result[key][0] for key in isotope_keys)
    total_atom = sum(result[key][1] for key in isotope_keys)
    assert total_mass == pytest.approx(1.0)
    assert total_atom == pytest.approx(1.0)


def test_invalid_isotope_segment_returns_empty(fuel):
    assert fuel.path_fractions("not-an-isotope") == {}
    assert fuel.path_fractions("not-an-isotope < o") == {}


def test_downward_path_wrong_root_raises(fuel):
    with pytest.raises(ValueError):
        fuel.path_fractions("UO2 > O > o-16")


def test_unsealed_raises():
    con = Constituent("Open", CompositionMode.Atom)
    with pytest.raises(RuntimeError):
        con.path_fractions("Open")


def test_normalize_path_matches_resolved_keys(fuel):
    query = "Fuel > UO2 > O > o-16"
    result = fuel.path_fractions(query)
    assert Constituent.normalize_path(query) in result


def test_display_path_fractions_headers_and_format(fuel):
    result = fuel.path_fractions("Fuel > * > O")
    output = fuel.display_path_fractions(result, to_string=True)
    assert output is not None
    assert "Path" in output
    assert "Mass Fraction" in output
    assert "Atom Fraction" in output
    for key, (mass, atom) in result.items():
        assert key in output
        assert f"{mass:.8e}" in output
        assert f"{atom:.8e}" in output


def _find_numeric_columns(line: str) -> tuple[int, int]:
    matches = list(re.finditer(r"\d\.\d{8}e[+-]\d{2}", line))
    assert len(matches) == 2, line
    return matches[0].start(), matches[1].start()


def test_display_path_fractions_column_alignment(fuel):
    result = fuel.path_fractions("Fuel > * > O")
    output = fuel.display_path_fractions(result, to_string=True)
    assert output is not None
    lines = output.rstrip("\n").split("\n")
    assert len(lines) >= 2

    first_mass_col, first_atom_col = _find_numeric_columns(lines[1])
    for line in lines[2:]:
        mass_col, atom_col = _find_numeric_columns(line)
        assert mass_col == first_mass_col
        assert atom_col == first_atom_col


def test_display_path_fractions_empty_dict(fuel):
    output = fuel.display_path_fractions({}, to_string=True)
    assert output is not None
    lines = output.rstrip("\n").split("\n")
    assert len(lines) == 1
    assert "Path" in lines[0]
    assert "Mass Fraction" in lines[0]
    assert "Atom Fraction" in lines[0]
