import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class EstimatorData:
    """Data class for individual estimator (collision, absorption, track-length)."""
    current_cycle_value: float
    cumulative_average: float
    uncertainty: float


@dataclass
class CombinationData:
    """Data class for combination estimates."""
    simple_average: float
    simple_uncertainty: float
    combined_average: float
    combined_uncertainty: float
    correlation: Optional[float] = None


@dataclass
class CycleData:
    """Data class representing k-effective and lifetime data for one cycle."""
    cycle: int
    active_cycles: int  # Number of active cycles averaged
    
    # Individual estimators
    k_collision: Optional[EstimatorData] = None
    k_absorption: Optional[EstimatorData] = None
    k_track_length: Optional[EstimatorData] = None
    rem_life_collision: Optional[EstimatorData] = None
    rem_life_absorption: Optional[EstimatorData] = None
    
    # Combination estimates
    k_col_abs: Optional[CombinationData] = None
    k_abs_tk_ln: Optional[CombinationData] = None
    k_tk_ln_col: Optional[CombinationData] = None
    k_col_abs_tk_ln: Optional[CombinationData] = None
    life_col_abs_tl: Optional[CombinationData] = None
    
    # Additional data
    source_points_generated: Optional[int] = None
    source_entropy: Optional[float] = None


@dataclass
class SkippedCycleData:
    """Data class for cycles that are skipped (before active cycles)."""
    cycle: int
    k_collision: Optional[float] = None
    prompt_removal_lifetime_abs: Optional[float] = None
    source_points_generated: Optional[int] = None
    source_entropy: Optional[float] = None


class Table175Parser:
    """Parser for MCNP output Table 175 - Estimated k-effective results by cycle."""
    
    def __init__(self):
        self.active_cycles: Dict[int, CycleData] = {}
        self.skipped_cycles: Dict[int, SkippedCycleData] = {}
        self._header_found = False
        self._in_estimator_block = False
        self._current_cycle_data = None
    
    def parse_lines(self, lines: List[str]) -> Tuple[Dict[int, CycleData], Dict[int, SkippedCycleData]]:
        """
        Parse lines from MCNP output containing Table 175 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Tuple of (active_cycles_dict, skipped_cycles_dict)
        """
        self.active_cycles.clear()
        self.skipped_cycles.clear()
        self._header_found = False
        self._in_estimator_block = False
        self._current_cycle_data = None
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                # Skip dump and source distribution lines
                if self._is_dump_or_source_line(line):
                    continue
                
                if self._is_skipped_cycle_line(line):
                    skipped_data = self._parse_skipped_cycle_line(line)
                    if skipped_data:
                        self.skipped_cycles[skipped_data.cycle] = skipped_data
                    continue
                
                if self._is_estimator_header_line(line):
                    cycle_info = self._parse_estimator_header(line)
                    if cycle_info:
                        cycle, active_cycles = cycle_info
                        self._current_cycle_data = CycleData(cycle=cycle, active_cycles=active_cycles)
                        self._in_estimator_block = True
                    continue
                
                if self._in_estimator_block:
                    if self._is_estimator_data_line(line):
                        self._parse_estimator_data_line(line)
                        continue
                    
                    if self._is_source_points_line(line):
                        self._parse_source_points_line(line)
                        # End of estimator block
                        if self._current_cycle_data:
                            self.active_cycles[self._current_cycle_data.cycle] = self._current_cycle_data
                        self._in_estimator_block = False
                        self._current_cycle_data = None
                        continue
        
        return self.active_cycles, self.skipped_cycles
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 175 header."""
        return "estimated keff results by cycle" in line.lower() and "print table 175" in line.lower()
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        stripped = line.strip()
        if not stripped:
            return False
        
        return ("print table" in line.lower() and "table 175" not in line.lower()) or \
               line.startswith("1") and any(x in line.lower() for x in [
                   "probid", "keff results", "run terminated"
               ])
    
    def _is_dump_or_source_line(self, line: str) -> bool:
        """Check if line is a dump or source distribution line to ignore."""
        return ("source distribution written to file" in line.lower() or 
                "dump no." in line.lower() or
                line.strip().startswith("*"))
    
    def _is_skipped_cycle_line(self, line: str) -> bool:
        """Check if line represents a skipped cycle."""
        return ("cycle" in line and "k(collision)" in line and 
                "prompt removal lifetime(abs)" in line and 
                "estimator" not in line)
    
    def _parse_skipped_cycle_line(self, line: str) -> Optional[SkippedCycleData]:
        """Parse a skipped cycle line."""
        try:
            # Extract cycle number
            cycle_match = re.search(r"cycle\s+(\d+)", line)
            if not cycle_match:
                return None
            cycle = int(cycle_match.group(1))
            
            # Extract k(collision)
            k_coll_match = re.search(r"k\(collision\)\s+([\d.E+-]+)", line)
            k_collision = float(k_coll_match.group(1)) if k_coll_match else None
            
            # Extract prompt removal lifetime
            lifetime_match = re.search(r"prompt removal lifetime\(abs\)\s+([\d.E+-]+)", line)
            lifetime = float(lifetime_match.group(1)) if lifetime_match else None
            
            # Extract source points
            points_match = re.search(r"source points generated\s+(\d+)", line)
            source_points = int(points_match.group(1)) if points_match else None
            
            # Check next line for source entropy
            source_entropy = None
            
            return SkippedCycleData(
                cycle=cycle,
                k_collision=k_collision,
                prompt_removal_lifetime_abs=lifetime,
                source_points_generated=source_points,
                source_entropy=source_entropy
            )
            
        except (ValueError, AttributeError):
            return None
    
    def _is_estimator_header_line(self, line: str) -> bool:
        """Check if line is an estimator block header."""
        return line.strip().startswith("estimator") and "cycle" in line and "ave of" in line
    
    def _parse_estimator_header(self, line: str) -> Optional[Tuple[int, int]]:
        """Parse estimator header to get cycle and active cycles count."""
        try:
            # Pattern: "estimator     cycle   300   ave of   100 cycles"
            match = re.search(r"cycle\s+(\d+)\s+ave of\s+(\d+) cycles", line)
            if match:
                cycle = int(match.group(1))
                active_cycles = int(match.group(2))
                return cycle, active_cycles
        except (ValueError, AttributeError):
            pass
        return None
    
    def _is_estimator_data_line(self, line: str) -> bool:
        """Check if line contains estimator data."""
        stripped = line.strip()
        return any(est in stripped for est in [
            "k(collision)", "k(absorption)", "k(trk length)", 
            "rem life(col)", "rem life(abs)",
            "k(col/abs)", "k(abs/tk ln)", "k(tk ln/col)", 
            "k(col/abs/tk ln)", "life(col/abs/tl)"
        ])
    
    def _parse_estimator_data_line(self, line: str) -> None:
        """Parse estimator data line and update current cycle data."""
        if not self._current_cycle_data:
            return
        
        stripped = line.strip()
        
        # Individual estimators (left side)
        if "k(collision)" in stripped:
            self._current_cycle_data.k_collision = self._parse_individual_estimator(stripped)
        elif "k(absorption)" in stripped:
            self._current_cycle_data.k_absorption = self._parse_individual_estimator(stripped)
        elif "k(trk length)" in stripped:
            self._current_cycle_data.k_track_length = self._parse_individual_estimator(stripped)
        elif "rem life(col)" in stripped:
            self._current_cycle_data.rem_life_collision = self._parse_individual_estimator(stripped)
        elif "rem life(abs)" in stripped:
            self._current_cycle_data.rem_life_absorption = self._parse_individual_estimator(stripped)
        
        # Combination estimators (right side)
        elif "k(col/abs)" in stripped and "k(col/abs/tk ln)" not in stripped:
            self._current_cycle_data.k_col_abs = self._parse_combination_estimator(stripped)
        elif "k(abs/tk ln)" in stripped:
            self._current_cycle_data.k_abs_tk_ln = self._parse_combination_estimator(stripped)
        elif "k(tk ln/col)" in stripped:
            self._current_cycle_data.k_tk_ln_col = self._parse_combination_estimator(stripped)
        elif "k(col/abs/tk ln)" in stripped:
            self._current_cycle_data.k_col_abs_tk_ln = self._parse_combination_estimator(stripped)
        elif "life(col/abs/tl)" in stripped:
            self._current_cycle_data.life_col_abs_tl = self._parse_combination_estimator(stripped)
    
    def _parse_individual_estimator(self, line: str) -> Optional[EstimatorData]:
        """Parse individual estimator line."""
        try:
            # Extract numeric values (should be 3: current, average, uncertainty)
            numbers = re.findall(r'[\d.E+-]+', line)
            if len(numbers) >= 3:
                current = float(numbers[0])
                average = float(numbers[1])
                uncertainty = float(numbers[2])
                return EstimatorData(
                    current_cycle_value=current,
                    cumulative_average=average,
                    uncertainty=uncertainty
                )
        except (ValueError, IndexError):
            pass
        return None
    
    def _parse_combination_estimator(self, line: str) -> Optional[CombinationData]:
        """Parse combination estimator line."""
        try:
            # Extract numeric values after the combination name
            # Pattern: simple_avg simple_unc combined_avg combined_unc [correlation]
            numbers = re.findall(r'[\d.E+-]+', line)
            if len(numbers) >= 4:
                simple_avg = float(numbers[0])
                simple_unc = float(numbers[1])
                combined_avg = float(numbers[2])
                combined_unc = float(numbers[3])
                correlation = float(numbers[4]) if len(numbers) > 4 else None
                
                return CombinationData(
                    simple_average=simple_avg,
                    simple_uncertainty=simple_unc,
                    combined_average=combined_avg,
                    combined_uncertainty=combined_unc,
                    correlation=correlation
                )
        except (ValueError, IndexError):
            pass
        return None
    
    def _is_source_points_line(self, line: str) -> bool:
        """Check if line contains source points generated."""
        return "source points generated" in line
    
    def _parse_source_points_line(self, line: str) -> None:
        """Parse source points and entropy line."""
        if not self._current_cycle_data:
            return
        
        # Extract source points generated
        points_match = re.search(r"source points generated\s+(\d+)", line)
        if points_match:
            self._current_cycle_data.source_points_generated = int(points_match.group(1))
        
        # Extract source entropy
        entropy_match = re.search(r"source_entropy\s+([\d.E+-]+)", line)
        if entropy_match:
            self._current_cycle_data.source_entropy = float(entropy_match.group(1))
    
    def get_cycle_data(self, cycle: int) -> Optional[CycleData]:
        """Get active cycle data for a specific cycle."""
        return self.active_cycles.get(cycle)
    
    def get_skipped_cycle_data(self, cycle: int) -> Optional[SkippedCycleData]:
        """Get skipped cycle data for a specific cycle."""
        return self.skipped_cycles.get(cycle)
    
    def get_all_active_cycles(self) -> List[int]:
        """Get list of all active cycle numbers."""
        return sorted(list(self.active_cycles.keys()))
    
    def get_all_skipped_cycles(self) -> List[int]:
        """Get list of all skipped cycle numbers."""
        return sorted(list(self.skipped_cycles.keys()))
    
    def get_final_k_effective(self) -> Optional[float]:
        """Get the final k-effective estimate (combined average from last cycle)."""
        if not self.active_cycles:
            return None
        
        last_cycle = max(self.active_cycles.keys())
        cycle_data = self.active_cycles[last_cycle]
        
        if cycle_data.k_col_abs_tk_ln:
            return cycle_data.k_col_abs_tk_ln.combined_average
        return None
    
    def get_final_k_effective_uncertainty(self) -> Optional[float]:
        """Get the final k-effective uncertainty."""
        if not self.active_cycles:
            return None
        
        last_cycle = max(self.active_cycles.keys())
        cycle_data = self.active_cycles[last_cycle]
        
        if cycle_data.k_col_abs_tk_ln:
            return cycle_data.k_col_abs_tk_ln.combined_uncertainty
        return None
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        return {
            'active_cycles': {
                cycle: {
                    'cycle': data.cycle,
                    'active_cycles': data.active_cycles,
                    'k_collision': {
                        'current_cycle_value': data.k_collision.current_cycle_value,
                        'cumulative_average': data.k_collision.cumulative_average,
                        'uncertainty': data.k_collision.uncertainty
                    } if data.k_collision else None,
                    'k_absorption': {
                        'current_cycle_value': data.k_absorption.current_cycle_value,
                        'cumulative_average': data.k_absorption.cumulative_average,
                        'uncertainty': data.k_absorption.uncertainty
                    } if data.k_absorption else None,
                    'k_track_length': {
                        'current_cycle_value': data.k_track_length.current_cycle_value,
                        'cumulative_average': data.k_track_length.cumulative_average,
                        'uncertainty': data.k_track_length.uncertainty
                    } if data.k_track_length else None,
                    'source_points_generated': data.source_points_generated,
                    'source_entropy': data.source_entropy,
                    # Add combination data...
                }
                for cycle, data in self.active_cycles.items()
            },
            'skipped_cycles': {
                cycle: {
                    'cycle': data.cycle,
                    'k_collision': data.k_collision,
                    'prompt_removal_lifetime_abs': data.prompt_removal_lifetime_abs,
                    'source_points_generated': data.source_points_generated,
                    'source_entropy': data.source_entropy
                }
                for cycle, data in self.skipped_cycles.items()
            }
        }


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1estimated keff results by cycle                                                                        print table 175",
        "",
        " cycle   100    k(collision)  0.997325    prompt removal lifetime(abs)  2.7475E+03    source points generated  99775",
        "                                          source_entropy =      0.93680",
        "",
        "  estimator     cycle   300   ave of   100 cycles      combination         simple average    combined average     corr",
        " k(collision)      0.999363       0.999931 0.0003     k(col/abs)          0.999901 0.0003     0.999885 0.0003   0.6312",
        " k(absorption)     0.995224       0.999870 0.0003     k(abs/tk ln)        0.999817 0.0003     0.999847 0.0003   0.4617",
        " k(trk length)     1.002570       0.999763 0.0004     k(tk ln/col)        0.999847 0.0003     0.999892 0.0003   0.7563",
        " rem life(col)   2.7198E+03     2.7088E+03 0.0007     k(col/abs/tk ln)    0.999855 0.0003     0.999857 0.0003",
        " rem life(abs)   2.7337E+03     2.7091E+03 0.0006     life(col/abs/tl)  2.7102E+03 0.0006   2.7145E+03 0.0005",
        " source points generated 100474                source_entropy   0.93720"
    ]
    
    parser = Table175Parser()
    active_cycles, skipped_cycles = parser.parse_lines(sample_lines)
    
    print(f"Found {len(skipped_cycles)} skipped cycles and {len(active_cycles)} active cycles")
    
    print(f"\nSkipped cycles:")
    for cycle, data in skipped_cycles.items():
        print(f"  Cycle {cycle}: k={data.k_collision:.6f}")
    
    print(f"\nActive cycles:")
    for cycle, data in active_cycles.items():
        print(f"  Cycle {cycle} (ave of {data.active_cycles}):")
        if data.k_collision:
            print(f"    k(collision): {data.k_collision.cumulative_average:.6f} ± {data.k_collision.uncertainty:.4f}")
        if data.k_col_abs_tk_ln:
            print(f"    k(combined): {data.k_col_abs_tk_ln.combined_average:.6f} ± {data.k_col_abs_tk_ln.combined_uncertainty:.4f}")
    
    final_k = parser.get_final_k_effective()
    final_unc = parser.get_final_k_effective_uncertainty()
    if final_k:
        print(f"\nFinal k-effective: {final_k:.6f} ± {final_unc:.4f}")