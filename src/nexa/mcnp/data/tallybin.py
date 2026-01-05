from enum import Enum


class McnpTallyBinEnum(Enum):
    """Enumeration of MCNP tally bin types."""

    # tuple: (int value, str description, boolean has_mctal_data)
    F = (0, "cell/surf/det", True)
    D = (1, "direct/flagged", False)
    U = (2, "user", False)
    S = (3, "segment", False)
    M = (4, "multiplier", False)
    C = (5, "cosine", True)
    E = (6, "energy", True)
    T = (7, "time", True)

    @classmethod
    def has_mctal_data(cls, bin_type: "McnpTallyBinEnum") -> bool:
        """Check if the given bin type has mctal data."""
        return bin_type.value[2]

    @classmethod
    def description(cls, bin_type: "McnpTallyBinEnum") -> str:
        """Get the description of the given bin type."""
        return bin_type.value[1]

    @classmethod
    def int_value(cls, bin_type: "McnpTallyBinEnum") -> int:
        """Get the integer value of the given bin type."""
        return bin_type.value[0]

    @classmethod
    def from_int(cls, value: int) -> "McnpTallyBinEnum":
        """Get the McnpTallyBinEnum member from its integer value."""
        for member in cls:
            if member.value[0] == value:
                return member
        raise ValueError(f"No McnpTallyBinEnum member with value {value}")


if __name__ == "__main__":
    for bin_type in McnpTallyBinEnum:
        print(f"{bin_type.name}: {bin_type.value}")

    bin_type = McnpTallyBinEnum["F"]
    print(f"{bin_type.name}: {bin_type.value}")
