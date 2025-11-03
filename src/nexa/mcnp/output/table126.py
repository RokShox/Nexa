import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class NeutronActivity:
    """Data class representing neutron activity data from MCNP Table 126."""
    cell_number: int
    tracks_entering: int
    population: int
    collisions: int
    collisions_weight_per_history: float
    number_weighted_energy: float
    flux_weighted_energy: float
    average_track_weight: float
    average_track_mfp: float


@dataclass
class NeutronActivityTotal:
    """Data class representing total neutron activity from MCNP Table 126."""
    total_tracks_entering: int
    total_population: int
    total_collisions: int
    total_collisions_weight: float


class Table126Parser:
    """Parser for MCNP output Table 126 - Neutron activity in each cell."""
    
    def __init__(self):
        self.activities: List[NeutronActivity] = []
        self.total: Optional[NeutronActivityTotal] = None
        self._header_found = False
        self._data_section = False
    
    def parse_lines(self, lines: List[str]) -> tuple[List[NeutronActivity], Optional[NeutronActivityTotal]]:
        """
        Parse lines from MCNP output containing Table 126 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Tuple of (list of NeutronActivity objects, NeutronActivityTotal object or None)
        """
        self.activities.clear()
        self.total = None
        self._header_found = False
        self._data_section = False
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_column_header(line):
                    self._data_section = True
                    continue
                
                if self._data_section:
                    if self._is_total_line(line):
                        self.total = self._parse_total_line(line)
                        break
                    
                    if self._is_data_line(line):
                        activity = self._parse_activity_line(line)
                        if activity:
                            self.activities.append(activity)
        
        return self.activities, self.total
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 126 header."""
        return "neutron  activity in each cell" in line.lower() and "print table 126" in line.lower()
    
    def _is_column_header(self, line: str) -> bool:
        """Check if line contains column headers."""
        return "cell" in line.lower() and "tracks" in line.lower() and "population" in line.lower()
    
    def _is_total_line(self, line: str) -> bool:
        """Check if line contains the total summary."""
        stripped = line.strip()
        return stripped.lower().startswith("total")
    
    def _is_data_line(self, line: str) -> bool:
        """Check if line contains cell activity data."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Look for lines that start with two numbers (cell index and cell number)
        pattern = r'^\s*\d+\s+\d+\s+'
        return bool(re.match(pattern, stripped))
    
    def _parse_activity_line(self, line: str) -> Optional[NeutronActivity]:
        """
        Parse a single line containing neutron activity data.
        
        Args:
            line: String containing activity data
            
        Returns:
            NeutronActivity object or None if parsing fails
        """
        try:
            parts = line.strip().split()
            
            if len(parts) < 10:
                return None
            
            # Skip the first column (index) and use the second as cell number
            cell_number = int(parts[1])
            tracks_entering = int(parts[2])
            population = int(parts[3])
            collisions = int(parts[4])
            collisions_weight_per_history = self._parse_scientific_notation(parts[5])
            number_weighted_energy = self._parse_scientific_notation(parts[6])
            flux_weighted_energy = self._parse_scientific_notation(parts[7])
            average_track_weight = self._parse_scientific_notation(parts[8])
            average_track_mfp = self._parse_scientific_notation(parts[9])
            
            return NeutronActivity(
                cell_number=cell_number,
                tracks_entering=tracks_entering,
                population=population,
                collisions=collisions,
                collisions_weight_per_history=collisions_weight_per_history,
                number_weighted_energy=number_weighted_energy,
                flux_weighted_energy=flux_weighted_energy,
                average_track_weight=average_track_weight,
                average_track_mfp=average_track_mfp
            )
            
        except (ValueError, IndexError) as e:
            print(f"Error parsing line: {line.strip()} - {e}")
            return None
    
    def _parse_total_line(self, line: str) -> Optional[NeutronActivityTotal]:
        """
        Parse the total line.
        
        Args:
            line: String containing total data
            
        Returns:
            NeutronActivityTotal object or None if parsing fails
        """
        try:
            parts = line.strip().split()
            
            if len(parts) < 5:
                return None
            
            # Skip "total" and parse the numeric values
            total_tracks_entering = int(parts[1])
            total_population = int(parts[2])
            total_collisions = int(parts[3])
            total_collisions_weight = self._parse_scientific_notation(parts[4])
            
            return NeutronActivityTotal(
                total_tracks_entering=total_tracks_entering,
                total_population=total_population,
                total_collisions=total_collisions,
                total_collisions_weight=total_collisions_weight
            )
            
        except (ValueError, IndexError) as e:
            print(f"Error parsing total line: {line.strip()} - {e}")
            return None
    
    def _parse_scientific_notation(self, value_str: str) -> float:
        """
        Parse scientific notation string to float.
        
        Args:
            value_str: String in format like '0.0000E+00' or '1.4997E+00'
            
        Returns:
            Float value
        """
        return float(value_str)
    
    def get_activity_by_cell(self, cell_number: int) -> Optional[NeutronActivity]:
        """Get neutron activity data for a specific cell."""
        for activity in self.activities:
            if activity.cell_number == cell_number:
                return activity
        return None
    
    def get_cells_with_activity(self) -> List[int]:
        """Get list of cell numbers that have neutron activity."""
        return [activity.cell_number for activity in self.activities 
                if activity.tracks_entering > 0 or activity.population > 0 or activity.collisions > 0]
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        result = {
            'activities': [
                {
                    'cell_number': a.cell_number,
                    'tracks_entering': a.tracks_entering,
                    'population': a.population,
                    'collisions': a.collisions,
                    'collisions_weight_per_history': a.collisions_weight_per_history,
                    'number_weighted_energy': a.number_weighted_energy,
                    'flux_weighted_energy': a.flux_weighted_energy,
                    'average_track_weight': a.average_track_weight,
                    'average_track_mfp': a.average_track_mfp
                }
                for a in self.activities
            ]
        }
        
        if self.total:
            result['total'] = {
                'total_tracks_entering': self.total.total_tracks_entering,
                'total_population': self.total.total_population,
                'total_collisions': self.total.total_collisions,
                'total_collisions_weight': self.total.total_collisions_weight
            }
        
        return result


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1neutron  activity in each cell                                                                         print table 126",
        "",
        "                       tracks     population   collisions   collisions     number        flux        average      average",
        "              cell    entering                               * weight     weighted     weighted   track weight   track mfp",
        "                                                          (per history)    energy       energy     (relative)      (cm)",
        "",
        "        1        1           0            0            0    0.0000E+00   0.0000E+00   0.0000E+00   0.0000E+00   0.0000E+00",
        "        2        2           0            0            0    0.0000E+00   0.0000E+00   0.0000E+00   0.0000E+00   0.0000E+00",
        "        3        3           0            0            0    0.0000E+00   0.0000E+00   0.0000E+00   0.0000E+00   0.0000E+00",
        "        4        4   183985067     74814275    180279774    1.4997E+00   9.5163E-04   6.7188E-01   8.8602E-01   2.3118E+00",
        "        5        5    39066739      3934658     14317404    1.2212E-01   1.5206E-03   7.6806E-01   8.8847E-01   2.5846E+00",
        "        6        6    72730745      3895070           86    8.0046E-07   1.3385E-03   7.4036E-01   8.8724E-01   2.5996E+04",
        "        7        7    78588135      3907144      2757103    2.4503E-02   1.2913E-03   7.3161E-01   8.8709E-01   3.7090E+00",
        "        8        8   112265465      3921553     40659870    3.3791E-01   1.1528E-03   7.1114E-01   8.8686E-01   2.3117E+00",
        "        9        9      219421       184271       217512    1.8142E-03   9.0431E-04   6.7713E-01   8.8775E-01   2.3158E+00",
        "",
        "           total   13072666372   1071815183   4631876755    3.5733E+01"
    ]
    
    parser = Table126Parser()
    activities, total = parser.parse_lines(sample_lines)
    
    print(f"Found {len(activities)} cell activities:")
    for activity in activities:
        if activity.tracks_entering > 0:  # Only show cells with activity
            print(f"  Cell {activity.cell_number}: {activity.tracks_entering} tracks, "
                  f"{activity.population} population, {activity.collisions} collisions")
    
    if total:
        print(f"\nTotal: {total.total_tracks_entering} tracks, "
              f"{total.total_population} population, {total.total_collisions} collisions")
    
    print(f"\nCells with activity: {parser.get_cells_with_activity()}")