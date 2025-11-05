from typing import List, Dict, Optional, Union, TextIO
from dataclasses import dataclass, field


@dataclass
class MaterialConstituent:
    """Represents a single constituent (isotope/element) in a material."""
    zaid: str  # ZZZAAA or ZZZAAA.abx format
    fraction: float  # Positive for atomic fraction, negative for weight fraction
    
    def __post_init__(self):
        """Validate the constituent data."""
        if self.fraction == 0.0:
            raise ValueError("Fraction cannot be zero")


class MaterialCard:
    """
    Represents an MCNP material card (M card).
    
    The material card defines the composition of a material including:
    - Material number
    - Constituent isotopes/elements with fractions
    - Optional keywords for library specifications and other parameters
    """
    
    def __init__(self, material_number: int):
        """
        Initialize a material card.
        
        Args:
            material_number: Material number (0-99,999,999). Use 0 for global keywords.
        """
        if not (0 <= material_number <= 99999999):
            raise ValueError("Material number must be between 0 and 99,999,999")
        
        self.material_number = material_number
        self.constituents: List[MaterialConstituent] = []
        self.keywords: Dict[str, Union[str, int, float, List[float]]] = {}
        
        # Track fraction type to ensure consistency
        self._fraction_type: Optional[str] = None  # 'atomic' or 'weight'
    
    def add_constituent(self, zaid: str, fraction: float) -> None:
        """
        Add a constituent to the material.
        
        Args:
            zaid: ZAID identifier (e.g., "1001", "92235.80c")
            fraction: Atomic fraction (>0) or weight fraction (<0)
        """
        if fraction == 0.0:
            raise ValueError("Fraction cannot be zero")
        
        # Check fraction type consistency
        fraction_type = 'atomic' if fraction > 0 else 'weight'
        if self._fraction_type is None:
            self._fraction_type = fraction_type
        elif self._fraction_type != fraction_type:
            raise ValueError("Cannot mix atomic and weight fractions in the same material")
        
        self.constituents.append(MaterialConstituent(zaid=zaid, fraction=fraction))
    
    def set_gas_flag(self, gas_flag: int) -> None:
        """Set the GAS keyword for density-effect correction."""
        if gas_flag not in [0, 1]:
            raise ValueError("GAS flag must be 0 or 1")
        self.keywords['GAS'] = gas_flag
    
    def set_estep(self, n: int) -> None:
        """Set the ESTEP keyword for electron sub-steps."""
        if n <= 0:
            raise ValueError("ESTEP must be positive")
        self.keywords['ESTEP'] = n
    
    def set_hstep(self, n: int) -> None:
        """Set the HSTEP keyword for charged-particle sub-steps."""
        if n <= 0:
            raise ValueError("HSTEP must be positive")
        self.keywords['HSTEP'] = n
    
    def set_library(self, lib_type: str, identifier: str) -> None:
        """
        Set library identifier for various particle types.
        
        Args:
            lib_type: Library type ('NLIB', 'PLIB', 'PNLIB', 'ELIB', 'HLIB', 'ALIB', 'SLIB', 'TLIB', 'DLIB')
            identifier: Library identifier string
        """
        valid_libs = {'NLIB', 'PLIB', 'PNLIB', 'ELIB', 'HLIB', 'ALIB', 'SLIB', 'TLIB', 'DLIB'}
        if lib_type not in valid_libs:
            raise ValueError(f"Invalid library type. Must be one of: {valid_libs}")
        self.keywords[lib_type] = identifier
    
    def set_conduction(self, value: float) -> None:
        """Set the COND keyword for material conduction state."""
        self.keywords['COND'] = value
    
    def set_refractive_index_constant(self, a: float) -> None:
        """Set constant refractive index using REFI keyword."""
        self.keywords['REFI'] = a
    
    def set_refractive_index_cauchy(self, a: float, b: float, c: float, d: float) -> None:
        """Set Cauchy coefficients for refractive index using REFI keyword."""
        self.keywords['REFI'] = [a, b, c, d]
    
    def set_refractive_index_sellmeier(self, b1: float, c1: float, b2: float, 
                                     c2: float, b3: float, c3: float) -> None:
        """Set Sellmeier coefficients for refractive index using REFS keyword."""
        self.keywords['REFS'] = [b1, c1, b2, c2, b3, c3]
    
    def _format_fraction(self, fraction: float) -> str:
        """Format fraction with appropriate precision."""
        if abs(fraction) >= 1e-3:
            return f"{fraction:.6f}".rstrip('0').rstrip('.')
        else:
            return f"{fraction:.6e}"
    
    def _format_keyword_value(self, key: str, value: Union[str, int, float, List[float]]) -> str:
        """Format a keyword-value pair."""
        if isinstance(value, str):
            return f"{key}={value}"
        elif isinstance(value, int):
            return f"{key}={value}"
        elif isinstance(value, float):
            if abs(value) >= 1e-3 and abs(value) < 1e6:
                formatted = f"{value:.6f}".rstrip('0').rstrip('.')
                return f"{key}={formatted}"
            else:
                return f"{key}={value:.6e}"
        elif isinstance(value, list):
            formatted_values = []
            for v in value:
                if abs(v) >= 1e-3 and abs(v) < 1e6:
                    formatted = f"{v:.6f}".rstrip('0').rstrip('.')
                    formatted_values.append(formatted)
                else:
                    formatted_values.append(f"{v:.6e}")
            return f"{key}={' '.join(formatted_values)}"
        else:
            return f"{key}={value}"
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert the material card to MCNP input format.
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted material card string
        """
        if not self.constituents and self.material_number != 0:
            raise ValueError("Material must have at least one constituent (unless material number is 0)")
        
        lines = []
        current_line = f"m{self.material_number}"
        
        # Add constituents
        for constituent in self.constituents:
            constituent_str = f" {constituent.zaid} {self._format_fraction(constituent.fraction)}"
            
            # Check if adding this constituent would exceed line length
            if len(current_line + constituent_str) > line_length:
                lines.append(current_line)
                current_line = "     " + constituent_str.strip()  # Continuation line with 5 spaces
            else:
                current_line += constituent_str
        
        # Add keywords
        for key, value in self.keywords.items():
            keyword_str = f" {self._format_keyword_value(key, value)}"
            
            # Check if adding this keyword would exceed line length
            if len(current_line + keyword_str) > line_length:
                lines.append(current_line)
                current_line = "     " + keyword_str.strip()  # Continuation line with 5 spaces
            else:
                current_line += keyword_str
        
        # Add the final line
        if current_line.strip():
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the material card to a file.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def get_total_atomic_fraction(self) -> float:
        """Get the sum of atomic fractions (should be 1.0 for normalized materials)."""
        if self._fraction_type != 'atomic':
            raise ValueError("Material does not use atomic fractions")
        return sum(const.fraction for const in self.constituents)
    
    def get_total_weight_fraction(self) -> float:
        """Get the sum of absolute weight fractions (should be 1.0 for normalized materials)."""
        if self._fraction_type != 'weight':
            raise ValueError("Material does not use weight fractions")
        return sum(abs(const.fraction) for const in self.constituents)
    
    def normalize_fractions(self) -> None:
        """Normalize fractions to sum to 1.0 (or -1.0 for weight fractions)."""
        if not self.constituents:
            return
        
        if self._fraction_type == 'atomic':
            total = sum(const.fraction for const in self.constituents)
            if total > 0:
                for const in self.constituents:
                    const.fraction /= total
        else:  # weight fractions
            total = sum(abs(const.fraction) for const in self.constituents)
            if total > 0:
                for const in self.constituents:
                    const.fraction = -(abs(const.fraction) / total)
    
    def __str__(self) -> str:
        """String representation of the material card."""
        return self.to_string()


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Water with atomic fractions
    water = MaterialCard(1)
    water.add_constituent("1001.80c", 0.666667)  # H-1
    water.add_constituent("8016.80c", 0.333333)  # O-16
    water.set_library("NLIB", "80c")
    
    print("Water (atomic fractions):")
    print(water)
    print()
    
    # Example 2: Steel with weight fractions
    steel = MaterialCard(2)
    steel.add_constituent("26056", -0.98)    # Fe-56 (weight fraction)
    steel.add_constituent("6012", -0.02)     # C-12 (weight fraction)
    steel.set_gas_flag(0)
    steel.set_estep(10)
    
    print("Steel (weight fractions):")
    print(steel)
    print()
    
    # Example 3: Material with refractive index
    glass = MaterialCard(3)
    glass.add_constituent("14028.80c", 0.5)
    glass.add_constituent("8016.80c", 0.5)
    glass.set_refractive_index_cauchy(1.5, 0.01, 0.001, 0.0001)
    
    print("Glass with Cauchy refractive index:")
    print(glass)
    print()
    
    # Example 4: Global keywords (material 0)
    global_keywords = MaterialCard(0)
    global_keywords.set_library("NLIB", "80c")
    global_keywords.set_library("PLIB", "04p")
    
    print("Global keywords (material 0):")
    print(global_keywords)
    print()
    
    # Test writing to file
    print("Writing to file example:")
    with open("test_materials.txt", "w") as f:
        water.write_to_file(f)
        f.write("\n")
        steel.write_to_file(f)
        f.write("\n")
        glass.write_to_file(f)
    
    print("Materials written to 'test_materials.txt'")
    
    # Test normalization
    print("\nNormalization test:")
    test_mat = MaterialCard(99)
    test_mat.add_constituent("1001", 2.0)
    test_mat.add_constituent("8016", 1.0)
    print(f"Before normalization: {test_mat.get_total_atomic_fraction():.6f}")
    test_mat.normalize_fractions()
    print(f"After normalization: {test_mat.get_total_atomic_fraction():.6f}")
    print(test_mat)