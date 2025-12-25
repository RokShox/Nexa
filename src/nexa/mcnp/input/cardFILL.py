from typing import List, Optional, Union, TextIO, Dict, Tuple, Any
import re
from cardTRCL import TRCLCard


class FILLCard:
    """
    Represents an MCNP FILL card for specifying universe filling.
    
    The FILL card can be used in multiple forms:
    1. Cell-card form: FILL = n (simple universe fill)
    2. Cell-card form: FILL = n (q) (with transformation reference)
    3. Cell-card form: FILL = n (transformation) (with explicit transformation)
    4. Cell-card form: FILL i1:i2 j1:j2 k1:k2 n1,1,1 ... (lattice array)
    5. Data-card form: FILL n1 n2 ... nJ (for all cells)
    
    Used to specify which universes fill cells, especially for lattice structures.
    """
    
    def __init__(self):
        """Initialize a FILL card."""
        self.fill_assignments: Dict[int, 'FillSpecification'] = {}  # cell_number -> fill_spec
        self.max_cell_number = 0
        self.use_degrees = False  # For *FILL form
    
    def set_simple_fill(self, cell_number: int, universe_number: int, 
                       transformation: Optional[Union[int, TRCLCard, List[float]]] = None) -> None:
        """
        Set simple universe fill for a cell.
        
        Args:
            cell_number: Cell number (1-based)
            universe_number: Universe number to fill with
            transformation: Optional transformation (TR number, TRCL object, or explicit values)
        """
        if not isinstance(cell_number, int) or cell_number < 1:
            raise ValueError("Cell number must be a positive integer")
        
        if not isinstance(universe_number, int):
            raise ValueError("Universe number must be an integer")
        
        if not (0 <= universe_number <= 99999999):
            raise ValueError("Universe number must be between 0 and 99,999,999")
        
        fill_spec = SimpleFillSpecification(universe_number, transformation)
        self.fill_assignments[cell_number] = fill_spec
        self.max_cell_number = max(self.max_cell_number, cell_number)
    
    def set_lattice_fill(self, cell_number: int, 
                        i_range: Tuple[int, int], j_range: Tuple[int, int], k_range: Tuple[int, int],
                        universe_array: List[List[List[int]]], 
                        transformations: Optional[Dict[Tuple[int, int, int], Union[int, TRCLCard, List[float]]]] = None) -> None:
        """
        Set lattice array fill for a cell.
        
        Args:
            cell_number: Cell number (1-based)
            i_range: (i1, i2) range for first lattice index
            j_range: (j1, j2) range for second lattice index  
            k_range: (k1, k2) range for third lattice index
            universe_array: 3D array of universe numbers [i][j][k]
            transformations: Optional transformations for specific lattice elements
        """
        if not isinstance(cell_number, int) or cell_number < 1:
            raise ValueError("Cell number must be a positive integer")
        
        # Validate ranges
        if not (isinstance(i_range, tuple) and len(i_range) == 2):
            raise ValueError("i_range must be a tuple of (i1, i2)")
        if not (isinstance(j_range, tuple) and len(j_range) == 2):
            raise ValueError("j_range must be a tuple of (j1, j2)")
        if not (isinstance(k_range, tuple) and len(k_range) == 2):
            raise ValueError("k_range must be a tuple of (k1, k2)")
        
        i1, i2 = i_range
        j1, j2 = j_range
        k1, k2 = k_range
        
        if i2 < i1 or j2 < j1 or k2 < k1:
            raise ValueError("Upper bounds must be >= lower bounds")
        
        # Validate array dimensions
        expected_i = i2 - i1 + 1
        expected_j = j2 - j1 + 1
        expected_k = k2 - k1 + 1
        
        if len(universe_array) != expected_i:
            raise ValueError(f"Universe array i-dimension {len(universe_array)} doesn't match range {expected_i}")
        
        for i, i_slice in enumerate(universe_array):
            if len(i_slice) != expected_j:
                raise ValueError(f"Universe array j-dimension at i={i} doesn't match range {expected_j}")
            for j, j_slice in enumerate(i_slice):
                if len(j_slice) != expected_k:
                    raise ValueError(f"Universe array k-dimension at i={i}, j={j} doesn't match range {expected_k}")
        
        # Validate universe numbers
        for i in range(expected_i):
            for j in range(expected_j):
                for k in range(expected_k):
                    universe = universe_array[i][j][k]
                    if not isinstance(universe, int):
                        raise ValueError(f"Universe at [{i},{j},{k}] must be an integer")
                    if not (0 <= universe <= 99999999):
                        raise ValueError(f"Universe at [{i},{j},{k}] must be between 0 and 99,999,999")
        
        fill_spec = LatticeFillSpecification(i_range, j_range, k_range, universe_array, transformations)
        self.fill_assignments[cell_number] = fill_spec
        self.max_cell_number = max(self.max_cell_number, cell_number)
    
    def set_fill_assignments(self, assignments: List[int]) -> None:
        """
        Set fill assignments for cells 1, 2, 3, ... in order.
        
        Args:
            assignments: List of universe numbers for cells 1, 2, 3, ... (0 for no fill)
        """
        self.fill_assignments.clear()
        
        for i, universe_num in enumerate(assignments, 1):
            if not isinstance(universe_num, int):
                raise ValueError(f"Universe number for cell {i} must be an integer")
            if not (0 <= universe_num <= 99999999):
                raise ValueError(f"Universe number for cell {i} must be between 0 and 99,999,999")
            
            if universe_num != 0:  # Only store non-zero assignments
                self.fill_assignments[i] = SimpleFillSpecification(universe_num)
        
        self.max_cell_number = len(assignments)
    
    def get_fill_specification(self, cell_number: int) -> Optional['FillSpecification']:
        """
        Get fill specification for a specific cell.
        
        Args:
            cell_number: Cell number
            
        Returns:
            FillSpecification or None if not assigned
        """
        return self.fill_assignments.get(cell_number)
    
    def is_filled_cell(self, cell_number: int) -> bool:
        """
        Check if a cell has fill specification.
        
        Args:
            cell_number: Cell number
            
        Returns:
            True if cell has fill specification
        """
        return cell_number in self.fill_assignments
    
    def is_lattice_fill(self, cell_number: int) -> bool:
        """
        Check if a cell has lattice fill specification.
        
        Args:
            cell_number: Cell number
            
        Returns:
            True if cell has lattice fill
        """
        spec = self.get_fill_specification(cell_number)
        return isinstance(spec, LatticeFillSpecification)
    
    def remove_fill(self, cell_number: int) -> bool:
        """
        Remove fill specification for a cell.
        
        Args:
            cell_number: Cell number to remove
            
        Returns:
            True if removed, False if not found
        """
        if cell_number in self.fill_assignments:
            del self.fill_assignments[cell_number]
            # Update max_cell_number if necessary
            if cell_number == self.max_cell_number:
                self.max_cell_number = max(self.fill_assignments.keys()) if self.fill_assignments else 0
            return True
        return False
    
    def clear_assignments(self) -> None:
        """Clear all fill assignments."""
        self.fill_assignments.clear()
        self.max_cell_number = 0
    
    def get_all_assignments(self) -> Dict[int, 'FillSpecification']:
        """Get a copy of all fill assignments."""
        return self.fill_assignments.copy()
    
    def get_max_cell_number(self) -> int:
        """Get the maximum cell number with fill assignment."""
        return self.max_cell_number
    
    def has_assignments(self) -> bool:
        """Check if any fill assignments are defined."""
        return len(self.fill_assignments) > 0
    
    def get_filled_cells(self) -> List[int]:
        """Get all cells with fill assignments."""
        return list(self.fill_assignments.keys())
    
    def set_use_degrees(self, use_degrees: bool) -> None:
        """Set whether to use degrees for transformations (*FILL form)."""
        self.use_degrees = use_degrees
    
    def _compress_assignments(self, assignment_list: List[int]) -> List[str]:
        """
        Compress consecutive identical assignments using jump notation.
        
        Args:
            assignment_list: List of universe assignments
            
        Returns:
            List of strings with jump notation
        """
        if not assignment_list:
            return []
        
        result = []
        i = 0
        
        while i < len(assignment_list):
            current_universe = assignment_list[i]
            
            # Count consecutive identical assignments
            count = 1
            while (i + count < len(assignment_list) and 
                   assignment_list[i + count] == current_universe):
                count += 1
            
            # Add entry with repeat notation if needed
            if current_universe == 0:
                # Use jump notation for non-filled cells
                if count == 1:
                    result.append("J")
                else:
                    result.append(f"{count}J")
            else:
                # Regular universe number
                if count == 1:
                    result.append(str(current_universe))
                else:
                    result.append(f"{count}R {current_universe}")
            
            i += count
        
        return result
    
    def to_data_card_string(self, line_length: int = 80) -> str:
        """
        Convert to data card form (FILL n1 n2 ... nJ).
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted FILL data card string
        """
        if self.max_cell_number == 0:
            card_name = "*fill" if self.use_degrees else "fill"
            return card_name
        
        # Build assignment list from 1 to max_cell_number
        assignment_list = []
        for i in range(1, self.max_cell_number + 1):
            spec = self.fill_assignments.get(i)
            if isinstance(spec, SimpleFillSpecification):
                assignment_list.append(spec.universe_number)
            else:
                assignment_list.append(0)  # Default to 0 (no fill)
        
        # Compress using repeat/jump notation
        compressed = self._compress_assignments(assignment_list)
        
        # Build card
        card_name = "*fill" if self.use_degrees else "fill"
        components = [card_name] + compressed
        
        # Handle line wrapping
        lines = []
        current_line = components[0]  # Start with "fill"
        
        for entry in compressed:
            if len(current_line + " " + entry) > line_length:
                lines.append(current_line)
                current_line = "     " + entry  # Continuation with 5 spaces
            else:
                current_line += " " + entry
        
        # Add final line
        if current_line.strip():
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def to_cell_parameter_string(self, cell_number: int) -> str:
        """
        Convert to cell parameter form for a specific cell.
        
        Args:
            cell_number: Cell number for the cell parameter
            
        Returns:
            Formatted FILL cell parameter string
        """
        spec = self.fill_assignments.get(cell_number)
        
        if spec is None:
            raise ValueError(f"No fill specification for cell {cell_number}")
        
        keyword = "*FILL" if self.use_degrees else "FILL"
        return f"{keyword}={spec.to_parameter_string()}"
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert to MCNP input format (data card form).
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted FILL card string
        """
        return self.to_data_card_string(line_length)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the FILL card to a file in data card form.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def write_cell_parameter_to_file(self, file: TextIO, cell_number: int) -> None:
        """
        Write a cell parameter form FILL specification to a file.
        
        Args:
            file: Open file object to write to
            cell_number: Cell number for the cell parameter
        """
        file.write(self.to_cell_parameter_string(cell_number) + '\n')
    
    def validate_fill_setup(self) -> List[str]:
        """
        Validate fill setup for potential issues.
        
        Returns:
            List of warning/error messages
        """
        warnings = []
        
        # Check for lattice fills without corresponding LAT assignments
        # (This would require access to LAT card information)
        
        # Check for large universe numbers
        for cell_num, spec in self.fill_assignments.items():
            if isinstance(spec, SimpleFillSpecification):
                if spec.universe_number > 10000:
                    warnings.append(f"Cell {cell_num}: Large universe number {spec.universe_number}")
            elif isinstance(spec, LatticeFillSpecification):
                for universe in spec.get_all_universes():
                    if universe > 10000:
                        warnings.append(f"Cell {cell_num}: Large universe number {universe} in lattice")
        
        return warnings
    
    def __str__(self) -> str:
        """String representation of the FILL card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the FILL card."""
        return (f"FILLCard(assignments={len(self.fill_assignments)}, "
                f"max_cell={self.max_cell_number}, degrees={self.use_degrees})")
    
    def __len__(self) -> int:
        """Return the number of cells with fill assignments."""
        return len(self.fill_assignments)


class FillSpecification:
    """Base class for fill specifications."""
    
    def to_parameter_string(self) -> str:
        """Convert to parameter string format."""
        raise NotImplementedError
    
    def to_data_string(self) -> str:
        """Convert to data card format."""
        raise NotImplementedError


class SimpleFillSpecification(FillSpecification):
    """Simple universe fill specification."""
    
    def __init__(self, universe_number: int, 
                 transformation: Optional[Union[int, TRCLCard, List[float]]] = None):
        """
        Initialize simple fill specification.
        
        Args:
            universe_number: Universe number to fill with
            transformation: Optional transformation (TR number, TRCL object, or explicit values)
        """
        self.universe_number = universe_number
        self.transformation = transformation
    
    def to_parameter_string(self) -> str:
        """Convert to parameter string format."""
        if self.transformation is None:
            return str(self.universe_number)
        elif isinstance(self.transformation, int):
            return f"{self.universe_number} ({self.transformation})"
        elif isinstance(self.transformation, TRCLCard):
            if self.transformation.is_reference_form:
                return f"{self.universe_number} ({self.transformation.transformation_reference})"
            else:
                # Explicit transformation
                return f"{self.universe_number} {self.transformation.to_cell_parameter_string()}"
        elif isinstance(self.transformation, list):
            # Explicit transformation values
            trans_str = " ".join(str(x) for x in self.transformation)
            return f"{self.universe_number} ({trans_str})"
        else:
            return str(self.universe_number)
    
    def to_data_string(self) -> str:
        """Convert to data card format."""
        return str(self.universe_number)


class LatticeFillSpecification(FillSpecification):
    """Lattice array fill specification."""
    
    def __init__(self, i_range: Tuple[int, int], j_range: Tuple[int, int], k_range: Tuple[int, int],
                 universe_array: List[List[List[int]]],
                 transformations: Optional[Dict[Tuple[int, int, int], Union[int, TRCLCard, List[float]]]] = None):
        """
        Initialize lattice fill specification.
        
        Args:
            i_range: (i1, i2) range for first lattice index
            j_range: (j1, j2) range for second lattice index
            k_range: (k1, k2) range for third lattice index
            universe_array: 3D array of universe numbers [i][j][k]
            transformations: Optional transformations for specific lattice elements
        """
        self.i_range = i_range
        self.j_range = j_range
        self.k_range = k_range
        self.universe_array = universe_array
        self.transformations = transformations or {}
    
    def get_universe(self, i: int, j: int, k: int) -> int:
        """Get universe number for lattice element [i, j, k]."""
        i1, i2 = self.i_range
        j1, j2 = self.j_range
        k1, k2 = self.k_range
        
        if not (i1 <= i <= i2 and j1 <= j <= j2 and k1 <= k <= k2):
            raise ValueError(f"Indices [{i},{j},{k}] out of range")
        
        return self.universe_array[i - i1][j - j1][k - k1]
    
    def get_all_universes(self) -> List[int]:
        """Get all universe numbers in the array."""
        universes = []
        for i_slice in self.universe_array:
            for j_slice in i_slice:
                universes.extend(j_slice)
        return universes
    
    def to_parameter_string(self) -> str:
        """Convert to parameter string format."""
        i1, i2 = self.i_range
        j1, j2 = self.j_range
        k1, k2 = self.k_range
        
        # Range specification
        range_str = f"{i1}:{i2} {j1}:{j2} {k1}:{k2}"
        
        # Universe array values
        values = []
        for k in range(k1, k2 + 1):
            for j in range(j1, j2 + 1):
                for i in range(i1, i2 + 1):
                    universe = self.universe_array[i - i1][j - j1][k - k1]
                    
                    # Check for transformation
                    if (i, j, k) in self.transformations:
                        trans = self.transformations[(i, j, k)]
                        if isinstance(trans, int):
                            values.append(f"{universe} ({trans})")
                        else:
                            values.append(str(universe))  # Simplified for now
                    else:
                        values.append(str(universe))
        
        return f"{range_str} {' '.join(values)}"
    
    def to_data_string(self) -> str:
        """Convert to data card format (not applicable for lattice fills)."""
        return "lattice_fill"


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Simple fill assignments
    print("Example 1: Simple fill assignments")
    fill1 = FILLCard()
    fill1.set_fill_assignments([0, 1, 2, 0, 3])
    print(f"Data card: {fill1}")
    print(f"Cell 2 parameter: {fill1.to_cell_parameter_string(2)}")
    print()
    
    # Example 2: Simple fill with transformation
    print("Example 2: Simple fill with transformation")
    fill2 = FILLCard()
    fill2.set_simple_fill(1, 1, transformation=5)  # Reference TR5
    fill2.set_simple_fill(2, 2, transformation=[1, 2, 3, 45, 90, 0])  # Explicit transformation
    print(f"Cell 1 parameter: {fill2.to_cell_parameter_string(1)}")
    print(f"Cell 2 parameter: {fill2.to_cell_parameter_string(2)}")
    print()
    
    # Example 3: Lattice fill
    print("Example 3: Lattice fill")
    fill3 = FILLCard()
    
    # 2x2x2 lattice array
    universe_array = [
        [[1, 2], [3, 4]],  # i=0
        [[5, 6], [7, 8]]   # i=1
    ]
    
    fill3.set_lattice_fill(1, 
                          i_range=(0, 1), j_range=(0, 1), k_range=(0, 1),
                          universe_array=universe_array)
    
    print(f"Cell 1 lattice parameter: {fill3.to_cell_parameter_string(1)}")
    print()
    
    # Example 4: Lattice fill with transformations
    print("Example 4: Lattice fill with transformations")
    fill4 = FILLCard()
    
    # Small lattice with some transformations
    small_array = [[[10, 20]]]  # 1x1x2 array
    transformations = {
        (0, 0, 1): 5  # TR5 transformation for element [0,0,1]
    }
    
    fill4.set_lattice_fill(2,
                          i_range=(0, 0), j_range=(0, 0), k_range=(0, 1),
                          universe_array=small_array,
                          transformations=transformations)
    
    print(f"Cell 2 lattice parameter: {fill4.to_cell_parameter_string(2)}")
    print()
    
    # Example 5: Large problem with compression
    print("Example 5: Large problem with compression")
    fill5 = FILLCard()
    assignments = [0] * 5 + [1] * 10 + [0] * 3 + [2] * 5
    fill5.set_fill_assignments(assignments)
    print(f"Data card: {fill5}")
    print()
    
    # Example 6: Using degrees (*FILL)
    print("Example 6: Using degrees (*FILL)")
    fill6 = FILLCard()
    fill6.set_use_degrees(True)
    fill6.set_simple_fill(1, 1)
    fill6.set_simple_fill(2, 2)
    print(f"Data card: {fill6}")
    print()
    
    # Test file writing
    print("Writing FILL cards to file:")
    with open("test_fill_cards.txt", "w") as f:
        f.write("c FILL card examples\n")
        f.write("c\n")
        f.write("c Simple assignments\n")
        fill1.write_to_file(f)
        f.write("c\n")
        f.write("c Degrees form\n")
        fill6.write_to_file(f)
        f.write("c\n")
        f.write("c Cell parameter examples\n")
        f.write("c Cell 2 simple fill\n")
        fill1.write_cell_parameter_to_file(f, 2)
        f.write("c Cell 1 fill with transformation\n")
        fill2.write_cell_parameter_to_file(f, 1)
    
    print("FILL cards written to 'test_fill_cards.txt'")
    
    # Test fill queries
    print("\nTesting fill queries:")
    test_fill = FILLCard()
    test_fill.set_simple_fill(1, 1)
    test_fill.set_simple_fill(2, 2)
    
    print(f"Initial: {test_fill}")
    print(f"Is cell 1 filled: {test_fill.is_filled_cell(1)}")
    print(f"Is cell 3 filled: {test_fill.is_filled_cell(3)}")
    print(f"Is cell 1 lattice fill: {test_fill.is_lattice_fill(1)}")
    
    # Add lattice fill
    lattice_array = [[[100]]]
    test_fill.set_lattice_fill(3, (0, 0), (0, 0), (0, 0), lattice_array)
    print(f"Is cell 3 lattice fill: {test_fill.is_lattice_fill(3)}")
    
    test_fill.remove_fill(2)
    print(f"After removing cell 2: {test_fill}")
    
    # Test validation
    print("\nTesting validation:")
    warnings = test_fill.validate_fill_setup()
    if warnings:
        for warning in warnings:
            print(f"Warning: {warning}")
    else:
        print("No validation warnings")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_fill = FILLCard()
        bad_fill.set_simple_fill(0, 1)  # Invalid cell number
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_fill = FILLCard()
        bad_fill.set_simple_fill(1, -1)  # Invalid universe number
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_fill = FILLCard()
        bad_array = [[[1, 2]]]  # Wrong size for range
        bad_fill.set_lattice_fill(1, (0, 1), (0, 0), (0, 0), bad_array)
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        test_fill = FILLCard()
        test_fill.set_simple_fill(1, 1)
        test_fill.to_cell_parameter_string(2)  # Cell without fill
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Show usage patterns
    print("\nCommon usage patterns:")
    
    print("\n1. Simple universe fill:")
    simple_fill = FILLCard()
    simple_fill.set_simple_fill(1, 10)
    print(f"   {simple_fill.to_cell_parameter_string(1)}")
    
    print("\n2. Fill with transformation:")
    trans_fill = FILLCard()
    trans_fill.set_simple_fill(1, 10, transformation=5)
    print(f"   {trans_fill.to_cell_parameter_string(1)}")
    
    print("\n3. 2D lattice (fuel assembly):")
    assembly_fill = FILLCard()
    fuel_array = [
        [[1, 1, 1], [1, 2, 1], [1, 1, 1]],  # Row 0
        [[1, 2, 1], [2, 3, 2], [1, 2, 1]],  # Row 1
        [[1, 1, 1], [1, 2, 1], [1, 1, 1]]   # Row 2
    ]
    assembly_fill.set_lattice_fill(1, (-1, 1), (-1, 1), (0, 0), fuel_array)
    print(f"   3x3 assembly lattice")
    
    print("\n4. Special lattice values:")
    print("   - 0: Element doesn't exist (real world lattice)")
    print("   - Same as lattice universe: Fill with cell material")
    
    print("\nFILL card features:")
    print("- Cell parameter form: FILL = n")
    print("- Data card form: FILL n1 n2 ... nJ")
    print("- Simple fill: FILL = n")
    print("- Fill with transformation: FILL = n (q) or FILL = n (transformation)")
    print("- Lattice fill: FILL i1:i2 j1:j2 k1:k2 n1,1,1 ...")
    print("- Degree notation: *FILL for angles in degrees")
    print("- Required for repeated structures")
    print("- Must match LAT and U specifications")
    