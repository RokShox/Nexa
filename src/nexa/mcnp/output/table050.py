from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CellVolumeData:
    """Data class representing cell volume and mass data."""
    cell_index: int
    cell_number: int
    atom_density: float
    gram_density: float
    input_volume: float
    calculated_volume: float
    mass: float
    pieces: int
    reason_volume_not_calculated: Optional[str] = None


@dataclass
class SurfaceAreaData:
    """Data class representing surface area data."""
    surface_index: int
    surface_number: int
    input_area: float
    calculated_area: float
    reason_area_not_calculated: Optional[str] = None


class Table050Parser:
    """Parser for MCNP output Table 50 - Cell volumes and masses, and surface areas."""
    
    def __init__(self):
        self.cells: Dict[int, CellVolumeData] = {}
        self.surfaces: Dict[int, SurfaceAreaData] = {}
        self._header_found = False
        self._parsing_mode = None  # 'volumes' or 'areas'
    
    def parse_lines(self, lines: List[str]) -> Tuple[Dict[int, CellVolumeData], Dict[int, SurfaceAreaData]]:
        """
        Parse lines from MCNP output containing Table 50 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Tuple of (cell_data_dict, surface_data_dict)
        """
        self.cells.clear()
        self.surfaces.clear()
        self._header_found = False
        self._parsing_mode = None
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                if "cell volumes and masses" in line.lower():
                    self._parsing_mode = "volumes"
                elif "surface areas" in line.lower():
                    self._parsing_mode = "areas"
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                if self._is_surface_areas_header(line):
                    self._parsing_mode = "areas"
                    continue
                
                if self._is_header_line(line):
                    continue
                
                if self._parsing_mode == "volumes" and self._is_volume_data_line(line):
                    cell_data = self._parse_volume_data_line(line)
                    if cell_data:
                        self.cells[cell_data.cell_number] = cell_data
                
                elif self._parsing_mode == "areas" and self._is_area_data_line(line):
                    surface_data = self._parse_area_data_line(line)
                    if surface_data:
                        self.surfaces[surface_data.surface_number] = surface_data
        
        return self.cells, self.surfaces
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains any table 50 header."""
        return ("cell volumes and masses" in line.lower() or "surface areas" in line.lower()) and "print table 50" in line.lower()
    
    def _is_surface_areas_header(self, line: str) -> bool:
        """Check if line contains the surface areas header."""
        return "surface areas" in line.lower() and "print table 50" in line.lower()
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Look for next table or other indicators
        return ("print table" in line.lower() and "table 50" not in line.lower()) or \
               line.startswith("1") and any(x in line.lower() for x in [
                   "probid", "keff results", "run terminated", "neutron creation", 
                   "neutron loss", "neutron activity", "weight balance", "material composition"
               ])
    
    def _is_header_line(self, line: str) -> bool:
        """Check if line contains column headers."""
        stripped = line.strip()
        return any(header in stripped.lower() for header in [
            "cell", "atom", "gram", "input", "calculated", "volume", "mass", "pieces", 
            "density", "reason", "surface", "area"
        ]) and not (self._is_volume_data_line(line) or self._is_area_data_line(line))
    
    def _is_volume_data_line(self, line: str) -> bool:
        """Check if line contains cell volume data."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Check if line starts with numbers and has enough columns for volume data
        parts = stripped.split()
        if len(parts) >= 8:  # Minimum expected columns for volume data
            try:
                # First two parts should be integers (cell index and cell number)
                int(parts[0])
                int(parts[1])
                # Check that we have the expected scientific notation pattern
                float(parts[2])  # atom density
                float(parts[3])  # gram density
                return True
            except ValueError:
                pass
        
        return False
    
    def _is_area_data_line(self, line: str) -> bool:
        """Check if line contains surface area data."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Check if line starts with numbers and has columns for area data
        parts = stripped.split()
        if len(parts) >= 4:  # Minimum expected columns for area data
            try:
                # First two parts should be integers (surface index and surface number)
                int(parts[0])
                int(parts[1])
                # Should have fewer columns than volume data
                float(parts[2])  # input area
                float(parts[3])  # calculated area
                return True
            except ValueError:
                pass
        
        return False
    
    def _parse_volume_data_line(self, line: str) -> Optional[CellVolumeData]:
        """Parse a data line containing cell volume information."""
        try:
            parts = line.strip().split()
            if len(parts) < 8:
                return None
            
            cell_index = int(parts[0])
            cell_number = int(parts[1])
            atom_density = float(parts[2])
            gram_density = float(parts[3])
            input_volume = float(parts[4])
            calculated_volume = float(parts[5])
            mass = float(parts[6])
            pieces = int(parts[7])
            
            # Check for reason why volume not calculated (optional last column)
            reason = None
            if len(parts) > 8:
                reason = ' '.join(parts[8:]).strip()
                if reason == '':
                    reason = None
            
            return CellVolumeData(
                cell_index=cell_index,
                cell_number=cell_number,
                atom_density=atom_density,
                gram_density=gram_density,
                input_volume=input_volume,
                calculated_volume=calculated_volume,
                mass=mass,
                pieces=pieces,
                reason_volume_not_calculated=reason
            )
            
        except (ValueError, IndexError):
            return None
    
    def _parse_area_data_line(self, line: str) -> Optional[SurfaceAreaData]:
        """Parse a data line containing surface area information."""
        try:
            parts = line.strip().split()
            if len(parts) < 4:
                return None
            
            surface_index = int(parts[0])
            surface_number = int(parts[1])
            input_area = float(parts[2])
            calculated_area = float(parts[3])
            
            # Check for reason why area not calculated (optional last column)
            reason = None
            if len(parts) > 4:
                reason = ' '.join(parts[4:]).strip()
                if reason == '':
                    reason = None
            
            return SurfaceAreaData(
                surface_index=surface_index,
                surface_number=surface_number,
                input_area=input_area,
                calculated_area=calculated_area,
                reason_area_not_calculated=reason
            )
            
        except (ValueError, IndexError):
            return None
    
    # Cell data methods
    def get_cell_data(self, cell_number: int) -> Optional[CellVolumeData]:
        """Get volume/mass data for a specific cell."""
        return self.cells.get(cell_number)
    
    def get_all_cells(self) -> List[int]:
        """Get list of all cell numbers."""
        return sorted(list(self.cells.keys()))
    
    def get_cells_with_calculated_volume(self) -> List[int]:
        """Get list of cells that have calculated volumes."""
        return [
            cell_num for cell_num, data in self.cells.items()
            if data.calculated_volume > 0.0
        ]
    
    def get_cells_with_input_volume(self) -> List[int]:
        """Get list of cells that have input volumes."""
        return [
            cell_num for cell_num, data in self.cells.items()
            if data.input_volume > 0.0
        ]
    
    def get_cells_with_infinite_volume(self) -> List[int]:
        """Get list of cells with infinite volume."""
        return [
            cell_num for cell_num, data in self.cells.items()
            if data.reason_volume_not_calculated and "infinite" in data.reason_volume_not_calculated.lower()
        ]
    
    def get_cells_with_mass(self) -> List[int]:
        """Get list of cells that have non-zero mass."""
        return [
            cell_num for cell_num, data in self.cells.items()
            if data.mass > 0.0
        ]
    
    def get_total_mass(self) -> float:
        """Get total mass of all cells."""
        return sum(data.mass for data in self.cells.values())
    
    def get_total_calculated_volume(self) -> float:
        """Get total calculated volume of all cells."""
        return sum(data.calculated_volume for data in self.cells.values())
    
    def get_total_input_volume(self) -> float:
        """Get total input volume of all cells."""
        return sum(data.input_volume for data in self.cells.values())
    
    # Surface data methods
    def get_surface_data(self, surface_number: int) -> Optional[SurfaceAreaData]:
        """Get area data for a specific surface."""
        return self.surfaces.get(surface_number)
    
    def get_all_surfaces(self) -> List[int]:
        """Get list of all surface numbers."""
        return sorted(list(self.surfaces.keys()))
    
    def get_surfaces_with_calculated_area(self) -> List[int]:
        """Get list of surfaces that have calculated areas."""
        return [
            surf_num for surf_num, data in self.surfaces.items()
            if data.calculated_area > 0.0
        ]
    
    def get_surfaces_with_input_area(self) -> List[int]:
        """Get list of surfaces that have input areas."""
        return [
            surf_num for surf_num, data in self.surfaces.items()
            if data.input_area > 0.0
        ]
    
    def get_total_calculated_area(self) -> float:
        """Get total calculated area of all surfaces."""
        return sum(data.calculated_area for data in self.surfaces.values())
    
    def get_total_input_area(self) -> float:
        """Get total input area of all surfaces."""
        return sum(data.input_area for data in self.surfaces.values())
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        return {
            'cells': {
                cell_num: {
                    'cell_index': data.cell_index,
                    'cell_number': data.cell_number,
                    'atom_density': data.atom_density,
                    'gram_density': data.gram_density,
                    'input_volume': data.input_volume,
                    'calculated_volume': data.calculated_volume,
                    'mass': data.mass,
                    'pieces': data.pieces,
                    'reason_volume_not_calculated': data.reason_volume_not_calculated
                }
                for cell_num, data in self.cells.items()
            },
            'surfaces': {
                surf_num: {
                    'surface_index': data.surface_index,
                    'surface_number': data.surface_number,
                    'input_area': data.input_area,
                    'calculated_area': data.calculated_area,
                    'reason_area_not_calculated': data.reason_area_not_calculated
                }
                for surf_num, data in self.surfaces.items()
            }
        }


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1cell volumes and masses                                                                                print table 50",
        "",
        "              cell     atom          gram         input       calculated                            reason volume",
        "                      density       density       volume        volume         mass       pieces    not calculated",
        "",
        "        1        1  5.61480E-02   1.01702E+01   0.00000E+00   2.10853E+02   2.14443E+03      1",
        "        2        2  3.48910E-05   2.31906E-04   0.00000E+00   8.40649E+00   1.94952E-03      1",
        "        4        4  7.36080E-02   7.34914E-01   4.37850E+02   0.00000E+00   3.21782E+02      0      infinite",
        "",
        "1surface areas                                                                                          print table 50",
        "",
        "           surface      input      calculated    reason area",
        "                        area          area       not calculated",
        "",
        "        1        1      0.00000E+00   2.67313E+03",
        "        2        2      0.00000E+00   2.67313E+03",
        "        3        3      0.00000E+00   2.67313E+03"
    ]
    
    parser = Table050Parser()
    cells, surfaces = parser.parse_lines(sample_lines)
    
    print(f"Found {len(cells)} cells and {len(surfaces)} surfaces:")
    
    print(f"\nCells:")
    for cell_num, data in cells.items():
        print(f"  Cell {cell_num}: mass={data.mass:.2e}, calc_vol={data.calculated_volume:.2e}")
        if data.reason_volume_not_calculated:
            print(f"    Reason: {data.reason_volume_not_calculated}")
    
    print(f"\nSurfaces:")
    for surf_num, data in surfaces.items():
        print(f"  Surface {surf_num}: input_area={data.input_area:.2e}, calc_area={data.calculated_area:.2e}")
        if data.reason_area_not_calculated:
            print(f"    Reason: {data.reason_area_not_calculated}")
    
    print(f"\nTotals:")
    print(f"  Total mass: {parser.get_total_mass():.2e}")
    print(f"  Total calculated volume: {parser.get_total_calculated_volume():.2e}")
    print(f"  Total calculated area: {parser.get_total_calculated_area():.2e}")