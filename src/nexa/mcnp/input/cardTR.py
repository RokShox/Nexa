from typing import List, Optional, Union, TextIO, Tuple
import math


class TRCard:
    """
    Represents an MCNP TR (coordinate transformation) card.
    
    The TR card defines coordinate transformations that can be used to:
    - Simplify geometric description of surfaces
    - Relate coordinate systems for surface source problems
    - Position universes within container cells
    
    The transformation consists of a displacement vector and rotation matrix.
    """
    
    def __init__(self, transformation_number: int, displacement: Optional[List[float]] = None,
                 rotation_matrix: Optional[List[List[float]]] = None, 
                 displacement_origin: int = 1, use_degrees: bool = False):
        """
        Initialize a TR card.
        
        Args:
            transformation_number: Transformation number (1-999 for surfaces, unlimited for TRCL)
            displacement: Displacement vector [o1, o2, o3] (default: [0, 0, 0])
            rotation_matrix: 3x3 rotation matrix or partial specification
            displacement_origin: 1 for auxiliary origin in main system, -1 for main origin in auxiliary
            use_degrees: If True, rotation matrix entries are angles in degrees (*TR form)
        """
        self.transformation_number = self._validate_transformation_number(transformation_number)
        self.displacement = displacement if displacement is not None else [0.0, 0.0, 0.0]
        self.displacement_origin = self._validate_displacement_origin(displacement_origin)
        self.use_degrees = use_degrees
        
        # Initialize rotation matrix
        if rotation_matrix is None:
            self.rotation_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
            self.matrix_specification = "identity"
        else:
            self.rotation_matrix, self.matrix_specification = self._process_rotation_matrix(rotation_matrix)
        
        self._validate_displacement()
    
    def _validate_transformation_number(self, number: int) -> int:
        """Validate transformation number."""
        if not isinstance(number, int):
            raise ValueError("Transformation number must be an integer")
        if number < 1:
            raise ValueError("Transformation number must be positive")
        return number
    
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
        
        Args:
            matrix_input: Partial or complete rotation matrix specification
            
        Returns:
            Tuple of (complete_matrix, specification_type)
        """
        # Flatten input for easier processing
        if isinstance(matrix_input[0], list):
            # 2D matrix input
            flat_input = []
            for row in matrix_input:
                flat_input.extend(row)
        else:
            # Already flat
            flat_input = matrix_input
        
        # Convert to float
        try:
            flat_input = [float(x) for x in flat_input]
        except (ValueError, TypeError):
            raise ValueError("Rotation matrix entries must be numeric")
        
        num_entries = len(flat_input)
        
        if num_entries == 0:
            # No entries - identity matrix
            return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], "identity"
        elif num_entries == 3:
            # One vector - MCNP will create other vectors arbitrarily
            return self._complete_matrix_one_vector(flat_input), "one_vector"
        elif num_entries == 5:
            # One vector each way (Eulerian angles)
            return self._complete_matrix_eulerian(flat_input), "eulerian"
        elif num_entries == 6:
            # Two vectors - complete by cross product
            return self._complete_matrix_two_vectors(flat_input), "two_vectors"
        elif num_entries == 9:
            # Complete matrix
            matrix = [[flat_input[0], flat_input[1], flat_input[2]],
                     [flat_input[3], flat_input[4], flat_input[5]],
                     [flat_input[6], flat_input[7], flat_input[8]]]
            self._validate_rotation_matrix(matrix)
            return matrix, "complete"
        else:
            raise ValueError(f"Invalid number of rotation matrix entries: {num_entries}. "
                           f"Expected 0, 3, 5, 6, or 9 entries.")
    
    def _complete_matrix_one_vector(self, vector: List[float]) -> List[List[float]]:
        """Complete matrix from one vector (3 values)."""
        # Normalize the input vector
        v = self._normalize_vector(vector)
        
        # Create two arbitrary orthogonal vectors
        # Choose a vector that's not parallel to v
        if abs(v[0]) < 0.9:
            u = [1.0, 0.0, 0.0]
        else:
            u = [0.0, 1.0, 0.0]
        
        # Create first orthogonal vector by cross product
        w1 = self._cross_product(v, u)
        w1 = self._normalize_vector(w1)
        
        # Create second orthogonal vector
        w2 = self._cross_product(v, w1)
        w2 = self._normalize_vector(w2)
        
        return [v, w1, w2]
    
    def _complete_matrix_eulerian(self, values: List[float]) -> List[List[float]]:
        """Complete matrix using Eulerian angles scheme (5 values)."""
        # This is a simplified implementation
        # In practice, MCNP uses a more sophisticated algorithm
        if len(values) != 5:
            raise ValueError("Eulerian scheme requires exactly 5 values")
        
        # Use first 3 as one vector, remaining 2 to constrain second vector
        v1 = self._normalize_vector(values[:3])
        
        # Create a second vector using the constraint
        # This is a simplified approach
        if abs(values[3]) < 1.0:
            v2 = [values[3], values[4], math.sqrt(1 - values[3]**2 - values[4]**2)]
        else:
            v2 = [values[3], math.sqrt(1 - values[3]**2), values[4]]
        
        v2 = self._normalize_vector(v2)
        
        # Third vector by cross product
        v3 = self._cross_product(v1, v2)
        v3 = self._normalize_vector(v3)
        
        return [v1, v2, v3]
    
    def _complete_matrix_two_vectors(self, values: List[float]) -> List[List[float]]:
        """Complete matrix from two vectors (6 values)."""
        v1 = self._normalize_vector(values[:3])
        v2 = self._normalize_vector(values[3:6])
        
        # Third vector by cross product
        v3 = self._cross_product(v1, v2)
        v3 = self._normalize_vector(v3)
        
        return [v1, v2, v3]
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize a vector to unit length."""
        magnitude = math.sqrt(sum(x**2 for x in vector))
        if magnitude == 0:
            raise ValueError("Cannot normalize zero vector")
        return [x/magnitude for x in vector]
    
    def _cross_product(self, v1: List[float], v2: List[float]) -> List[float]:
        """Calculate cross product of two 3D vectors."""
        return [
            v1[1]*v2[2] - v1[2]*v2[1],
            v1[2]*v2[0] - v1[0]*v2[2],
            v1[0]*v2[1] - v1[1]*v2[0]
        ]
    
    def _validate_rotation_matrix(self, matrix: List[List[float]]) -> None:
        """Validate that the rotation matrix is orthogonal."""
        # Check dimensions
        if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
            raise ValueError("Rotation matrix must be 3x3")
        
        # Check orthogonality (simplified check)
        tolerance = 0.001
        for i in range(3):
            for j in range(3):
                dot_product = sum(matrix[i][k] * matrix[j][k] for k in range(3))
                expected = 1.0 if i == j else 0.0
                if abs(dot_product - expected) > tolerance:
                    print(f"Warning: Rotation matrix non-orthogonality detected: {abs(dot_product - expected):.6f}")
                    break
    
    def set_displacement(self, o1: float, o2: float, o3: float) -> None:
        """Set the displacement vector."""
        self.displacement = [float(o1), float(o2), float(o3)]
    
    def set_displacement_origin(self, origin: int) -> None:
        """Set the displacement origin flag."""
        self.displacement_origin = self._validate_displacement_origin(origin)
    
    def set_rotation_matrix(self, matrix: List[List[float]]) -> None:
        """Set the rotation matrix."""
        self.rotation_matrix, self.matrix_specification = self._process_rotation_matrix(matrix)
    
    def set_identity_transformation(self) -> None:
        """Set to identity transformation (no rotation or displacement)."""
        self.displacement = [0.0, 0.0, 0.0]
        self.rotation_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        self.matrix_specification = "identity"
        self.displacement_origin = 1
    
    def set_translation_only(self, o1: float, o2: float, o3: float) -> None:
        """Set pure translation (no rotation)."""
        self.set_displacement(o1, o2, o3)
        self.rotation_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        self.matrix_specification = "identity"
    
    def is_identity(self) -> bool:
        """Check if this is an identity transformation."""
        identity_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        zero_displacement = [0.0, 0.0, 0.0]
        
        return (self.displacement == zero_displacement and 
                self.rotation_matrix == identity_matrix and
                self.displacement_origin == 1)
    
    def is_translation_only(self) -> bool:
        """Check if this is a pure translation (no rotation)."""
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
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert the TR card to MCNP input format.
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted TR card string
        """
        # Start with card name
        card_name = f"*tr{self.transformation_number}" if self.use_degrees else f"tr{self.transformation_number}"
        
        components = [card_name]
        
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
        
        # Handle line wrapping
        current_line = components[0]  # Start with card name
        lines = []
        
        for component in components[1:]:
            if len(current_line + " " + component) > line_length:
                lines.append(current_line)
                current_line = "     " + component  # Continuation with 5 spaces
            else:
                current_line += " " + component
        
        # Add final line
        if current_line.strip():
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the TR card to a file.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def get_transformation_description(self) -> str:
        """Get a description of the transformation."""
        desc = f"TR{self.transformation_number}: "
        
        if self.is_identity():
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
    
    @classmethod
    def create_translation(cls, transformation_number: int, o1: float, o2: float, o3: float,
                          displacement_origin: int = 1) -> 'TRCard':
        """Create a pure translation transformation."""
        tr_card = cls(transformation_number, displacement_origin=displacement_origin)
        tr_card.set_translation_only(o1, o2, o3)
        return tr_card
    
    @classmethod
    def create_rotation_x(cls, transformation_number: int, angle_degrees: float) -> 'TRCard':
        """Create a rotation about the x-axis."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        rotation_matrix = [
            [1.0, 0.0, 0.0],
            [0.0, cos_a, -sin_a],
            [0.0, sin_a, cos_a]
        ]
        
        return cls(transformation_number, rotation_matrix=rotation_matrix)
    
    @classmethod
    def create_rotation_y(cls, transformation_number: int, angle_degrees: float) -> 'TRCard':
        """Create a rotation about the y-axis."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        rotation_matrix = [
            [cos_a, 0.0, sin_a],
            [0.0, 1.0, 0.0],
            [-sin_a, 0.0, cos_a]
        ]
        
        return cls(transformation_number, rotation_matrix=rotation_matrix)
    
    @classmethod
    def create_rotation_z(cls, transformation_number: int, angle_degrees: float) -> 'TRCard':
        """Create a rotation about the z-axis."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        rotation_matrix = [
            [cos_a, -sin_a, 0.0],
            [sin_a, cos_a, 0.0],
            [0.0, 0.0, 1.0]
        ]
        
        return cls(transformation_number, rotation_matrix=rotation_matrix)
    
    def __str__(self) -> str:
        """String representation of the TR card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the TR card."""
        return (f"TRCard(transformation_number={self.transformation_number}, "
                f"displacement={self.displacement}, "
                f"matrix_spec='{self.matrix_specification}', "
                f"origin={self.displacement_origin}, "
                f"degrees={self.use_degrees})")


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Identity transformation
    print("Example 1: Identity transformation")
    tr1 = TRCard(1)
    print(f"Card: {tr1}")
    print(f"Description: {tr1.get_transformation_description()}")
    print(f"Is identity: {tr1.is_identity()}")
    print()
    
    # Example 2: Pure translation
    print("Example 2: Pure translation")
    tr2 = TRCard.create_translation(2, 10.0, 20.0, 30.0)
    print(f"Card: {tr2}")
    print(f"Description: {tr2.get_transformation_description()}")
    print(f"Is translation only: {tr2.is_translation_only()}")
    print()
    
    # Example 3: Rotation about z-axis
    print("Example 3: Rotation about z-axis")
    tr3 = TRCard.create_rotation_z(3, 45.0)
    print(f"Card: {tr3}")
    print(f"Description: {tr3.get_transformation_description()}")
    print()
    
    # Example 4: Combined translation and rotation
    print("Example 4: Combined translation and rotation")
    tr4 = TRCard.create_rotation_x(4, 90.0)
    tr4.set_displacement(5.0, 0.0, 0.0)
    print(f"Card: {tr4}")
    print(f"Description: {tr4.get_transformation_description()}")
    print()
    
    # Example 5: Custom rotation matrix
    print("Example 5: Custom rotation matrix")
    custom_matrix = [
        [0.707, -0.707, 0.0],
        [0.707, 0.707, 0.0],
        [0.0, 0.0, 1.0]
    ]
    tr5 = TRCard(5, displacement=[1.0, 2.0, 3.0], rotation_matrix=custom_matrix)
    print(f"Card: {tr5}")
    print()
    
    # Example 6: Partial matrix specification (one vector)
    print("Example 6: Partial matrix specification (one vector)")
    tr6 = TRCard(6, rotation_matrix=[[1.0, 1.0, 0.0]])  # Will be normalized and completed
    print(f"Card: {tr6}")
    print(f"Matrix specification: {tr6.matrix_specification}")
    print()
    
    # Example 7: Using degrees for angles (*TR form)
    print("Example 7: Using degrees (*TR form)")
    angle_matrix = [
        [0.0, 90.0, 90.0],  # Angles in degrees
        [90.0, 0.0, 90.0],
        [90.0, 90.0, 0.0]
    ]
    tr7 = TRCard(7, rotation_matrix=angle_matrix, use_degrees=True)
    print(f"Card: {tr7}")
    print()
    
    # Example 8: Alternative displacement origin
    print("Example 8: Alternative displacement origin")
    tr8 = TRCard(8, displacement=[10.0, 20.0, 30.0], displacement_origin=-1)
    print(f"Card: {tr8}")
    print(f"Description: {tr8.get_transformation_description()}")
    print()
    
    # Test file writing
    print("Writing TR cards to file:")
    with open("test_tr_cards.txt", "w") as f:
        f.write("c TR card examples\n")
        f.write("c\n")
        f.write("c Identity transformation\n")
        tr1.write_to_file(f)
        f.write("c\n")
        f.write("c Pure translation\n")
        tr2.write_to_file(f)
        f.write("c\n")
        f.write("c Rotation about z-axis\n")
        tr3.write_to_file(f)
        f.write("c\n")
        f.write("c Combined transformation\n")
        tr4.write_to_file(f)
        f.write("c\n")
        f.write("c Custom matrix\n")
        tr5.write_to_file(f)
    
    print("TR cards written to 'test_tr_cards.txt'")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_tr = TRCard(0)  # Invalid transformation number
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_tr = TRCard(1, displacement=[1.0, 2.0])  # Wrong displacement size
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_tr = TRCard(1, displacement_origin=2)  # Invalid origin flag
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_tr = TRCard(1, rotation_matrix=[[1.0, 2.0]])  # Invalid matrix size
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Show convenience methods
    print("\nConvenience transformations:")
    print("X-rotation 90°:", TRCard.create_rotation_x(10, 90.0))
    print("Y-rotation 45°:", TRCard.create_rotation_y(11, 45.0))
    print("Z-rotation 30°:", TRCard.create_rotation_z(12, 30.0))
    print("Translation:", TRCard.create_translation(13, 5.0, 10.0, 15.0))
    
    print("\nTR card features:")
    print("- Displacement vector: origin translation")
    print("- Rotation matrix: 3x3 orthogonal matrix")
    print("- Partial specification: 0, 3, 5, 6, or 9 matrix entries")
    print("- Degree notation: *TR for angles in degrees")
    print("- Origin flag: 1 (default) or -1 for coordinate system reference")
    print("- Surface transformations: n = 1-999")
    print("- Cell transformations (TRCL): unlimited n")
    