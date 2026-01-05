from typing import Dict, List, Optional, TextIO, Tuple, Union

from nexa.data import Abundances, Elements, Isotope, Isotopes, LibEndf81
from nexa.globals import CompositionMode
from nexa.material import Constituent


class MaterialCard:
    """
    Represents an MCNP material card (M card).

    The material card defines the composition of a material including:
    - Material number
    - Constituent isotopes/elements with fractions
    - Optional keywords for library specifications and other parameters
    """

    def __init__(self, material_number: int):
        """
        Initialize a material card.

        Args:
            material_number: Material number (0-99,999,999). Use 0 for global keywords.
        """
        if not (0 <= material_number <= 99999999):
            raise ValueError("Material number must be between 0 and 99,999,999")

        self.material_number = material_number
        self._constituent: Constituent
        self.keywords: Dict[str, Union[str, int, float, List[float]]] = {}

        # Track fraction type to ensure consistency
        self._fraction_type: Optional[str] = None  # 'atomic' or 'weight'

    def constituent(self, con: Constituent) -> None:
        """
        Set the material constituent.

        Args:
            con: Constituent object
        """

        self._constituent = con

    def set_gas_flag(self, gas_flag: int) -> None:
        """Set the GAS keyword for density-effect correction."""
        if gas_flag not in [0, 1]:
            raise ValueError("GAS flag must be 0 or 1")
        self.keywords["GAS"] = gas_flag

    def set_estep(self, n: int) -> None:
        """Set the ESTEP keyword for electron sub-steps."""
        if n <= 0:
            raise ValueError("ESTEP must be positive")
        self.keywords["ESTEP"] = n

    def set_hstep(self, n: int) -> None:
        """Set the HSTEP keyword for charged-particle sub-steps."""
        if n <= 0:
            raise ValueError("HSTEP must be positive")
        self.keywords["HSTEP"] = n

    def set_library(self, lib_type: str, identifier: str) -> None:
        """
        Set library identifier for various particle types.

        Args:
            lib_type: Library type ('NLIB', 'PLIB', 'PNLIB', 'ELIB', 'HLIB', 'ALIB', 'SLIB', 'TLIB', 'DLIB')
            identifier: Library identifier string
        """
        valid_libs = {"NLIB", "PLIB", "PNLIB", "ELIB", "HLIB", "ALIB", "SLIB", "TLIB", "DLIB"}
        if lib_type not in valid_libs:
            raise ValueError(f"Invalid library type. Must be one of: {valid_libs}")
        self.keywords[lib_type] = identifier

    def set_conduction(self, value: float) -> None:
        """Set the COND keyword for material conduction state."""
        self.keywords["COND"] = value

    def set_refractive_index_constant(self, a: float) -> None:
        """Set constant refractive index using REFI keyword."""
        self.keywords["REFI"] = a

    def set_refractive_index_cauchy(self, a: float, b: float, c: float, d: float) -> None:
        """Set Cauchy coefficients for refractive index using REFI keyword."""
        self.keywords["REFI"] = [a, b, c, d]

    def set_refractive_index_sellmeier(
        self, b1: float, c1: float, b2: float, c2: float, b3: float, c3: float
    ) -> None:
        """Set Sellmeier coefficients for refractive index using REFS keyword."""
        self.keywords["REFS"] = [b1, c1, b2, c2, b3, c3]

    def _format_fraction(self, fraction: float) -> str:
        """Format fraction with appropriate precision."""
        if abs(fraction) >= 1e-3:
            return f"{fraction:.6f}".rstrip("0").rstrip(".")
        else:
            return f"{fraction:.6e}"

    def _format_keyword_value(self, key: str, value: Union[str, int, float, List[float]]) -> str:
        """Format a keyword-value pair."""
        if isinstance(value, str):
            return f"{key}={value}"
        elif isinstance(value, int):
            return f"{key}={value}"
        elif isinstance(value, float):
            if abs(value) >= 1e-3 and abs(value) < 1e6:
                formatted = f"{value:.6f}".rstrip("0").rstrip(".")
                return f"{key}={formatted}"
            else:
                return f"{key}={value:.6e}"
        elif isinstance(value, list):
            formatted_values = []
            for v in value:
                if abs(v) >= 1e-3 and abs(v) < 1e6:
                    formatted = f"{v:.6f}".rstrip("0").rstrip(".")
                    formatted_values.append(formatted)
                else:
                    formatted_values.append(f"{v:.6e}")
            return f"{key}={' '.join(formatted_values)}"
        else:
            return f"{key}={value}"

    def to_string(self, line_length: int = 132) -> str:
        """
        Convert the material card to MCNP input format.

        Args:
            line_length: Maximum line length for formatting

        Returns:
            Formatted material card string
        """
        if not self._constituent and self.material_number != 0:
            raise ValueError(
                "Material must have at least one constituent (unless material number is 0)"
            )

        lines = []
        current_line = f"m{self.material_number}"
        lines.append(current_line)

        # Add isotopes
        isos: Dict[str, Tuple[Isotope, float, float]] = self._constituent.isotopes()

        for iso_name, value in isos.items():
            iso = value[0]
            afrac = value[2]
            current_line = f"     {iso.zaid:>6} {afrac:.6e} $ {iso.name}"
            lines.append(current_line)

        # Add keywords
        current_line = "     "
        for key, value in self.keywords.items():
            keyword_str = f" {self._format_keyword_value(key, value)}"

            # Check if adding this keyword would exceed line length
            if len(current_line + keyword_str) > line_length:
                lines.append(current_line)
                current_line = "     " + keyword_str.strip()  # Continuation line with 5 spaces
            else:
                current_line += keyword_str

        # Add the final line
        if current_line.strip():
            lines.append(current_line)

        return "\n".join(lines)

    def write_to_file(self, file: TextIO, line_length: int = 132) -> None:
        """
        Write the material card to a file.

        Args:
            file: Open file object to write to
            line_length: Maximum line length for formatting
        """
        file.write(self.to_string(line_length) + "\n")

    def __str__(self) -> str:
        """String representation of the material card."""
        return self.to_string()


# Example usage and test functions
if __name__ == "__main__":

    abund: Abundances = Abundances()
    isos: Isotopes = Isotopes()
    elms: Elements = Elements()

    tempK: float = 600.0
    ext81: str = LibEndf81.ext_by_tempK(tempK)

    # Example 1: Water with atomic fractions
    con_h: Constituent = abund["h"]
    con_o: Constituent = abund["o"]
    con_water = Constituent("water", CompositionMode.Atom)
    con_water.add(con_h, 2.0).add(con_o, 1.0).seal()
    print(f"{con_water = }")

    m_water = MaterialCard(1)
    m_water.constituent(con_water)
    m_water.set_library("NLIB", ext81)
    print(m_water.to_string())

    con_c: Constituent = abund["C"]
    con_h: Constituent = abund["H"]
    con_n: Constituent = abund["N"]
    con_acryl: Constituent = Constituent("Acrylonitrile", CompositionMode.Atom)
    con_acryl.add(con_c, 3.0 / 7.0).add(con_h, 3.0 / 7.0).add(con_n, 1.0 / 7.0).seal()
    con_butad: Constituent = Constituent("Butadiene", CompositionMode.Atom)
    con_butad.add(con_c, 0.4).add(con_h, 0.6).seal()
    con_rubber: Constituent = Constituent("Nitrile Rubber", CompositionMode.Mass)
    con_rubber.add(con_acryl, 0.5).add(con_butad, 0.5).seal()

    m_rubber = MaterialCard(2)
    m_rubber.constituent(con_rubber)
    m_rubber.set_library("NLIB", ext81)
    print(m_rubber.to_string())
