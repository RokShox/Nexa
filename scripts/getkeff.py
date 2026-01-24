import os
import sys
from pathlib import Path
from nexa.mcnp.output.output import MCNPOutputParser

def test_mcnp_output_parser():

    run_dir = Path(r'D:\Projects\DeepFission\Run\v1.1')
    os.chdir(run_dir)

    out_name = sys.argv[1] if len(sys.argv) > 1 else print ("Usage: getkeff.py <output_name>") & sys.exit(1)
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
    with open(f"{case_name}.keff", 'w', encoding='utf-8') as o:
        print(criticality[0].header() if len(criticality) > 0 else "", file=o)
        for crit in parsed_data['criticality']:
            print(crit, file=o)

if __name__ == "__main__":
    test_mcnp_output_parser()

