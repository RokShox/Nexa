import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class NeutronicsData:
    """Data class representing neutronics and burnup data for a step."""
    step: int
    duration_days: float
    time_days: float
    power_mw: float
    keff: float
    flux: float
    ave_nu: float
    ave_q: float
    burnup_gwd_mtu: float
    source_nts_sec: float


@dataclass
class MaterialBurnupData:
    """Data class representing individual material burnup data for a step."""
    step: int
    duration_days: float
    time_days: float
    power_fraction: float
    burnup_gwd_mtu: float


@dataclass
class NuclideInventoryData:
    """Data class representing nuclide inventory data."""
    number: int
    zaid: int
    mass_gm: float
    activity_ci: float
    spec_activity_ci_gm: float
    atom_density_a_b_cm: float
    atom_fraction: float
    mass_fraction: float


@dataclass
class InventoryTotals:
    """Data class representing inventory totals."""
    mass_gm: float
    activity_ci: float
    spec_activity_ci_gm: float
    atom_density_a_b_cm: float
    atom_fraction: float
    mass_fraction: float


@dataclass
class MaterialInventory:
    """Data class representing complete inventory for a material at a specific step."""
    material_id: int
    step: int
    time_days: float
    power_mw: float
    volume_cm3: float
    actinide_nuclides: List[NuclideInventoryData] = field(default_factory=list)
    actinide_totals: Optional[InventoryTotals] = None
    nonactinide_nuclides: List[NuclideInventoryData] = field(default_factory=list)
    nonactinide_totals: Optional[InventoryTotals] = None


class Table210Parser:
    """Parser for MCNP output Table 210 - Burnup summary table by material."""
    
    def __init__(self):
        self.neutronics_data: List[NeutronicsData] = []
        self.material_burnup_data: Dict[int, List[MaterialBurnupData]] = {}
        self.material_inventories: Dict[int, List[MaterialInventory]] = {}
        self._header_found = False
        self._parsing_state = None
        self._current_material = None
        self._current_step = None
        self._current_inventory = None
        self._inventory_type = None
    
    def parse_lines(self, lines: List[str]) -> Tuple[List[NeutronicsData], Dict[int, List[MaterialBurnupData]], Dict[int, List[MaterialInventory]]]:
        """
        Parse lines from MCNP output containing Table 210 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Tuple of (neutronics_data, material_burnup_data, material_inventories)
        """
        self.neutronics_data.clear()
        self.material_burnup_data.clear()
        self.material_inventories.clear()
        self._header_found = False
        self._parsing_state = None
        self._current_material = None
        self._current_step = None
        self._current_inventory = None
        self._inventory_type = None
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                if self._is_neutronics_header(line):
                    self._parsing_state = "neutronics"
                    continue
                
                if self._is_material_burnup_header(line):
                    self._parsing_state = "material_burnup"
                    continue
                
                if self._is_material_number_line(line):
                    self._current_material = self._extract_material_number(line)
                    continue
                
                if self._is_inventory_header(line):
                    inventory_info = self._parse_inventory_header(line)
                    if inventory_info:
                        self._current_material, self._current_step, time_days, power_mw, volume_cm3, self._inventory_type = inventory_info
                        self._current_inventory = MaterialInventory(
                            material_id=self._current_material,
                            step=self._current_step,
                            time_days=time_days,
                            power_mw=power_mw,
                            volume_cm3=volume_cm3
                        )
                    continue
                
                if self._parsing_state == "neutronics" and self._is_neutronics_data_line(line):
                    neutronics = self._parse_neutronics_line(line)
                    if neutronics:
                        self.neutronics_data.append(neutronics)
                
                elif self._parsing_state == "material_burnup" and self._is_material_burnup_data_line(line):
                    burnup = self._parse_material_burnup_line(line)
                    if burnup and self._current_material:
                        if self._current_material not in self.material_burnup_data:
                            self.material_burnup_data[self._current_material] = []
                        self.material_burnup_data[self._current_material].append(burnup)
                
                elif self._current_inventory and self._is_inventory_data_line(line):
                    if self._is_totals_line(line):
                        totals = self._parse_totals_line(line)
                        if totals:
                            if self._inventory_type == "actinide":
                                self._current_inventory.actinide_totals = totals
                            else:
                                self._current_inventory.nonactinide_totals = totals
                            
                            # Store completed inventory
                            if self._current_material not in self.material_inventories:
                                self.material_inventories[self._current_material] = []
                            self.material_inventories[self._current_material].append(self._current_inventory)
                            self._current_inventory = None
                    else:
                        nuclide = self._parse_inventory_data_line(line)
                        if nuclide:
                            if self._inventory_type == "actinide":
                                self._current_inventory.actinide_nuclides.append(nuclide)
                            else:
                                self._current_inventory.nonactinide_nuclides.append(nuclide)
        
        return self.neutronics_data, self.material_burnup_data, self.material_inventories
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 210 header."""
        return "burnup summary table by material" in line.lower() and "print table 210" in line.lower()
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        return "print table 220" in line.lower() or "burnup summary table summed over all materials" in line.lower()
    
    def _is_neutronics_header(self, line: str) -> bool:
        """Check if line contains neutronics data header."""
        return "neutronics and burnup data" in line.lower()
    
    def _is_material_burnup_header(self, line: str) -> bool:
        """Check if line contains material burnup header."""
        return "individual material burnup" in line.lower()
    
    def _is_material_number_line(self, line: str) -> bool:
        """Check if line contains material number."""
        return line.strip().startswith("Material #:")
    
    def _extract_material_number(self, line: str) -> int:
        """Extract material number from line."""
        match = re.search(r"Material #:\s*(\d+)", line)
        return int(match.group(1)) if match else None
    
    def _is_inventory_header(self, line: str) -> bool:
        """Check if line contains inventory header."""
        return ("actinide inventory" in line.lower() or "nonactinide inventory" in line.lower()) and "material" in line.lower()
    
    def _parse_inventory_header(self, line: str) -> Optional[Tuple[int, int, float, float, float, str]]:
        """Parse inventory header to extract material, step, time, power, volume, and type."""
        try:
            # Extract inventory type
            inv_type = "actinide" if "actinide" in line.lower() else "nonactinide"
            
            # Extract material number
            mat_match = re.search(r"material\s+(\d+)", line)
            material_id = int(mat_match.group(1)) if mat_match else None
            
            # Extract step
            step_match = re.search(r"step\s+(\d+)", line)
            step = int(step_match.group(1)) if step_match else None
            
            # Extract time
            time_match = re.search(r"time\s+([\d.E+-]+)", line)
            time_days = float(time_match.group(1)) if time_match else None
            
            # Extract power
            power_match = re.search(r"power\s+([\d.E+-]+)", line)
            power_mw = float(power_match.group(1)) if power_match else None
            
            # Extract volume (from previous line context or this line)
            volume_match = re.search(r"volume\s+([\d.E+-]+)", line)
            volume_cm3 = float(volume_match.group(1)) if volume_match else 0.0
            
            if all(x is not None for x in [material_id, step, time_days, power_mw]):
                return material_id, step, time_days, power_mw, volume_cm3, inv_type
            
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _is_neutronics_data_line(self, line: str) -> bool:
        """Check if line contains neutronics data."""
        stripped = line.strip()
        if not stripped or "step" in stripped.lower() or "duration" in stripped.lower():
            return False
        parts = stripped.split()
        return len(parts) >= 9 and parts[0].isdigit()
    
    def _is_material_burnup_data_line(self, line: str) -> bool:
        """Check if line contains material burnup data."""
        stripped = line.strip()
        if not stripped or "step" in stripped.lower() or "duration" in stripped.lower():
            return False
        parts = stripped.split()
        return len(parts) >= 4 and parts[0].isdigit()
    
    def _is_inventory_data_line(self, line: str) -> bool:
        """Check if line contains inventory data."""
        stripped = line.strip()
        if not stripped or "no." in stripped.lower() or "zaid" in stripped.lower():
            return False
        return stripped.split() and (stripped.split()[0].isdigit() or stripped.startswith("totals"))
    
    def _is_totals_line(self, line: str) -> bool:
        """Check if line contains totals."""
        return line.strip().startswith("totals")
    
    def _parse_neutronics_line(self, line: str) -> Optional[NeutronicsData]:
        """Parse neutronics data line."""
        try:
            parts = line.strip().split()
            if len(parts) < 9:
                return None
            
            return NeutronicsData(
                step=int(parts[0]),
                duration_days=float(parts[1]),
                time_days=float(parts[2]),
                power_mw=float(parts[3]),
                keff=float(parts[4]),
                flux=float(parts[5]),
                ave_nu=float(parts[6]),
                ave_q=float(parts[7]),
                burnup_gwd_mtu=float(parts[8]),
                source_nts_sec=float(parts[9])
            )
        except (ValueError, IndexError):
            return None
    
    def _parse_material_burnup_line(self, line: str) -> Optional[MaterialBurnupData]:
        """Parse material burnup data line."""
        try:
            parts = line.strip().split()
            if len(parts) < 4:
                return None
            
            return MaterialBurnupData(
                step=int(parts[0]),
                duration_days=float(parts[1]),
                time_days=float(parts[2]),
                power_fraction=float(parts[3]),
                burnup_gwd_mtu=float(parts[4])
            )
        except (ValueError, IndexError):
            return None
    
    def _parse_inventory_data_line(self, line: str) -> Optional[NuclideInventoryData]:
        """Parse inventory data line."""
        try:
            parts = line.strip().split()
            if len(parts) < 7:
                return None
            
            return NuclideInventoryData(
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
    
    def _parse_totals_line(self, line: str) -> Optional[InventoryTotals]:
        """Parse totals line."""
        try:
            parts = line.strip().split()
            if len(parts) < 7:
                return None
            
            return InventoryTotals(
                mass_gm=float(parts[1]),
                activity_ci=float(parts[2]),
                spec_activity_ci_gm=float(parts[3]),
                atom_density_a_b_cm=float(parts[4]),
                atom_fraction=float(parts[5]),
                mass_fraction=float(parts[6])
            )
        except (ValueError, IndexError):
            return None
    
    def get_neutronics_at_step(self, step: int) -> Optional[NeutronicsData]:
        """Get neutronics data for a specific step."""
        for data in self.neutronics_data:
            if data.step == step:
                return data
        return None
    
    def get_material_burnup(self, material_id: int) -> List[MaterialBurnupData]:
        """Get burnup data for a specific material."""
        return self.material_burnup_data.get(material_id, [])
    
    def get_material_inventory(self, material_id: int, step: int) -> Optional[MaterialInventory]:
        """Get inventory data for a specific material at a specific step."""
        if material_id in self.material_inventories:
            for inventory in self.material_inventories[material_id]:
                if inventory.step == step:
                    return inventory
        return None
    
    def get_all_materials(self) -> List[int]:
        """Get list of all material IDs."""
        materials = set()
        materials.update(self.material_burnup_data.keys())
        materials.update(self.material_inventories.keys())
        return sorted(list(materials))
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        return {
            'neutronics_data': [
                {
                    'step': n.step,
                    'duration_days': n.duration_days,
                    'time_days': n.time_days,
                    'power_mw': n.power_mw,
                    'keff': n.keff,
                    'flux': n.flux,
                    'ave_nu': n.ave_nu,
                    'ave_q': n.ave_q,
                    'burnup_gwd_mtu': n.burnup_gwd_mtu,
                    'source_nts_sec': n.source_nts_sec
                }
                for n in self.neutronics_data
            ],
            'material_burnup_data': {
                mat_id: [
                    {
                        'step': b.step,
                        'duration_days': b.duration_days,
                        'time_days': b.time_days,
                        'power_fraction': b.power_fraction,
                        'burnup_gwd_mtu': b.burnup_gwd_mtu
                    }
                    for b in burnup_list
                ]
                for mat_id, burnup_list in self.material_burnup_data.items()
            },
            'material_inventories': {
                mat_id: [
                    {
                        'material_id': inv.material_id,
                        'step': inv.step,
                        'time_days': inv.time_days,
                        'power_mw': inv.power_mw,
                        'volume_cm3': inv.volume_cm3,
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
                    for inv in inv_list
                ]
                for mat_id, inv_list in self.material_inventories.items()
            }
        }


# Example usage:
if __name__ == "__main__":
    # This would be used with actual MCNP output lines
    parser = Table210Parser()
    # neutronics_data, material_burnup_data, material_inventories = parser.parse_lines(sample_lines)
    print("Table210Parser ready for use")