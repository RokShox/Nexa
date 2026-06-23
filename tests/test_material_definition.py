import pytest
from ruamel.yaml import YAML

from nexa.data import Constituent, Isotope, abundances, isotopes
from nexa.globals import CompositionMode
from nexa.material import Material


def _element_stanza(element: str, *, mass_density: float = 1.0) -> dict:
    return {
        "mode": "mass",
        "mass_density": mass_density,
        "fractions": {element: 1.0},
    }


def test_isotope_fraction_keys_build_level_one_constituent():
    mat = Material.from_definition(
        "U235_fuel",
        {
            "mode": "atom",
            "atom_density": 0.05,
            "fractions": {"u-235": 0.05, "u-238": 0.95},
        },
    )
    assert mat.composition is not None
    assert mat.composition.level == 1
    children = mat.composition.constituents()
    assert len(children) == 2
    assert all(isinstance(c, Isotope) for c in children)


def test_element_symbol_resolves_to_abundances():
    mat = Material.from_definition("Iron", _element_stanza("fe", mass_density=7.87))
    assert mat.composition is not None
    assert mat.composition.level == 2
    child = mat.composition.constituents()[0]
    assert isinstance(child, Constituent)
    assert child.name == "fe"
    assert child is abundances["fe"]


def test_element_symbol_case_insensitive():
    mat = Material.from_definition("Iron", _element_stanza("Fe", mass_density=7.87))
    assert mat.composition is not None
    child = mat.composition.constituents()[0]
    assert child.name == "fe"


def test_material_reference_from_problem_materials():
    base = Material.from_definition("Graphite", _element_stanza("c", mass_density=2.266))
    mix = Material.from_definition(
        "FuelComp",
        {
            "mode": "mass",
            "mass_density": 10.0,
            "fractions": {"Graphite": 0.2, "u": 0.8},
        },
        problem_materials={"Graphite": base},
    )
    assert mix.composition is not None
    names = {c.name for c in mix.composition.constituents()}
    assert names == {"Graphite", "u"}


def test_material_reference_from_master_materials():
    base = Material.from_definition("Graphite", _element_stanza("c", mass_density=2.266))
    mix = Material.from_definition(
        "FuelComp",
        {
            "mode": "mass",
            "mass_density": 10.0,
            "fractions": {"Graphite": 0.2, "u": 0.8},
        },
        master_materials={"Graphite": base},
    )
    assert mix.composition is not None
    names = {c.name for c in mix.composition.constituents()}
    assert names == {"Graphite", "u"}


def test_problem_materials_precedence_over_master_materials():
    problem = Material.from_definition("Graphite", _element_stanza("c", mass_density=1.0))
    master = Material.from_definition("Graphite", _element_stanza("c", mass_density=2.266))
    mix = Material.from_definition(
        "FuelComp",
        {
            "mode": "mass",
            "mass_density": 10.0,
            "fractions": {"Graphite": 1.0},
        },
        problem_materials={"Graphite": problem},
        master_materials={"Graphite": master},
    )
    assert mix.composition is not None
    child = mix.composition.constituents()[0]
    assert child.name == "Graphite"
    assert child.a_value == problem.composition.a_value  # type: ignore[union-attr]


def test_isotope_precedence_over_element_symbol():
    """u-235 resolves as isotope, not as element u natural abundance."""
    mat = Material.from_definition(
        "SingleIso",
        {
            "mode": "atom",
            "atom_density": 0.05,
            "fractions": {"u-235": 1.0},
        },
    )
    assert mat.composition is not None
    assert mat.composition.level == 1
    child = mat.composition.constituents()[0]
    assert isinstance(child, Isotope)
    assert child.name == "u-235"
    assert child is isotopes["u-235"]


def test_reject_material_name_matching_isotope_symbol():
    with pytest.raises(ValueError, match="isotope symbol"):
        Material.from_definition("u-235", _element_stanza("c"))


def test_reject_material_name_matching_element_symbol():
    with pytest.raises(ValueError, match="element symbol"):
        Material.from_definition("fe", _element_stanza("fe"))


def test_reject_override_key():
    with pytest.raises(ValueError, match="Override is not supported"):
        Material.from_definition(
            "BadMat",
            {
                "mode": "mass",
                "mass_density": 1.0,
                "fractions": {"u": 1.0},
                "override": {"u": {"mode": "atom", "fractions": {"u-235": 1.0}}},
            },
        )


def test_reject_forward_reference():
    with pytest.raises(ValueError, match="not found"):
        Material.from_definition(
            "Mix",
            {
                "mode": "mass",
                "mass_density": 1.0,
                "fractions": {"UndefinedMat": 1.0},
            },
        )


def test_reject_duplicate_name_in_batch():
    d: dict[str, Material] = {}
    d["Graphite"] = Material.from_definition(
        "Graphite", _element_stanza("c"), problem_materials=d
    )
    with pytest.raises(ValueError, match="not found"):
        Material.from_definition(
            "Mix",
            {
                "mode": "mass",
                "mass_density": 1.0,
                "fractions": {"Graphite": 1.0, "FutureMat": 0.5},
            },
            problem_materials=d,
        )


def test_batch_loading_pattern():
    yaml = YAML(typ="safe")
    documents = list(
        yaml.load_all(
            """
---
title: Test Materials
---
Graphite:
  mode: atom
  mass_density: 2.266
  fractions:
    c: 1.0
Mix:
  mode: mass
  mass_density: 5.0
  fractions:
    Graphite: 0.5
    c: 0.5
"""
        )
    )
    raw_dict = documents[1]
    d: dict[str, Material] = {}
    for name, data in raw_dict.items():
        d[name] = Material.from_definition(name, data, master_materials=d)

    assert "Graphite" in d
    assert "Mix" in d
    assert d["Mix"].composition is not None
    names = {c.name for c in d["Mix"].composition.constituents()}
    assert names == {"Graphite", "c"}


def test_reject_missing_mode():
    with pytest.raises(ValueError, match="Mode not defined"):
        Material.from_definition("Bad", {"mass_density": 1.0, "fractions": {"c": 1.0}})


def test_reject_missing_density():
    with pytest.raises(ValueError, match="No density defined"):
        Material.from_definition("Bad", {"mode": "mass", "fractions": {"c": 1.0}})


def test_reject_empty_fractions():
    with pytest.raises(ValueError, match="No fractions defined"):
        Material.from_definition(
            "Bad", {"mode": "mass", "mass_density": 1.0, "fractions": {}}
        )


def test_reject_negative_fraction():
    with pytest.raises(ValueError, match="must be positive or zero"):
        Material.from_definition(
            "Bad",
            {"mode": "mass", "mass_density": 1.0, "fractions": {"c": -0.1}},
        )


def test_parse_composition_mode_from_string():
    mat = Material.from_definition(
        "Test",
        {"mode": "atom", "atom_density": 1.0, "fractions": {"c": 1.0}},
    )
    assert mat.composition is not None
    assert mat.composition.mode == CompositionMode.Atom
