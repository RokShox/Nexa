import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class IsotopeComposition:
    """Data class representing an isotope in a material composition."""
    zaid: int
    atom_fraction: Optional[float] = None
    mass_fraction: Optional[float] = None


@dataclass
class MaterialComposition:
    """Data class representing a complete material composition."""
    material_number: int
    isotopes: Dict[int, IsotopeComposition] = field(default_factory=dict)  # zaid -> IsotopeComposition
    thermal_sab_data: Optional[str] = None


class Table040Parser:
    """Parser for MCNP output Table 40 - Material composition."""
    
    def __init__(self):
        self.materials: Dict[int, MaterialComposition] = {}
        self._header_found = False
        self._current_material = None
        self._parsing_mode = None  # 'atom' or 'mass'
    
    def parse_lines(self, lines: List[str]) -> Dict[int, MaterialComposition]:
        """
        Parse lines from MCNP output containing Table 40 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Dictionary mapping material_number -> MaterialComposition
        """
        self.materials.clear()
        self._header_found = False
        self._current_material = None
        self._parsing_mode = None
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                # Determine if this is atom or mass fraction subtable
                if "atom fraction" in line.lower():
                    self._parsing_mode = "atom"
                elif "mass fraction" in line.lower():
                    self._parsing_mode = "mass"
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                # Check for subtable headers
                if self._is_fraction_type_header(line):
                    if "atom fraction" in line.lower():
                        self._parsing_mode = "atom"
                    elif "mass fraction" in line.lower():
                        self._parsing_mode = "mass"
                    continue
                
                if self._is_material_number_line(line):
                    material_num = self._extract_material_number(line)
                    if material_num is not None:
                        self._current_material = material_num
                        
                        # Create material if not exists
                        if material_num not in self.materials:
                            self.materials[material_num] = MaterialComposition(material_number=material_num)
                        
                        # Parse isotopes on the same line
                        isotopes = self._parse_isotopes_from_line(line)
                        self._update_material_isotopes(material_num, isotopes)
                    continue
                
                if self._is_sab_data_line(line):
                    if self._current_material is not None:
                        sab_data = self._extract_sab_data(line)
                        if sab_data:
                            self.materials[self._current_material].thermal_sab_data = sab_data
                    continue
                
                if self._is_continuation_line(line):
                    if self._current_material is not None:
                        isotopes = self._parse_isotopes_from_line(line)
                        self._update_material_isotopes(self._current_material, isotopes)
                    continue
        
        return self.materials
    
    def _update_material_isotopes(self, material_num: int, isotopes: List[Tuple[int, float]]):
        """Update material isotopes with atom or mass fractions."""
        material = self.materials[material_num]
        
        for zaid, fraction in isotopes:
            if zaid not in material.isotopes:
                material.isotopes[zaid] = IsotopeComposition(zaid=zaid)
            
            if self._parsing_mode == "atom":
                material.isotopes[zaid].atom_fraction = fraction
            elif self._parsing_mode == "mass":
                material.isotopes[zaid].mass_fraction = fraction
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 40 header."""
        return ("material composition" in line.lower() or 
                ("material" in line.lower() and ("atom fraction" in line.lower() or "mass fraction" in line.lower()))) and \
               "print table 40" in line.lower()
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Look for next table or other indicators
        return ("print table" in line.lower() and "table 40" not in line.lower()) or \
               line.startswith("1") and any(x in line.lower() for x in [
                   "probid", "keff results", "run terminated", "neutron creation", 
                   "neutron loss", "neutron activity", "weight balance"
               ])
    
    def _is_fraction_type_header(self, line: str) -> bool:
        """Check if line is a header indicating fraction type."""
        return ("component nuclide" in line.lower() and 
                ("atom fraction" in line.lower() or "mass fraction" in line.lower()))
    
    def _is_material_number_line(self, line: str) -> bool:
        """Check if line starts with a material number."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Look for lines that start with a number followed by isotope data
        parts = stripped.split()
        if len(parts) >= 3:
            # First part should be a number (material number)
            # Second part should be a ZAID
            # Third part should be a comma (part of "ZAID,")
            try:
                int(parts[0])  # Material number
                zaid_part = parts[1].rstrip(',')
                int(zaid_part)  # ZAID
                return True
            except ValueError:
                pass
        
        return False
    
    def _extract_material_number(self, line: str) -> Optional[int]:
        """Extract material number from the beginning of a line."""
        parts = line.strip().split()
        if parts:
            try:
                return int(parts[0])
            except ValueError:
                pass
        return None
    
    def _is_sab_data_line(self, line: str) -> bool:
        """Check if line contains S(a,b) data information."""
        return "associated thermal s(a,b) data sets:" in line.lower()
    
    def _extract_sab_data(self, line: str) -> Optional[str]:
        """Extract S(a,b) data set name from line."""
        match = re.search(r"associated thermal s\(a,b\) data sets:\s*(.+)", line, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _is_continuation_line(self, line: str) -> bool:
        """Check if line is a continuation of isotope data."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Check if line starts with whitespace and contains isotope data
        if line.startswith(' ' * 10):  # Significant indentation
            # Look for comma-separated ZAID, fraction pairs
            return ',' in stripped and any(c.isdigit() for c in stripped)
        
        return False
    
    def _parse_isotopes_from_line(self, line: str) -> List[Tuple[int, float]]:
        """Parse isotope compositions from a line."""
        isotopes = []
        
        # Remove material number if present (for first line of material)
        content = line.strip()
        parts = content.split()
        
        # Skip the first part if it's a material number
        if parts and self._is_material_number_line(line):
            parts = parts[1:]  # Skip material number
        
        # Rejoin and parse comma-separated pairs
        content = ' '.join(parts)
        
        # Use regex to find ZAID, fraction pairs
        pattern = r'(\d+),\s*([\d.E+-]+)'
        matches = re.findall(pattern, content)
        
        for zaid_str, fraction_str in matches:
            try:
                zaid = int(zaid_str)
                fraction = float(fraction_str)
                isotopes.append((zaid, fraction))
            except ValueError:
                continue
        
        return isotopes
    
    def get_material_composition(self, material_number: int) -> Optional[MaterialComposition]:
        """Get composition for a specific material."""
        return self.materials.get(material_number)
    
    def get_all_materials(self) -> List[int]:
        """Get list of all material numbers."""
        return sorted(list(self.materials.keys()))
    
    def get_materials_with_sab_data(self) -> List[int]:
        """Get list of materials that have associated S(a,b) data."""
        return [
            mat_num for mat_num, composition in self.materials.items()
            if composition.thermal_sab_data is not None
        ]
    
    def get_isotope_in_material(self, material_number: int, zaid: int) -> Optional[IsotopeComposition]:
        """Get specific isotope data for a material."""
        material = self.get_material_composition(material_number)
        if material:
            return material.isotopes.get(zaid)
        return None
    
    def get_materials_with_isotope(self, zaid: int) -> List[int]:
        """Get list of materials that contain a specific isotope."""
        result = []
        for mat_num, composition in self.materials.items():
            if zaid in composition.isotopes:
                result.append(mat_num)
        return sorted(result)
    
    def get_isotope_atom_fraction(self, material_number: int, zaid: int) -> Optional[float]:
        """Get atom fraction for a specific isotope in a material."""
        isotope = self.get_isotope_in_material(material_number, zaid)
        return isotope.atom_fraction if isotope else None
    
    def get_isotope_mass_fraction(self, material_number: int, zaid: int) -> Optional[float]:
        """Get mass fraction for a specific isotope in a material."""
        isotope = self.get_isotope_in_material(material_number, zaid)
        return isotope.mass_fraction if isotope else None
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        return {
            'materials': {
                mat_num: {
                    'material_number': composition.material_number,
                    'isotopes': {
                        zaid: {
                            'zaid': isotope.zaid,
                            'atom_fraction': isotope.atom_fraction,
                            'mass_fraction': isotope.mass_fraction
                        }
                        for zaid, isotope in composition.isotopes.items()
                    },
                    'thermal_sab_data': composition.thermal_sab_data
                }
                for mat_num, composition in self.materials.items()
            }
        }


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1material composition                                                                                   print table 40",
        "",
        " material",
        "  number     component nuclide, atom fraction",
        "",
        "        8            6012, 1.54496E-04       6013, 1.67099E-06       7014, 7.85241E-01       7015, 2.86872E-03",
        "                     8016, 2.11220E-01       8017, 8.04591E-05       8018, 4.34055E-04",
        "        9           22046, 8.25000E-02      22047, 7.44000E-02      22048, 7.37200E-01      22049, 5.41000E-02",
        "                    22050, 5.18000E-02",
        "1material                                                                                               print table 40",
        "  number     component nuclide, mass fraction",
        "",
        "        8            6012, 1.28494E-04       6013, 1.50596E-06       7014, 7.62098E-01       7015, 2.98241E-03",
        "                     8016, 2.34154E-01       8017, 9.47951E-05       8018, 5.41479E-04",
        "        9           22046, 7.92010E-02      22047, 7.29778E-02      22048, 7.38451E-01      22049, 5.53219E-02",
        "                    22050, 5.40488E-02"
    ]
    
    parser = Table040Parser()
    materials = parser.parse_lines(sample_lines)
    
    print(f"Found {len(materials)} materials:")
    for mat_num, composition in materials.items():
        print(f"\nMaterial {mat_num}: {len(composition.isotopes)} isotopes")
        if composition.thermal_sab_data:
            print(f"  S(a,b) data: {composition.thermal_sab_data}")
        
        # Show first few isotopes with both fractions
        for i, (zaid, isotope) in enumerate(list(composition.isotopes.items())[:3]):
            atom_frac = f"{isotope.atom_fraction:.5e}" if isotope.atom_fraction else "None"
            mass_frac = f"{isotope.mass_fraction:.5e}" if isotope.mass_fraction else "None"
            print(f"    {zaid}: atom={atom_frac}, mass={mass_frac}")
        
        if len(composition.isotopes) > 3:
            print(f"    ... and {len(composition.isotopes) - 3} more isotopes")
    
    print(f"\nMaterials with S(a,b) data: {parser.get_materials_with_sab_data()}")
    
    # Test specific queries
    print(f"\nMaterial 8, ZAID 7014:")
    print(f"  Atom fraction: {parser.get_isotope_atom_fraction(8, 7014)}")
    print(f"  Mass fraction: {parser.get_isotope_mass_fraction(8, 7014)}")