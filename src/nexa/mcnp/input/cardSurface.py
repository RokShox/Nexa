from typing import List, Optional, Union, TextIO
from abc import ABC, abstractmethod
from dataclasses import dataclass
import math


@dataclass
class SurfaceParameters:
    """Base class for surface parameters."""
    pass


@dataclass
class PlaneParameters(SurfaceParameters):
    """Parameters for plane surfaces."""
    A: float = 0.0
    B: float = 0.0
    C: float = 0.0
    D: float = 0.0


@dataclass
class SphereParameters(SurfaceParameters):
    """Parameters for sphere surfaces."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    R: float = 0.0


@dataclass
class CylinderParameters(SurfaceParameters):
    """Parameters for cylinder surfaces."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    R: float = 0.0


@dataclass
class ConeParameters(SurfaceParameters):
    """Parameters for cone surfaces."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    t_squared: float = 0.0
    sheet: int = 1  # +1 or -1 for one-sheet cones


@dataclass
class QuadricParameters(SurfaceParameters):
    """Parameters for general quadric surfaces (SQ)."""
    A: float = 0.0
    B: float = 0.0
    C: float = 0.0
    D: float = 0.0
    E: float = 0.0
    F: float = 0.0
    G: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class GeneralQuadricParameters(SurfaceParameters):
    """Parameters for general quadric surfaces (GQ)."""
    A: float = 0.0
    B: float = 0.0
    C: float = 0.0
    D: float = 0.0
    E: float = 0.0
    F: float = 0.0
    G: float = 0.0
    H: float = 0.0
    J: float = 0.0
    K: float = 0.0


@dataclass
class TorusParameters(SurfaceParameters):
    """Parameters for torus surfaces."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    A: float = 0.0
    B: float = 0.0
    C: float = 0.0


class SurfaceCard:
    """
    Represents an MCNP surface card.
    
    Surface cards define geometric surfaces using various equations and mnemonics.
    They can be normal, reflecting (*), or white boundary (+) surfaces.
    """
    
    # Valid surface types and their parameter counts
    SURFACE_TYPES = {
        # Planes
        'P': 4,    # General plane: A, B, C, D
        'PX': 1,   # Normal to x-axis: D
        'PY': 1,   # Normal to y-axis: D
        'PZ': 1,   # Normal to z-axis: D
        
        # Spheres
        'SO': 1,   # Centered at origin: R
        'S': 4,    # General sphere: x, y, z, R
        'SX': 2,   # Centered on x-axis: x, R
        'SY': 2,   # Centered on y-axis: y, R
        'SZ': 2,   # Centered on z-axis: z, R
        
        # Cylinders
        'C/X': 3,  # Parallel to x-axis: y, z, R
        'C/Y': 3,  # Parallel to y-axis: x, z, R
        'C/Z': 3,  # Parallel to z-axis: x, y, R
        'CX': 1,   # On x-axis: R
        'CY': 1,   # On y-axis: R
        'CZ': 1,   # On z-axis: R
        
        # Cones
        'K/X': 5,  # Parallel to x-axis: x, y, z, t², ±1
        'K/Y': 5,  # Parallel to y-axis: x, y, z, t², ±1
        'K/Z': 5,  # Parallel to z-axis: x, y, z, t², ±1
        'KX': 3,   # On x-axis: x, t², ±1
        'KY': 3,   # On y-axis: y, t², ±1
        'KZ': 3,   # On z-axis: z, t², ±1
        
        # General surfaces
        'SQ': 10,  # Ellipsoid/hyperboloid/paraboloid/cylinder: A,B,C,D,E,F,G,x,y,z
        'GQ': 10,  # General quadric: A,B,C,D,E,F,G,H,J,K
        
        # Tori
        'TX': 6,   # Elliptical torus parallel to x-axis: x,y,z,A,B,C
        'TY': 6,   # Elliptical torus parallel to y-axis: x,y,z,A,B,C
        'TZ': 6,   # Elliptical torus parallel to z-axis: x,y,z,A,B,C
    }
    
    def __init__(self, surface_number: int, surface_type: str, parameters: List[float], 
                 transformation: Optional[int] = None, reflecting: bool = False, 
                 white_boundary: bool = False):
        """
        Initialize a surface card.
        
        Args:
            surface_number: Surface number (1-99,999,999)
            surface_type: Surface mnemonic from Table 5.1
            parameters: List of numerical parameters for the surface
            transformation: Transformation number (positive) or periodic surface (negative)
            reflecting: True if this is a reflecting surface (*)
            white_boundary: True if this is a white boundary surface (+)
        """
        self.surface_number = self._validate_surface_number(surface_number)
        self.surface_type = self._validate_surface_type(surface_type)
        self.parameters = self._validate_parameters(surface_type, parameters)
        self.transformation = transformation
        self.reflecting = reflecting
        self.white_boundary = white_boundary
        
        # Validate mutually exclusive options
        if reflecting and white_boundary:
            raise ValueError("Surface cannot be both reflecting and white boundary")
        
        # Validate transformation restrictions
        if transformation is not None and (reflecting or white_boundary):
            if transformation < 0:
                raise ValueError("Periodic surfaces cannot be reflecting or white boundary")
    
    def _validate_surface_number(self, surface_number: int) -> int:
        """Validate surface number."""
        if not isinstance(surface_number, int):
            raise ValueError("Surface number must be an integer")
        if not (1 <= surface_number <= 99999999):
            raise ValueError("Surface number must be between 1 and 99,999,999")
        return surface_number
    
    def _validate_surface_type(self, surface_type: str) -> str:
        """Validate surface type mnemonic."""
        if not isinstance(surface_type, str):
            raise ValueError("Surface type must be a string")
        
        surface_type = surface_type.upper()
        if surface_type not in self.SURFACE_TYPES:
            raise ValueError(f"Unknown surface type: {surface_type}")
        
        return surface_type
    
    def _validate_parameters(self, surface_type: str, parameters: List[float]) -> List[float]:
        """Validate parameters for the given surface type."""
        if not isinstance(parameters, list):
            raise ValueError("Parameters must be a list")
        
        expected_count = self.SURFACE_TYPES[surface_type]
        if len(parameters) != expected_count:
            raise ValueError(f"Surface type {surface_type} requires {expected_count} parameters, got {len(parameters)}")
        
        # Convert to float and validate
        try:
            validated_params = [float(p) for p in parameters]
        except (ValueError, TypeError):
            raise ValueError("All parameters must be numeric")
        
        # Special validations for specific surface types
        if surface_type in ['SO', 'S', 'SX', 'SY', 'SZ', 'CX', 'CY', 'CZ', 'C/X', 'C/Y', 'C/Z']:
            # Radius must be positive for spheres and cylinders
            radius_index = -1  # Radius is always the last parameter
            if validated_params[radius_index] <= 0:
                raise ValueError(f"Radius must be positive for {surface_type} surface")
        
        if surface_type in ['K/X', 'K/Y', 'K/Z', 'KX', 'KY', 'KZ']:
            # Cone sheet parameter must be ±1
            sheet_param = validated_params[-1]
            if sheet_param not in [1, -1]:
                raise ValueError("Cone sheet parameter must be +1 or -1")
        
        return validated_params
    
    def get_surface_prefix(self) -> str:
        """Get the surface number prefix based on surface properties."""
        if self.reflecting:
            return f"*{self.surface_number}"
        elif self.white_boundary:
            return f"+{self.surface_number}"
        else:
            return str(self.surface_number)
    
    def is_periodic(self) -> bool:
        """Check if this surface is periodic."""
        return self.transformation is not None and self.transformation < 0
    
    def get_periodic_partner(self) -> Optional[int]:
        """Get the periodic partner surface number."""
        if self.is_periodic():
            return abs(self.transformation)
        return None
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert the surface card to MCNP input format.
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted surface card string
        """
        # Build the card components
        components = [self.get_surface_prefix()]
        
        # Add transformation if present
        if self.transformation is not None:
            components.append(str(self.transformation))
        
        # Add surface type
        components.append(self.surface_type.lower())
        
        # Add parameters
        for param in self.parameters:
            if isinstance(param, float):
                if param == int(param):
                    components.append(str(int(param)))
                else:
                    components.append(f"{param:.6g}")
            else:
                components.append(str(param))
        
        # Join components and handle line wrapping
        current_line = " ".join(components)
        
        if len(current_line) <= line_length:
            return current_line
        
        # Need to wrap - split after surface type
        lines = []
        base_part = " ".join(components[:3])  # number, transformation, type
        lines.append(base_part)
        
        # Add parameters with continuation
        param_parts = components[3:]
        current_line = "     "  # 5 spaces for continuation
        
        for part in param_parts:
            if len(current_line + " " + part) > line_length:
                lines.append(current_line.rstrip())
                current_line = "     " + part
            else:
                if current_line.strip():
                    current_line += " " + part
                else:
                    current_line += part
        
        if current_line.strip():
            lines.append(current_line.rstrip())
        
        return "\n".join(lines)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the surface card to a file.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def get_equation_description(self) -> str:
        """Get a description of the surface equation."""
        descriptions = {
            'P': f"General plane: {self.parameters[0]}x + {self.parameters[1]}y + {self.parameters[2]}z - {self.parameters[3]} = 0",
            'PX': f"Plane normal to x-axis: x - {self.parameters[0]} = 0",
            'PY': f"Plane normal to y-axis: y - {self.parameters[0]} = 0",
            'PZ': f"Plane normal to z-axis: z - {self.parameters[0]} = 0",
            'SO': f"Sphere centered at origin: x² + y² + z² - {self.parameters[0]}² = 0",
            'S': f"General sphere: (x-{self.parameters[0]})² + (y-{self.parameters[1]})² + (z-{self.parameters[2]})² - {self.parameters[3]}² = 0",
            'SX': f"Sphere centered on x-axis: (x-{self.parameters[0]})² + y² + z² - {self.parameters[1]}² = 0",
            'SY': f"Sphere centered on y-axis: x² + (y-{self.parameters[0]})² + z² - {self.parameters[1]}² = 0",
            'SZ': f"Sphere centered on z-axis: x² + y² + (z-{self.parameters[0]})² - {self.parameters[1]}² = 0",
            'CX': f"Cylinder on x-axis: y² + z² - {self.parameters[0]}² = 0",
            'CY': f"Cylinder on y-axis: x² + z² - {self.parameters[0]}² = 0",
            'CZ': f"Cylinder on z-axis: x² + y² - {self.parameters[0]}² = 0",
            'C/X': f"Cylinder parallel to x-axis: (y-{self.parameters[0]})² + (z-{self.parameters[1]})² - {self.parameters[2]}² = 0",
            'C/Y': f"Cylinder parallel to y-axis: (x-{self.parameters[0]})² + (z-{self.parameters[1]})² - {self.parameters[2]}² = 0",
            'C/Z': f"Cylinder parallel to z-axis: (x-{self.parameters[0]})² + (y-{self.parameters[1]})² - {self.parameters[2]}² = 0",
        }
        
        return descriptions.get(self.surface_type, f"{self.surface_type} surface with parameters {self.parameters}")
    
    @classmethod
    def create_plane(cls, surface_number: int, A: float, B: float, C: float, D: float, **kwargs) -> 'SurfaceCard':
        """Create a general plane surface."""
        return cls(surface_number, 'P', [A, B, C, D], **kwargs)
    
    @classmethod
    def create_plane_x(cls, surface_number: int, D: float, **kwargs) -> 'SurfaceCard':
        """Create a plane normal to x-axis."""
        return cls(surface_number, 'PX', [D], **kwargs)
    
    @classmethod
    def create_plane_y(cls, surface_number: int, D: float, **kwargs) -> 'SurfaceCard':
        """Create a plane normal to y-axis."""
        return cls(surface_number, 'PY', [D], **kwargs)
    
    @classmethod
    def create_plane_z(cls, surface_number: int, D: float, **kwargs) -> 'SurfaceCard':
        """Create a plane normal to z-axis."""
        return cls(surface_number, 'PZ', [D], **kwargs)
    
    @classmethod
    def create_sphere_origin(cls, surface_number: int, radius: float, **kwargs) -> 'SurfaceCard':
        """Create a sphere centered at origin."""
        return cls(surface_number, 'SO', [radius], **kwargs)
    
    @classmethod
    def create_sphere(cls, surface_number: int, x: float, y: float, z: float, radius: float, **kwargs) -> 'SurfaceCard':
        """Create a general sphere."""
        return cls(surface_number, 'S', [x, y, z, radius], **kwargs)
    
    @classmethod
    def create_cylinder_z(cls, surface_number: int, x: float, y: float, radius: float, **kwargs) -> 'SurfaceCard':
        """Create a cylinder parallel to z-axis."""
        return cls(surface_number, 'C/Z', [x, y, radius], **kwargs)
    
    @classmethod
    def create_cylinder_on_z(cls, surface_number: int, radius: float, **kwargs) -> 'SurfaceCard':
        """Create a cylinder on z-axis."""
        return cls(surface_number, 'CZ', [radius], **kwargs)
    
    @classmethod
    def create_cone_z(cls, surface_number: int, x: float, y: float, z: float, t_squared: float, sheet: int = 1, **kwargs) -> 'SurfaceCard':
        """Create a cone parallel to z-axis."""
        return cls(surface_number, 'K/Z', [x, y, z, t_squared, sheet], **kwargs)
    
    @classmethod
    def create_torus_z(cls, surface_number: int, x: float, y: float, z: float, A: float, B: float, C: float, **kwargs) -> 'SurfaceCard':
        """Create an elliptical torus with axis parallel to z-axis."""
        return cls(surface_number, 'TZ', [x, y, z, A, B, C], **kwargs)
    
    def __str__(self) -> str:
        """String representation of the surface card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the surface card."""
        return (f"SurfaceCard(surface_number={self.surface_number}, "
                f"surface_type='{self.surface_type}', parameters={self.parameters}, "
                f"transformation={self.transformation}, reflecting={self.reflecting}, "
                f"white_boundary={self.white_boundary})")


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Simple planes
    print("Example 1: Plane surfaces")
    plane_x = SurfaceCard.create_plane_x(1, 5.0)
    plane_y = SurfaceCard.create_plane_y(2, -3.0)
    plane_z = SurfaceCard.create_plane_z(3, 10.0)
    print(f"X-plane: {plane_x}")
    print(f"Y-plane: {plane_y}")
    print(f"Z-plane: {plane_z}")
    print()
    
    # Example 2: Spheres
    print("Example 2: Sphere surfaces")
    sphere_origin = SurfaceCard.create_sphere_origin(10, 5.0)
    sphere_general = SurfaceCard.create_sphere(11, 1.0, 2.0, 3.0, 4.0)
    print(f"Sphere at origin: {sphere_origin}")
    print(f"General sphere: {sphere_general}")
    print(f"Equation: {sphere_general.get_equation_description()}")
    print()
    
    # Example 3: Cylinders
    print("Example 3: Cylinder surfaces")
    cylinder_z = SurfaceCard.create_cylinder_z(20, 0.0, 0.0, 2.5)
    cylinder_on_z = SurfaceCard.create_cylinder_on_z(21, 1.0)
    print(f"Cylinder parallel to z: {cylinder_z}")
    print(f"Cylinder on z-axis: {cylinder_on_z}")
    print()
    
    # Example 4: Reflecting and white boundary surfaces
    print("Example 4: Special surface types")
    reflecting_plane = SurfaceCard.create_plane_z(30, 0.0, reflecting=True)
    white_sphere = SurfaceCard.create_sphere_origin(31, 10.0, white_boundary=True)
    print(f"Reflecting plane: {reflecting_plane}")
    print(f"White boundary sphere: {white_sphere}")
    print()
    
    # Example 5: Transformed surfaces
    print("Example 5: Transformed surfaces")
    transformed_cylinder = SurfaceCard.create_cylinder_z(40, 0.0, 0.0, 1.0, transformation=1)
    periodic_plane = SurfaceCard.create_plane_x(41, 5.0, transformation=-42)
    print(f"Transformed cylinder: {transformed_cylinder}")
    print(f"Periodic plane: {periodic_plane}")
    print(f"Periodic partner: {periodic_plane.get_periodic_partner()}")
    print()
    
    # Example 6: Cones and tori
    print("Example 6: Cones and tori")
    cone_z = SurfaceCard.create_cone_z(50, 0.0, 0.0, 0.0, 1.0, sheet=1)
    torus_z = SurfaceCard.create_torus_z(51, 0.0, 0.0, 0.0, 5.0, 2.0, 1.0)
    print(f"Cone: {cone_z}")
    print(f"Torus: {torus_z}")
    print()
    
    # Example 7: General quadric surfaces
    print("Example 7: General surfaces")
    quadric = SurfaceCard(60, 'SQ', [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, -25.0, 0.0, 0.0, 0.0])
    general_quadric = SurfaceCard(61, 'GQ', [1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0])
    print(f"SQ surface: {quadric}")
    print(f"GQ surface: {general_quadric}")
    print()
    
    # Test file writing
    print("Writing surface cards to file:")
    with open("test_surfaces.txt", "w") as f:
        f.write("c Surface card examples\n")
        f.write("c\n")
        plane_x.write_to_file(f)
        sphere_general.write_to_file(f)
        cylinder_z.write_to_file(f)
        reflecting_plane.write_to_file(f)
        cone_z.write_to_file(f)
        quadric.write_to_file(f)
    
    print("Surface cards written to 'test_surfaces.txt'")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_surface = SurfaceCard(1, 'SO', [])  # Missing radius
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_surface = SurfaceCard(1, 'SO', [-5.0])  # Negative radius
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_surface = SurfaceCard(1, 'INVALID', [1.0])  # Invalid surface type
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_surface = SurfaceCard(1, 'KZ', [0.0, 1.0, 0.5])  # Invalid cone sheet
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Demonstrate all surface types
    print("\nAll supported surface types:")
    for surface_type, param_count in SurfaceCard.SURFACE_TYPES.items():
        print(f"  {surface_type}: {param_count} parameters")
    