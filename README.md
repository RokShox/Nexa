# Nexa: Material Descriptions for Nuclear Analysis

Nexa is a Python-based tool for specifying isotopic compositions of material.

Pre-release components only are implemented. Currently just material handling.

# Install

## Basic Idea

- Configure git and python
- Create a virtual environment
- Clone the nexa repo
- Install nexa as editable. Editable install allows edit of src files without reinstall.

## Windows

- Download/install/configure latest python 3.13 from https://www.python.org/downloads/
- Download/install/configure git
- Working in your repos folder (e.g., C:\Tools\Repos)
- Create a python virtual environment and activate it
- Clone the repo. E.g.,
    - git clone git@github.com:RokShox/nexa.git
- Install the repo as editable
    - cd nexa
    - pip install -e .


## Linux

- Configure git
- Configure python 3.13
- Work in repos directory (e.g., ~/repos)
- Create and activate venv
    - $ python -m venv venv313
    - $ source ./venv313/bin/activate
- Clone the repo
    - $ git clone git@github.com:RokShox/nexa.git
- Pip install as editable
    - $ cd nexa
    - $ pip install -e .

## Uninstall

To uninstall use pip or just delete the venv.

    $ pip uninstall nexa

# Usage

## Invoke

The pip installation creates two executables automatically available on your path:

Run main() in nexa/src/main.py

    
    $ nexa

Run main_cli() which just drops you into a repl loop

    $ nexa-cli

## Basic Usage

See main.py function main() for examples. 

The primary class is Constituent(name, CompositionMode). A composition is a tree of Constituents. A composition knows the mass/atom fractions of its children but does not know its total mass or atom density.

Three dicts are created and are available for defining compositions:
- isos = Isotopes(): Isotope instances keyed by symbol
- elms = Elements(): Element instances keyed by symbol. Not used directly to build compositions.
- abund = Abundances(): Each value is a Constitutent containing isotopes at their natural abundances.

Only sealed Constituents may be added to a parent.
Once sealed, a Constituent may not be modified.
Constituents maintain copies of their child Constituents, not references.

To output to a file, create a filehandle and pass it as argument to display() method. See main().

### Example

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


# Contact

- Charles Henkel (csh@henktech.com)

