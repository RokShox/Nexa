import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class SummaryNuclideData:
    """Data class representing summary nuclide inventory data for all materials."""
    number: int
    zaid: int
    mass_gm: float
    activity_ci: float
    spec_activity_ci_gm: float
    atom_density_a_b_cm: float
    atom_fraction: float
    mass_fraction: float


@dataclass
class SummaryTotals:
    """Data class representing summary totals for all materials."""
    mass_gm: float
    activity_ci: float
    spec_activity_ci_gm: float
    atom_density_a_b_cm: float
    atom_fraction: float
    mass_fraction: float


@dataclass
class SummaryInventory:
    """Data class representing complete summary inventory for all materials at a specific step."""
    step: int
    time_days: float
    power_mw: float
    total_volume_cm3: float
    actinide_nuclides: List[SummaryNuclideData] = field(default_factory=list)
    actinide_totals: Optional[SummaryTotals] = None
    nonactinide_nuclides: List[SummaryNuclideData] = field(default_factory=list)
    nonactinide_totals: Optional[SummaryTotals] = None


class Table220Parser:
    """Parser for MCNP output Table 220 - Burnup summary table summed over all materials."""
    
    def __init__(self):
        self.summary_inventories: List[SummaryInventory] = []
        self._header_found = False
        self._current_step = None
        self._current_inventory = None
        self._inventory_type = None
        self._total_volume = None
    
    def parse_lines(self, lines: List[str]) -> List[SummaryInventory]:
        """
        Parse lines from MCNP output containing Table 220 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            List of SummaryInventory objects
        """
        self.summary_inventories.clear()
        self._header_found = False
        self._current_step = None
        self._current_inventory = None
        self._inventory_type = None
        self._total_volume = None
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                if self._is_volume_line(line):
                    self._total_volume = self._extract_volume(line)
                    continue
                
                if self._is_inventory_header(line):
                    inventory_info = self._parse_inventory_header(line)
                    if inventory_info:
                        self._current_step, time_days, power_mw, self._inventory_type = inventory_info
                        
                        # Find existing inventory for this step or create new one
                        existing_inv = self._find_inventory_by_step(self._current_step)
                        if existing_inv:
                            self._current_inventory = existing_inv
                        else:
                            self._current_inventory = SummaryInventory(
                                step=self._current_step,
                                time_days=time_days,
                                power_mw=power_mw,
                                total_volume_cm3=self._total_volume or 0.0
                            )
                            self.summary_inventories.append(self._current_inventory)
                    continue
                
                if self._current_inventory and self._is_inventory_data_line(line):
                    if self._is_totals_line(line):
                        totals = self._parse_totals_line(line)
                        if totals:
                            if self._inventory_type == "actinide":
                                self._current_inventory.actinide_totals = totals
                            else:
                                self._current_inventory.nonactinide_totals = totals
                    else:
                        nuclide = self._parse_inventory_data_line(line)
                        if nuclide:
                            if self._inventory_type == "actinide":
                                self._current_inventory.actinide_nuclides.append(nuclide)
                            else:
                                self._current_inventory.nonactinide_nuclides.append(nuclide)
        
        return self.summary_inventories
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 220 header."""
        return "burnup summary table summed over all materials" in line.lower() and "print table 220" in line.lower()
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        # Check for next table or end of output
        stripped = line.strip()
        if not stripped:
            return False
        
        # Look for indicators of next section
        return ("print table" in line.lower() and "table 220" not in line.lower()) or \
               line.startswith("1") and any(x in line.lower() for x in ["probid", "keff results", "run terminated"])
    
    def _is_volume_line(self, line: str) -> bool:
        """Check if line contains volume information."""
        return "volume" in line.lower() and "cm**3" in line
    
    def _extract_volume(self, line: str) -> float:
        """Extract total volume from line."""
        match = re.search(r"volume\s+([\d.E+-]+)", line)
        return float(match.group(1)) if match else 0.0
    
    def _is_inventory_header(self, line: str) -> bool:
        """Check if line contains inventory header."""
        return ("actinide inventory" in line.lower() or "nonactinide inventory" in line.lower()) and "sum of materials" in line.lower()
    
    def _parse_inventory_header(self, line: str) -> Optional[Tuple[int, float, float, str]]:
        """Parse inventory header to extract step, time, power, and type."""
        try:
            # Extract inventory type
            inv_type = "actinide" if "actinide" in line.lower() else "nonactinide"
            
            # Extract step
            step_match = re.search(r"step\s+(\d+)", line)
            step = int(step_match.group(1)) if step_match else None
            
            # Extract time
            time_match = re.search(r"time\s+([\d.E+-]+)", line)
            time_days = float(time_match.group(1)) if time_match else None
            
            # Extract power
            power_match = re.search(r"power\s+([\d.E+-]+)", line)
            power_mw = float(power_match.group(1)) if power_match else None
            
            if all(x is not None for x in [step, time_days, power_mw]):
                return step, time_days, power_mw, inv_type
            
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _find_inventory_by_step(self, step: int) -> Optional[SummaryInventory]:
        """Find existing inventory for a given step."""
        for inventory in self.summary_inventories:
            if inventory.step == step:
                return inventory
        return None
    
    def _is_inventory_data_line(self, line: str) -> bool:
        """Check if line contains inventory data."""
        stripped = line.strip()
        if not stripped or "no." in stripped.lower() or "zaid" in stripped.lower():
            return False
        return stripped.split() and (stripped.split()[0].isdigit() or stripped.startswith("totals"))
    
    def _is_totals_line(self, line: str) -> bool:
        """Check if line contains totals."""
        return line.strip().startswith("totals")
    
    def _parse_inventory_data_line(self, line: str) -> Optional[SummaryNuclideData]:
        """Parse inventory data line."""
        try:
            parts = line.strip().split()
            if len(parts) < 7:
                return None
            
            return SummaryNuclideData(
                number=int(parts[0]),
                zaid=int(parts[1]),
                mass_gm=float(parts[2]),
                activity_ci=float(parts[3]),
                spec_activity_ci_gm=float(parts[4]),
                atom_density_a_b_cm=float(parts[5]),
                atom_fraction=float(parts[6]),
                mass_fraction=float(parts[7])
            )
        except (ValueError, IndexError):
            return None
    
    def _parse_totals_line(self, line: str) -> Optional[SummaryTotals]:
        """Parse totals line."""
        try:
            parts = line.strip().split()
            if len(parts) < 7:
                return None
            
            return SummaryTotals(
                mass_gm=float(parts[1]),
                activity_ci=float(parts[2]),
                spec_activity_ci_gm=float(parts[3]),
                atom_density_a_b_cm=float(parts[4]),
                atom_fraction=float(parts[5]),
                mass_fraction=float(parts[6])
            )
        except (ValueError, IndexError):
            return None
    
    def get_inventory_at_step(self, step: int) -> Optional[SummaryInventory]:
        """Get summary inventory for a specific step."""
        for inventory in self.summary_inventories:
            if inventory.step == step:
                return inventory
        return None
    
    def get_all_steps(self) -> List[int]:
        """Get list of all available steps."""
        return sorted([inv.step for inv in self.summary_inventories])
    
    def get_actinide_nuclide_at_step(self, step: int, zaid: int) -> Optional[SummaryNuclideData]:
        """Get specific actinide nuclide data at a step."""
        inventory = self.get_inventory_at_step(step)
        if inventory:
            for nuclide in inventory.actinide_nuclides:
                if nuclide.zaid == zaid:
                    return nuclide
        return None
    
    def get_nonactinide_nuclide_at_step(self, step: int, zaid: int) -> Optional[SummaryNuclideData]:
        """Get specific non-actinide nuclide data at a step."""
        inventory = self.get_inventory_at_step(step)
        if inventory:
            for nuclide in inventory.nonactinide_nuclides:
                if nuclide.zaid == zaid:
                    return nuclide
        return None
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        return {
            'summary_inventories': [
                {
                    'step': inv.step,
                    'time_days': inv.time_days,
                    'power_mw': inv.power_mw,
                    'total_volume_cm3': inv.total_volume_cm3,
                    'actinide_nuclides': [
                        {
                            'number': n.number,
                            'zaid': n.zaid,
                            'mass_gm': n.mass_gm,
                            'activity_ci': n.activity_ci,
                            'spec_activity_ci_gm': n.spec_activity_ci_gm,
                            'atom_density_a_b_cm': n.atom_density_a_b_cm,
                            'atom_fraction': n.atom_fraction,
                            'mass_fraction': n.mass_fraction
                        }
                        for n in inv.actinide_nuclides
                    ],
                    'actinide_totals': {
                        'mass_gm': inv.actinide_totals.mass_gm,
                        'activity_ci': inv.actinide_totals.activity_ci,
                        'spec_activity_ci_gm': inv.actinide_totals.spec_activity_ci_gm,
                        'atom_density_a_b_cm': inv.actinide_totals.atom_density_a_b_cm,
                        'atom_fraction': inv.actinide_totals.atom_fraction,
                        'mass_fraction': inv.actinide_totals.mass_fraction
                    } if inv.actinide_totals else None,
                    'nonactinide_nuclides': [
                        {
                            'number': n.number,
                            'zaid': n.zaid,
                            'mass_gm': n.mass_gm,
                            'activity_ci': n.activity_ci,
                            'spec_activity_ci_gm': n.spec_activity_ci_gm,
                            'atom_density_a_b_cm': n.atom_density_a_b_cm,
                            'atom_fraction': n.atom_fraction,
                            'mass_fraction': n.mass_fraction
                        }
                        for n in inv.nonactinide_nuclides
                    ],
                    'nonactinide_totals': {
                        'mass_gm': inv.nonactinide_totals.mass_gm,
                        'activity_ci': inv.nonactinide_totals.activity_ci,
                        'spec_activity_ci_gm': inv.nonactinide_totals.spec_activity_ci_gm,
                        'atom_density_a_b_cm': inv.nonactinide_totals.atom_density_a_b_cm,
                        'atom_fraction': inv.nonactinide_totals.atom_fraction,
                        'mass_fraction': inv.nonactinide_totals.mass_fraction
                    } if inv.nonactinide_totals else None
                }
                for inv in self.summary_inventories
            ]
        }


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1burnup summary table summed over all materials                                                         print table 220",
        "",
        " nuclides with atom fractions below 1.000E-10 for a material are zeroed and deleted from print tables after t=0",
        "",
        " nuclide data are sorted by increasing zaid summed over all materials volume  2.3748E+05 (cm**3)",
        "",
        " actinide inventory for sum of materials at end of step  0, time 0.000E+00 (days), power 1.000E+00 (MW)",
        "",
        "  no. zaid     mass      activity   sp. act.  atom den.   atom fr.   mass fr.",
        "               (gm)        (Ci)     (Ci/gm)    (a/b-cm)",
        "   1  90230  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00",
        "   2  90231  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00",
        "   3  90232  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00  0.000E+00",
        "     totals  2.191E+06  0.000E+00  0.000E+00  2.335E-02  3.333E-01  8.814E-01",
        "",
        " actinide inventory for sum of materials at end of step  1, time 4.000E+00 (days), power 1.000E+00 (MW)",
        "",
        "  no. zaid     mass      activity   sp. act.  atom den.   atom fr.   mass fr.",
        "               (gm)        (Ci)     (Ci/gm)    (a/b-cm)",
        "   1  92234  1.025E+03  6.374E+00  6.217E-03  1.111E-05  1.585E-04  4.124E-04",
        "   2  92235  1.084E+05  2.344E-01  2.161E-06  1.170E-03  1.670E-02  4.363E-02",
        "   3  92236  3.281E+01  2.122E-03  6.467E-05  3.524E-07  5.030E-06  1.320E-05",
        "     totals  2.191E+06  6.192E+05  2.826E-01  2.335E-02  3.333E-01  8.814E-01"
    ]
    
    parser = Table220Parser()
    inventories = parser.parse_lines(sample_lines)
    
    print(f"Found {len(inventories)} summary inventories:")
    for inv in inventories:
        print(f"  Step {inv.step}: {len(inv.actinide_nuclides)} actinides, {len(inv.nonactinide_nuclides)} non-actinides")
        if inv.actinide_totals:
            print(f"    Actinide total mass: {inv.actinide_totals.mass_gm:.2e} gm")
        if inv.nonactinide_totals:
            print(f"    Non-actinide total mass: {inv.nonactinide_totals.mass_gm:.2e} gm")
    
    print(f"\nAvailable steps: {parser.get_all_steps()}")