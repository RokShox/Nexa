from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CellData:
    """Data class representing cell data from Table 60."""
    cell_index: int
    cell_number: int
    material_number: Optional[int]
    is_source_cell: bool
    atom_density: float
    gram_density: float
    volume: float
    mass: float
    pieces: int
    neutron_importance: float
    photon_importance: float


@dataclass
class TableTotals:
    """Data class representing table totals."""
    total_volume: float
    total_mass: float


class Table060Parser:
    """Parser for MCNP output Table 60 - Cells."""
    
    def __init__(self):
        self.cells: Dict[int, CellData] = {}
        self.totals: Optional[TableTotals] = None
        self._header_found = False
    
    def parse_lines(self, lines: List[str]) -> Dict[int, CellData]:
        """
        Parse lines from MCNP output containing Table 60 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Dictionary mapping cell_number -> CellData
        """
        self.cells.clear()
        self.totals = None
        self._header_found = False
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                if self._is_header_line(line):
                    continue
                
                if self._is_totals_line(line):
                    self.totals = self._parse_totals_line(line)
                    continue
                
                if self._is_data_line(line):
                    cell_data = self._parse_data_line(line)
                    if cell_data:
                        self.cells[cell_data.cell_number] = cell_data
        
        return self.cells
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 60 header."""
        return "cells" in line.lower() and "print table 60" in line.lower() and line.startswith("1")
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Look for next table or other indicators
        return ("print table" in line.lower() and "table 60" not in line.lower()) or \
               line.startswith("1") and any(x in line.lower() for x in [
                   "probid", "keff results", "run terminated", "neutron creation", 
                   "neutron loss", "neutron activity", "weight balance", "material composition"
               ])
    
    def _is_header_line(self, line: str) -> bool:
        """Check if line contains column headers."""
        stripped = line.strip()
        return any(header in stripped.lower() for header in [
            "cell", "mat", "atom", "gram", "density", "volume", "mass", 
            "pieces", "importance", "neutron", "photon"
        ]) and not self._is_data_line(line) and not self._is_totals_line(line)
    
    def _is_totals_line(self, line: str) -> bool:
        """Check if line contains totals."""
        return line.strip().startswith("total")
    
    def _is_data_line(self, line: str) -> bool:
        """Check if line contains cell data."""
        stripped = line.strip()
        if not stripped or stripped.startswith("total"):
            return False
        
        # Check if line starts with numbers (cell index and cell number)
        parts = stripped.split()
        if len(parts) >= 10:  # Minimum expected columns
            try:
                # First two parts should be integers (cell index and cell number)
                int(parts[0])
                int(parts[1])
                return True
            except ValueError:
                pass
        
        return False
    
    def _parse_material_field(self, mat_field: str) -> Tuple[Optional[int], bool]:
        """
        Parse material field to extract material number and source indicator.
        
        Args:
            mat_field: String containing material number, possibly with 's' suffix
            
        Returns:
            Tuple of (material_number, is_source_cell)
        """
        if not mat_field or mat_field == "0":
            return None, False
        
        is_source = mat_field.endswith('s')
        if is_source:
            mat_field = mat_field.rstrip('s')
        
        try:
            material_number = int(mat_field)
            return material_number, is_source
        except ValueError:
            return None, False
    
    def _parse_data_line(self, line: str) -> Optional[CellData]:
        """Parse a data line containing cell information."""
        try:
            parts = line.strip().split()
            if len(parts) < 10:
                return None
            
            cell_index = int(parts[0])
            cell_number = int(parts[1])
            
            # Parse material field (may have 's' suffix for source cells)
            material_number, is_source_cell = self._parse_material_field(parts[2])
            
            atom_density = float(parts[3])
            gram_density = float(parts[4])
            volume = float(parts[5])
            mass = float(parts[6])
            pieces = int(parts[7])
            neutron_importance = float(parts[8])
            photon_importance = float(parts[9])
            
            return CellData(
                cell_index=cell_index,
                cell_number=cell_number,
                material_number=material_number,
                is_source_cell=is_source_cell,
                atom_density=atom_density,
                gram_density=gram_density,
                volume=volume,
                mass=mass,
                pieces=pieces,
                neutron_importance=neutron_importance,
                photon_importance=photon_importance
            )
            
        except (ValueError, IndexError):
            return None
    
    def _parse_totals_line(self, line: str) -> Optional[TableTotals]:
        """Parse totals line."""
        try:
            parts = line.strip().split()
            if len(parts) < 3:
                return None
            
            # Skip "total" and get volume and mass
            total_volume = float(parts[1])
            total_mass = float(parts[2])
            
            return TableTotals(
                total_volume=total_volume,
                total_mass=total_mass
            )
            
        except (ValueError, IndexError):
            return None
    
    def get_cell_data(self, cell_number: int) -> Optional[CellData]:
        """Get data for a specific cell."""
        return self.cells.get(cell_number)
    
    def get_all_cells(self) -> List[int]:
        """Get list of all cell numbers."""
        return sorted(list(self.cells.keys()))
    
    def get_cell_material(self, cell_number: int) -> Optional[int]:
        """
        Get material number for a specific cell (without source indicator).
        
        Args:
            cell_number: Cell number to query
            
        Returns:
            Material number or None if cell has no material or doesn't exist
        """
        cell_data = self.cells.get(cell_number)
        return cell_data.material_number if cell_data else None
    
    def is_source_cell(self, cell_number: int) -> bool:
        """
        Check if a cell is a source cell.
        
        Args:
            cell_number: Cell number to query
            
        Returns:
            True if cell is a source cell, False otherwise
        """
        cell_data = self.cells.get(cell_number)
        return cell_data.is_source_cell if cell_data else False
    
    def get_source_cells(self) -> List[int]:
        """Get list of all source cells."""
        return [
            cell_num for cell_num, data in self.cells.items()
            if data.is_source_cell
        ]
    
    def get_cells_with_material(self, material_number: int) -> List[int]:
        """Get list of cells using a specific material."""
        return [
            cell_num for cell_num, data in self.cells.items()
            if data.material_number == material_number
        ]
    
    def get_void_cells(self) -> List[int]:
        """Get list of void cells (no material assigned)."""
        return [
            cell_num for cell_num, data in self.cells.items()
            if data.material_number is None
        ]
    
    def get_cells_with_mass(self) -> List[int]:
        """Get list of cells that have non-zero mass."""
        return [
            cell_num for cell_num, data in self.cells.items()
            if data.mass > 0.0
        ]
    
    def get_cells_with_volume(self) -> List[int]:
        """Get list of cells that have non-zero volume."""
        return [
            cell_num for cell_num, data in self.cells.items()
            if data.volume > 0.0
        ]
    
    def get_all_materials(self) -> List[int]:
        """Get list of all material numbers used in cells."""
        materials = set()
        for data in self.cells.values():
            if data.material_number is not None:
                materials.add(data.material_number)
        return sorted(list(materials))
    
    def get_total_mass(self) -> float:
        """Get total mass from table totals or calculated from cells."""
        if self.totals:
            return self.totals.total_mass
        return sum(data.mass for data in self.cells.values())
    
    def get_total_volume(self) -> float:
        """Get total volume from table totals or calculated from cells."""
        if self.totals:
            return self.totals.total_volume
        return sum(data.volume for data in self.cells.values())
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        result = {
            'cells': {
                cell_num: {
                    'cell_index': data.cell_index,
                    'cell_number': data.cell_number,
                    'material_number': data.material_number,
                    'is_source_cell': data.is_source_cell,
                    'atom_density': data.atom_density,
                    'gram_density': data.gram_density,
                    'volume': data.volume,
                    'mass': data.mass,
                    'pieces': data.pieces,
                    'neutron_importance': data.neutron_importance,
                    'photon_importance': data.photon_importance
                }
                for cell_num, data in self.cells.items()
            }
        }
        
        if self.totals:
            result['totals'] = {
                'total_volume': self.totals.total_volume,
                'total_mass': self.totals.total_mass
            }
        
        return result


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1cells                                                                                                  print table 60",
        "",
        "                               atom        gram                                            neutron    photon",
        "              cell      mat   density     density     volume       mass            pieces importance importance",
        "",
        "        1        1        4  5.61480E-02 1.01702E+01 2.10853E+02 2.14443E+03           1  1.0000E+00 1.0000E+00",
        "        2        2       30  3.48910E-05 2.31906E-04 8.40649E+00 1.94952E-03           1  1.0000E+00 1.0000E+00",
        "        3        3       25  8.75870E-02 7.94012E+00 4.97721E+01 3.95197E+02           1  1.0000E+00 1.0000E+00",
        "        4        4  9002101s 7.36080E-02 7.34914E-01 4.37850E+02 3.21782E+02           0  1.0000E+00 1.0000E+00",
        "        5        5  1220100s 7.00630E-02 1.04670E+01 1.12442E+01 1.17693E+02           0  1.0000E+00 1.0000E+00",
        "        6        6       30  3.48910E-05 2.31906E-04 0.00000E+00 0.00000E+00           0  1.0000E+00 1.0000E+00",
        "        7        7        3  4.33690E-02 6.57803E+00 0.00000E+00 0.00000E+00           0  1.0000E+00 1.0000E+00",
        "",
        " total                                               5.45330E+07 1.51238E+08"
    ]
    
    parser = Table060Parser()
    cells = parser.parse_lines(sample_lines)
    
    print(f"Found {len(cells)} cells:")
    for cell_num, data in cells.items():
        print(f"  Cell {cell_num}:")
        print(f"    Material: {data.material_number}")
        print(f"    Source cell: {data.is_source_cell}")
        print(f"    Mass: {data.mass:.2e}")
        print(f"    Volume: {data.volume:.2e}")
    
    print(f"\nSource cells: {parser.get_source_cells()}")
    print(f"Void cells: {parser.get_void_cells()}")
    print(f"All materials: {parser.get_all_materials()}")
    
    # Test specific query functions
    print(f"\nCell 4 material: {parser.get_cell_material(4)}")
    print(f"Cell 4 is source: {parser.is_source_cell(4)}")
    print(f"Cell 1 is source: {parser.is_source_cell(1)}")
    
    print(f"\nTotal mass: {parser.get_total_mass():.2e}")
    print(f"Total volume: {parser.get_total_volume():.2e}")