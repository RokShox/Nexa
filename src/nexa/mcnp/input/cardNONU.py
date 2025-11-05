from typing import List, Optional, TextIO, Union


class NONUCard:
    """
    Represents an MCNP NONU card for disabling fission in cells.
    
    The NONU card provides the ability to disable fission in cells by treating
    fission as simple capture. This is useful for problems where fission is
    already modeled in the source (like SSR) and should not be duplicated
    in transport.
    """
    
    def __init__(self, cell_values: Optional[Union[int, List[Optional[int]]]] = None):
        """
        Initialize a NONU card.
        
        Args:
            cell_values: Can be:
                - None: Apply default behavior (fission as capture with gammas) to all cells
                - int: Single value to apply to all cells
                - List[Optional[int]]: Values for each cell (None for blank entries)
        """
        if cell_values is None:
            self.cell_values = []  # Empty list means apply default to all cells
        elif isinstance(cell_values, int):
            if not self._is_valid_value(cell_values):
                raise ValueError("NONU value must be 0, 1, or 2")
            self.cell_values = [cell_values]
        elif isinstance(cell_values, list):
            for value in cell_values:
                if value is not None and not self._is_valid_value(value):
                    raise ValueError("NONU values must be 0, 1, 2, or None (blank)")
            self.cell_values = cell_values.copy()
        else:
            raise ValueError("cell_values must be None, int, or List[Optional[int]]")
    
    def _is_valid_value(self, value: int) -> bool:
        """Check if a NONU value is valid (0, 1, or 2)."""
        return value in [0, 1, 2]
    
    def set_single_value(self, value: Optional[int]) -> None:
        """
        Set a single value to apply to all cells.
        
        Args:
            value: NONU value (0, 1, 2, or None for blank)
        """
        if value is not None and not self._is_valid_value(value):
            raise ValueError("NONU value must be 0, 1, or 2")
        
        if value is None:
            self.cell_values = []  # Blank entry
        else:
            self.cell_values = [value]
    
    def set_cell_values(self, values: List[Optional[int]]) -> None:
        """
        Set values for individual cells.
        
        Args:
            values: List of NONU values for each cell (None for blank)
        """
        for value in values:
            if value is not None and not self._is_valid_value(value):
                raise ValueError("NONU values must be 0, 1, 2, or None (blank)")
        
        self.cell_values = values.copy()
    
    def add_cell_value(self, value: Optional[int]) -> None:
        """
        Add a value for an additional cell.
        
        Args:
            value: NONU value for the cell (0, 1, 2, or None for blank)
        """
        if value is not None and not self._is_valid_value(value):
            raise ValueError("NONU value must be 0, 1, 2, or None (blank)")
        
        self.cell_values.append(value)
    
    def get_cell_values(self) -> List[Optional[int]]:
        """Get a copy of the cell values list."""
        return self.cell_values.copy()
    
    def get_num_cells(self) -> int:
        """Get the number of cells specified."""
        return len(self.cell_values)
    
    def is_empty(self) -> bool:
        """Check if the card has no values (applies default to all cells)."""
        return len(self.cell_values) == 0
    
    def has_single_value(self) -> bool:
        """Check if the card has a single value for all cells."""
        return len(self.cell_values) == 1
    
    def get_single_value(self) -> Optional[int]:
        """Get the single value if card has only one value."""
        if self.has_single_value():
            return self.cell_values[0]
        return None
    
    def set_fission_as_capture_with_gammas(self, cell_index: Optional[int] = None) -> None:
        """
        Set fission to be treated as capture with gammas produced (value = 0).
        
        Args:
            cell_index: Index of cell to modify, or None to set single value for all cells
        """
        if cell_index is None:
            self.set_single_value(0)
        else:
            if cell_index >= len(self.cell_values):
                # Extend list if necessary
                while len(self.cell_values) <= cell_index:
                    self.cell_values.append(None)
            self.cell_values[cell_index] = 0
    
    def set_fission_as_real(self, cell_index: Optional[int] = None) -> None:
        """
        Set fission to be treated as real fission (value = 1).
        
        Args:
            cell_index: Index of cell to modify, or None to set single value for all cells
        """
        if cell_index is None:
            self.set_single_value(1)
        else:
            if cell_index >= len(self.cell_values):
                # Extend list if necessary
                while len(self.cell_values) <= cell_index:
                    self.cell_values.append(None)
            self.cell_values[cell_index] = 1
    
    def set_fission_as_capture_no_gammas(self, cell_index: Optional[int] = None) -> None:
        """
        Set fission to be treated as capture without gammas (value = 2).
        This is typically used with SSR for fission source problems.
        
        Args:
            cell_index: Index of cell to modify, or None to set single value for all cells
        """
        if cell_index is None:
            self.set_single_value(2)
        else:
            if cell_index >= len(self.cell_values):
                # Extend list if necessary
                while len(self.cell_values) <= cell_index:
                    self.cell_values.append(None)
            self.cell_values[cell_index] = 2
    
    def _format_value(self, value: Optional[int]) -> str:
        """Format a single value for output."""
        if value is None:
            return ""  # Blank entry
        else:
            return str(value)
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert the NONU card to MCNP input format.
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted NONU card string
        """
        if self.is_empty():
            # No entries - applies default (capture with gammas) to all cells
            return "nonu"
        
        lines = []
        current_line = "nonu"
        
        # Add cell values
        for i, value in enumerate(self.cell_values):
            value_str = f" {self._format_value(value)}"
            
            # Check if adding this value would exceed line length
            if len(current_line + value_str) > line_length:
                lines.append(current_line)
                current_line = "     " + value_str.strip()  # Continuation line with 5 spaces
            else:
                current_line += value_str
        
        # Add the final line
        if current_line.strip():
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the NONU card to a file.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def __str__(self) -> str:
        """String representation of the NONU card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the NONU card."""
        return f"NONUCard(cell_values={self.cell_values})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another NONUCard."""
        if not isinstance(other, NONUCard):
            return False
        return self.cell_values == other.cell_values


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Default behavior (no entries)
    print("Example 1: Default NONU card (applies capture with gammas to all cells)")
    nonu_default = NONUCard()
    print(f"Card: {nonu_default}")
    print(f"Is empty: {nonu_default.is_empty()}")
    print()
    
    # Example 2: Single value for all cells
    print("Example 2: Single value for all cells (capture without gammas)")
    nonu_single = NONUCard(2)
    print(f"Card: {nonu_single}")
    print(f"Has single value: {nonu_single.has_single_value()}")
    print(f"Single value: {nonu_single.get_single_value()}")
    print()
    
    # Example 3: Individual cell values
    print("Example 3: Individual cell values")
    nonu_cells = NONUCard([0, 1, 2, None, 0])
    print(f"Card: {nonu_cells}")
    print(f"Number of cells: {nonu_cells.get_num_cells()}")
    print(f"Cell values: {nonu_cells.get_cell_values()}")
    print()
    
    # Example 4: Building card programmatically
    print("Example 4: Building card programmatically")
    nonu_prog = NONUCard()
    nonu_prog.set_fission_as_capture_no_gammas()  # For SSR problems
    print(f"For SSR problems: {nonu_prog}")
    
    nonu_prog.set_cell_values([1, 0, 2])  # Mixed values
    print(f"Mixed cell values: {nonu_prog}")
    
    nonu_prog.add_cell_value(1)  # Add another cell
    print(f"After adding cell: {nonu_prog}")
    print()
    
    # Example 5: Common use cases
    print("Example 5: Common use cases")
    
    # For SSR fission source problems
    print("For SSR fission source problems (treat fission as capture, no gammas):")
    ssr_nonu = NONUCard()
    ssr_nonu.set_fission_as_capture_no_gammas()
    print(f"  {ssr_nonu}")
    
    # Turn off fission in specific cells
    print("Turn off fission in specific cells:")
    selective_nonu = NONUCard([1, 0, 1, 2])  # Real, capture+gamma, real, capture no gamma
    print(f"  {selective_nonu}")
    print()
    
    # Test file writing
    print("Writing NONU cards to file:")
    with open("test_nonu_cards.txt", "w") as f:
        f.write("c NONU card examples\n")
        f.write("c\n")
        f.write("c Default (no entries)\n")
        nonu_default.write_to_file(f)
        f.write("c\n")
        f.write("c For SSR problems\n")
        ssr_nonu.write_to_file(f)
        f.write("c\n")
        f.write("c Individual cell values\n")
        nonu_cells.write_to_file(f)
    
    print("NONU cards written to 'test_nonu_cards.txt'")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_nonu = NONUCard(3)  # Invalid value
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_nonu = NONUCard([0, 1, 3])  # Invalid value in list
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_nonu = NONUCard("invalid")  # Wrong type
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Test setting individual cells
    print("\nTesting individual cell setting:")
    test_nonu = NONUCard()
    test_nonu.set_fission_as_real(0)  # Cell 0: real fission
    test_nonu.set_fission_as_capture_with_gammas(1)  # Cell 1: capture with gammas
    test_nonu.set_fission_as_capture_no_gammas(2)  # Cell 2: capture without gammas
    print(f"Individual settings: {test_nonu}")
    
    # Test equality
    print("\nTesting equality:")
    nonu1 = NONUCard([0, 1, 2])
    nonu2 = NONUCard([0, 1, 2])
    nonu3 = NONUCard([0, 1])
    print(f"[0,1,2] == [0,1,2]: {nonu1 == nonu2}")
    print(f"[0,1,2] == [0,1]: {nonu1 == nonu3}")
    
    # Show value meanings
    print("\nNONU value meanings:")
    print("  0: Fission treated as capture; gammas produced")
    print("  1: Fission treated as real; gammas produced")
    print("  2: Fission treated as capture; gammas NOT produced (for SSR)")
    print("  blank: Same as 0 (capture with gammas)")