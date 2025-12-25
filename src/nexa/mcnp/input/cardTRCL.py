from typing import List, Optional, Union, TextIO, Tuple
import math
from cardTR import TRCard


class TRCLCard:
    """
    Represents an MCNP TRCL (cell coordinate transformation) parameter.
    
    The TRCL parameter can be applied to a cell using either:
    1. Reference form: TRCL = n (references a TR n card)
    2. Explicit form: TRCL = (o1 o2 o3 xx' yx' zx' xy' yy' zy' xz' yz' zz' m)
    
    Cell transformations are especially useful for repeated structures and
    positioning universes within container cells.
    """
    
    def __init__(self, transformation_reference: Optional[int] = None,
                 displacement: Optional[List[float]] = None,
                 rotation_matrix: Optional[List[List[float]]] = None,
                 displacement_origin: int = 1, use_degrees: bool = False):
        """
        Initialize a TRCL parameter.
        
        Args:
            transformation_reference: TR card number to reference (None for explicit form)
            displacement: Displacement vector [o1, o2, o3] (for explicit form)
            rotation_matrix: 3x3 rotation matrix or partial specification (for explicit form)
            displacement_origin: 1 for auxiliary origin in main system, -1 for main origin in auxiliary
            use_degrees: If True, rotation matrix entries are angles in degrees (*TRCL form)
        """
        self.use_degrees = use_degrees
        
        if transformation_reference is not None:
            # Reference form
            self.is_reference_form = True
            self.transformation_reference = self._validate_transformation_reference(transformation_reference)
            self.displacement = None
            self.rotation_matrix = None
            self.displacement_origin = None
        else:
            # Explicit form
            self.is_reference_form = False
            self.transformation_reference = None
            self.displacement = displacement if displacement is not None else [0.0, 0.0, 0.0]
            self.displacement_origin = self._validate_displacement_origin(displacement_origin)
            
            # Initialize rotation matrix
            if rotation_matrix is None:
                self.rotation_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
                self.matrix_specification = "identity"
            else:
                self.rotation_matrix, self.matrix_specification = self._process_rotation_matrix(rotation_matrix)
            
            self._validate_displacement()
    
    def _validate_transformation_reference(self, reference: int) -> int:
        """Validate transformation reference number."""
        if not isinstance(reference, int):
            raise ValueError("Transformation reference must be an integer")
        if reference < 0:
            raise ValueError("Transformation reference must be non-negative")
        return reference
    
    def _validate_displacement_origin(self, origin: int) -> int:
        """Validate displacement origin flag."""
        if origin not in [1, -1]:
            raise ValueError("Displacement origin must be 1 or -1")
        return origin
    
    def _validate_displacement(self) -> None:
        """Validate displacement vector."""
        if not isinstance(self.displacement, list) or len(self.displacement) != 3:
            raise ValueError("Displacement must be a list of 3 numbers")
        
        try:
            self.displacement = [float(x) for x in self.displacement]
        except (ValueError, TypeError):
            raise ValueError("Displacement components must be numeric")
    
    def _process_rotation_matrix(self, matrix_input: List[List[float]]) -> Tuple[List[List[float]], str]:
        """
        Process rotation matrix input and complete it if partially specified.
        Uses the same logic as TRCard.
        """
        # Create a temporary TRCard to use its matrix processing logic
        temp_tr = TRCard(1, rotation_matrix=matrix_input)
        return temp_tr.rotation_matrix, temp_tr.matrix_specification
    
    @classmethod
    def create_reference(cls, transformation_number: int, use_degrees: bool = False) -> 'TRCLCard':
        """
        Create a TRCL parameter that references a TR card.
        
        Args:
            transformation_number: TR card number to reference
            use_degrees: If True, uses *TRCL form
            
        Returns:
            TRCLCard in reference form
        """
        return cls(transformation_reference=transformation_number, use_degrees=use_degrees)
    
    @classmethod
    def create_explicit(cls, displacement: Optional[List[float]] = None,
                       rotation_matrix: Optional[List[List[float]]] = None,
                       displacement_origin: int = 1, use_degrees: bool = False) -> 'TRCLCard':
        """
        Create a TRCL parameter with explicit transformation.
        
        Args:
            displacement: Displacement vector [o1, o2, o3]
            rotation_matrix: 3x3 rotation matrix or partial specification
            displacement_origin: 1 for auxiliary origin in main system, -1 for main origin in auxiliary
            use_degrees: If True, uses *TRCL form
            
        Returns:
            TRCLCard in explicit form
        """
        return cls(displacement=displacement, rotation_matrix=rotation_matrix,
                  displacement_origin=displacement_origin, use_degrees=use_degrees)
    
    @classmethod
    def create_identity(cls) -> 'TRCLCard':
        """Create an identity TRCL parameter (no transformation)."""
        return cls.create_reference(0)
    
    @classmethod
    def create_translation(cls, o1: float, o2: float, o3: float,
                          displacement_origin: int = 1, use_degrees: bool = False) -> 'TRCLCard':
        """Create a pure translation TRCL parameter."""
        return cls.create_explicit(displacement=[o1, o2, o3],
                                  displacement_origin=displacement_origin,
                                  use_degrees=use_degrees)
    
    @classmethod
    def create_rotation_x(cls, angle_degrees: float, use_degrees: bool = False) -> 'TRCLCard':
        """Create a rotation about the x-axis."""
        if use_degrees:
            rotation_matrix = [
                [0.0, 0.0, 0.0],
                [0.0, angle_degrees, -90.0],
                [0.0, 90.0, angle_degrees]
            ]
        else:
            angle_rad = math.radians(angle_degrees)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            rotation_matrix = [
                [1.0, 0.0, 0.0],
                [0.0, cos_a, -sin_a],
                [0.0, sin_a, cos_a]
            ]
        
        return cls.create_explicit(rotation_matrix=rotation_matrix, use_degrees=use_degrees)
    
    @classmethod
    def create_rotation_y(cls, angle_degrees: float, use_degrees: bool = False) -> 'TRCLCard':
        """Create a rotation about the y-axis."""
        if use_degrees:
            rotation_matrix = [
                [angle_degrees, 0.0, 90.0],
                [0.0, 0.0, 0.0],
                [-90.0, 0.0, angle_degrees]
            ]
        else:
            angle_rad = math.radians(angle_degrees)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            rotation_matrix = [
                [cos_a, 0.0, sin_a],
                [0.0, 1.0, 0.0],
                [-sin_a, 0.0, cos_a]
            ]
        
        return cls.create_explicit(rotation_matrix=rotation_matrix, use_degrees=use_degrees)
    
    @classmethod
    def create_rotation_z(cls, angle_degrees: float, use_degrees: bool = False) -> 'TRCLCard':
        """Create a rotation about the z-axis."""
        if use_degrees:
            rotation_matrix = [
                [angle_degrees, -90.0, 0.0],
                [90.0, angle_degrees, 0.0],
                [0.0, 0.0, 0.0]
            ]
        else:
            angle_rad = math.radians(angle_degrees)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            rotation_matrix = [
                [cos_a, -sin_a, 0.0],
                [sin_a, cos_a, 0.0],
                [0.0, 0.0, 1.0]
            ]
        
        return cls.create_explicit(rotation_matrix=rotation_matrix, use_degrees=use_degrees)
    
    def is_identity_transformation(self) -> bool:
        """Check if this represents an identity transformation."""
        if self.is_reference_form:
            return self.transformation_reference == 0
        else:
            identity_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
            zero_displacement = [0.0, 0.0, 0.0]
            return (self.displacement == zero_displacement and 
                    self.rotation_matrix == identity_matrix and
                    self.displacement_origin == 1)
    
    def is_translation_only(self) -> bool:
        """Check if this is a pure translation (no rotation)."""
        if self.is_reference_form:
            return False  # Cannot determine without the referenced TR card
        else:
            identity_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
            return self.rotation_matrix == identity_matrix
    
    def _format_number(self, value: float) -> str:
        """Format a number for output."""
        if value == 0.0:
            return "0"
        elif value == 1.0:
            return "1"
        elif value == -1.0:
            return "-1"
        elif abs(value) >= 1e-3 and abs(value) < 1e6:
            formatted = f"{value:.6f}".rstrip('0').rstrip('.')
            return formatted
        else:
            return f"{value:.6e}"
    
    def to_cell_parameter_string(self) -> str:
        """
        Convert to cell parameter format for use on cell cards.
        
        Returns:
            Formatted TRCL parameter string
        """
        if self.is_reference_form:
            # Reference form: TRCL = n or *TRCL = n
            keyword = "*TRCL" if self.use_degrees else "TRCL"
            return f"{keyword}={self.transformation_reference}"
        else:
            # Explicit form: TRCL = (o1 o2 o3 xx' yx' zx' xy' yy' zy' xz' yz' zz' m)
            keyword = "*TRCL" if self.use_degrees else "TRCL"
            
            components = []
            
            # Add displacement vector
            for component in self.displacement:
                components.append(self._format_number(component))
            
            # Add rotation matrix (flattened)
            for row in self.rotation_matrix:
                for component in row:
                    components.append(self._format_number(component))
            
            # Add displacement origin if not default
            if self.displacement_origin != 1:
                components.append(str(self.displacement_origin))
            
            # Join with spaces and enclose in parentheses
            parameter_values = " ".join(components)
            return f"{keyword}=({parameter_values})"
    
    def to_string(self) -> str:
        """String representation of the TRCL parameter."""
        return self.to_cell_parameter_string()
    
    def get_transformation_description(self) -> str:
        """Get a description of the transformation."""
        if self.is_reference_form:
            desc = f"TRCL reference to TR{self.transformation_reference}"
            if self.transformation_reference == 0:
                desc += " (identity transformation)"
        else:
            desc = "TRCL explicit: "
            if self.is_identity_transformation():
                desc += "Identity transformation"
            elif self.is_translation_only():
                desc += f"Translation by ({self.displacement[0]}, {self.displacement[1]}, {self.displacement[2]})"
            else:
                desc += f"Translation by ({self.displacement[0]}, {self.displacement[1]}, {self.displacement[2]}) "
                desc += f"with rotation (matrix specification: {self.matrix_specification})"
            
            if self.displacement_origin == -1:
                desc += " [main origin in auxiliary system]"
        
        if self.use_degrees:
            desc += " [angles in degrees]"
        
        return desc
    
    def convert_to_tr_card(self, transformation_number: int) -> Optional[TRCard]:
        """
        Convert explicit TRCL to equivalent TR card.
        
        Args:
            transformation_number: Number for the TR card
            
        Returns:
            TRCard if this is explicit form, None if reference form
        """
        if self.is_reference_form:
            return None
        
        return TRCard(transformation_number, 
                     displacement=self.displacement.copy(),
                     rotation_matrix=[row.copy() for row in self.rotation_matrix],
                     displacement_origin=self.displacement_origin,
                     use_degrees=self.use_degrees)
    
    def __str__(self) -> str:
        """String representation of the TRCL parameter."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the TRCL parameter."""
        if self.is_reference_form:
            return (f"TRCLCard(reference={self.transformation_reference}, "
                    f"degrees={self.use_degrees})")
        else:
            return (f"TRCLCard(displacement={self.displacement}, "
                    f"matrix_spec='{self.matrix_specification}', "
                    f"origin={self.displacement_origin}, "
                    f"degrees={self.use_degrees})")


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Reference form
    print("Example 1: Reference form")
    trcl1 = TRCLCard.create_reference(1)
    trcl2 = TRCLCard.create_identity()
    print(f"Reference TR1: {trcl1}")
    print(f"Identity: {trcl2}")
    print(f"Description: {trcl1.get_transformation_description()}")
    print()
    
    # Example 2: Explicit translation
    print("Example 2: Explicit translation")
    trcl3 = TRCLCard.create_translation(10.0, 20.0, 30.0)
    print(f"Translation: {trcl3}")
    print(f"Description: {trcl3.get_transformation_description()}")
    print(f"Is translation only: {trcl3.is_translation_only()}")
    print()
    
    # Example 3: Explicit rotation
    print("Example 3: Explicit rotation")
    trcl4 = TRCLCard.create_rotation_z(45.0)
    print(f"Z-rotation: {trcl4}")
    print(f"Description: {trcl4.get_transformation_description()}")
    print()
    
    # Example 4: Combined transformation
    print("Example 4: Combined transformation")
    trcl5 = TRCLCard.create_explicit(
        displacement=[5.0, 10.0, 15.0],
        rotation_matrix=[
            [0.707, -0.707, 0.0],
            [0.707, 0.707, 0.0],
            [0.0, 0.0, 1.0]
        ]
    )
    print(f"Combined: {trcl5}")
    print(f"Description: {trcl5.get_transformation_description()}")
    print()
    
    # Example 5: Using degrees (*TRCL)
    print("Example 5: Using degrees (*TRCL)")
    trcl6 = TRCLCard.create_rotation_x(90.0, use_degrees=True)
    print(f"X-rotation with degrees: {trcl6}")
    print()
    
    # Example 6: Alternative displacement origin
    print("Example 6: Alternative displacement origin")
    trcl7 = TRCLCard.create_translation(1.0, 2.0, 3.0, displacement_origin=-1)
    print(f"Alternative origin: {trcl7}")
    print(f"Description: {trcl7.get_transformation_description()}")
    print()
    
    # Example 7: Using in cell card context
    print("Example 7: Cell card usage")
    from cardCell import CellCard
    
    # Create a cell with TRCL parameter
    cell = CellCard(1, material_number=1, density=-1.0, geometry="1 -2 3")
    
    # Add TRCL as a parameter (this would need to be integrated into CellCard)
    trcl_ref = TRCLCard.create_reference(5)
    trcl_explicit = TRCLCard.create_translation(10.0, 0.0, 0.0)
    
    print(f"TRCL reference parameter: {trcl_ref.to_cell_parameter_string()}")
    print(f"TRCL explicit parameter: {trcl_explicit.to_cell_parameter_string()}")
    print()
    
    # Example 8: Convert to TR card
    print("Example 8: Convert to TR card")
    tr_card = trcl5.convert_to_tr_card(10)
    if tr_card:
        print(f"Converted TR card: {tr_card}")
    
    ref_tr = trcl1.convert_to_tr_card(11)
    print(f"Reference form conversion: {ref_tr}")
    print()
    
    # Test file writing (example of how it might be used)
    print("Example cell cards with TRCL:")
    cell_with_ref = CellCard(10, material_number=1, density=-1.0, geometry="1 -2")
    cell_with_explicit = CellCard(11, material_number=2, density=-2.0, geometry="3 -4")
    
    print(f"Cell 10: {cell_with_ref} {trcl_ref.to_cell_parameter_string()}")
    print(f"Cell 11: {cell_with_explicit} {trcl_explicit.to_cell_parameter_string()}")
    print()
    
    # Test error handling
    print("Testing error handling:")
    try:
        bad_trcl = TRCLCard.create_reference(-1)  # Invalid reference
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_trcl = TRCLCard.create_explicit(displacement=[1.0, 2.0])  # Wrong size
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_trcl = TRCLCard.create_explicit(displacement_origin=2)  # Invalid origin
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Show convenience methods
    print("\nConvenience transformations:")
    print("Reference TR5:", TRCLCard.create_reference(5))
    print("Identity:", TRCLCard.create_identity())
    print("X-rotation 90°:", TRCLCard.create_rotation_x(90.0))
    print("Y-rotation 45°:", TRCLCard.create_rotation_y(45.0))
    print("Z-rotation 30°:", TRCLCard.create_rotation_z(30.0))
    print("Translation:", TRCLCard.create_translation(5.0, 10.0, 15.0))
    
    print("\nTRCL parameter features:")
    print("- Reference form: TRCL = n (references TR n card)")
    print("- Explicit form: TRCL = (o1 o2 o3 xx' yx' zx' xy' yy' zy' xz' yz' zz' m)")
    print("- Degree notation: *TRCL for angles in degrees")
    print("- Cell transformations: no limit on transformation numbers")
    print("- Generated surfaces: original + 1000 × cell_number")
    print("- Surface number limit: original surfaces < 1000")
    print("- Cell number limit: ≤ 6 digits")
    