import sys
import os
import argparse
import re
from pathlib import Path
from nexa.mcnp.output import MctalParser, MctalOverview


def main():
    """Parse MCNP MCTAL files provided as command-line arguments and print summary information.
    
    mctal file name should match <series><ii>b<dd>d[0|1]m
        where <series> is the case series, <ii> is case index<dd> is the two-digit burn step,
        'b' indicates burnup, d indicates depletion step type 0=predictor 1=corrector
    
    Usage:        python getMCNPFlux.py <MCTAL_FILE> [--tally TALLY_NUM] [--origen]
    Example:      python getMCNPFlux.py example.mctal -t 4 --origen
    """

    parser = argparse.ArgumentParser(prog="getMCNPFlux", description="Parse MCNP MCTAL file and extract flux for Ampera analysis.")
    # parser.add_argument("file", metavar="FILE", type=str, nargs="+", help="Path to the MCTAL file to parse")
    parser.add_argument("file", metavar="MCTAL_FILE", type=str, help="Path to the MCTAL file to parse")
    parser.add_argument("--tally", "-t", metavar="TALLY_NUM", type=int, default=4, help="Tally number to extract flux from (default: 4)")
    parser.add_argument("--origen", action="store_true", help="Output groups from high to low energy for ORIGEN")
    args = parser.parse_args()

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            print(f"Processing file: {args.file}")
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File not found: {args.file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    parser = MctalParser()
    mctal: MctalOverview = parser.parse_lines(lines)
    mctal.case = Path(args.file).stem[:-1] # remove trailing m
    print(mctal)
    for tal_num in mctal.tally_nums:
        tal = mctal.tallies.get(tal_num, None)
        if tal:
            print(f"Tally {tal.tally_num} has {len(tal.vals_data)} VALS entries")
            print(f"value at tfc bin {tal.tfc_bin}: {tal.value(tal.tfc_bin)}")

    # 'F', 'D', 'U', 'S', 'M', 'C', 'E', 'T'
    fixed = {"D": 0, "U": 0, "S": 0, "M": 0, "C": 0, "T": 0}
    # Think of free list as an odometer with the last enetry iterating on the inner loop
    free = ["F", "E"]
    tal = mctal.tallies.get(14, None)
    print(f"\nTally details:\n{tal}")
    if tal:
        # print(f"\nIterating COORDS data for Tally 14 with free params {free} and fixed {fixed}:")
        # it = tal.iterator()
        # # for coord in it.iter_coords(free, fixed, format="tuple"):
        # #     print(f"{coord}: {tal.value(coord)}\n")
        # iter_gen = it.iter_coords(free, fixed, format="tuple")
        # for f in range(it.sizes["F"]):
        #     for e in range(it.sizes["E"]):
        #         coord = next(iter_gen)
        #         print(f"{tal.value(coord)[0]:10.6e} {tal.value(coord)[1]:.4f} ", end="")
        #     print()

        # Output for ORIGEN
        reCase: re = re.compile(r'^(?P<series>\w+)(?P<index>\d{2})b(?P<step>\d{2})d(?P<depl>\d)$')
        match = reCase.match(mctal.case)
        if match:
            case_series: str = f"{match.group('series')}"
            case_index: int = int(f"{match.group('index')}")
            case_step: int = int(f"{match.group('step')}")
            case_depl: int = int(f"{match.group('depl')}")
        else:
            raise ValueError(f"Invalid MCTAL case name format: {mctal.case}")

        if args.origen:
            print("\nORIGEN format (high to low energy):")
            nper = 6
            it = tal.iterator()
            free = ["F", "E"]
            iter_gen = it.iter_coords(free, fixed, format="tuple")

            for f in range(it.sizes["F"]):
                case_name = f"{case_series}{case_index:02d}b{case_step:02d}z{f+1:02d}d{case_depl}Flux"
                with open(f"{case_name}", 'w', encoding='utf-8') as o:
                    flux = []
                    # open output file
                    for e in range(it.sizes["E"]):
                        coord = next(iter_gen)
                        flux.append(tal.value(coord)[0])  # get flux value
                    line = "    "
                    for bin, val in enumerate(reversed(flux)):
                        if bin == 0:
                            total_flux = val
                            print(f"Total Flux:\t{total_flux:10.6e}\tHigh to low energy", file=o)
                        else:
                            line += f"{val:10.6e} "
                            if bin % nper == 0 or bin == len(flux) - 1:
                                print(line.rstrip(), file=o)
                                line = "    "

