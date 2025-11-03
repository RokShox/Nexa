import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class EventData:
    """Data class representing event data for a specific cell."""
    entering: float = 0.0
    source: float = 0.0
    energy_cutoff: float = 0.0
    time_cutoff: float = 0.0
    exiting: float = 0.0
    total: float = 0.0


@dataclass
class VarianceReductionData:
    """Data class representing variance reduction events for a specific cell."""
    weight_window: float = 0.0
    cell_importance: float = 0.0
    weight_cutoff: float = 0.0
    e_or_t_importance: float = 0.0
    dxtran: float = 0.0
    forced_collisions: float = 0.0
    exp_transform: float = 0.0
    total: float = 0.0


@dataclass
class PhysicalEventsData:
    """Data class representing physical events for a specific cell."""
    capture: float = 0.0
    n_xn: float = 0.0
    loss_to_n_xn: float = 0.0
    fission: float = 0.0
    loss_to_fission: float = 0.0
    photonuclear: float = 0.0
    nucl_interaction: float = 0.0
    tabular_boundary: float = 0.0
    decay_gain: float = 0.0
    tabular_sampling: float = 0.0
    decay_loss: float = 0.0
    photofission: float = 0.0
    total: float = 0.0


@dataclass
class CellWeightBalance:
    """Data class representing complete weight balance for a cell."""
    cell_number: int
    external_events: EventData = field(default_factory=EventData)
    variance_reduction: VarianceReductionData = field(default_factory=VarianceReductionData)
    physical_events: PhysicalEventsData = field(default_factory=PhysicalEventsData)
    total: float = 0.0


@dataclass
class WeightBalanceTotals:
    """Data class representing totals across all cells."""
    external_events: EventData = field(default_factory=EventData)
    variance_reduction: VarianceReductionData = field(default_factory=VarianceReductionData)
    physical_events: PhysicalEventsData = field(default_factory=PhysicalEventsData)
    total: float = 0.0


class Table130Parser:
    """Parser for MCNP output Table 130 - Neutron weight balance in each cell."""
    
    def __init__(self):
        self.cell_balances: Dict[int, CellWeightBalance] = {}
        self.totals: Optional[WeightBalanceTotals] = None
        self._header_found = False
        self._current_cells = []
        self._parsing_state = None
    
    def parse_lines(self, lines: List[str]) -> Tuple[Dict[int, CellWeightBalance], Optional[WeightBalanceTotals]]:
        """
        Parse lines from MCNP output containing Table 130 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Tuple of (dict of cell_number -> CellWeightBalance, WeightBalanceTotals or None)
        """
        self.cell_balances.clear()
        self.totals = None
        self._header_found = False
        self._current_cells = []
        self._parsing_state = None
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                if self._is_cell_header(line):
                    self._parse_cell_header(line)
                    continue
                
                if self._is_section_header(line):
                    self._parsing_state = self._get_section_type(line)
                    continue
                
                if self._is_data_line(line):
                    self._parse_data_line(line)
                    continue
                
                if self._is_total_line(line):
                    self._parse_total_line(line)
                    continue
        
        # Initialize totals if not already done
        if self.totals is None:
            self.totals = WeightBalanceTotals()
        
        return self.cell_balances, self.totals
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 130 header."""
        return "neutron  weight balance in each cell" in line.lower() and "print table 130" in line.lower()
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        stripped = line.strip()
        if not stripped:
            return False
        # End when we hit a line that doesn't start with "cell index" after the data section
        return (self._header_found and 
                not stripped.lower().startswith("cell index") and 
                not stripped.startswith("cell number") and
                not any(x in stripped.lower() for x in ["external events", "variance reduction", "physical events", "total"]) and
                not stripped.startswith("-") and
                not self._is_data_line(line))
    
    def _is_cell_header(self, line: str) -> bool:
        """Check if line contains cell index or cell number headers."""
        stripped = line.strip().lower()
        return stripped.startswith("cell index") or stripped.startswith("cell number")
    
    def _is_section_header(self, line: str) -> bool:
        """Check if line contains section headers."""
        stripped = line.strip().lower()
        return any(x in stripped for x in ["external events:", "variance reduction events:", "physical events:"])
    
    def _is_data_line(self, line: str) -> bool:
        """Check if line contains event data."""
        stripped = line.strip()
        if not stripped or stripped.startswith("-"):
            return False
        
        # Look for lines with event names and scientific notation values
        event_names = [
            "entering", "source", "energy cutoff", "time cutoff", "exiting",
            "weight window", "cell importance", "weight cutoff", "e or t importance",
            "dxtran", "forced collisions", "exp. transform",
            "capture", "(n,xn)", "loss to (n,xn)", "fission", "loss to fission",
            "photonuclear", "nucl. interaction", "tabular boundary", "decay gain",
            "tabular sampling", "decay loss", "photofission"
        ]
        
        return any(stripped.lower().startswith(event.lower()) for event in event_names)
    
    def _is_total_line(self, line: str) -> bool:
        """Check if line contains totals."""
        stripped = line.strip().lower()
        return stripped.startswith("total")
    
    def _parse_cell_header(self, line: str):
        """Parse cell index or cell number header line."""
        parts = line.strip().split()
        if "cell number" in line.lower():
            # Extract cell numbers (skip the first two words "cell number")
            self._current_cells = [int(x) for x in parts[2:] if x.isdigit()]
            # Initialize cell balance objects
            for cell_num in self._current_cells:
                if cell_num not in self.cell_balances:
                    self.cell_balances[cell_num] = CellWeightBalance(cell_number=cell_num)
    
    def _get_section_type(self, line: str) -> str:
        """Determine which section type from the header."""
        line_lower = line.lower()
        if "external events" in line_lower:
            return "external"
        elif "variance reduction" in line_lower:
            return "variance"
        elif "physical events" in line_lower:
            return "physical"
        return None
    
    def _parse_data_line(self, line: str):
        """Parse a data line containing event values."""
        if not self._current_cells or not self._parsing_state:
            return
        
        parts = line.strip().split()
        if len(parts) < 2:
            return
        
        event_name = parts[0].lower()
        values = []
        
        # Parse numeric values (skip the event name)
        for part in parts[1:]:
            try:
                if part != "----------":
                    values.append(float(part))
            except ValueError:
                continue
        
        # Map values to cells and totals column
        for i, cell_num in enumerate(self._current_cells):
            if i < len(values):
                self._set_event_value(cell_num, event_name, values[i])
        
        # Handle totals column (last value if more values than cells)
        if len(values) > len(self._current_cells):
            self._set_total_value(event_name, values[-1])
    
    def _parse_total_line(self, line: str):
        """Parse total line for each section."""
        if not self._current_cells:
            return
        
        parts = line.strip().split()
        if len(parts) < 2:
            return
        
        values = []
        for part in parts[1:]:  # Skip "total"
            try:
                if part != "----------":
                    values.append(float(part))
            except ValueError:
                continue
        
        # Set section totals for each cell
        for i, cell_num in enumerate(self._current_cells):
            if i < len(values):
                self._set_section_total(cell_num, values[i])
        
        # Handle totals column
        if len(values) > len(self._current_cells):
            self._set_section_total_overall(values[-1])
    
    def _set_event_value(self, cell_num: int, event_name: str, value: float):
        """Set event value for a specific cell."""
        if cell_num not in self.cell_balances:
            return
        
        cell_balance = self.cell_balances[cell_num]
        
        if self._parsing_state == "external":
            if event_name == "entering":
                cell_balance.external_events.entering = value
            elif event_name == "source":
                cell_balance.external_events.source = value
            elif "energy" in event_name and "cutoff" in event_name:
                cell_balance.external_events.energy_cutoff = value
            elif "time" in event_name and "cutoff" in event_name:
                cell_balance.external_events.time_cutoff = value
            elif event_name == "exiting":
                cell_balance.external_events.exiting = value
        
        elif self._parsing_state == "variance":
            if "weight" in event_name and "window" in event_name:
                cell_balance.variance_reduction.weight_window = value
            elif "cell" in event_name and "importance" in event_name:
                cell_balance.variance_reduction.cell_importance = value
            elif "weight" in event_name and "cutoff" in event_name:
                cell_balance.variance_reduction.weight_cutoff = value
            elif "e or t importance" in event_name:
                cell_balance.variance_reduction.e_or_t_importance = value
            elif event_name == "dxtran":
                cell_balance.variance_reduction.dxtran = value
            elif "forced" in event_name:
                cell_balance.variance_reduction.forced_collisions = value
            elif "exp." in event_name or "transform" in event_name:
                cell_balance.variance_reduction.exp_transform = value
        
        elif self._parsing_state == "physical":
            if event_name == "capture":
                cell_balance.physical_events.capture = value
            elif event_name == "(n,xn)":
                cell_balance.physical_events.n_xn = value
            elif "loss" in event_name and "(n,xn)" in event_name:
                cell_balance.physical_events.loss_to_n_xn = value
            elif event_name == "fission":
                cell_balance.physical_events.fission = value
            elif "loss" in event_name and "fission" in event_name:
                cell_balance.physical_events.loss_to_fission = value
            elif event_name == "photonuclear":
                cell_balance.physical_events.photonuclear = value
            elif "nucl." in event_name and "interaction" in event_name:
                cell_balance.physical_events.nucl_interaction = value
            elif "tabular" in event_name and "boundary" in event_name:
                cell_balance.physical_events.tabular_boundary = value
            elif "decay" in event_name and "gain" in event_name:
                cell_balance.physical_events.decay_gain = value
            elif "tabular" in event_name and "sampling" in event_name:
                cell_balance.physical_events.tabular_sampling = value
            elif "decay" in event_name and "loss" in event_name:
                cell_balance.physical_events.decay_loss = value
            elif event_name == "photofission":
                cell_balance.physical_events.photofission = value
    
    def _set_section_total(self, cell_num: int, value: float):
        """Set section total for a specific cell."""
        if cell_num not in self.cell_balances:
            return
        
        cell_balance = self.cell_balances[cell_num]
        
        if self._parsing_state == "external":
            cell_balance.external_events.total = value
        elif self._parsing_state == "variance":
            cell_balance.variance_reduction.total = value
        elif self._parsing_state == "physical":
            cell_balance.physical_events.total = value
    
    def _set_total_value(self, event_name: str, value: float):
        """Set event value for totals."""
        if self.totals is None:
            self.totals = WeightBalanceTotals()
        
        if self._parsing_state == "external":
            if event_name == "entering":
                self.totals.external_events.entering = value
            elif event_name == "source":
                self.totals.external_events.source = value
            elif "energy" in event_name and "cutoff" in event_name:
                self.totals.external_events.energy_cutoff = value
            elif "time" in event_name and "cutoff" in event_name:
                self.totals.external_events.time_cutoff = value
            elif event_name == "exiting":
                self.totals.external_events.exiting = value
        
        elif self._parsing_state == "variance":
            if "weight" in event_name and "window" in event_name:
                self.totals.variance_reduction.weight_window = value
            elif "cell" in event_name and "importance" in event_name:
                self.totals.variance_reduction.cell_importance = value
            elif "weight" in event_name and "cutoff" in event_name:
                self.totals.variance_reduction.weight_cutoff = value
            elif "e or t importance" in event_name:
                self.totals.variance_reduction.e_or_t_importance = value
            elif event_name == "dxtran":
                self.totals.variance_reduction.dxtran = value
            elif "forced" in event_name:
                self.totals.variance_reduction.forced_collisions = value
            elif "exp." in event_name or "transform" in event_name:
                self.totals.variance_reduction.exp_transform = value
        
        elif self._parsing_state == "physical":
            if event_name == "capture":
                self.totals.physical_events.capture = value
            elif event_name == "(n,xn)":
                self.totals.physical_events.n_xn = value
            elif "loss" in event_name and "(n,xn)" in event_name:
                self.totals.physical_events.loss_to_n_xn = value
            elif event_name == "fission":
                self.totals.physical_events.fission = value
            elif "loss" in event_name and "fission" in event_name:
                self.totals.physical_events.loss_to_fission = value
            elif event_name == "photonuclear":
                self.totals.physical_events.photonuclear = value
            elif "nucl." in event_name and "interaction" in event_name:
                self.totals.physical_events.nucl_interaction = value
            elif "tabular" in event_name and "boundary" in event_name:
                self.totals.physical_events.tabular_boundary = value
            elif "decay" in event_name and "gain" in event_name:
                self.totals.physical_events.decay_gain = value
            elif "tabular" in event_name and "sampling" in event_name:
                self.totals.physical_events.tabular_sampling = value
            elif "decay" in event_name and "loss" in event_name:
                self.totals.physical_events.decay_loss = value
            elif event_name == "photofission":
                self.totals.physical_events.photofission = value
    
    def _set_section_total_overall(self, value: float):
        """Set section total for overall totals."""
        if self.totals is None:
            self.totals = WeightBalanceTotals()
        
        if self._parsing_state == "external":
            self.totals.external_events.total = value
        elif self._parsing_state == "variance":
            self.totals.variance_reduction.total = value
        elif self._parsing_state == "physical":
            self.totals.physical_events.total = value
    
    def get_cell_balance(self, cell_number: int) -> Optional[CellWeightBalance]:
        """Get weight balance data for a specific cell."""
        return self.cell_balances.get(cell_number)
    
    def get_cells_with_activity(self) -> List[int]:
        """Get list of cell numbers that have any neutron activity."""
        active_cells = []
        for cell_num, balance in self.cell_balances.items():
            if (abs(balance.external_events.total) > 1e-10 or 
                abs(balance.variance_reduction.total) > 1e-10 or 
                abs(balance.physical_events.total) > 1e-10):
                active_cells.append(cell_num)
        return sorted(active_cells)
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        result = {
            'cell_balances': {},
            'totals': None
        }
        
        for cell_num, balance in self.cell_balances.items():
            result['cell_balances'][cell_num] = {
                'cell_number': balance.cell_number,
                'external_events': {
                    'entering': balance.external_events.entering,
                    'source': balance.external_events.source,
                    'energy_cutoff': balance.external_events.energy_cutoff,
                    'time_cutoff': balance.external_events.time_cutoff,
                    'exiting': balance.external_events.exiting,
                    'total': balance.external_events.total
                },
                'variance_reduction': {
                    'weight_window': balance.variance_reduction.weight_window,
                    'cell_importance': balance.variance_reduction.cell_importance,
                    'weight_cutoff': balance.variance_reduction.weight_cutoff,
                    'e_or_t_importance': balance.variance_reduction.e_or_t_importance,
                    'dxtran': balance.variance_reduction.dxtran,
                    'forced_collisions': balance.variance_reduction.forced_collisions,
                    'exp_transform': balance.variance_reduction.exp_transform,
                    'total': balance.variance_reduction.total
                },
                'physical_events': {
                    'capture': balance.physical_events.capture,
                    'n_xn': balance.physical_events.n_xn,
                    'loss_to_n_xn': balance.physical_events.loss_to_n_xn,
                    'fission': balance.physical_events.fission,
                    'loss_to_fission': balance.physical_events.loss_to_fission,
                    'photonuclear': balance.physical_events.photonuclear,
                    'nucl_interaction': balance.physical_events.nucl_interaction,
                    'tabular_boundary': balance.physical_events.tabular_boundary,
                    'decay_gain': balance.physical_events.decay_gain,
                    'tabular_sampling': balance.physical_events.tabular_sampling,
                    'decay_loss': balance.physical_events.decay_loss,
                    'photofission': balance.physical_events.photofission,
                    'total': balance.physical_events.total
                },
                'total': balance.total
            }
        
        if self.totals:
            result['totals'] = {
                'external_events': {
                    'entering': self.totals.external_events.entering,
                    'source': self.totals.external_events.source,
                    'energy_cutoff': self.totals.external_events.energy_cutoff,
                    'time_cutoff': self.totals.external_events.time_cutoff,
                    'exiting': self.totals.external_events.exiting,
                    'total': self.totals.external_events.total
                },
                'variance_reduction': {
                    'weight_window': self.totals.variance_reduction.weight_window,
                    'cell_importance': self.totals.variance_reduction.cell_importance,
                    'weight_cutoff': self.totals.variance_reduction.weight_cutoff,
                    'e_or_t_importance': self.totals.variance_reduction.e_or_t_importance,
                    'dxtran': self.totals.variance_reduction.dxtran,
                    'forced_collisions': self.totals.variance_reduction.forced_collisions,
                    'exp_transform': self.totals.variance_reduction.exp_transform,
                    'total': self.totals.variance_reduction.total
                },
                'physical_events': {
                    'capture': self.totals.physical_events.capture,
                    'n_xn': self.totals.physical_events.n_xn,
                    'loss_to_n_xn': self.totals.physical_events.loss_to_n_xn,
                    'fission': self.totals.physical_events.fission,
                    'loss_to_fission': self.totals.physical_events.loss_to_fission,
                    'photonuclear': self.totals.physical_events.photonuclear,
                    'nucl_interaction': self.totals.physical_events.nucl_interaction,
                    'tabular_boundary': self.totals.physical_events.tabular_boundary,
                    'decay_gain': self.totals.physical_events.decay_gain,
                    'tabular_sampling': self.totals.physical_events.tabular_sampling,
                    'decay_loss': self.totals.physical_events.decay_loss,
                    'photofission': self.totals.physical_events.photofission,
                    'total': self.totals.physical_events.total
                },
                'total': self.totals.total
            }
        
        return result


# Example usage:
if __name__ == "__main__":
    # This would be used with actual MCNP output lines
    parser = Table130Parser()
    # cell_balances, totals = parser.parse_lines(sample_lines)
    print("Table130Parser ready for use")