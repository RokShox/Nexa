import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ParticleEnergyLimit:
    """Data class representing particle energy limits from MCNP Table 101."""
    particle_num: int
    particle_symbol: str
    particle_name: str
    cutoff_energy: float
    maximum_particle_energy: float
    smallest_table_maximum: float
    largest_table_maximum: float
    always_use_table_below: float
    always_use_model_above: float


class Table101Parser:
    """Parser for MCNP output Table 101 - Particles and Energy Limits."""
    
    def __init__(self):
        self.particles: List[ParticleEnergyLimit] = []
        self._header_found = False
    
    def parse_lines(self, lines: List[str]) -> List[ParticleEnergyLimit]:
        """
        Parse lines from MCNP output containing Table 101 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            List of ParticleEnergyLimit objects
        """
        self.particles.clear()
        self._header_found = False
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found and self._is_data_line(line):
                particle = self._parse_particle_line(line)
                if particle:
                    self.particles.append(particle)
        
        return self.particles
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 101 header."""
        return "particles and energy limits" in line.lower() and "print table 101" in line.lower()
    
    def _is_data_line(self, line: str) -> bool:
        """Check if line contains particle data."""
        # Look for lines that start with a number followed by particle symbol
        pattern = r'^\s*\d+\s+[a-z]+\s+'
        return bool(re.match(pattern, line.strip()))
    
    def _parse_particle_line(self, line: str) -> Optional[ParticleEnergyLimit]:
        """
        Parse a single line containing particle energy limit data.
        
        Args:
            line: String containing particle data
            
        Returns:
            ParticleEnergyLimit object or None if parsing fails
        """
        try:
            # Split the line into components
            parts = line.strip().split()
            
            if len(parts) < 9:
                return None
            
            particle_num = int(parts[0])
            particle_symbol = parts[1]
            particle_name = parts[2]
            
            # Parse energy values (in scientific notation)
            cutoff_energy = self._parse_scientific_notation(parts[3])
            maximum_particle_energy = self._parse_scientific_notation(parts[4])
            smallest_table_maximum = self._parse_scientific_notation(parts[5])
            largest_table_maximum = self._parse_scientific_notation(parts[6])
            always_use_table_below = self._parse_scientific_notation(parts[7])
            always_use_model_above = self._parse_scientific_notation(parts[8])
            
            return ParticleEnergyLimit(
                particle_num=particle_num,
                particle_symbol=particle_symbol,
                particle_name=particle_name,
                cutoff_energy=cutoff_energy,
                maximum_particle_energy=maximum_particle_energy,
                smallest_table_maximum=smallest_table_maximum,
                largest_table_maximum=largest_table_maximum,
                always_use_table_below=always_use_table_below,
                always_use_model_above=always_use_model_above
            )
            
        except (ValueError, IndexError) as e:
            print(f"Error parsing line: {line.strip()} - {e}")
            return None
    
    def _parse_scientific_notation(self, value_str: str) -> float:
        """
        Parse scientific notation string to float.
        
        Args:
            value_str: String in format like '0.0000E+00' or '2.0000E+02'
            
        Returns:
            Float value
        """
        return float(value_str)
    
    def get_particle_by_symbol(self, symbol: str) -> Optional[ParticleEnergyLimit]:
        """Get particle data by symbol (e.g., 'n' for neutron)."""
        for particle in self.particles:
            if particle.particle_symbol == symbol:
                return particle
        return None
    
    def get_particle_by_number(self, num: int) -> Optional[ParticleEnergyLimit]:
        """Get particle data by particle number."""
        for particle in self.particles:
            if particle.particle_num == num:
                return particle
        return None
    
    def to_dict(self) -> List[Dict]:
        """Convert parsed data to list of dictionaries."""
        return [
            {
                'particle_num': p.particle_num,
                'particle_symbol': p.particle_symbol,
                'particle_name': p.particle_name,
                'cutoff_energy': p.cutoff_energy,
                'maximum_particle_energy': p.maximum_particle_energy,
                'smallest_table_maximum': p.smallest_table_maximum,
                'largest_table_maximum': p.largest_table_maximum,
                'always_use_table_below': p.always_use_table_below,
                'always_use_model_above': p.always_use_model_above
            }
            for p in self.particles
        ]


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        "1particles and energy limits                                                                            print table 101",
        "",
        "                         particle      maximum       smallest      largest       always        always",
        "                         cutoff        particle      table         table         use table     use model",
        "   particle type         energy        energy        maximum       maximum       below         above",
        "",
        "    1  n    neutron     0.0000E+00    2.0000E+02    2.0000E+01    2.0000E+02    1.0000E+36    1.0000E+36"
    ]
    
    parser = Table101Parser()
    particles = parser.parse_lines(sample_lines)
    
    for particle in particles:
        print(f"Particle: {particle.particle_name} ({particle.particle_symbol})")
        print(f"  Cutoff Energy: {particle.cutoff_energy}")
        print(f"  Max Particle Energy: {particle.maximum_particle_energy}")