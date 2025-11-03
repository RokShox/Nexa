import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class NuclideActivity:
    """Data class representing neutron activity for a nuclide."""
    nuclide_id: str  # e.g., "22046.00c"
    atom_fraction: Optional[float] = None  # Only in cell-by-cell data
    total_collisions: int = 0
    collisions_weight: float = 0.0
    weight_lost_to_capture: float = 0.0
    weight_gain_by_fission: float = 0.0
    weight_gain_by_nxn: float = 0.0
    photons_produced: int = 0
    photon_weight_produced: float = 0.0
    avg_photon_energy: float = 0.0


@dataclass
class CellActivity:
    """Data class representing neutron activity for all nuclides in a cell."""
    cell_index: int
    cell_name: int
    nuclides: Dict[str, NuclideActivity] = field(default_factory=dict)


@dataclass
class TableTotals:
    """Data class representing table totals."""
    total_collisions: int
    collisions_weight: float
    weight_lost_to_capture: float
    weight_gain_by_fission: float
    weight_gain_by_nxn: float
    photons_produced: int
    photon_weight_produced: float
    avg_photon_energy: float


class Table140Parser:
    """Parser for MCNP output Table 140 - Neutron activity by nuclide."""
    
    def __init__(self):
        self.cells: Dict[int, CellActivity] = {}
        self.nuclide_totals: Dict[str, NuclideActivity] = {}
        self.table_totals: Optional[TableTotals] = None
        self._header_found = False
        self._in_cell_section = True
        self._current_cell = None
    
    def parse_lines(self, lines: List[str]) -> Tuple[Dict[int, CellActivity], Dict[str, NuclideActivity], Optional[TableTotals]]:
        """
        Parse lines from MCNP output containing Table 140 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Tuple of (cells_dict, nuclide_totals_dict, table_totals)
        """
        self.cells.clear()
        self.nuclide_totals.clear()
        self.table_totals = None
        self._header_found = False
        self._in_cell_section = True
        self._current_cell = None
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                if self._is_column_header(line):
                    continue
                
                if self._is_nuclide_totals_header(line):
                    self._in_cell_section = False
                    continue
                
                if self._in_cell_section:
                    if self._is_cell_header_line(line):
                        cell_data = self._parse_cell_header(line)
                        if cell_data:
                            cell_index, cell_name = cell_data
                            self._current_cell = CellActivity(cell_index=cell_index, cell_name=cell_name)
                            self.cells[cell_name] = self._current_cell
                            
                            # Check if nuclide data is on same line
                            nuclide_data = self._parse_nuclide_line(line, include_atom_fraction=True)
                            if nuclide_data and self._current_cell:
                                self._current_cell.nuclides[nuclide_data.nuclide_id] = nuclide_data
                        continue
                    
                    if self._is_nuclide_continuation_line(line):
                        nuclide_data = self._parse_nuclide_line(line, include_atom_fraction=True)
                        if nuclide_data and self._current_cell:
                            self._current_cell.nuclides[nuclide_data.nuclide_id] = nuclide_data
                        continue
                    
                    if self._is_table_totals_line(line):
                        self.table_totals = self._parse_totals_line(line)
                        continue
                
                else:  # In nuclide totals section
                    if self._is_nuclide_total_line(line):
                        nuclide_data = self._parse_nuclide_line(line, include_atom_fraction=False)
                        if nuclide_data:
                            self.nuclide_totals[nuclide_data.nuclide_id] = nuclide_data
                        continue
        
        return self.cells, self.nuclide_totals, self.table_totals
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 140 header."""
        return "neutron activity of each nuclide in each cell" in line.lower() and "print table 140" in line.lower()
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        stripped = line.strip()
        if not stripped:
            return False
        
        return ("print table" in line.lower() and "table 140" not in line.lower()) or \
               line.startswith("1") and any(x in line.lower() for x in [
                   "probid", "keff results", "run terminated"
               ])
    
    def _is_column_header(self, line: str) -> bool:
        """Check if line contains column headers."""
        return any(header in line.lower() for header in [
            "cell index", "cell name", "nuclides", "atom fraction", 
            "total collisions", "wgt. lost", "photons produced"
        ])
    
    def _is_nuclide_totals_header(self, line: str) -> bool:
        """Check if line is the header for nuclide totals section."""
        return "total over all cells by nuclide" in line.lower()
    
    def _is_cell_header_line(self, line: str) -> bool:
        """Check if line starts a new cell."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Should start with cell index and cell name (numbers)
        parts = stripped.split()
        if len(parts) >= 2:
            try:
                int(parts[0])  # cell index
                int(parts[1])  # cell name
                return True
            except ValueError:
                pass
        
        return False
    
    def _parse_cell_header(self, line: str) -> Optional[Tuple[int, int]]:
        """Parse cell header to extract cell index and name."""
        try:
            parts = line.strip().split()
            if len(parts) >= 2:
                cell_index = int(parts[0])
                cell_name = int(parts[1])
                return cell_index, cell_name
        except (ValueError, IndexError):
            pass
        return None
    
    def _is_nuclide_continuation_line(self, line: str) -> bool:
        """Check if line is a continuation with nuclide data."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Should start with significant whitespace and contain nuclide ID
        if line.startswith('                     '):  # About 21 spaces
            parts = stripped.split()
            if len(parts) >= 1:
                # Check if first part looks like a nuclide ID
                return bool(re.match(r'\d+\.\d+[a-z]', parts[0]))
        
        return False
    
    def _is_table_totals_line(self, line: str) -> bool:
        """Check if line contains table totals."""
        stripped = line.strip()
        return stripped.startswith("total") and "over all cells" not in stripped.lower()
    
    def _is_nuclide_total_line(self, line: str) -> bool:
        """Check if line contains nuclide total data."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Should start with nuclide ID
        parts = stripped.split()
        if len(parts) >= 8:  # Minimum expected columns for nuclide total
            return bool(re.match(r'\d+\.\d+[a-z]', parts[0]))
        
        return False
    
    def _parse_nuclide_line(self, line: str, include_atom_fraction: bool) -> Optional[NuclideActivity]:
        """Parse a line containing nuclide activity data."""
        try:
            parts = line.strip().split()
            
            # Find the nuclide ID (looks like "22046.00c")
            nuclide_idx = None
            for i, part in enumerate(parts):
                if re.match(r'\d+\.\d+[a-z]', part):
                    nuclide_idx = i
                    break
            
            if nuclide_idx is None:
                return None
            
            nuclide_id = parts[nuclide_idx]
            
            # Parse values starting after nuclide ID
            values_start = nuclide_idx + 1
            
            if include_atom_fraction:
                if len(parts) < values_start + 8:
                    return None
                atom_fraction = float(parts[values_start])
                data_start = values_start + 1
            else:
                if len(parts) < values_start + 7:
                    return None
                atom_fraction = None
                data_start = values_start
            
            total_collisions = int(parts[data_start])
            collisions_weight = float(parts[data_start + 1])
            weight_lost_to_capture = float(parts[data_start + 2])
            weight_gain_by_fission = float(parts[data_start + 3])
            weight_gain_by_nxn = float(parts[data_start + 4])
            photons_produced = int(parts[data_start + 5])
            photon_weight_produced = float(parts[data_start + 6])
            avg_photon_energy = float(parts[data_start + 7])
            
            return NuclideActivity(
                nuclide_id=nuclide_id,
                atom_fraction=atom_fraction,
                total_collisions=total_collisions,
                collisions_weight=collisions_weight,
                weight_lost_to_capture=weight_lost_to_capture,
                weight_gain_by_fission=weight_gain_by_fission,
                weight_gain_by_nxn=weight_gain_by_nxn,
                photons_produced=photons_produced,
                photon_weight_produced=photon_weight_produced,
                avg_photon_energy=avg_photon_energy
            )
            
        except (ValueError, IndexError):
            return None
    
    def _parse_totals_line(self, line: str) -> Optional[TableTotals]:
        """Parse table totals line."""
        try:
            parts = line.strip().split()
            if len(parts) < 8:
                return None
            
            # Skip "total" and parse numeric values
            total_collisions = int(parts[1])
            collisions_weight = float(parts[2])
            weight_lost_to_capture = float(parts[3])
            weight_gain_by_fission = float(parts[4])
            weight_gain_by_nxn = float(parts[5])
            photons_produced = int(parts[6])
            photon_weight_produced = float(parts[7])
            avg_photon_energy = float(parts[8])
            
            return TableTotals(
                total_collisions=total_collisions,
                collisions_weight=collisions_weight,
                weight_lost_to_capture=weight_lost_to_capture,
                weight_gain_by_fission=weight_gain_by_fission,
                weight_gain_by_nxn=weight_gain_by_nxn,
                photons_produced=photons_produced,
                photon_weight_produced=photon_weight_produced,
                avg_photon_energy=avg_photon_energy
            )
            
        except (ValueError, IndexError):
            return None
    
    def get_cell_activity(self, cell_name: int) -> Optional[CellActivity]:
        """Get activity data for a specific cell."""
        return self.cells.get(cell_name)
    
    def get_nuclide_total(self, nuclide_id: str) -> Optional[NuclideActivity]:
        """Get total activity for a specific nuclide across all cells."""
        return self.nuclide_totals.get(nuclide_id)
    
    def get_all_cells(self) -> List[int]:
        """Get list of all cell names."""
        return sorted(list(self.cells.keys()))
    
    def get_all_nuclides(self) -> List[str]:
        """Get list of all nuclide IDs."""
        nuclides = set()
        for cell in self.cells.values():
            nuclides.update(cell.nuclides.keys())
        nuclides.update(self.nuclide_totals.keys())
        return sorted(list(nuclides))
    
    def get_nuclide_in_cell(self, cell_name: int, nuclide_id: str) -> Optional[NuclideActivity]:
        """Get activity for a specific nuclide in a specific cell."""
        cell = self.get_cell_activity(cell_name)
        if cell:
            return cell.nuclides.get(nuclide_id)
        return None
    
    def get_cells_with_nuclide(self, nuclide_id: str) -> List[int]:
        """Get list of cells that contain a specific nuclide."""
        result = []
        for cell_name, cell in self.cells.items():
            if nuclide_id in cell.nuclides:
                result.append(cell_name)
        return sorted(result)
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        return {
            'cells': {
                cell_name: {
                    'cell_index': cell.cell_index,
                    'cell_name': cell.cell_name,
                    'nuclides': {
                        nuclide_id: {
                            'nuclide_id': nuclide.nuclide_id,
                            'atom_fraction': nuclide.atom_fraction,
                            'total_collisions': nuclide.total_collisions,
                            'collisions_weight': nuclide.collisions_weight,
                            'weight_lost_to_capture': nuclide.weight_lost_to_capture,
                            'weight_gain_by_fission': nuclide.weight_gain_by_fission,
                            'weight_gain_by_nxn': nuclide.weight_gain_by_nxn,
                            'photons_produced': nuclide.photons_produced,
                            'photon_weight_produced': nuclide.photon_weight_produced,
                            'avg_photon_energy': nuclide.avg_photon_energy
                        }
                        for nuclide_id, nuclide in cell.nuclides.items()
                    }
                }
                for cell_name, cell in self.cells.items()
            },
            'nuclide_totals': {
                nuclide_id: {
                    'nuclide_id': nuclide.nuclide_id,
                    'total_collisions': nuclide.total_collisions,
                    'collisions_weight': nuclide.collisions_weight,
                    'weight_lost_to_capture': nuclide.weight_lost_to_capture,
                    'weight_gain_by_fission': nuclide.weight_gain_by_fission,
                    'weight_gain_by_nxn': nuclide.weight_gain_by_nxn,
                    'photons_produced': nuclide.photons_produced,
                    'photon_weight_produced': nuclide.photon_weight_produced,
                    'avg_photon_energy': nuclide.avg_photon_energy
                }
                for nuclide_id, nuclide in self.nuclide_totals.items()
            },
            'table_totals': {
                'total_collisions': self.table_totals.total_collisions,
                'collisions_weight': self.table_totals.collisions_weight,
                'weight_lost_to_capture': self.table_totals.weight_lost_to_capture,
                'weight_gain_by_fission': self.table_totals.weight_gain_by_fission,
                'weight_gain_by_nxn': self.table_totals.weight_gain_by_nxn,
                'photons_produced': self.table_totals.photons_produced,
                'photon_weight_produced': self.table_totals.photon_weight_produced,
                'avg_photon_energy': self.table_totals.avg_photon_energy
            } if self.table_totals else None
        }


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1neutron activity of each nuclide in each cell, per source particle                                     print table 140",
        "",
        "      cell     cell   nuclides     atom       total  collisions   wgt. lost   wgt. gain   wgt. gain     photons  photon wgt  avg photon",
        "     index     name            fraction  collisions    * weight  to capture  by fission   by (n,xn)    produced    produced      energy",
        "",
        "         6        6  22046.00c 8.25E-02     9845075  9.8451E-02  5.5165E-03  0.0000E+00  2.0000E-08           0  0.0000E+00  0.0000E+00",
        "                     22047.00c 7.44E-02    13745244  1.3745E-01  1.3944E-02  0.0000E+00  4.5000E-07           0  0.0000E+00  0.0000E+00",
        "         7        7   4009.00c 1.00E+00  2843576766  2.8436E+01  2.7830E-02  0.0000E+00  1.7589E-02           0  0.0000E+00  0.0000E+00",
        "",
        "              total                      6547221092  6.5472E+01  1.0856E+00  3.8761E-01  1.7810E-02           0  0.0000E+00  0.0000E+00",
        "",
        "        total over all cells by nuclide       total  collisions   wgt. lost   wgt. gain   wgt. gain     photons  photon wgt  avg photon",
        "                                         collisions    * weight  to capture  by fission   by (n,xn)    produced    produced      energy",
        "",
        "                      2003.00c                   67  6.7000E-07  6.7000E-07  0.0000E+00  0.0000E+00           0  0.0000E+00  0.0000E+00",
        "                      4009.00c           2843576766  2.8436E+01  2.7830E-02  0.0000E+00  1.7589E-02           0  0.0000E+00  0.0000E+00"
    ]
    
    parser = Table140Parser()
    cells, nuclide_totals, table_totals = parser.parse_lines(sample_lines)
    
    print(f"Found {len(cells)} cells and {len(nuclide_totals)} nuclide totals")
    
    print(f"\nCells:")
    for cell_name, cell in cells.items():
        print(f"  Cell {cell_name}: {len(cell.nuclides)} nuclides")
        for nuclide_id, nuclide in list(cell.nuclides.items())[:2]:  # Show first 2
            print(f"    {nuclide_id}: {nuclide.total_collisions:,} collisions, atom fraction={nuclide.atom_fraction:.2e}")
    
    print(f"\nNuclide totals:")
    for nuclide_id, nuclide in list(nuclide_totals.items())[:3]:  # Show first 3
        print(f"  {nuclide_id}: {nuclide.total_collisions:,} collisions")
    
    if table_totals:
        print(f"\nTable totals: {table_totals.total_collisions:,} total collisions")
    
    print(f"\nAll nuclides: {parser.get_all_nuclides()[:5]}...")  # Show first 5