import re
from pathlib import Path
from typing import Dict, List, Optional, Union

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
    
    def _parse_criticality(self) -> Dict:
        """Parse criticality calculations (k-effective, etc.)."""
        criticality = {}
        
        # Parse k-effective
        keff_pattern = r'the final estimated combined collision/absorption/track-length keff = ([\d.]+) with an estimated standard deviation of ([\d.]+)'
        keff_match = re.search(keff_pattern, self.content, re.IGNORECASE)
        
        if keff_match:
            criticality['keff'] = {
                'value': float(keff_match.group(1)),
                'std_dev': float(keff_match.group(2))
            }
            
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
            'keff': self.parsed_data.get('criticality', {}).get('keff')
        }
        
        return summary