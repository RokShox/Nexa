from typing import Optional, TextIO


class TOTNUCard:
    """
    Represents an MCNP TOTNU card for controlling fission neutron sampling.
    
    The TOTNU card specifies whether to use total nu (prompt + delayed) or
    only prompt nu for fission neutron production. This affects how fission
    neutrons are sampled for all fissionable nuclides.
    """
    
    def __init__(self, value: Optional[str] = None):
        """
        Initialize a TOTNU card.
        
        Args:
            value: Control value for fission neutron sampling
                  - None or blank: Use total nu (prompt + delayed) [DEFAULT]
                  - "NO": Use only prompt nu
        """
        self.value = self._validate_and_set_value(value)
    
    def _validate_and_set_value(self, value: Optional[str]) -> Optional[str]:
        """
        Validate and set the TOTNU value.
        
        Args:
            value: The value to validate
            
        Returns:
            The validated value
            
        Raises:
            ValueError: If the value is invalid
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            value_upper = value.strip().upper()
            if value_upper == "":
                return None
            elif value_upper == "NO":
                return "NO"
            else:
                raise ValueError("TOTNU value must be blank/None or 'NO'")
        else:
            raise ValueError("TOTNU value must be a string or None")
    
    def set_total_nu(self) -> None:
        """Set the card to use total nu (prompt + delayed fission neutrons)."""
        self.value = None
    
    def set_prompt_only(self) -> None:
        """Set the card to use only prompt nu (prompt fission neutrons only)."""
        self.value = "NO"
    
    def is_total_nu(self) -> bool:
        """Check if the card is set to use total nu (prompt + delayed)."""
        return self.value is None
    
    def is_prompt_only(self) -> bool:
        """Check if the card is set to use only prompt nu."""
        return self.value == "NO"
    
    def get_value(self) -> Optional[str]:
        """Get the current TOTNU value."""
        return self.value
    
    def to_string(self) -> str:
        """
        Convert the TOTNU card to MCNP input format.
        
        Returns:
            Formatted TOTNU card string
        """
        if self.value is None:
            return "totnu"
        else:
            return f"totnu {self.value}"
    
    def write_to_file(self, file: TextIO) -> None:
        """
        Write the TOTNU card to a file.
        
        Args:
            file: Open file object to write to
        """
        file.write(self.to_string() + '\n')
    
    def __str__(self) -> str:
        """String representation of the TOTNU card."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer representation of the TOTNU card."""
        return f"TOTNUCard(value={self.value!r})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another TOTNUCard."""
        if not isinstance(other, TOTNUCard):
            return False
        return self.value == other.value


# Example usage and test functions
if __name__ == "__main__":
    # Example 1: Default behavior (total nu - prompt + delayed)
    print("Example 1: Default TOTNU card (total nu)")
    totnu_default = TOTNUCard()
    print(f"Card: {totnu_default}")
    print(f"Uses total nu: {totnu_default.is_total_nu()}")
    print(f"Uses prompt only: {totnu_default.is_prompt_only()}")
    print()
    
    # Example 2: Explicit blank value (same as default)
    print("Example 2: Explicit blank TOTNU card")
    totnu_blank = TOTNUCard("")
    print(f"Card: {totnu_blank}")
    print(f"Uses total nu: {totnu_blank.is_total_nu()}")
    print()
    
    # Example 3: Prompt only
    print("Example 3: Prompt only TOTNU card")
    totnu_prompt = TOTNUCard("NO")
    print(f"Card: {totnu_prompt}")
    print(f"Uses total nu: {totnu_prompt.is_total_nu()}")
    print(f"Uses prompt only: {totnu_prompt.is_prompt_only()}")
    print()
    
    # Example 4: Setting values programmatically
    print("Example 4: Programmatic setting")
    totnu_prog = TOTNUCard()
    print(f"Initial: {totnu_prog}")
    
    totnu_prog.set_prompt_only()
    print(f"After set_prompt_only(): {totnu_prog}")
    
    totnu_prog.set_total_nu()
    print(f"After set_total_nu(): {totnu_prog}")
    print()
    
    # Test case insensitivity
    print("Example 5: Case insensitive input")
    totnu_lower = TOTNUCard("no")
    totnu_mixed = TOTNUCard("No")
    print(f"Lower case 'no': {totnu_lower}")
    print(f"Mixed case 'No': {totnu_mixed}")
    print(f"Both are prompt only: {totnu_lower.is_prompt_only() and totnu_mixed.is_prompt_only()}")
    print()
    
    # Test file writing
    print("Writing TOTNU cards to file:")
    with open("test_totnu_cards.txt", "w") as f:
        f.write("c TOTNU card examples\n")
        f.write("c\n")
        f.write("c Default behavior (total nu)\n")
        totnu_default.write_to_file(f)
        f.write("c\n")
        f.write("c Prompt only\n")
        totnu_prompt.write_to_file(f)
    
    print("TOTNU cards written to 'test_totnu_cards.txt'")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        bad_totnu = TOTNUCard("INVALID")
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        bad_totnu = TOTNUCard(123)  # Not a string
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Test equality
    print("\nTesting equality:")
    totnu1 = TOTNUCard()
    totnu2 = TOTNUCard(None)
    totnu3 = TOTNUCard("")
    totnu4 = TOTNUCard("NO")
    
    print(f"TOTNUCard() == TOTNUCard(None): {totnu1 == totnu2}")
    print(f"TOTNUCard() == TOTNUCard(''): {totnu1 == totnu3}")
    print(f"TOTNUCard() == TOTNUCard('NO'): {totnu1 == totnu4}")
    print(f"TOTNUCard('NO') == TOTNUCard('no'): {totnu4 == TOTNUCard('no')}")
    
    # Show different representations
    print("\nDifferent representations:")
    print(f"str(totnu_default): {str(totnu_default)}")
    print(f"repr(totnu_default): {repr(totnu_default)}")
    print(f"str(totnu_prompt): {str(totnu_prompt)}")
    print(f"repr(totnu_prompt): {repr(totnu_prompt)}")
    
    # Demonstrate typical usage scenarios
    print("\nTypical usage scenarios:")
    
    print("\n1. Standard criticality calculation (include delayed neutrons):")
    criticality_totnu = TOTNUCard()
    print(f"   {criticality_totnu}")
    
    print("\n2. Prompt neutron calculation (exclude delayed neutrons):")
    prompt_totnu = TOTNUCard("NO")
    print(f"   {prompt_totnu}")
    
    print("\n3. Checking current setting:")
    if criticality_totnu.is_total_nu():
        print("   Using total nu (prompt + delayed neutrons)")
    if prompt_totnu.is_prompt_only():
        print("   Using prompt nu only")