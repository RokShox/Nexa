from typing import List, Dict, Tuple, TextIO, Optional


class MT0Card:
    """
    Represents an MCNP MT0 card for S(α,β) special treatment of specific isotopes.
    
    The MT0 card is used to explicitly associate S(α,β) datasets (SABIDs) with 
    specific isotope identifiers (ZAIDs) when using stochastic mixing or when
    materials include isotopes at different temperatures. This card ensures that
    the correct S(α,β) data is used with the corresponding cross-section data
    at the same temperature.
    """
    
    def __init__(self):
        """
        Initialize an MT0 card.
        
        The MT0 card contains pairs of (SABID, ZAID) associations.
        """
        self.sabid_zaid_pairs: List[Tuple[str, str]] = []
    
    def add_association(self, sabid: str, zaid: str) -> None:
        """
        Add a SABID-ZAID association to the MT0 card.
        
        Args:
            sabid: S(α,β) dataset identifier (e.g., "h-h2o.40t")
            zaid: Material isotope identifier (e.g., "1001.80c")
        """
        if not sabid.strip():
            raise ValueError("SABID cannot be empty")
        if not zaid.strip():
            raise ValueError("ZAID cannot be empty")
        
        # Validate SABID format (should have .nnT format)
        if not self._is_valid_sabid_format(sabid):
            raise ValueError(f"SABID '{sabid}' must be in format 'sabname.nnT' with version and type explicitly included")
        
        # Validate ZAID format (should have .nnC format)
        if not self._is_valid_zaid_format(zaid):
            raise ValueError(f"ZAID '{zaid}' must be in format 'ZZZAAA.nnC' with version and type explicitly included")
        
        # Check for duplicate SABID
        for existing_sabid, _ in self.sabid_zaid_pairs:
            if existing_sabid == sabid:
                raise ValueError(f"SABID '{sabid}' already exists in MT0 card")
        
        # Check for duplicate ZAID
        for _, existing_zaid in self.sabid_zaid_pairs:
            if existing_zaid == zaid:
                raise ValueError(f"ZAID '{zaid}' already exists in MT0 card")
        
        self.sabid_zaid_pairs.append((sabid, zaid))
    
    def remove_association(self, sabid: str) -> bool:
        """
        Remove a SABID-ZAID association by SABID.
        
        Args:
            sabid: S(α,β) dataset identifier to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, (existing_sabid, _) in enumerate(self.sabid_zaid_pairs):
            if existing_sabid == sabid:
                del self.sabid_zaid_pairs[i]
                return True
        return False
    
    def remove_association_by_zaid(self, zaid: str) -> bool:
        """
        Remove a SABID-ZAID association by ZAID.
        
        Args:
            zaid: Material isotope identifier to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, (_, existing_zaid) in enumerate(self.sabid_zaid_pairs):
            if existing_zaid == zaid:
                del self.sabid_zaid_pairs[i]
                return True
        return False
    
    def clear_associations(self) -> None:
        """Remove all SABID-ZAID associations from the card."""
        self.sabid_zaid_pairs.clear()
    
    def get_associations(self) -> List[Tuple[str, str]]:
        """Get a copy of all SABID-ZAID associations."""
        return self.sabid_zaid_pairs.copy()
    
    def get_zaid_for_sabid(self, sabid: str) -> Optional[str]:
        """Get the ZAID associated with a specific SABID."""
        for existing_sabid, zaid in self.sabid_zaid_pairs:
            if existing_sabid == sabid:
                return zaid
        return None
    
    def get_sabid_for_zaid(self, zaid: str) -> Optional[str]:
        """Get the SABID associated with a specific ZAID."""
        for sabid, existing_zaid in self.sabid_zaid_pairs:
            if existing_zaid == zaid:
                return sabid
        return None
    
    def has_sabid(self, sabid: str) -> bool:
        """Check if a specific SABID is present in the card."""
        return any(existing_sabid == sabid for existing_sabid, _ in self.sabid_zaid_pairs)
    
    def has_zaid(self, zaid: str) -> bool:
        """Check if a specific ZAID is present in the card."""
        return any(existing_zaid == zaid for _, existing_zaid in self.sabid_zaid_pairs)
    
    def _is_valid_sabid_format(self, sabid: str) -> bool:
        """
        Validate SABID format (sabname.nnT).
        
        Args:
            sabid: SABID to validate
            
        Returns:
            True if format is valid
        """
        import re
        # Pattern: alphanumeric name, dot, version number, type letter
        pattern = r'^[a-zA-Z0-9\-_]+\.\d+[a-zA-Z]$'
        return bool(re.match(pattern, sabid))
    
    def _is_valid_zaid_format(self, zaid: str) -> bool:
        """
        Validate ZAID format (ZZZAAA.nnC).
        
        Args:
            zaid: ZAID to validate
            
        Returns:
            True if format is valid
        """
        import re
        # Pattern: 3-6 digits, dot, version number, 'c' or 'C'
        pattern = r'^\d{3,6}\.\d+[cC]$'
        return bool(re.match(pattern, zaid))
    
    def to_string(self, line_length: int = 80) -> str:
        """
        Convert the MT0 card to MCNP input format.
        
        Args:
            line_length: Maximum line length for formatting
            
        Returns:
            Formatted MT0 card string
        """
        if not self.sabid_zaid_pairs:
            raise ValueError("MT0 card must have at least one SABID-ZAID pair")
        
        lines = []
        current_line = "mt0"
        
        # Add SABID-ZAID pairs
        for sabid, zaid in self.sabid_zaid_pairs:
            pair_str = f" {sabid} {zaid}"
            
            # Check if adding this pair would exceed line length
            if len(current_line + pair_str) > line_length:
                lines.append(current_line)
                current_line = "     " + pair_str.strip()  # Continuation line with 5 spaces
            else:
                current_line += pair_str
        
        # Add the final line
        if current_line.strip():
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def write_to_file(self, file: TextIO, line_length: int = 80) -> None:
        """
        Write the MT0 card to a file.
        
        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + '\n')
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert associations to a dictionary mapping SABID to ZAID.
        
        Returns:
            Dictionary with SABID as key and ZAID as value
        """
        return {sabid: zaid for sabid, zaid in self.sabid_zaid_pairs}
    
    def from_dict(self, associations: Dict[str, str]) -> None:
        """
        Load associations from a dictionary.
        
        Args:
            associations: Dictionary mapping SABID to ZAID
        """
        self.clear_associations()
        for sabid, zaid in associations.items():
            self.add_association(sabid, zaid)
    
    def __str__(self) -> str:
        """String representation of the MT0 card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the MT0 card."""
        return f"MT0Card(pairs={self.sabid_zaid_pairs})"
    
    def __len__(self) -> int:
        """Return the number of SABID-ZAID pairs."""
        return len(self.sabid_zaid_pairs)


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Stochastic mixing for hydrogen in water at different temperatures
    print("Example 1: Stochastic mixing for H in water")
    mt0 = MT0Card()
    mt0.add_association("h-h2o.40t", "1001.80c")    # Cold hydrogen S(α,β) with cold ZAID
    mt0.add_association("h-h2o.41t", "1001.81c")    # Hot hydrogen S(α,β) with hot ZAID
    print(mt0)
    print()
    
    # Example 2: Multiple isotopes with temperature-dependent data
    print("Example 2: Multiple isotopes with stochastic mixing")
    mt0_multi = MT0Card()
    mt0_multi.add_association("h-h2o.40t", "1001.80c")      # H cold
    mt0_multi.add_association("h-h2o.41t", "1001.81c")      # H hot
    mt0_multi.add_association("d-d2o.40t", "1002.80c")      # D cold
    mt0_multi.add_association("d-d2o.41t", "1002.81c")      # D hot
    print(mt0_multi)
    print()
    
    # Example 3: Graphite at different temperatures
    print("Example 3: Graphite at different temperatures")
    mt0_graphite = MT0Card()
    mt0_graphite.add_association("grph.40t", "6012.80c")    # Cold graphite
    mt0_graphite.add_association("grph.41t", "6012.81c")    # Hot graphite
    print(mt0_graphite)
    print()
    
    # Test file writing
    print("Writing MT0 cards to file:")
    with open("test_mt0_cards.txt", "w") as f:
        f.write("c MT0 cards for S(alpha,beta) associations\n")
        f.write("c\n")
        mt0.write_to_file(f)
        f.write("c\n")
        mt0_multi.write_to_file(f)
        f.write("c\n")
        mt0_graphite.write_to_file(f)
    
    print("MT0 cards written to 'test_mt0_cards.txt'")
    
    # Test utility methods
    print("\nTesting utility methods:")
    print(f"ZAID for h-h2o.40t: {mt0_multi.get_zaid_for_sabid('h-h2o.40t')}")
    print(f"SABID for 1002.81c: {mt0_multi.get_sabid_for_zaid('1002.81c')}")
    print(f"Has SABID d-d2o.40t: {mt0_multi.has_sabid('d-d2o.40t')}")
    print(f"Has ZAID 1003.80c: {mt0_multi.has_zaid('1003.80c')}")
    print(f"Number of associations: {len(mt0_multi)}")
    
    # Test dictionary conversion
    print(f"\nAs dictionary: {mt0.to_dict()}")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_mt0 = MT0Card()
        bad_mt0.add_association("invalid_sabid", "1001.80c")
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_mt0 = MT0Card()
        bad_mt0.add_association("h-h2o.40t", "invalid_zaid")
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_mt0 = MT0Card()
        bad_mt0.add_association("h-h2o.40t", "1001.80c")
        bad_mt0.add_association("h-h2o.40t", "1001.81c")  # Duplicate SABID
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        empty_mt0 = MT0Card()
        empty_mt0.to_string()  # No associations
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Test removal methods
    print("\nTesting removal methods:")
    test_mt0 = MT0Card()
    test_mt0.add_association("h-h2o.40t", "1001.80c")
    test_mt0.add_association("d-d2o.40t", "1002.80c")
    
    print(f"Before removal: {len(test_mt0)} associations")
    print(f"Removed h-h2o.40t: {test_mt0.remove_association('h-h2o.40t')}")
    print(f"Removed 1002.80c: {test_mt0.remove_association_by_zaid('1002.80c')}")
    print(f"After removal: {len(test_mt0)} associations")