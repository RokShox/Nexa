import os
import sys
import glob
import argparse
from pathlib import Path
from nexa.mcnp.output.output import MCNPOutputParser

def main():

    parser = argparse.ArgumentParser(prog="getkeff", description="Parse MCNP output files for criticality results.")
    parser.add_argument("--head", action="store_true", help="Print header", default=False)
    parser.add_argument("files", metavar="FILE", nargs='+', type=str, help="Path to the MCNP output files to parse")
    args = parser.parse_args()

    # Windows compatibility: expand any argument that looks like it contains a glob
    expanded = []
    for arg in args.files:
        if '*' in arg or '?' in arg:
            matches = glob.glob(arg, recursive=False)   # or recursive=True
            if matches:
                expanded.extend(matches)
            else:
                expanded.append(arg)  # keep original if no match (bash-like behavior)
        else:
            expanded.append(arg)

    # Now use expanded instead of args.files
    # print("Processing:", expanded)

    with open(f"keff.txt", 'w', encoding='utf-8') as o:

        for i, file in enumerate(expanded):
            if not os.path.isfile(file):
                print(f"Error: File '{file}' does not exist.")
                sys.exit(1)
            out_name = file
            if not out_name.endswith('o'):
                out_name += 'o'
            case_name = out_name[:-1]

            # parser = MCNPOutputParser(r'D:\Projects\Ampera\Run\v1.0\ckb06umo')
            parser = MCNPOutputParser(out_name)
            parsed_data = parser.parse()
            
            assert 'run_info' in parsed_data
            assert 'tallies' in parsed_data
            assert 'criticality' in parsed_data
            assert 'warnings' in parsed_data
            assert 'errors' in parsed_data
            
            run_info = parsed_data['run_info']
            assert 'cycles' in run_info
            # assert run_info['cycles'] == 1000  # Example expected value
            
            criticality = parsed_data['criticality']
            assert len(criticality) > 0
            # assert 'keff' in criticality[0]
            # assert 'keff_sd' in criticality[0]
            
            summary = parser.get_summary()
            assert summary['has_errors'] is False
            assert summary['has_warnings'] is True
            # assert summary['num_tallies'] > 0

            # print(parsed_data['criticality'])
            if criticality:
                print(f"case\t{criticality[0].header()}", file=o) if args.head and i == 0 else None
                for crit in parsed_data['criticality']:
                    print(f"{case_name}", file=o, end="\t")
                    print(crit, file=o)

                print(f"{'case':<20} {criticality[0].header()}") if args.head and i == 0 else None
                for crit in parsed_data['criticality']:
                    print(f"{case_name:<20}", end=" ")
                    print(crit)


if __name__ == "__main__":
    main()

