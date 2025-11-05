from typing import List, Dict, Optional, Union, TextIO, Set
from dataclasses import dataclass


@dataclass
class CellParameter:
    """Represents a cell parameter with optional particle designators."""
    keyword: str
    value: Union[float, int, str, List[Union[float, int, str]]]
    particles: Optional[Set[str]] = None  # e.g., {'n', 'p'} for neutrons and photons
    
    def __post_init__(self):
        """Validate the parameter."""
        if self.particles is not None and not isinstance(self.particles, set):
            self.particles = set(self.particles) if self.particles else None


class CellCard:
    """
    Represents an MCNP cell card (Form 1).
    
    The cell card defines a geometric region with material assignment and
    optional cell parameters. It specifies the cell number, material, density,
    geometry specification, and optional parameters.
    """
    
    # Valid cell parameter keywords
    VALID_KEYWORDS = {
        'IMP', 'VOL', 'PWT', 'EXT', 'FCL', 'WWN', 'DXC', 'NONU', 'PD', 'TMP', 
        'U', 'TRCL', 'LAT', 'FILL', 'ELPT', 'COSY', 'BFLCL', 'UNC'
    }
    
    # Keywords that require particle designators
    PARTICLE_KEYWORDS = {'IMP', 'PWT', 'EXT', 'FCL', 'WWN', 'DXC', 'PD'}
    
    # Valid particle types
    VALID_PARTICLES = {'n', 'p', 'e', 'h', 'a', 's', 't', 'd', 'g'}
    
    def __init__(self, cell_number: int, material_number: Optional[int] = None, 
                 density: Optional[float] = None, geometry: str = ""):
        """
        Initialize a cell card.
        
        Args:
            cell_number: Cell number (1-99,999,999)
            material_number: Material number (1-99,999,999) or 0 for void, None for void
            density: Material density (>0 for atomic, <0 for mass density)
            geometry: Geometry specification with surface numbers and Boolean operators
        """
        self.cell_number = self._validate_cell_number(cell_number)
        self.material_number = self._validate_material_number(material_number)
        self.density = self._validate_density(density, material_number)
        self.geometry = geometry.strip()
        self.parameters: List[CellParameter] = []
    
    def _validate_cell_number(self, cell_number: int) -> int:
        """Validate cell number."""
        if not isinstance(cell_number, int):
            raise ValueError("Cell number must be an integer")
        if not (1 <= cell_number <= 99999999):
            raise ValueError("Cell number must be between 1 and 99,999,999")
        return cell_number
    
    def _validate_material_number(self, material_number: Optional[int]) -> Optional[int]:
        """Validate material number."""
        if material_number is None:
            return 0  # Void cell
        
        if not isinstance(material_number, int):
            raise ValueError("Material number must be an integer")
        if not (0 <= material_number <= 99999999):
            raise ValueError("Material number must be between 0 and 99,999,999")
        return material_number
    
    def _validate_density(self, density: Optional[float], material_number: Optional[int]) -> Optional[float]:
        """Validate density based on material number."""
        if material_number == 0 or material_number is None:
            # Void cell - density should be None
            if density is not None:
                raise ValueError("Void cells (material 0) cannot have density")
            return None
        else:
            # Material cell - density is required
            if density is None:
                raise ValueError("Material cells must have density specified")
            if not isinstance(density, (int, float)):
                raise ValueError("Density must be numeric")
            if density == 0:
                raise ValueError("Density cannot be zero")
            return float(density)
    
    def is_void(self) -> bool:
        """Check if this is a void cell."""
        return self.material_number == 0 or self.material_number is None
    
    def set_geometry(self, geometry: str) -> None:
        """Set the geometry specification."""
        self.geometry = geometry.strip()
    
    def add_parameter(self, keyword: str, value: Union[float, int, str, List[Union[float, int, str]]], 
                     particles: Optional[Union[str, List[str], Set[str]]] = None) -> None:
        """
        Add a cell parameter.
        
        Args:
            keyword: Parameter keyword (e.g., 'IMP', 'VOL', 'TMP')
            value: Parameter value(s)
            particles: Particle designators for keywords that require them
        """
        keyword = keyword.upper()
        
        # Validate keyword
        if keyword not in self.VALID_KEYWORDS:
            raise ValueError(f"Invalid keyword: {keyword}. Must be one of: {self.VALID_KEYWORDS}")
        
        # Handle particle designators
        particle_set = None
        if particles is not None:
            if isinstance(particles, str):
                particle_set = {particles.lower()}
            elif isinstance(particles, (list, set)):
                particle_set = {p.lower() for p in particles}
            else:
                raise ValueError("Particles must be string, list, or set")
            
            # Validate particles
            invalid_particles = particle_set - self.VALID_PARTICLES
            if invalid_particles:
                raise ValueError(f"Invalid particles: {invalid_particles}. Valid particles: {self.VALID_PARTICLES}")
        
        # Check if keyword requires particles
        if keyword in self.PARTICLE_KEYWORDS and particle_set is None:
            raise ValueError(f"Keyword {keyword} requires particle designators")
        
        # Check if keyword should not have particles
        if keyword not in self.PARTICLE_KEYWORDS and particle_set is not None:
            raise ValueError(f"Keyword {keyword} does not accept particle designators")
        
        # Remove existing parameter with same keyword and particles
        self.parameters = [p for p in self.parameters 
                          if not (p.keyword == keyword and p.particles == particle_set)]
        
        # Add new parameter
        self.parameters.append(CellParameter(keyword, value, particle_set))
    
    def remove_parameter(self, keyword: str, particles: Optional[Union[str, List[str], Set[str]]] = None) -> bool:
        """
        Remove a cell parameter.
        
        Args:
            keyword: Parameter keyword
            particles: Particle designators (if applicable)
            
        Returns:
            True if parameter was removed, False if not found
        """
        keyword = keyword.upper()
        
        # Handle particle designators
        particle_set = None
        if particles is not None:
            if isinstance(particles, str):
                particle_set = {particles.lower()}
            elif isinstance(particles, (list, set)):
                particle_set = {p.lower() for p in particles}
        
        # Find and remove parameter
        initial_count = len(self.parameters)
        self.parameters = [p for p in self.parameters 
                          if not (p.keyword == keyword and p.particles == particle_set)]
        
        return len(self.parameters) < initial_count
    
    def get_parameter(self, keyword: str, particles: Optional[Union[str, List[str], Set[str]]] = None) -> Optional[CellParameter]:
        """
        Get a cell parameter.
        
        Args:
            keyword: Parameter keyword
            particles: Particle designators (if applicable)
            
        Returns:
            CellParameter if found, None otherwise
        """
        keyword = keyword.upper()
        
        # Handle particle designators
        particle_set = None
        if particles is not None:
            if isinstance(particles, str):
                particle_set = {particles.lower()}
            elif isinstance(particles, (list, set)):
                particle_set = {p.lower() for p in particles}
        
        # Find parameter
        for param in self.parameters:
            if param.keyword == keyword and param.particles == particle_set:
                return param
        
        return None
    
    def set_importance(self, particles: Union[str, List[str]], importance: float) -> None:
        """Set importance for specified particles."""
        self.add_parameter('IMP', importance, particles)
    
    def set_volume(self, volume: float) -> None:
        """Set cell volume."""
        if volume <= 0:
            raise ValueError("Volume must be positive")
        self.add_parameter('VOL', volume)
    
    def set_temperature(self, temperature: Union[float, List[float]]) -> None:
        """Set cell temperature(s)."""
        if isinstance(temperature, (int, float)):
            if temperature <= 0:
                raise ValueError("Temperature must be positive")
            self.add_parameter('TMP', temperature)
        elif isinstance(temperature, list):
            if any(t <= 0 for t in temperature):
                raise ValueError("All temperatures must be positive")
            self.add_parameter('TMP', temperature)
        else:
            raise ValueError("Temperature must be numeric or list of numbers")
    
    def set_universe(self, universe: int) -> None:
        """Set universe number."""
        if not isinstance(universe, int):
            raise ValueError("Universe must be an integer")
        self.add_parameter('U', universe)
    
    def set_fill(self, fill_value: Union[int, str]) -> None:
        """Set fill specification."""
        self.add_parameter('FILL', fill_value)
    
    def set_lattice(self, lattice_type: int) -> None:
        """Set lattice type (1 for square, 2 for hexagonal)."""
        if lattice_type not in [1, 2]:
            raise ValueError("Lattice type must be 1 (square) or 2 (hexagonal)")
        self.add_parameter('LAT', lattice_type)
    
    def _format_parameter_value(self, value: Union[float, int, str, List[Union[float, int, str]]]) -> str:
        """Format parameter value for output."""
        if isinstance(value, str):
            return value
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            if abs(value) >= 1e-3 and abs(value) < 1e6:
                formatted = f"{value:.6f}".rstrip('0').rstrip('.')
                return formatted
            else:
                return f"{value:.6e}"
        elif isinstance(value, list):
            formatted_values = []
            for v in value:
                if isinstance(v, str):
                    formatted_values.append(v)
                elif isinstance(v, int):
                    formatted_values.append(str(v))
                elif isinstance(v, float):
                    if abs(v) >= 1e-3 and abs(v) < 1e6:
                        formatted = f"{v:.6f}".rstrip('0').rstrip('.')
                        formatted_values.append(formatted)
                    else:
                        formatted_values.append(f"{v:.6e}")
            return ' '.join(formatted_values)
        else:
            return str(value)
    
    def _format_parameter(self, param: CellParameter) -> str:
        """Format a parameter for output."""
        if param.particles:
            particles_str = ','.join(sorted(param.particles))
            return f"{param.keyword}:{particles_str}={self._format_parameter_value(param.value)}"
        else:
            return f"{param.keyword}={self._format_parameter_value(param.value)}"
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert the cell card to MCNP input format.
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted cell card string
        """
        # Build the basic cell specification
        components = [str(self.cell_number)]
        
        # Add material and density
        if self.is_void():
            components.append("0")
        else:
            components.append(str(self.material_number))
            components.append(self._format_parameter_value(self.density))
        
        # Add geometry
        if self.geometry:
            components.append(self.geometry)
        
        # Add parameters
        param_strings = []
        for param in self.parameters:
            param_strings.append(self._format_parameter(param))
        
        # Combine all components
        all_components = components + param_strings
        
        # Handle line wrapping
        lines = []
        current_line = " ".join(all_components[:len(components)])
        
        # Add parameters with wrapping
        for param_str in param_strings:
            if len(current_line + " " + param_str) > line_length:
                lines.append(current_line)
                current_line = "     " + param_str  # Continuation with 5 spaces
            else:
                current_line += " " + param_str
        
        # Add final line
        if current_line.strip():
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the cell card to a file.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def __str__(self) -> str:
        """String representation of the cell card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the cell card."""
        return (f"CellCard(cell_number={self.cell_number}, "
                f"material_number={self.material_number}, "
                f"density={self.density}, geometry='{self.geometry}', "
                f"parameters={len(self.parameters)})")


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Simple void cell
    print("Example 1: Void cell")
    void_cell = CellCard(1, geometry="1 -2 3")
    void_cell.set_importance(['n', 'p'], 1.0)
    print(f"Void cell: {void_cell}")
    print()
    
    # Example 2: Material cell with density
    print("Example 2: Material cell")
    fuel_cell = CellCard(2, material_number=1, density=-10.4, geometry="4 -5 6 -7")
    fuel_cell.set_importance(['n'], 1.0)
    fuel_cell.set_importance(['p'], 0.01)
    fuel_cell.set_temperature(600.0)
    fuel_cell.set_volume(1000.0)
    print(f"Fuel cell: {fuel_cell}")
    print()
    
    # Example 3: Cell with universe and fill
    print("Example 3: Universe cell")
    universe_cell = CellCard(3, material_number=2, density=0.001, geometry="8 -9")
    universe_cell.set_universe(1)
    universe_cell.set_fill(2)
    universe_cell.set_lattice(1)
    print(f"Universe cell: {universe_cell}")
    print()
    
    # Example 4: Cell with multiple temperatures
    print("Example 4: Cell with multiple temperatures")
    temp_cell = CellCard(4, material_number=3, density=-8.96, geometry="10 -11 12")
    temp_cell.set_temperature([300.0, 400.0, 500.0])
    temp_cell.add_parameter('WWN', [1e-6, 1e-5, 1e-4], 'n')
    print(f"Temperature cell: {temp_cell}")
    print()
    
    # Example 5: Complex cell with many parameters
    print("Example 5: Complex cell")
    complex_cell = CellCard(5, material_number=4, density=1.225e-3, 
                           geometry="(1 -2 3) : (4 -5 6) #7")
    complex_cell.set_importance(['n', 'p'], 1.0)
    complex_cell.set_importance(['e'], 0.1)
    complex_cell.add_parameter('EXT', 0.9, 'p')
    complex_cell.add_parameter('PWT', 0.25, ['n', 'p'])
    complex_cell.add_parameter('TRCL', [1, 2, 3, 45, 90, 0])
    print(f"Complex cell: {complex_cell}")
    print()
    
    # Test file writing
    print("Writing cell cards to file:")
    with open("test_cells.txt", "w") as f:
        f.write("c Cell card examples\n")
        f.write("c\n")
        void_cell.write_to_file(f)
        fuel_cell.write_to_file(f)
        universe_cell.write_to_file(f)
        temp_cell.write_to_file(f)
        complex_cell.write_to_file(f)
    
    print("Cell cards written to 'test_cells.txt'")
    
    # Test parameter manipulation
    print("\nTesting parameter manipulation:")
    test_cell = CellCard(99, material_number=1, density=-1.0, geometry="1 -2")
    
    print(f"Initial: {test_cell}")
    
    test_cell.set_importance('n', 1.0)
    print(f"After setting neutron importance: {test_cell}")
    
    imp_param = test_cell.get_parameter('IMP', 'n')
    print(f"Retrieved neutron importance: {imp_param.value if imp_param else 'Not found'}")
    
    test_cell.remove_parameter('IMP', 'n')
    print(f"After removing neutron importance: {test_cell}")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_cell = CellCard(0)  # Invalid cell number
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_cell = CellCard(1, material_number=1)  # Material without density
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_cell = CellCard(1, material_number=0, density=1.0)  # Void with density
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        test_cell = CellCard(1, material_number=1, density=1.0)
        test_cell.add_parameter('INVALID', 1.0)  # Invalid keyword
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        test_cell = CellCard(1, material_number=1, density=1.0)
        test_cell.add_parameter('IMP', 1.0)  # Missing particles for IMP
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Show all valid keywords
    print(f"\nValid cell parameter keywords: {sorted(CellCard.VALID_KEYWORDS)}")
    print(f"Keywords requiring particles: {sorted(CellCard.PARTICLE_KEYWORDS)}")
    print(f"Valid particle types: {sorted(CellCard.VALID_PARTICLES)}")
    