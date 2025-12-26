from typing import List, TextIO


class MTCard:
    """
    Represents an MCNP thermal neutron scattering card (MT card).

    The MT card specifies S(α,β) thermal neutron scattering data for isotopes
    in a material. It associates specific S(α,β) datasets (SABIDs) with a material
    defined on an M card.
    """

    def __init__(self, material_number: int):
        """
        Initialize an MT card.

        Args:
            material_number: Material number corresponding to an M card (1-99,999,999)
        """
        if not (1 <= material_number <= 99999999):
            raise ValueError("Material number must be between 1 and 99,999,999")

        self.material_number = material_number
        self.sabids: List[str] = []

    def add_sabid(self, sabid: str) -> None:
        """
        Add an S(α,β) dataset identifier to the card.

        Args:
            sabid: S(α,β) identifier (e.g., "h-h2o.40t", "grph.40t")
        """
        if not sabid.strip():
            raise ValueError("SABID cannot be empty")

        # Check if SABID already exists
        if sabid in self.sabids:
            raise ValueError(f"SABID '{sabid}' already exists in this MT card")

        self.sabids.append(sabid)

    def remove_sabid(self, sabid: str) -> bool:
        """
        Remove an S(α,β) dataset identifier from the card.

        Args:
            sabid: S(α,β) identifier to remove

        Returns:
            True if removed, False if not found
        """
        try:
            self.sabids.remove(sabid)
            return True
        except ValueError:
            return False

    def clear_sabids(self) -> None:
        """Remove all S(α,β) dataset identifiers from the card."""
        self.sabids.clear()

    def get_sabids(self) -> List[str]:
        """Get a copy of the list of S(α,β) dataset identifiers."""
        return self.sabids.copy()

    def has_sabid(self, sabid: str) -> bool:
        """Check if a specific SABID is present in the card."""
        return sabid in self.sabids

    def to_string(self, line_length: int = 80) -> str:
        """
        Convert the MT card to MCNP input format.

        Args:
            line_length: Maximum line length for formatting

        Returns:
            Formatted MT card string
        """
        if not self.sabids:
            raise ValueError("MT card must have at least one SABID")

        lines = []
        current_line = f"mt{self.material_number}"

        # Add SABIDs
        for sabid in self.sabids:
            sabid_str = f" {sabid}"

            # Check if adding this SABID would exceed line length
            if len(current_line + sabid_str) > line_length:
                lines.append(current_line)
                current_line = "     " + sabid.strip()  # Continuation line with 5 spaces
            else:
                current_line += sabid_str

        # Add the final line
        if current_line.strip():
            lines.append(current_line)

        return "\n".join(lines)

    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the MT card to a file.

        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + "\n")

    def __str__(self) -> str:
        """String representation of the MT card."""
        return self.to_string()

    def __repr__(self) -> str:
        """Developer representation of the MT card."""
        return f"MTCard(material_number={self.material_number}, sabids={self.sabids})"


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Water with hydrogen thermal scattering
    print("Example 1: Water thermal scattering")
    water_mt = MTCard(1)
    water_mt.add_sabid("h-h2o.40t")  # Hydrogen in water
    print(water_mt)
    print()

    # Example 2: Heavy water
    print("Example 2: Heavy water thermal scattering")
    heavy_water_mt = MTCard(2)
    heavy_water_mt.add_sabid("d-d2o.40t")  # Deuterium in heavy water
    print(heavy_water_mt)
    print()

    # Example 3: Graphite
    print("Example 3: Graphite thermal scattering")
    graphite_mt = MTCard(3)
    graphite_mt.add_sabid("grph.40t")  # Graphite
    print(graphite_mt)
    print()

    # Example 4: Multiple S(α,β) libraries for different isotopes
    print("Example 4: Multiple thermal scattering libraries")
    mixed_mt = MTCard(4)
    mixed_mt.add_sabid("h-h2o.40t")  # Hydrogen in water
    mixed_mt.add_sabid("o-h2o.40t")  # Oxygen in water (if available)
    print(mixed_mt)
    print()

    # Example 5: Long line wrapping
    print("Example 5: Long line that will wrap")
    long_mt = MTCard(5)
    long_mt.add_sabid("very-long-sabid-name-1.40t")
    long_mt.add_sabid("very-long-sabid-name-2.40t")
    long_mt.add_sabid("very-long-sabid-name-3.40t")
    long_mt.add_sabid("very-long-sabid-name-4.40t")
    print(long_mt.to_string(line_length=60))  # Shorter line length to force wrapping
    print()

    # Test file writing
    print("Writing MT cards to file:")
    with open("test_mt_cards.txt", "w") as f:
        f.write("c Thermal neutron scattering cards\n")
        f.write("c\n")
        water_mt.write_to_file(f)
        heavy_water_mt.write_to_file(f)
        graphite_mt.write_to_file(f)
        mixed_mt.write_to_file(f)

    print("MT cards written to 'test_mt_cards.txt'")

    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_mt = MTCard(0)  # Invalid material number
    except ValueError as e:
        print(f"Caught expected error: {e}")

    try:
        test_mt = MTCard(10)
        test_mt.add_sabid("")  # Empty SABID
    except ValueError as e:
        print(f"Caught expected error: {e}")

    try:
        test_mt = MTCard(10)
        test_mt.add_sabid("h-h2o.40t")
        test_mt.add_sabid("h-h2o.40t")  # Duplicate SABID
    except ValueError as e:
        print(f"Caught expected error: {e}")

    try:
        empty_mt = MTCard(10)
        empty_mt.to_string()  # No SABIDs
    except ValueError as e:
        print(f"Caught expected error: {e}")

    # Test utility methods
    print("\nTesting utility methods:")
    test_mt = MTCard(99)
    test_mt.add_sabid("h-h2o.40t")
    test_mt.add_sabid("grph.40t")

    print(f"SABIDs: {test_mt.get_sabids()}")
    print(f"Has h-h2o.40t: {test_mt.has_sabid('h-h2o.40t')}")
    print(f"Has be.40t: {test_mt.has_sabid('be.40t')}")
    print(f"Removed grph.40t: {test_mt.remove_sabid('grph.40t')}")
    print(f"Removed be.40t: {test_mt.remove_sabid('be.40t')}")
    print(f"Final SABIDs: {test_mt.get_sabids()}")

    test_mt.clear_sabids()
    print(f"After clear: {test_mt.get_sabids()}")
