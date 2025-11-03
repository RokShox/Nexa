import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class IsotopeData:
    """Data class representing isotope cross-section data."""
    zaid_library: str  # e.g., "1001.00c"
    length: int
    description: str  # Multi-line description
    mat_identifier: str  # e.g., "mat 125"
    evaluation_date: str  # e.g., "05/02/18"
    source_file: str  # The file this isotope data comes from


@dataclass
class CrossSectionFile:
    """Data class representing a cross-section data file and its isotopes."""
    filename: str
    isotopes: List[IsotopeData] = field(default_factory=list)


class Table100Parser:
    """Parser for MCNP output Table 100 - Cross-section tables."""
    
    def __init__(self):
        self.xsdir_path: Optional[str] = None
        self.cross_section_files: List[CrossSectionFile] = []
        self.isotopes: Dict[str, IsotopeData] = {}  # zaid_library -> IsotopeData
        self._header_found = False
        self._current_file = None
        self._current_isotope = None
        self._collecting_description = False
    
    def parse_lines(self, lines: List[str]) -> Dict[str, IsotopeData]:
        """
        Parse lines from MCNP output containing Table 100 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Dictionary mapping zaid_library -> IsotopeData
        """
        self.xsdir_path = None
        self.cross_section_files.clear()
        self.isotopes.clear()
        self._header_found = False
        self._current_file = None
        self._current_isotope = None
        self._collecting_description = False
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                if self._is_xsdir_line(line):
                    self.xsdir_path = self._extract_xsdir_path(line)
                    continue
                
                if self._is_file_header_line(line):
                    filename = self._extract_filename(line)
                    if filename:
                        self._current_file = CrossSectionFile(filename=filename)
                        self.cross_section_files.append(self._current_file)
                    continue
                
                if self._is_isotope_data_line(line):
                    self._finalize_current_isotope()
                    isotope_data = self._parse_isotope_data_line(line)
                    if isotope_data and self._current_file:
                        isotope_data.source_file = self._current_file.filename
                        self._current_isotope = isotope_data
                        self._collecting_description = True
                    continue
                
                if self._collecting_description and self._is_description_continuation(line):
                    if self._current_isotope:
                        # Add to description with newline
                        if self._current_isotope.description:
                            self._current_isotope.description += "\n" + line.rstrip()
                        else:
                            self._current_isotope.description = line.rstrip()
                    continue
                
                # If we hit a non-continuation line, finalize current isotope
                if self._collecting_description and not self._is_description_continuation(line):
                    self._finalize_current_isotope()
        
        # Finalize last isotope if any
        self._finalize_current_isotope()
        
        return self.isotopes
    
    def _finalize_current_isotope(self):
        """Finalize the current isotope being processed."""
        if self._current_isotope and self._current_file:
            self._current_file.isotopes.append(self._current_isotope)
            self.isotopes[self._current_isotope.zaid_library] = self._current_isotope
            self._current_isotope = None
            self._collecting_description = False
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 100 header."""
        return "cross-section tables" in line.lower() and "print table 100" in line.lower()
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Look for next table or other indicators
        return ("print table" in line.lower() and "table 100" not in line.lower()) or \
               line.startswith("1") and any(x in line.lower() for x in [
                   "probid", "keff results", "run terminated", "neutron creation", 
                   "neutron loss", "neutron activity", "weight balance"
               ])
    
    def _is_xsdir_line(self, line: str) -> bool:
        """Check if line contains XSDIR path information."""
        return "XSDIR used:" in line
    
    def _extract_xsdir_path(self, line: str) -> str:
        """Extract XSDIR path from line."""
        match = re.search(r"XSDIR used:\s*(.+)", line)
        return match.group(1).strip() if match else ""
    
    def _is_file_header_line(self, line: str) -> bool:
        """Check if line contains 'tables from file' header."""
        return "tables from file" in line.lower()
    
    def _extract_filename(self, line: str) -> Optional[str]:
        """Extract filename from 'tables from file' line."""
        match = re.search(r"tables from file\s+(.+)", line, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _is_isotope_data_line(self, line: str) -> bool:
        """Check if line contains isotope data (starts with zaid.library format)."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Look for pattern like "1001.00c" at the beginning
        parts = stripped.split()
        if len(parts) >= 5:
            # First part should match zaid.library pattern
            zaid_library_pattern = r'^\d+\.\d+[a-z]$'
            return bool(re.match(zaid_library_pattern, parts[0]))
        
        return False
    
    def _parse_isotope_data_line(self, line: str) -> Optional[IsotopeData]:
        """Parse isotope data line (fixed format)."""
        try:
            # Fixed format parsing - positions based on the example
            zaid_library = line[3:12].strip()  # e.g., "1001.00c"
            length_str = line[12:20].strip()   # e.g., "5296"
            
            # Description starts around column 20 and goes to mat identifier
            # Find the mat identifier (should be near the end)
            mat_match = re.search(r'(mat\s+\d+)', line)
            if not mat_match:
                return None
            
            mat_start = mat_match.start()
            mat_identifier = mat_match.group(1)
            
            # Description is between length and mat identifier
            description = line[20:mat_start].strip()
            
            # Date should be at the end after mat identifier
            date_match = re.search(r'(\d{2}/\d{2}/\d{2})\s*$', line)
            evaluation_date = date_match.group(1) if date_match else ""
            
            try:
                length = int(length_str)
            except ValueError:
                return None
            
            return IsotopeData(
                zaid_library=zaid_library,
                length=length,
                description=description,
                mat_identifier=mat_identifier,
                evaluation_date=evaluation_date,
                source_file=""  # Will be set by caller
            )
            
        except (IndexError, ValueError):
            return None
    
    def _is_description_continuation(self, line: str) -> bool:
        """Check if line is a continuation of the isotope description."""
        if not line.strip():
            return False
        
        # Check if line starts with significant whitespace (indented)
        if not line.startswith('                     '):  # About 21 spaces
            return False
        
        # Make sure it's not another isotope line or file header
        if self._is_isotope_data_line(line) or self._is_file_header_line(line):
            return False
        
        return True
    
    def get_isotope_data(self, zaid_library: str) -> Optional[IsotopeData]:
        """Get data for a specific isotope."""
        return self.isotopes.get(zaid_library)
    
    def get_all_isotopes(self) -> List[str]:
        """Get list of all isotope identifiers."""
        return sorted(list(self.isotopes.keys()))
    
    def get_isotopes_from_file(self, filename: str) -> List[IsotopeData]:
        """Get all isotopes from a specific file."""
        for cs_file in self.cross_section_files:
            if cs_file.filename == filename:
                return cs_file.isotopes
        return []
    
    def get_all_files(self) -> List[str]:
        """Get list of all cross-section data files."""
        return [cs_file.filename for cs_file in self.cross_section_files]
    
    def get_isotopes_by_zaid(self, zaid: int) -> List[IsotopeData]:
        """Get all isotopes with a specific ZAID (different libraries)."""
        result = []
        for isotope in self.isotopes.values():
            # Extract ZAID from zaid_library (e.g., "1001" from "1001.00c")
            zaid_part = isotope.zaid_library.split('.')[0]
            try:
                if int(zaid_part) == zaid:
                    result.append(isotope)
            except ValueError:
                continue
        return result
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        return {
            'xsdir_path': self.xsdir_path,
            'cross_section_files': [
                {
                    'filename': cs_file.filename,
                    'isotopes': [
                        {
                            'zaid_library': isotope.zaid_library,
                            'length': isotope.length,
                            'description': isotope.description,
                            'mat_identifier': isotope.mat_identifier,
                            'evaluation_date': isotope.evaluation_date,
                            'source_file': isotope.source_file
                        }
                        for isotope in cs_file.isotopes
                    ]
                }
                for cs_file in self.cross_section_files
            ],
            'isotopes': {
                zaid_lib: {
                    'zaid_library': isotope.zaid_library,
                    'length': isotope.length,
                    'description': isotope.description,
                    'mat_identifier': isotope.mat_identifier,
                    'evaluation_date': isotope.evaluation_date,
                    'source_file': isotope.source_file
                }
                for zaid_lib, isotope in self.isotopes.items()
            }
        }


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1cross-section tables                                                                                   print table 100",
        "     XSDIR used: \\\\HTC01\\Dacono\\mcnp6.3\\MCNP_DATA/xsdir_mcnp6.3",
        "",
        "     table    length",
        "",
        "                        tables from file Lib80x/H/1001.800nc",
        "",
        "   1001.00c    5296  H1 Lib80x (jlconlin)  Reference LA-UR-18-24034 by Conlin, J.L, et al.        mat 125      05/02/18",
        "                     Energy range:   1.00000E-11  to  2.00000E+01 MeV.",
        "                     particle-production data for deuterons being expunged from   1001.00c",
        "                     temperature = 2.5301E-08 adjusted at collisions.",
        "",
        "                        tables from file Lib80x/H/1002.800nc",
        "",
        "   1002.00c   39776  H2 Lib80x (jlconlin)  Reference LA-UR-18-24034 by Conlin, J.L, et al.        mat 128      05/01/18",
        "                     Energy range:   1.00000E-11  to  1.50000E+02 MeV.",
        "                     particle-production data for protons   being expunged from   1002.00c",
        "                     particle-production data for tritons   being expunged from   1002.00c",
        "                     temperature = 2.5301E-08 adjusted at collisions."
    ]
    
    parser = Table100Parser()
    isotopes = parser.parse_lines(sample_lines)
    
    print(f"XSDIR path: {parser.xsdir_path}")
    print(f"Found {len(isotopes)} isotopes from {len(parser.cross_section_files)} files:")
    
    for zaid_lib, isotope in isotopes.items():
        print(f"\n{zaid_lib}:")
        print(f"  Length: {isotope.length}")
        print(f"  File: {isotope.source_file}")
        print(f"  Mat: {isotope.mat_identifier}")
        print(f"  Date: {isotope.evaluation_date}")
        print(f"  Description: {isotope.description[:50]}...")
    
    print(f"\nAll files: {parser.get_all_files()}")
    print(f"H-1 isotopes: {[iso.zaid_library for iso in parser.get_isotopes_by_zaid(1001)]}")