from typing import List, Optional, Union, TextIO, Dict, Set


class LATCard:
    """
    Represents an MCNP LAT (lattice) card for defining lattice cells.
    
    The LAT card can be used in two forms:
    1. Cell-card form: LAT = n (as a cell parameter)
    2. Data-card form: LAT n1 n2 ... nJ (for all cells in the problem)
    
    Lattice types:
    - LAT = 1: Rectangular (square) lattice of hexahedra (6 faces)
    - LAT = 2: Hexagonal (triangular) lattice of hexagonal prisms (8 faces)
    """
    
    # Valid lattice types
    VALID_LATTICE_TYPES = {1, 2}
    
    # Surface ordering requirements for each lattice type
    HEXAHEDRAL_SURFACES = 6  # [+x, -x, +y, -y, +z, -z]
    HEXAGONAL_PRISM_SURFACES = 8  # [+x, -x, +y, -y, -x+y, +x-y, +z, -z]
    
    def __init__(self):
        """Initialize a LAT card."""
        self.lattice_assignments: Dict[int, int] = {}  # cell_number -> lattice_type
        self.max_cell_number = 0
    
    def set_lattice_type(self, cell_number: int, lattice_type: int) -> None:
        """
        Set lattice type for a specific cell.
        
        Args:
            cell_number: Cell number (1-based)
            lattice_type: Lattice type (1 for hexahedral, 2 for hexagonal prism, 0 for non-lattice)
        """
        if not isinstance(cell_number, int) or cell_number < 1:
            raise ValueError("Cell number must be a positive integer")
        
        if not isinstance(lattice_type, int):
            raise ValueError("Lattice type must be an integer")
        
        if lattice_type != 0 and lattice_type not in self.VALID_LATTICE_TYPES:
            raise ValueError(f"Lattice type must be 0, 1, or 2. Got: {lattice_type}")
        
        if lattice_type == 0:
            # Remove lattice assignment for non-lattice cells
            if cell_number in self.lattice_assignments:
                del self.lattice_assignments[cell_number]
                # Update max_cell_number if necessary
                if cell_number == self.max_cell_number:
                    self.max_cell_number = max(self.lattice_assignments.keys()) if self.lattice_assignments else 0
        else:
            self.lattice_assignments[cell_number] = lattice_type
            self.max_cell_number = max(self.max_cell_number, cell_number)
    
    def set_lattice_assignments(self, assignments: List[int]) -> None:
        """
        Set lattice types for cells 1, 2, 3, ... in order.
        
        Args:
            assignments: List of lattice types for cells 1, 2, 3, ... (0 for non-lattice)
        """
        self.lattice_assignments.clear()
        
        for i, lattice_type in enumerate(assignments, 1):
            if not isinstance(lattice_type, int):
                raise ValueError(f"Lattice type for cell {i} must be an integer")
            if lattice_type != 0 and lattice_type not in self.VALID_LATTICE_TYPES:
                raise ValueError(f"Lattice type for cell {i} must be 0, 1, or 2. Got: {lattice_type}")
            
            if lattice_type != 0:  # Only store non-zero assignments
                self.lattice_assignments[i] = lattice_type
        
        self.max_cell_number = len(assignments)
    
    def get_lattice_type(self, cell_number: int) -> int:
        """
        Get lattice type for a specific cell.
        
        Args:
            cell_number: Cell number
            
        Returns:
            Lattice type (0 if not a lattice cell)
        """
        return self.lattice_assignments.get(cell_number, 0)
    
    def is_lattice_cell(self, cell_number: int) -> bool:
        """
        Check if a cell is a lattice cell.
        
        Args:
            cell_number: Cell number
            
        Returns:
            True if cell is a lattice cell
        """
        return self.get_lattice_type(cell_number) != 0
    
    def is_hexahedral_lattice(self, cell_number: int) -> bool:
        """
        Check if a cell is a hexahedral lattice (LAT = 1).
        
        Args:
            cell_number: Cell number
            
        Returns:
            True if cell is a hexahedral lattice
        """
        return self.get_lattice_type(cell_number) == 1
    
    def is_hexagonal_prism_lattice(self, cell_number: int) -> bool:
        """
        Check if a cell is a hexagonal prism lattice (LAT = 2).
        
        Args:
            cell_number: Cell number
            
        Returns:
            True if cell is a hexagonal prism lattice
        """
        return self.get_lattice_type(cell_number) == 2
    
    def get_required_surfaces(self, cell_number: int) -> int:
        """
        Get the number of surfaces required for a lattice cell.
        
        Args:
            cell_number: Cell number
            
        Returns:
            Number of required surfaces (0 for non-lattice cells)
        """
        lattice_type = self.get_lattice_type(cell_number)
        if lattice_type == 1:
            return self.HEXAHEDRAL_SURFACES
        elif lattice_type == 2:
            return self.HEXAGONAL_PRISM_SURFACES
        else:
            return 0
    
    def get_surface_order_description(self, cell_number: int) -> str:
        """
        Get description of surface ordering for a lattice cell.
        
        Args:
            cell_number: Cell number
            
        Returns:
            Description of required surface ordering
        """
        lattice_type = self.get_lattice_type(cell_number)
        
        if lattice_type == 1:
            return ("Hexahedral lattice surface order:\n"
                   "1st surface: [+1,0,0] element beyond\n"
                   "2nd surface: [-1,0,0] element beyond\n"
                   "3rd surface: [0,+1,0] element beyond\n"
                   "4th surface: [0,-1,0] element beyond\n"
                   "5th surface: [0,0,+1] element beyond\n"
                   "6th surface: [0,0,-1] element beyond")
        elif lattice_type == 2:
            return ("Hexagonal prism lattice surface order:\n"
                   "1st surface: [+1,0,0] element beyond\n"
                   "2nd surface: [-1,0,0] element beyond\n"
                   "3rd surface: [0,+1,0] element beyond\n"
                   "4th surface: [0,-1,0] element beyond\n"
                   "5th surface: [-1,+1,0] element beyond\n"
                   "6th surface: [+1,-1,0] element beyond\n"
                   "7th surface: [0,0,+1] element beyond\n"
                   "8th surface: [0,0,-1] element beyond")
        else:
            return "Not a lattice cell"
    
    def remove_lattice(self, cell_number: int) -> bool:
        """
        Remove lattice assignment for a cell.
        
        Args:
            cell_number: Cell number to remove
            
        Returns:
            True if removed, False if not found
        """
        if cell_number in self.lattice_assignments:
            del self.lattice_assignments[cell_number]
            # Update max_cell_number if necessary
            if cell_number == self.max_cell_number:
                self.max_cell_number = max(self.lattice_assignments.keys()) if self.lattice_assignments else 0
            return True
        return False
    
    def clear_assignments(self) -> None:
        """Clear all lattice assignments."""
        self.lattice_assignments.clear()
        self.max_cell_number = 0
    
    def get_all_assignments(self) -> Dict[int, int]:
        """Get a copy of all lattice assignments."""
        return self.lattice_assignments.copy()
    
    def get_max_cell_number(self) -> int:
        """Get the maximum cell number with lattice assignment."""
        return self.max_cell_number
    
    def has_assignments(self) -> bool:
        """Check if any lattice assignments are defined."""
        return len(self.lattice_assignments) > 0
    
    def get_lattice_cells(self, lattice_type: Optional[int] = None) -> List[int]:
        """
        Get all cells with lattice assignments.
        
        Args:
            lattice_type: Specific lattice type to filter (None for all)
            
        Returns:
            List of cell numbers with lattice assignments
        """
        if lattice_type is None:
            return list(self.lattice_assignments.keys())
        else:
            return [cell for cell, lat_type in self.lattice_assignments.items() 
                    if lat_type == lattice_type]
    
    def get_used_lattice_types(self) -> Set[int]:
        """Get set of all lattice types used."""
        return set(self.lattice_assignments.values())
    
    def _compress_assignments(self, assignment_list: List[int]) -> List[str]:
        """
        Compress consecutive identical assignments using jump notation.
        
        Args:
            assignment_list: List of lattice assignments
            
        Returns:
            List of strings with jump notation
        """
        if not assignment_list:
            return []
        
        result = []
        i = 0
        
        while i < len(assignment_list):
            current_type = assignment_list[i]
            
            # Count consecutive identical assignments
            count = 1
            while (i + count < len(assignment_list) and 
                   assignment_list[i + count] == current_type):
                count += 1
            
            # Add entry with repeat notation if needed
            if current_type == 0:
                # Use jump notation for non-lattice cells
                if count == 1:
                    result.append("J")
                else:
                    result.append(f"{count}J")
            else:
                # Regular lattice type
                if count == 1:
                    result.append(str(current_type))
                else:
                    result.append(f"{count}R {current_type}")
            
            i += count
        
        return result
    
    def to_data_card_string(self, line_length: int = 80) -> str:
        """
        Convert to data card form (LAT n1 n2 ... nJ).
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted LAT data card string
        """
        if self.max_cell_number == 0:
            return "lat"
        
        # Build assignment list from 1 to max_cell_number
        assignment_list = []
        for i in range(1, self.max_cell_number + 1):
            assignment_list.append(self.lattice_assignments.get(i, 0))
        
        # Compress using repeat/jump notation
        compressed = self._compress_assignments(assignment_list)
        
        # Build card
        components = ["lat"] + compressed
        
        # Handle line wrapping
        lines = []
        current_line = components[0]  # Start with "lat"
        
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
        Convert to cell parameter form for a specific cell (LAT = n).
        
        Args:
            cell_number: Cell number for the cell parameter
            
        Returns:
            Formatted LAT cell parameter string
        """
        lattice_type = self.lattice_assignments.get(cell_number)
        
        if lattice_type is None:
            raise ValueError(f"No lattice assignment for cell {cell_number}")
        
        return f"LAT={lattice_type}"
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert to MCNP input format (data card form).
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted LAT card string
        """
        return self.to_data_card_string(line_length)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the LAT card to a file in data card form.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def write_cell_parameter_to_file(self, file: TextIO, cell_number: int) -> None:
        """
        Write a cell parameter form LAT specification to a file.
        
        Args:
            file: Open file object to write to
            cell_number: Cell number for the cell parameter
        """
        file.write(self.to_cell_parameter_string(cell_number) + '\n')
    
    def validate_lattice_setup(self) -> List[str]:
        """
        Validate lattice setup for potential issues.
        
        Returns:
            List of warning/error messages
        """
        warnings = []
        
        # Check for lattice cells without universe assignments
        # (This would require access to U card information)
        
        # Check for consistent lattice types
        used_types = self.get_used_lattice_types()
        if len(used_types) > 1:
            warnings.append(f"Multiple lattice types used: {sorted(used_types)}")
        
        # Inform about surface requirements
        for cell_num, lat_type in self.lattice_assignments.items():
            required_surfaces = self.get_required_surfaces(cell_num)
            warnings.append(f"Cell {cell_num} (LAT={lat_type}) requires {required_surfaces} surfaces in specific order")
        
        return warnings
    
    def get_lattice_type_description(self, lattice_type: int) -> str:
        """
        Get description of a lattice type.
        
        Args:
            lattice_type: Lattice type (1 or 2)
            
        Returns:
            Description of the lattice type
        """
        if lattice_type == 1:
            return "Rectangular (square) lattice of hexahedra (6 faces)"
        elif lattice_type == 2:
            return "Hexagonal (triangular) lattice of hexagonal prisms (8 faces)"
        elif lattice_type == 0:
            return "Non-lattice cell"
        else:
            return f"Invalid lattice type: {lattice_type}"
    
    def __str__(self) -> str:
        """String representation of the LAT card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the LAT card."""
        return (f"LATCard(assignments={dict(sorted(self.lattice_assignments.items()))}, "
                f"max_cell={self.max_cell_number})")
    
    def __len__(self) -> int:
        """Return the number of cells with lattice assignments."""
        return len(self.lattice_assignments)


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Simple lattice assignments
    print("Example 1: Simple lattice assignments")
    lat1 = LATCard()
    lat1.set_lattice_assignments([0, 1, 1, 0, 2])
    print(f"Data card: {lat1}")
    print(f"Cell 2 parameter: {lat1.to_cell_parameter_string(2)}")
    print(f"Cell 5 parameter: {lat1.to_cell_parameter_string(5)}")
    print()
    
    # Example 2: Individual lattice assignment
    print("Example 2: Individual lattice assignment")
    lat2 = LATCard()
    lat2.set_lattice_type(1, 1)  # Hexahedral lattice
    lat2.set_lattice_type(3, 2)  # Hexagonal prism lattice
    lat2.set_lattice_type(5, 1)  # Another hexahedral lattice
    print(f"Data card: {lat2}")
    print(f"Lattice cells: {lat2.get_lattice_cells()}")
    print(f"Hexahedral cells: {lat2.get_lattice_cells(1)}")
    print(f"Hexagonal prism cells: {lat2.get_lattice_cells(2)}")
    print()
    
    # Example 3: Surface ordering information
    print("Example 3: Surface ordering information")
    lat3 = LATCard()
    lat3.set_lattice_type(1, 1)  # Hexahedral
    lat3.set_lattice_type(2, 2)  # Hexagonal prism
    
    print("Hexahedral lattice (cell 1):")
    print(lat3.get_surface_order_description(1))
    print(f"Required surfaces: {lat3.get_required_surfaces(1)}")
    print()
    
    print("Hexagonal prism lattice (cell 2):")
    print(lat3.get_surface_order_description(2))
    print(f"Required surfaces: {lat3.get_required_surfaces(2)}")
    print()
    
    # Example 4: Large problem with compression
    print("Example 4: Large problem with compression")
    lat4 = LATCard()
    assignments = [0] * 5 + [1] * 10 + [0] * 3 + [2] * 5 + [0] * 2
    lat4.set_lattice_assignments(assignments)
    print(f"Data card: {lat4}")
    print()
    
    # Example 5: Integration with cell cards
    print("Example 5: Integration with cell cards")
    from .cardCell import CellCard
    
    # Create lattice cells
    hex_cell = CellCard(1, material_number=0, geometry="1 -2 3 -4 5 -6")
    hex_cell.set_lattice(1)  # This would use the existing method
    hex_cell.set_universe(1)
    hex_cell.set_fill("1 2 3")
    
    hexprism_cell = CellCard(2, material_number=0, geometry="10 -11 12 -13 14 -15 16 -17 18 -19")
    hexprism_cell.set_lattice(2)
    hexprism_cell.set_universe(2)
    hexprism_cell.set_fill("4 5 6")
    
    print(f"Hexahedral cell: {hex_cell}")
    print(f"Hexagonal prism cell: {hexprism_cell}")
    print()
    
    # Create corresponding LAT card
    lat5 = LATCard()
    lat5.set_lattice_type(1, 1)
    lat5.set_lattice_type(2, 2)
    print(f"LAT data card: {lat5}")
    print()
    
    # Test file writing
    print("Writing LAT cards to file:")
    with open("test_lat_cards.txt", "w") as f:
        f.write("c LAT card examples\n")
        f.write("c\n")
        f.write("c Simple assignments\n")
        lat1.write_to_file(f)
        f.write("c\n")
        f.write("c Individual assignments\n")
        lat2.write_to_file(f)
        f.write("c\n")
        f.write("c Cell parameter examples\n")
        f.write("c Cell 2 lattice\n")
        lat1.write_cell_parameter_to_file(f, 2)
        f.write("c Cell 1 lattice\n")
        lat2.write_cell_parameter_to_file(f, 1)
    
    print("LAT cards written to 'test_lat_cards.txt'")
    
    # Test lattice queries
    print("\nTesting lattice queries:")
    test_lat = LATCard()
    test_lat.set_lattice_type(1, 1)
    test_lat.set_lattice_type(2, 2)
    test_lat.set_lattice_type(3, 0)  # Non-lattice
    
    print(f"Initial: {test_lat}")
    print(f"Cell 1 lattice type: {test_lat.get_lattice_type(1)}")
    print(f"Cell 3 lattice type: {test_lat.get_lattice_type(3)}")
    print(f"Is cell 1 lattice: {test_lat.is_lattice_cell(1)}")
    print(f"Is cell 3 lattice: {test_lat.is_lattice_cell(3)}")
    print(f"Is cell 1 hexahedral: {test_lat.is_hexahedral_lattice(1)}")
    print(f"Is cell 2 hexagonal prism: {test_lat.is_hexagonal_prism_lattice(2)}")
    
    test_lat.remove_lattice(2)
    print(f"After removing cell 2: {test_lat}")
    
    # Test validation
    print("\nTesting validation:")
    warnings = test_lat.validate_lattice_setup()
    if warnings:
        for warning in warnings:
            print(f"Info: {warning}")
    else:
        print("No validation warnings")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_lat = LATCard()
        bad_lat.set_lattice_type(0, 1)  # Invalid cell number
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_lat = LATCard()
        bad_lat.set_lattice_type(1, 3)  # Invalid lattice type
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        test_lat = LATCard()
        test_lat.set_lattice_type(1, 1)
        test_lat.to_cell_parameter_string(2)  # Cell without lattice
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Show lattice descriptions
    print("\nLattice type descriptions:")
    for lat_type in [0, 1, 2]:
        print(f"LAT = {lat_type}: {lat1.get_lattice_type_description(lat_type)}")
    
    print("\nLAT card features:")
    print("- Cell parameter form: LAT = n")
    print("- Data card form: LAT n1 n2 ... nJ")
    print("- LAT = 1: Hexahedral lattice (6 surfaces)")
    print("- LAT = 2: Hexagonal prism lattice (8 surfaces)")
    print("- Surface ordering defines lattice element relationships")
    print("- Must be used with FILL and U parameters")
    print("- Lattice must be only thing in its universe")
    print("- [0,0,0] element is the base lattice cell")
