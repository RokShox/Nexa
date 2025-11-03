import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SABAssignment:
    """Data class representing S(a,b) assignment from MCNP Table 102."""
    mat: Optional[int]
    nuclide: str
    sab_table: str


class Table102Parser:
    """Parser for MCNP output Table 102 - Assignment of S(a,b) data to nuclides."""
    
    def __init__(self):
        self.assignments: List[SABAssignment] = []
        self._header_found = False
        self._current_mat = None
    
    def parse_lines(self, lines: List[str]) -> List[SABAssignment]:
        """
        Parse lines from MCNP output containing Table 102 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            List of SABAssignment objects
        """
        self.assignments.clear()
        self._header_found = False
        self._current_mat = None
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                if self._is_data_line(line):
                    assignment = self._parse_assignment_line(line)
                    if assignment:
                        self.assignments.append(assignment)
        
        return self.assignments
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 102 header."""
        return "assignment of s(a,b) data to nuclides" in line.lower() and "print table 102" in line.lower()
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        return "comment." in line.lower() or "setting up hash-based" in line.lower()
    
    def _is_data_line(self, line: str) -> bool:
        """Check if line contains assignment data."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Skip header lines
        if "mat" in stripped.lower() and "nuclide" in stripped.lower():
            return False
        
        # Look for lines with nuclide and S(a,b) table data
        # Either starts with mat number or is continuation line with nuclide
        pattern = r'^\s*(\d+\s+\S+\.\d+\w+\s+\S+|\S+\.\d+\w+\s+\S+)'
        return bool(re.match(pattern, stripped))
    
    def _parse_assignment_line(self, line: str) -> Optional[SABAssignment]:
        """
        Parse a single line containing S(a,b) assignment data.
        
        Args:
            line: String containing assignment data
            
        Returns:
            SABAssignment object or None if parsing fails
        """
        try:
            parts = line.strip().split()
            
            if len(parts) < 2:
                return None
            
            # Check if line starts with material number
            if parts[0].isdigit():
                # New material entry: mat nuclide sab_table
                if len(parts) >= 3:
                    self._current_mat = int(parts[0])
                    nuclide = parts[1]
                    sab_table = parts[2]
                else:
                    return None
            else:
                # Continuation line: nuclide sab_table (uses previous mat)
                if len(parts) >= 2:
                    nuclide = parts[0]
                    sab_table = parts[1]
                else:
                    return None
            
            return SABAssignment(
                mat=self._current_mat,
                nuclide=nuclide,
                sab_table=sab_table
            )
            
        except (ValueError, IndexError) as e:
            print(f"Error parsing line: {line.strip()} - {e}")
            return None
    
    def get_assignments_by_mat(self, mat: int) -> List[SABAssignment]:
        """Get all S(a,b) assignments for a specific material."""
        return [assignment for assignment in self.assignments if assignment.mat == mat]
    
    def get_assignment_by_nuclide(self, nuclide: str) -> List[SABAssignment]:
        """Get S(a,b) assignments for a specific nuclide."""
        return [assignment for assignment in self.assignments if assignment.nuclide == nuclide]
    
    def get_unique_materials(self) -> List[int]:
        """Get list of unique material numbers."""
        mats = set()
        for assignment in self.assignments:
            if assignment.mat is not None:
                mats.add(assignment.mat)
        return sorted(list(mats))
    
    def get_unique_sab_tables(self) -> List[str]:
        """Get list of unique S(a,b) tables."""
        tables = set()
        for assignment in self.assignments:
            tables.add(assignment.sab_table)
        return sorted(list(tables))
    
    def to_dict(self) -> List[Dict]:
        """Convert parsed data to list of dictionaries."""
        return [
            {
                'mat': a.mat,
                'nuclide': a.nuclide,
                'sab_table': a.sab_table
            }
            for a in self.assignments
        ]


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1assignment of s(a,b) data to nuclides.                                                                 print table 102",
        "",
        "       mat        nuclide         s(a,b)",
        "        32       1001.01c      h-h2o.53t",
        "        28       1001.01c      h-h2o.49t",
        "        10       1001.01c      h-h2o.49t",
        "   9000101       1001.00c      h-h2o.52t",
        "   1220100       8016.02c      o-uo2.46t",
        "                 8017.02c      o-uo2.46t",
        "                 8018.02c      o-uo2.46t",
        "                92234.02c      u-uo2.46t",
        "                92235.02c      u-uo2.46t",
        "                92238.02c      u-uo2.46t",
        "   1220200       8016.02c      o-uo2.46t",
        "                 8017.02c      o-uo2.46t",
        "                 8018.02c      o-uo2.46t",
        "                92234.02c      u-uo2.46t",
        "                92235.02c      u-uo2.46t",
        "                92238.02c      u-uo2.46t",
        "  comment.  setting up hash-based fast table search for xsec tables"
    ]
    
    parser = Table102Parser()
    assignments = parser.parse_lines(sample_lines)
    
    print(f"Found {len(assignments)} S(a,b) assignments:")
    for assignment in assignments:
        print(f"  Mat: {assignment.mat}, Nuclide: {assignment.nuclide}, S(a,b): {assignment.sab_table}")
    
    print(f"\nUnique materials: {parser.get_unique_materials()}")
    print(f"Unique S(a,b) tables: {parser.get_unique_sab_tables()}")