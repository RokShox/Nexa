from typing import List, Optional, Union, TextIO, Dict, Set


class UCard:
    """
    Represents an MCNP U (universe) card for assigning cells to universes.
    
    The U card can be used in two forms:
    1. Cell-card form: U = n (as a cell parameter)
    2. Data-card form: U n1 n2 ... nJ (for all cells in the problem)
    
    Universes enable repeated structures and hierarchical geometry modeling
    with up to 20 levels of nesting.
    """
    
    def __init__(self):
        """Initialize a U card."""
        self.universe_assignments: Dict[int, int] = {}  # cell_number -> universe_number
        self.optimized_cells: Set[int] = set()  # cells with minus sign optimization
        self.max_cell_number = 0
    
    def set_universe(self, cell_number: int, universe_number: int, optimized: bool = False) -> None:
        """
        Set universe assignment for a specific cell.
        
        Args:
            cell_number: Cell number (1-based)
            universe_number: Universe number (0 for real world, 1-99,999,999)
            optimized: If True, use minus sign optimization for boundary calculations
        """
        if not isinstance(cell_number, int) or cell_number < 1:
            raise ValueError("Cell number must be a positive integer")
        
        if not isinstance(universe_number, int):
            raise ValueError("Universe number must be an integer")
        
        if not (0 <= universe_number <= 99999999):
            raise ValueError("Universe number must be between 0 and 99,999,999")
        
        self.universe_assignments[cell_number] = universe_number
        self.max_cell_number = max(self.max_cell_number, cell_number)
        
        if optimized:
            self.optimized_cells.add(cell_number)
        elif cell_number in self.optimized_cells:
            self.optimized_cells.remove(cell_number)
    
    def set_universe_assignments(self, assignments: List[int], optimized_cells: Optional[List[bool]] = None) -> None:
        """
        Set universe assignments for cells 1, 2, 3, ... in order.
        
        Args:
            assignments: List of universe numbers for cells 1, 2, 3, ...
            optimized_cells: List of optimization flags (True for minus sign)
        """
        self.universe_assignments.clear()
        self.optimized_cells.clear()
        
        if optimized_cells is not None and len(optimized_cells) != len(assignments):
            raise ValueError("Optimized cells list must have same length as assignments")
        
        for i, universe_num in enumerate(assignments, 1):
            if not isinstance(universe_num, int):
                raise ValueError(f"Universe number for cell {i} must be an integer")
            if not (0 <= universe_num <= 99999999):
                raise ValueError(f"Universe number for cell {i} must be between 0 and 99,999,999")
            
            self.universe_assignments[i] = universe_num
            
            if optimized_cells and optimized_cells[i-1]:
                self.optimized_cells.add(i)
        
        self.max_cell_number = len(assignments)
    
    def get_universe(self, cell_number: int) -> Optional[int]:
        """
        Get universe assignment for a specific cell.
        
        Args:
            cell_number: Cell number
            
        Returns:
            Universe number or None if not assigned
        """
        return self.universe_assignments.get(cell_number)
    
    def is_optimized(self, cell_number: int) -> bool:
        """
        Check if a cell has optimization flag set.
        
        Args:
            cell_number: Cell number
            
        Returns:
            True if cell is optimized (minus sign)
        """
        return cell_number in self.optimized_cells
    
    def set_optimization(self, cell_number: int, optimized: bool) -> None:
        """
        Set optimization flag for a cell.
        
        Args:
            cell_number: Cell number
            optimized: True to enable optimization (minus sign)
        """
        if not isinstance(cell_number, int) or cell_number < 1:
            raise ValueError("Cell number must be a positive integer")
        
        if optimized:
            self.optimized_cells.add(cell_number)
        else:
            self.optimized_cells.discard(cell_number)
    
    def remove_universe(self, cell_number: int) -> bool:
        """
        Remove universe assignment for a cell.
        
        Args:
            cell_number: Cell number to remove
            
        Returns:
            True if removed, False if not found
        """
        if cell_number in self.universe_assignments:
            del self.universe_assignments[cell_number]
            self.optimized_cells.discard(cell_number)
            
            # Update max_cell_number if necessary
            if cell_number == self.max_cell_number:
                self.max_cell_number = max(self.universe_assignments.keys()) if self.universe_assignments else 0
            return True
        return False
    
    def clear_assignments(self) -> None:
        """Clear all universe assignments."""
        self.universe_assignments.clear()
        self.optimized_cells.clear()
        self.max_cell_number = 0
    
    def get_all_assignments(self) -> Dict[int, int]:
        """Get a copy of all universe assignments."""
        return self.universe_assignments.copy()
    
    def get_optimized_cells(self) -> Set[int]:
        """Get a copy of all optimized cell numbers."""
        return self.optimized_cells.copy()
    
    def get_max_cell_number(self) -> int:
        """Get the maximum cell number with universe assignment."""
        return self.max_cell_number
    
    def has_assignments(self) -> bool:
        """Check if any universe assignments are defined."""
        return len(self.universe_assignments) > 0
    
    def get_cells_in_universe(self, universe_number: int) -> List[int]:
        """
        Get all cells assigned to a specific universe.
        
        Args:
            universe_number: Universe number to search for
            
        Returns:
            List of cell numbers in the universe
        """
        return [cell for cell, universe in self.universe_assignments.items() 
                if universe == universe_number]
    
    def get_used_universes(self) -> Set[int]:
        """Get set of all universe numbers used."""
        return set(self.universe_assignments.values())
    
    def is_real_world_cell(self, cell_number: int) -> bool:
        """
        Check if a cell belongs to the real world (universe 0).
        
        Args:
            cell_number: Cell number
            
        Returns:
            True if cell is in real world or not assigned to any universe
        """
        universe = self.get_universe(cell_number)
        return universe is None or universe == 0
    
    def _compress_assignments(self, assignment_list: List[int], optimization_list: List[bool]) -> List[str]:
        """
        Compress consecutive identical assignments using jump notation.
        
        Args:
            assignment_list: List of universe assignments
            optimization_list: List of optimization flags
            
        Returns:
            List of strings with jump notation
        """
        if not assignment_list:
            return []
        
        result = []
        i = 0
        
        while i < len(assignment_list):
            current_universe = assignment_list[i]
            current_optimized = optimization_list[i]
            
            # Count consecutive identical assignments
            count = 1
            while (i + count < len(assignment_list) and 
                   assignment_list[i + count] == current_universe and
                   optimization_list[i + count] == current_optimized):
                count += 1
            
            # Format the entry
            if current_optimized and current_universe != 0:
                entry = f"-{current_universe}"
            else:
                entry = str(current_universe)
            
            # Add jump notation if needed
            if count == 1:
                result.append(entry)
            else:
                result.append(f"{count}R {entry}")
            
            i += count
        
        return result
    
    def to_data_card_string(self, line_length: int = 80) -> str:
        """
        Convert to data card form (U n1 n2 ... nJ).
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted U data card string
        """
        if self.max_cell_number == 0:
            return "u"
        
        # Build assignment list from 1 to max_cell_number
        assignment_list = []
        optimization_list = []
        
        for i in range(1, self.max_cell_number + 1):
            universe = self.universe_assignments.get(i, 0)  # Default to 0 (real world)
            optimized = i in self.optimized_cells
            
            assignment_list.append(universe)
            optimization_list.append(optimized)
        
        # Compress using repeat notation
        compressed = self._compress_assignments(assignment_list, optimization_list)
        
        # Build card
        components = ["u"] + compressed
        
        # Handle line wrapping
        lines = []
        current_line = components[0]  # Start with "u"
        
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
        Convert to cell parameter form for a specific cell (U = n).
        
        Args:
            cell_number: Cell number for the cell parameter
            
        Returns:
            Formatted U cell parameter string
        """
        universe = self.universe_assignments.get(cell_number)
        
        if universe is None:
            raise ValueError(f"No universe assignment for cell {cell_number}")
        
        optimized = cell_number in self.optimized_cells
        
        if optimized and universe != 0:
            return f"U=-{universe}"
        else:
            return f"U={universe}"
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert to MCNP input format (data card form).
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted U card string
        """
        return self.to_data_card_string(line_length)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the U card to a file in data card form.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def write_cell_parameter_to_file(self, file: TextIO, cell_number: int) -> None:
        """
        Write a cell parameter form U specification to a file.
        
        Args:
            file: Open file object to write to
            cell_number: Cell number for the cell parameter
        """
        file.write(self.to_cell_parameter_string(cell_number) + '\n')
    
    def validate_hierarchy(self) -> List[str]:
        """
        Validate universe hierarchy for potential issues.
        
        Returns:
            List of warning messages
        """
        warnings = []
        used_universes = self.get_used_universes()
        
        # Check for universe 0 assignments (real world)
        real_world_cells = self.get_cells_in_universe(0)
        if real_world_cells:
            warnings.append(f"Cells {real_world_cells} explicitly assigned to universe 0 (real world)")
        
        # Check for large universe numbers (potential typos)
        large_universes = [u for u in used_universes if u > 10000]
        if large_universes:
            warnings.append(f"Large universe numbers detected: {large_universes}")
        
        # Check optimization on universe 0 cells
        optimized_real_world = [cell for cell in self.optimized_cells 
                               if self.get_universe(cell) == 0]
        if optimized_real_world:
            warnings.append(f"Optimization flag on real world cells: {optimized_real_world}")
        
        return warnings
    
    def __str__(self) -> str:
        """String representation of the U card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the U card."""
        return (f"UCard(assignments={dict(sorted(self.universe_assignments.items()))}, "
                f"optimized={sorted(self.optimized_cells)}, "
                f"max_cell={self.max_cell_number})")
    
    def __len__(self) -> int:
        """Return the number of cells with universe assignments."""
        return len(self.universe_assignments)


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Simple universe assignments
    print("Example 1: Simple universe assignments")
    u1 = UCard()
    u1.set_universe_assignments([0, 1, 1, 2, 2, 2])
    print(f"Data card: {u1}")
    print(f"Cell 2 parameter: {u1.to_cell_parameter_string(2)}")
    print()
    
    # Example 2: Individual universe assignment
    print("Example 2: Individual universe assignment")
    u2 = UCard()
    u2.set_universe(1, 0)  # Real world
    u2.set_universe(2, 1)  # Universe 1
    u2.set_universe(3, 1)  # Universe 1
    u2.set_universe(4, 2, optimized=True)  # Universe 2 with optimization
    print(f"Data card: {u2}")
    print(f"Cell 4 parameter: {u2.to_cell_parameter_string(4)}")
    print()
    
    # Example 3: Optimized cells
    print("Example 3: Optimized cells")
    u3 = UCard()
    assignments = [0, 1, 1, 2, 2]
    optimizations = [False, False, True, True, False]
    u3.set_universe_assignments(assignments, optimizations)
    print(f"Data card: {u3}")
    print(f"Optimized cells: {u3.get_optimized_cells()}")
    print()
    
    # Example 4: Repeated structures
    print("Example 4: Repeated structures")
    u4 = UCard()
    # Pin cells in universe 1, assembly in universe 2, core in real world
    for i in range(1, 10):  # Pin cells
        u4.set_universe(i, 1)
    for i in range(10, 20):  # Assembly cells
        u4.set_universe(i, 2)
    for i in range(20, 25):  # Core cells (real world)
        u4.set_universe(i, 0)
    
    print(f"Data card: {u4}")
    print(f"Cells in universe 1: {u4.get_cells_in_universe(1)}")
    print(f"Cells in universe 2: {u4.get_cells_in_universe(2)}")
    print(f"Used universes: {u4.get_used_universes()}")
    print()
    
    # Example 5: Large problem with compression
    print("Example 5: Large problem with compression")
    u5 = UCard()
    assignments = [0] * 5 + [1] * 10 + [2] * 3 + [0] * 2
    u5.set_universe_assignments(assignments)
    print(f"Data card: {u5}")
    print()
    
    # Test file writing
    print("Writing U cards to file:")
    with open("test_u_cards.txt", "w") as f:
        f.write("c U card examples\n")
        f.write("c\n")
        f.write("c Simple assignments\n")
        u1.write_to_file(f)
        f.write("c\n")
        f.write("c Individual assignments\n")
        u2.write_to_file(f)
        f.write("c\n")
        f.write("c Cell parameter examples\n")
        f.write("c Cell 2 universe\n")
        u1.write_cell_parameter_to_file(f, 2)
        f.write("c Cell 4 universe (optimized)\n")
        u2.write_cell_parameter_to_file(f, 4)
    
    print("U cards written to 'test_u_cards.txt'")
    
    # Test universe queries
    print("\nTesting universe queries:")
    test_u = UCard()
    test_u.set_universe(1, 0)
    test_u.set_universe(2, 1)
    test_u.set_universe(3, 1)
    test_u.set_universe(4, 2)
    
    print(f"Initial: {test_u}")
    print(f"Universe for cell 2: {test_u.get_universe(2)}")
    print(f"Universe for cell 5: {test_u.get_universe(5)}")
    print(f"Is cell 1 real world: {test_u.is_real_world_cell(1)}")
    print(f"Is cell 2 real world: {test_u.is_real_world_cell(2)}")
    
    test_u.set_optimization(2, True)
    print(f"After optimizing cell 2: {test_u}")
    
    test_u.remove_universe(3)
    print(f"After removing cell 3: {test_u}")
    
    # Test validation
    print("\nTesting validation:")
    warnings = test_u.validate_hierarchy()
    if warnings:
        for warning in warnings:
            print(f"Warning: {warning}")
    else:
        print("No validation warnings")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_u = UCard()
        bad_u.set_universe(0, 1)  # Invalid cell number
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_u = UCard()
        bad_u.set_universe(1, -1)  # Invalid universe number
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_u = UCard()
        bad_u.set_universe(1, 100000000)  # Universe number too large
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        test_u = UCard()
        test_u.set_universe(1, 1)
        test_u.to_cell_parameter_string(2)  # Cell without universe
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Show usage patterns
    print("\nCommon usage patterns:")
    
    print("\n1. Pin cell geometry (universe 1):")
    pin_u = UCard()
    pin_u.set_universe_assignments([1] * 5)  # All pin cells in universe 1
    print(f"   {pin_u}")
    
    print("\n2. Assembly with pins (universe 2 contains universe 1):")
    assembly_u = UCard()
    assembly_u.set_universe_assignments([0, 0, 2, 2, 2])  # Core cells + assembly cells
    print(f"   {assembly_u}")
    
    print("\n3. Optimized infinite cells:")
    opt_u = UCard()
    opt_u.set_universe(1, 1, optimized=True)  # Infinite cell, no boundary calculations
    print(f"   {opt_u.to_cell_parameter_string(1)}")
    
    print("\nU card features:")
    print("- Cell parameter form: U = n")
    print("- Data card form: U n1 n2 ... nJ")
    print("- Universe 0: real world (default)")
    print("- Optimization: minus sign (-n) for infinite cells")
    print("- Hierarchical: up to 20 levels of nesting")
    print("- Repeated structures: same universe in multiple locations")
    print("- FILL integration: universes fill cells")
    