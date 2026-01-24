from dataclasses import dataclass
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

@dataclass
class MCNPOutputKeff:
    """Data class to hold k-effective related information."""
    keff: float
    keff_sd: float
    lifetime: Optional[float] = None
    lifetime_sd: Optional[float] = None
    anecf: Optional[float] = None
    ealf: Optional[float] = None
    nubar: Optional[float] = None

    def __str__(self):
        return f"{self.keff:.6f}\t{self.keff_sd:.6f}\t{self.lifetime:8.4e}\t{self.lifetime_sd:8.4e}\t" \
               f"{self.anecf:8.4e}\t{self.ealf:8.4e}\t{self.nubar:.3f}"

    def header(self) -> str:
        return f"keff\tkeff_sd\tlifetime\tlifetime_sd\tanecf\tealf\tnubar"


class MCNPOutputParser:
    """Parser for MCNP output files."""
    
    def __init__(self, filepath: Union[str, Path]):
        """Initialize the parser with an output file path.
        
        Args:
            filepath: Path to the MCNP output file
        """
        self.filepath = Path(filepath)
        self.content = ""
        self.parsed_data = {}
        
    def read_file(self) -> None:
        """Read the output file content."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Output file not found: {self.filepath}")
        except Exception as e:
            raise Exception(f"Error reading file: {e}")
    
    def parse(self) -> Dict:
        """Parse the MCNP output file and extract key information.
        
        Returns:
            Dictionary containing parsed data
        """
        if not self.content:
            self.read_file()
            
        self.parsed_data = {
            'run_info': self._parse_run_info(),
            'tallies': self._parse_tallies(),
            'criticality': self._parse_criticality(),
            'warnings': self._parse_warnings(),
            'errors': self._parse_errors()
        }
        
        return self.parsed_data
    
    def _parse_run_info(self) -> Dict:
        """Parse basic run information."""
        run_info = {}
        
        # Extract run time
        time_match = re.search(r'run terminated when\s+(\d+)\s+kcode cycles were done', self.content, re.IGNORECASE)
        if time_match:
            run_info['cycles'] = int(time_match.group(1))
            
        return run_info
    
    def _parse_tallies(self) -> Dict:
        """Parse tally results."""
        tallies = {}
        
        # Find tally sections
        tally_pattern = r'1tally\s+(\d+).*?nps\s*=\s*(\d+)'
        matches = re.finditer(tally_pattern, self.content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            tally_num = match.group(1)
            tallies[f'tally_{tally_num}'] = {
                'number': tally_num,
                'nps': int(match.group(2))
            }
            
        return tallies
    
    def _parse_criticality(self) -> List[MCNPOutputKeff]:
        """Parse criticality calculations (k-effective, etc.)."""
        criticality = []
        self.nkeff = 0
        # Parse k-effective
        keff_pattern = r'the final estimated combined collision/absorption/track-length keff = ([\d.]+) with an estimated standard deviation of ([\d.]+)'
        keff_matches = re.finditer(keff_pattern, self.content, re.DOTALL | re.IGNORECASE)
        
        for match in keff_matches:
            criticality.append(MCNPOutputKeff(
                keff=float(match.group(1)),
                keff_sd=float(match.group(2))
            ))
            
        # Parse lifetime
        life_pattern = r'the final combined \(col/abs/tl\) prompt removal lifetime = ([\d.Ee+-]+) seconds with an estimated standard deviation of ([\d.Ee+-]+)'
        life_matches = re.finditer(life_pattern, self.content, re.DOTALL | re.IGNORECASE)
        
        for (i, match) in enumerate(life_matches):
            criticality[i].lifetime = float(match.group(1))
            criticality[i].lifetime_sd = float(match.group(2))

        # Parse anecf
        anecf_pattern = r'the average neutron energy causing fission = ([\d.Ee+-]+) mev'
        anecf_matches = re.finditer(anecf_pattern, self.content, re.DOTALL | re.IGNORECASE)
        
        for (i, match) in enumerate(anecf_matches):
            criticality[i].anecf = float(match.group(1))

        # Parse ealf
        ealf_pattern = r'the energy corresponding to the average neutron lethargy causing fission = ([\d.Ee+-]+) mev'
        ealf_matches = re.finditer(ealf_pattern, self.content, re.DOTALL | re.IGNORECASE)
        
        for (i, match) in enumerate(ealf_matches):
            criticality[i].ealf = float(match.group(1))

        # Parse nubar
        nubar_pattern = r'the average number of neutrons produced per fission = ([\d.Ee+-]+)'
        nubar_matches = re.finditer(nubar_pattern, self.content, re.DOTALL | re.IGNORECASE)
        
        for (i, match) in enumerate(nubar_matches):
            criticality[i].nubar = float(match.group(1))
            self.nkeff += 1

        return criticality
    
    def _parse_warnings(self) -> List[str]:
        """Parse warning messages."""
        warnings = []
        warning_pattern = r'warning\..*'
        matches = re.finditer(warning_pattern, self.content, re.IGNORECASE)
        
        for match in matches:
            warnings.append(match.group(0).strip())
            
        return warnings
    
    def _parse_errors(self) -> List[str]:
        """Parse error messages."""
        errors = []
        error_pattern = r'fatal error\..*'
        matches = re.finditer(error_pattern, self.content, re.IGNORECASE)
        
        for match in matches:
            errors.append(match.group(0).strip())
            
        return errors
    
    def get_summary(self) -> Dict:
        """Get a summary of the parsed output.
        
        Returns:
            Dictionary with summary information
        """
        if not self.parsed_data:
            self.parse()
            
        summary = {
            'file_path': str(self.filepath),
            'has_errors': len(self.parsed_data.get('errors', [])) > 0,
            'has_warnings': len(self.parsed_data.get('warnings', [])) > 0,
            'num_tallies': len(self.parsed_data.get('tallies', {})),
        }
        
        return summary