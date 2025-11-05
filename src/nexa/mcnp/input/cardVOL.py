from typing import List, Optional, Union, TextIO, Dict


class VOLCard:
    """
    Represents an MCNP VOL card for cell volumes.
    
    The VOL card specifies volumes for cells, either as a data card with volumes
    for all cells or as individual cell card specifications. It supports the NO
    keyword to bypass volume calculations and uses jump (J) notation for 
    unspecified volumes.
    """
    
    def __init__(self, no_calculation: bool = False):
        """
        Initialize a VOL card.
        
        Args:
            no_calculation: If True, includes NO keyword to bypass volume calculations
        """
        self.no_calculation = no_calculation
        self.volumes: Dict[int, Optional[float]] = {}  # cell_number -> volume (None for unspecified)
        self.max_cell_number = 0
    
    def set_volume(self, cell_number: int, volume: Optional[float]) -> None:
        """
        Set volume for a specific cell.
        
        Args:
            cell_number: Cell number (1-based)
            volume: Volume value (None for unspecified/jump)
        """
        if not isinstance(cell_number, int) or cell_number < 1:
            raise ValueError("Cell number must be a positive integer")
        
        if volume is not None:
            if not isinstance(volume, (int, float)):
                raise ValueError("Volume must be numeric or None")
            if volume < 0:
                raise ValueError("Volume must be non-negative")
            volume = float(volume)
        
        self.volumes[cell_number] = volume
        self.max_cell_number = max(self.max_cell_number, cell_number)
    
    def set_volumes(self, volumes: List[Optional[float]]) -> None:
        """
        Set volumes for cells 1, 2, 3, ... in order.
        
        Args:
            volumes: List of volumes (None for unspecified cells)
        """
        self.volumes.clear()
        for i, volume in enumerate(volumes, 1):
            if volume is not None:
                if not isinstance(volume, (int, float)):
                    raise ValueError(f"Volume for cell {i} must be numeric or None")
                if volume < 0:
                    raise ValueError(f"Volume for cell {i} must be non-negative")
                volume = float(volume)
            self.volumes[i] = volume
        
        self.max_cell_number = len(volumes)
    
    def get_volume(self, cell_number: int) -> Optional[float]:
        """
        Get volume for a specific cell.
        
        Args:
            cell_number: Cell number
            
        Returns:
            Volume value or None if unspecified
        """
        return self.volumes.get(cell_number)
    
    def remove_volume(self, cell_number: int) -> bool:
        """
        Remove volume specification for a cell.
        
        Args:
            cell_number: Cell number to remove
            
        Returns:
            True if removed, False if not found
        """
        if cell_number in self.volumes:
            del self.volumes[cell_number]
            # Update max_cell_number if necessary
            if cell_number == self.max_cell_number:
                self.max_cell_number = max(self.volumes.keys()) if self.volumes else 0
            return True
        return False
    
    def clear_volumes(self) -> None:
        """Clear all volume specifications."""
        self.volumes.clear()
        self.max_cell_number = 0
    
    def get_all_volumes(self) -> Dict[int, Optional[float]]:
        """Get a copy of all volume specifications."""
        return self.volumes.copy()
    
    def get_max_cell_number(self) -> int:
        """Get the maximum cell number with volume specification."""
        return self.max_cell_number
    
    def has_volumes(self) -> bool:
        """Check if any volumes are specified."""
        return len(self.volumes) > 0
    
    def set_no_calculation(self, no_calculation: bool) -> None:
        """Set whether to bypass volume calculations."""
        self.no_calculation = no_calculation
    
    def _compress_jumps(self, volume_list: List[Optional[float]]) -> List[str]:
        """
        Compress consecutive None values into jump notation (nJ).
        
        Args:
            volume_list: List of volumes with None for unspecified
            
        Returns:
            List of strings with jump notation
        """
        if not volume_list:
            return []
        
        result = []
        i = 0
        
        while i < len(volume_list):
            if volume_list[i] is None:
                # Count consecutive None values
                jump_count = 0
                while i < len(volume_list) and volume_list[i] is None:
                    jump_count += 1
                    i += 1
                
                # Add jump notation
                if jump_count == 1:
                    result.append("J")
                else:
                    result.append(f"{jump_count}J")
            else:
                # Add the volume value
                volume = volume_list[i]
                if volume == int(volume):
                    result.append(str(int(volume)))
                else:
                    result.append(f"{volume:.6g}")
                i += 1
        
        return result
    
    def to_data_card_string(self, line_length: int = 80) -> str:
        """
        Convert to data card form (VOL [NO] x1 x2 ... xJ).
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted VOL data card string
        """
        if self.max_cell_number == 0 and not self.no_calculation:
            return "vol"
        
        # Build volume list from 1 to max_cell_number
        volume_list = []
        for i in range(1, self.max_cell_number + 1):
            volume_list.append(self.volumes.get(i))
        
        # Compress jumps
        compressed = self._compress_jumps(volume_list)
        
        # Build card
        components = ["vol"]
        if self.no_calculation:
            components.append("no")
        
        components.extend(compressed)
        
        # Handle line wrapping
        if not compressed:
            return " ".join(components[:2])  # Just "vol" or "vol no"
        
        lines = []
        current_line = " ".join(components[:2])  # "vol" or "vol no"
        
        # Add volume entries with wrapping
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
    
    def to_cell_card_string(self, cell_number: int) -> str:
        """
        Convert to cell card form for a specific cell (VOL x).
        
        Args:
            cell_number: Cell number for the cell card
            
        Returns:
            Formatted VOL cell card string for the specified cell
        """
        volume = self.volumes.get(cell_number)
        
        if volume is None:
            raise ValueError(f"No volume specified for cell {cell_number}")
        
        if volume == int(volume):
            return f"vol {int(volume)}"
        else:
            return f"vol {volume:.6g}"
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert to MCNP input format (data card form).
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted VOL card string
        """
        return self.to_data_card_string(line_length)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the VOL card to a file in data card form.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def write_cell_card_to_file(self, file: TextIO, cell_number: int) -> None:
        """
        Write a cell card form VOL specification to a file.
        
        Args:
            file: Open file object to write to
            cell_number: Cell number for the cell card
        """
        file.write(self.to_cell_card_string(cell_number) + '\n')
    
    def __str__(self) -> str:
        """String representation of the VOL card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the VOL card."""
        return (f"VOLCard(no_calculation={self.no_calculation}, "
                f"volumes={dict(sorted(self.volumes.items()))}, "
                f"max_cell={self.max_cell_number})")
    
    def __len__(self) -> int:
        """Return the number of cells with volume specifications."""
        return len(self.volumes)


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Simple volume specifications
    print("Example 1: Simple volume specifications")
    vol1 = VOLCard()
    vol1.set_volumes([100.0, 200.0, 300.0])
    print(f"Data card: {vol1}")
    print(f"Cell 2 card: {vol1.to_cell_card_string(2)}")
    print()
    
    # Example 2: Volumes with jumps
    print("Example 2: Volumes with jumps")
    vol2 = VOLCard()
    vol2.set_volumes([100.0, None, None, 400.0, None, 600.0])
    print(f"Data card: {vol2}")
    print(f"Cell 1 card: {vol2.to_cell_card_string(1)}")
    print(f"Cell 4 card: {vol2.to_cell_card_string(4)}")
    print()
    
    # Example 3: NO keyword with some volumes
    print("Example 3: NO keyword with volumes")
    vol3 = VOLCard(no_calculation=True)
    vol3.set_volume(1, 150.0)
    vol3.set_volume(3, 350.0)
    vol3.set_volume(5, 550.0)
    print(f"Data card: {vol3}")
    print()
    
    # Example 4: Individual volume setting
    print("Example 4: Individual volume setting")
    vol4 = VOLCard()
    vol4.set_volume(1, 1000.0)
    vol4.set_volume(3, 2000.0)
    vol4.set_volume(5, 3000.0)
    vol4.set_volume(10, 4000.0)
    print(f"Data card: {vol4}")
    print(f"Max cell number: {vol4.get_max_cell_number()}")
    print()
    
    # Example 5: Large sequence with many jumps
    print("Example 5: Large sequence with jumps")
    vol5 = VOLCard()
    volumes = [100.0] + [None] * 10 + [200.0] + [None] * 5 + [300.0, 400.0] + [None] * 3
    vol5.set_volumes(volumes)
    print(f"Data card: {vol5}")
    print()
    
    # Example 6: NO keyword only
    print("Example 6: NO keyword only")
    vol6 = VOLCard(no_calculation=True)
    print(f"Data card: {vol6}")
    print()
    
    # Test file writing
    print("Writing VOL cards to file:")
    with open("test_vol_cards.txt", "w") as f:
        f.write("c VOL card examples\n")
        f.write("c\n")
        f.write("c Simple volumes\n")
        vol1.write_to_file(f)
        f.write("c\n")
        f.write("c Volumes with jumps\n")
        vol2.write_to_file(f)
        f.write("c\n")
        f.write("c NO calculation with some volumes\n")
        vol3.write_to_file(f)
        f.write("c\n")
        f.write("c Cell card examples\n")
        f.write("c Cell 1 volume\n")
        vol1.write_cell_card_to_file(f, 1)
        f.write("c Cell 4 volume\n")
        vol2.write_cell_card_to_file(f, 4)
    
    print("VOL cards written to 'test_vol_cards.txt'")
    
    # Test volume manipulation
    print("\nTesting volume manipulation:")
    test_vol = VOLCard()
    print(f"Initial: {test_vol}")
    
    test_vol.set_volume(1, 100.0)
    test_vol.set_volume(2, 200.0)
    print(f"After setting volumes: {test_vol}")
    
    print(f"Volume for cell 1: {test_vol.get_volume(1)}")
    print(f"Volume for cell 3: {test_vol.get_volume(3)}")
    
    test_vol.remove_volume(2)
    print(f"After removing cell 2: {test_vol}")
    
    test_vol.clear_volumes()
    print(f"After clearing: {test_vol}")
    
    # Test jump compression
    print("\nTesting jump compression:")
    jump_vol = VOLCard()
    
    # Single jump
    jump_vol.set_volumes([100.0, None, 200.0])
    print(f"Single jump: {jump_vol}")
    
    # Multiple consecutive jumps
    jump_vol.set_volumes([100.0, None, None, None, 200.0])
    print(f"Multiple jumps: {jump_vol}")
    
    # Jumps at start and end
    jump_vol.set_volumes([None, None, 100.0, None, None, None])
    print(f"Jumps at start/end: {jump_vol}")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_vol = VOLCard()
        bad_vol.set_volume(0, 100.0)  # Invalid cell number
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_vol = VOLCard()
        bad_vol.set_volume(1, -100.0)  # Negative volume
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        test_vol = VOLCard()
        test_vol.set_volume(1, 100.0)
        test_vol.to_cell_card_string(2)  # Cell without volume
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Test line wrapping with many volumes
    print("\nTesting line wrapping:")
    many_vol = VOLCard()
    volumes = []
    for i in range(50):
        if i % 3 == 0:
            volumes.append(float(i * 100))
        else:
            volumes.append(None)
    many_vol.set_volumes(volumes)
    print("VOL card with many entries (line wrapping):")
    print(many_vol.to_string(line_length=60))
    print()
    
    # Show different use cases
    print("Common use cases:")
    print("\n1. Specify volumes for all cells:")
    use1 = VOLCard()
    use1.set_volumes([1000.0, 2000.0, 3000.0, 4000.0])
    print(f"   {use1}")
    
    print("\n2. Specify volumes for some cells only:")
    use2 = VOLCard()
    use2.set_volumes([1000.0, None, None, 4000.0])
    print(f"   {use2}")
    
    print("\n3. Bypass volume calculation:")
    use3 = VOLCard(no_calculation=True)
    print(f"   {use3}")
    
    print("\n4. Bypass calculation but provide some volumes:")
    use4 = VOLCard(no_calculation=True)
    use4.set_volume(1, 1000.0)
    use4.set_volume(3, 3000.0)
    print(f"   {use4}")
    
    print("\nVOL card features:")
    print("- Data card form: VOL [NO] x1 x2 ... xJ")
    print("- Cell card form: VOL x (for individual cells)")
    print("- Jump notation: J for single skip, nJ for n consecutive skips")
    print("- NO keyword: bypasses volume calculations")
    print("- Required for some tallies when volumes cannot be calculated")
    