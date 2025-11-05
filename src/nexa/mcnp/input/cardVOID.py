from typing import List, Optional, TextIO, Union


class VOIDCard:
    """
    Represents an MCNP VOID card for material void treatment.
    
    The VOID card provides the ability to set material number and density to zero
    for specified cells or all cells. This is useful for debugging geometry and
    calculating volumes stochastically.
    """
    
    def __init__(self, cell_numbers: Optional[Union[int, List[int]]] = None):
        """
        Initialize a VOID card.
        
        Args:
            cell_numbers: Can be:
                - None: Apply void to all cells (blank VOID card)
                - int: Single cell number to void
                - List[int]: List of cell numbers to void
        """
        if cell_numbers is None:
            self.cell_numbers = []  # Empty list means void all cells
            self.void_all = True
        elif isinstance(cell_numbers, int):
            if cell_numbers <= 0:
                raise ValueError("Cell numbers must be positive integers")
            self.cell_numbers = [cell_numbers]
            self.void_all = False
        elif isinstance(cell_numbers, list):
            if not cell_numbers:
                # Empty list same as None
                self.cell_numbers = []
                self.void_all = True
            else:
                for cell_num in cell_numbers:
                    if not isinstance(cell_num, int) or cell_num <= 0:
                        raise ValueError("Cell numbers must be positive integers")
                # Remove duplicates and sort
                self.cell_numbers = sorted(list(set(cell_numbers)))
                self.void_all = False
        else:
            raise ValueError("cell_numbers must be None, int, or List[int]")
    
    def set_void_all_cells(self) -> None:
        """
        Set the card to void all cells (blank VOID card).
        
        When blank, material number and density is set to zero for all cells,
        FM cards are turned off, heating tallies become flux tallies, and
        NPS 100000 is effectively applied if no NPS card exists.
        """
        self.cell_numbers = []
        self.void_all = True
    
    def set_specific_cells(self, cell_numbers: List[int]) -> None:
        """
        Set specific cells to be voided.
        
        Args:
            cell_numbers: List of cell numbers to void
        """
        if not cell_numbers:
            self.set_void_all_cells()
            return
        
        for cell_num in cell_numbers:
            if not isinstance(cell_num, int) or cell_num <= 0:
                raise ValueError("Cell numbers must be positive integers")
        
        # Remove duplicates and sort
        self.cell_numbers = sorted(list(set(cell_numbers)))
        self.void_all = False
    
    def add_cell(self, cell_number: int) -> None:
        """
        Add a cell to be voided.
        
        Args:
            cell_number: Cell number to add
        """
        if not isinstance(cell_number, int) or cell_number <= 0:
            raise ValueError("Cell number must be a positive integer")
        
        if self.void_all:
            # Convert from void_all to specific cells
            self.cell_numbers = [cell_number]
            self.void_all = False
        elif cell_number not in self.cell_numbers:
            self.cell_numbers.append(cell_number)
            self.cell_numbers.sort()
    
    def remove_cell(self, cell_number: int) -> bool:
        """
        Remove a cell from the void list.
        
        Args:
            cell_number: Cell number to remove
            
        Returns:
            True if removed, False if not found
        """
        if self.void_all:
            # Cannot remove from void_all - would need to specify all other cells
            return False
        
        try:
            self.cell_numbers.remove(cell_number)
            return True
        except ValueError:
            return False
    
    def clear_cells(self) -> None:
        """Clear all specific cells (resulting in void all behavior)."""
        self.set_void_all_cells()
    
    def get_cell_numbers(self) -> List[int]:
        """Get a copy of the cell numbers list."""
        return self.cell_numbers.copy()
    
    def is_void_all(self) -> bool:
        """Check if the card voids all cells (blank card)."""
        return self.void_all
    
    def has_specific_cells(self) -> bool:
        """Check if the card specifies specific cells to void."""
        return not self.void_all and len(self.cell_numbers) > 0
    
    def is_empty(self) -> bool:
        """Check if the card has no effect (no cells specified)."""
        return not self.void_all and len(self.cell_numbers) == 0
    
    def contains_cell(self, cell_number: int) -> bool:
        """
        Check if a specific cell is voided by this card.
        
        Args:
            cell_number: Cell number to check
            
        Returns:
            True if the cell is voided
        """
        if self.void_all:
            return True
        return cell_number in self.cell_numbers
    
    def get_num_cells(self) -> int:
        """Get the number of specifically listed cells."""
        return len(self.cell_numbers)
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert the VOID card to MCNP input format.
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted VOID card string
        """
        if self.void_all:
            # Blank VOID card
            return "void"
        
        if self.is_empty():
            # This shouldn't happen in normal usage, but handle it
            return "void"
        
        lines = []
        current_line = "void"
        
        # Add cell numbers
        for cell_num in self.cell_numbers:
            cell_str = f" {cell_num}"
            
            # Check if adding this cell would exceed line length
            if len(current_line + cell_str) > line_length:
                lines.append(current_line)
                current_line = "     " + str(cell_num)  # Continuation line with 5 spaces
            else:
                current_line += cell_str
        
        # Add the final line
        if current_line.strip():
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the VOID card to a file.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def __str__(self) -> str:
        """String representation of the VOID card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the VOID card."""
        if self.void_all:
            return "VOIDCard(void_all=True)"
        else:
            return f"VOIDCard(cell_numbers={self.cell_numbers})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another VOIDCard."""
        if not isinstance(other, VOIDCard):
            return False
        return self.void_all == other.void_all and self.cell_numbers == other.cell_numbers
    
    def __len__(self) -> int:
        """Return the number of specifically listed cells."""
        return len(self.cell_numbers)


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Void all cells (blank VOID card)
    print("Example 1: Void all cells (blank VOID card)")
    void_all = VOIDCard()
    print(f"Card: {void_all}")
    print(f"Voids all cells: {void_all.is_void_all()}")
    print(f"Contains cell 5: {void_all.contains_cell(5)}")
    print()
    
    # Example 2: Void specific cells
    print("Example 2: Void specific cells")
    void_specific = VOIDCard([1, 3, 5, 7])
    print(f"Card: {void_specific}")
    print(f"Has specific cells: {void_specific.has_specific_cells()}")
    print(f"Cell numbers: {void_specific.get_cell_numbers()}")
    print(f"Contains cell 3: {void_specific.contains_cell(3)}")
    print(f"Contains cell 4: {void_specific.contains_cell(4)}")
    print()
    
    # Example 3: Single cell
    print("Example 3: Single cell void")
    void_single = VOIDCard(10)
    print(f"Card: {void_single}")
    print(f"Number of cells: {void_single.get_num_cells()}")
    print()
    
    # Example 4: Building card programmatically
    print("Example 4: Building card programmatically")
    void_prog = VOIDCard()
    print(f"Initial (void all): {void_prog}")
    
    void_prog.set_specific_cells([2, 4, 6])
    print(f"After setting specific cells: {void_prog}")
    
    void_prog.add_cell(8)
    print(f"After adding cell 8: {void_prog}")
    
    void_prog.remove_cell(4)
    print(f"After removing cell 4: {void_prog}")
    
    void_prog.set_void_all_cells()
    print(f"After setting void all: {void_prog}")
    print()
    
    # Example 5: Common use cases
    print("Example 5: Common use cases")
    
    # Geometry debugging - void all materials
    print("For geometry debugging (void all materials):")
    debug_void = VOIDCard()
    print(f"  {debug_void}")
    
    # Check effect of specific objects
    print("Check effect of removing specific objects:")
    selective_void = VOIDCard([101, 102, 103])  # Void control rods, for example
    print(f"  {selective_void}")
    
    # Volume calculation
    print("For stochastic volume calculation:")
    volume_void = VOIDCard()
    print(f"  {volume_void}")
    print()
    
    # Test file writing
    print("Writing VOID cards to file:")
    with open("test_void_cards.txt", "w") as f:
        f.write("c VOID card examples\n")
        f.write("c\n")
        f.write("c Void all cells for geometry debugging\n")
        void_all.write_to_file(f)
        f.write("c\n")
        f.write("c Void specific cells\n")
        void_specific.write_to_file(f)
        f.write("c\n")
        f.write("c Single cell void\n")
        void_single.write_to_file(f)
    
    print("VOID cards written to 'test_void_cards.txt'")
    
    # Test line wrapping with many cells
    print("\nTesting line wrapping:")
    many_cells = list(range(1, 31))  # Cells 1 through 30
    void_many = VOIDCard(many_cells)
    print("VOID card with many cells (line wrapping):")
    print(void_many.to_string(line_length=50))  # Shorter line to force wrapping
    print()
    
    # Test error handling
    print("Testing error handling:")
    try:
        bad_void = VOIDCard([1, 0, 3])  # Zero is invalid
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_void = VOIDCard([-1])  # Negative is invalid
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_void = VOIDCard("invalid")  # Wrong type
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Test duplicate handling
    print("\nTesting duplicate handling:")
    void_duplicates = VOIDCard([1, 3, 1, 5, 3])
    print(f"Input [1,3,1,5,3] becomes: {void_duplicates.get_cell_numbers()}")
    
    # Test equality
    print("\nTesting equality:")
    void1 = VOIDCard([1, 2, 3])
    void2 = VOIDCard([3, 1, 2])  # Same cells, different order
    void3 = VOIDCard([1, 2])
    void4 = VOIDCard()  # Void all
    void5 = VOIDCard()  # Another void all
    
    print(f"[1,2,3] == [3,1,2]: {void1 == void2}")
    print(f"[1,2,3] == [1,2]: {void1 == void3}")
    print(f"void_all == void_all: {void4 == void5}")
    print(f"[1,2,3] == void_all: {void1 == void4}")
    
    # Show effects description
    print("\nVOID card effects:")
    print("Blank VOID card (void all):")
    print("  - Material number and density set to zero for all cells")
    print("  - FM cards turned off")
    print("  - Heating tallies become flux tallies")
    print("  - NPS 100000 applied if no NPS card exists")
    print("\nSpecific cells VOID card:")
    print("  - Material number and density set to zero for specified cells only")
    print("  - Useful for checking effect of removing specific objects")