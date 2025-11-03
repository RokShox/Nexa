import re
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ParticlePoint:
    """Data class representing a particle position in the geometry hierarchy."""
    x: float
    y: float
    z: float
    r: float  # Distance from origin: sqrt(x^2 + y^2 + z^2)
    cell: int
    lattice_indices: Optional[Tuple[int, int, int]] = None  # [i, j, k] if in lattice
    surface: Optional[int] = None
    u: float = 0.0  # Direction cosine
    v: float = 0.0  # Direction cosine
    w: float = 0.0  # Direction cosine


@dataclass
class SourceParticle:
    """Data class representing a complete source particle with geometry hierarchy."""
    nps: int  # Particle number
    energy: float
    weight: float
    time: float
    points: List[ParticlePoint] = field(default_factory=list)  # Geometry hierarchy
    
    @property
    def birth_point(self) -> Optional[ParticlePoint]:
        """Get the birth point (first point in hierarchy)."""
        return self.points[0] if self.points else None


class Table110Parser:
    """Parser for MCNP output Table 110 - Starting source particles."""
    
    def __init__(self):
        self.particles: Dict[int, SourceParticle] = {}
        self._header_found = False
        self._current_particle = None
    
    def parse_lines(self, lines: List[str]) -> Dict[int, SourceParticle]:
        """
        Parse lines from MCNP output containing Table 110 data.
        
        Args:
            lines: List of strings from MCNP output file
            
        Returns:
            Dictionary mapping nps -> SourceParticle
        """
        self.particles.clear()
        self._header_found = False
        self._current_particle = None
        
        for line in lines:
            if self._is_table_header(line):
                self._header_found = True
                continue
            
            if self._header_found:
                if self._is_end_of_table(line):
                    break
                
                if self._is_column_header(line):
                    continue
                
                if self._is_particle_start_line(line):
                    particle_data = self._parse_particle_start_line(line)
                    if particle_data:
                        nps, point, energy, weight, time = particle_data
                        self._current_particle = SourceParticle(
                            nps=nps,
                            energy=energy,
                            weight=weight,
                            time=time
                        )
                        self._current_particle.points.append(point)
                        self.particles[nps] = self._current_particle
                    continue
                
                if self._is_geometry_continuation_line(line):
                    if self._current_particle:
                        point = self._parse_geometry_line(line)
                        if point:
                            self._current_particle.points.append(point)
                    continue
        
        return self.particles
    
    def _is_table_header(self, line: str) -> bool:
        """Check if line contains the table 110 header."""
        # Table 110 may not have an explicit "print table 110" but has characteristic header
        return line.strip().startswith("nps") and "x" in line and "y" in line and "z" in line and "cell" in line
    
    def _is_end_of_table(self, line: str) -> bool:
        """Check if line marks the end of the table."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Look for next table or other indicators
        return ("print table" in line.lower()) or \
               line.startswith("1") and any(x in line.lower() for x in [
                   "probid", "keff results", "run terminated", "neutron creation", 
                   "neutron loss", "neutron activity", "weight balance"
               ])
    
    def _is_column_header(self, line: str) -> bool:
        """Check if line contains column headers."""
        return "nps" in line.lower() and "cell" in line.lower() and "energy" in line.lower()
    
    def _is_particle_start_line(self, line: str) -> bool:
        """Check if line starts a new particle (contains energy, weight, time)."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Should start with a number and have energy, weight, time at the end
        parts = stripped.split()
        if len(parts) >= 10:  # Minimum expected for full particle line
            try:
                int(parts[0])  # nps
                # Check if we have energy, weight, time at the end
                float(parts[-3])  # energy
                float(parts[-2])  # weight
                float(parts[-1])  # time
                return True
            except (ValueError, IndexError):
                pass
        
        return False
    
    def _is_geometry_continuation_line(self, line: str) -> bool:
        """Check if line is a geometry continuation (no nps, energy, weight, time)."""
        stripped = line.strip()
        if not stripped:
            return False
        
        # Should have coordinates and cell but no energy/weight/time
        parts = stripped.split()
        if len(parts) >= 7 and len(parts) < 10:  # Geometry lines are shorter
            try:
                float(parts[0])  # x
                float(parts[1])  # y
                float(parts[2])  # z
                int(parts[3])    # cell (or part of it)
                return True
            except (ValueError, IndexError):
                pass
        
        return False
    
    def _calculate_r(self, x: float, y: float, z: float) -> float:
        """Calculate distance from origin."""
        return math.sqrt(x*x + y*y + z*z)
    
    def _parse_lattice_indices(self, cell_field: str) -> Tuple[Optional[int], Optional[Tuple[int, int, int]]]:
        """
        Parse cell field that may contain lattice indices.
        
        Args:
            cell_field: String like "1483[   2    1    0]" or just "232"
            
        Returns:
            Tuple of (cell_number, lattice_indices)
        """
        # Look for pattern like "1483[   2    1    0]"
        lattice_match = re.match(r'(\d+)\[\s*(\d+)\s+(\d+)\s+(\d+)\s*\]', cell_field)
        if lattice_match:
            cell = int(lattice_match.group(1))
            i = int(lattice_match.group(2))
            j = int(lattice_match.group(3))
            k = int(lattice_match.group(4))
            return cell, (i, j, k)
        
        # Just a cell number
        try:
            cell = int(cell_field)
            return cell, None
        except ValueError:
            return None, None
    
    def _parse_particle_start_line(self, line: str) -> Optional[Tuple[int, ParticlePoint, float, float, float]]:
        """Parse the first line of a particle (contains nps and full data)."""
        try:
            parts = line.strip().split()
            if len(parts) < 10:
                return None
            
            nps = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            z = float(parts[3])
            r = self._calculate_r(x, y, z)
            
            # Parse cell (may have lattice info)
            cell, lattice_indices = self._parse_lattice_indices(parts[4])
            if cell is None:
                return None
            
            # Find where surface starts (look for optional surface number)
            surface = None
            direction_start = 5
            
            # Check if next field is a surface number or direction
            if len(parts) > 5:
                try:
                    # If it's a number and not too large, it might be a surface
                    potential_surface = int(parts[5])
                    if abs(potential_surface) < 10000:  # Reasonable surface number
                        surface = potential_surface
                        direction_start = 6
                except ValueError:
                    pass
            
            # Parse direction cosines
            u = float(parts[direction_start])
            v = float(parts[direction_start + 1])
            w = float(parts[direction_start + 2])
            
            # Parse energy, weight, time (last 3 fields)
            energy = float(parts[-3])
            weight = float(parts[-2])
            time = float(parts[-1])
            
            point = ParticlePoint(
                x=x, y=y, z=z, r=r,
                cell=cell,
                lattice_indices=lattice_indices,
                surface=surface,
                u=u, v=v, w=w
            )
            
            return nps, point, energy, weight, time
            
        except (ValueError, IndexError):
            return None
    
    def _parse_geometry_line(self, line: str) -> Optional[ParticlePoint]:
        """Parse a geometry continuation line."""
        try:
            parts = line.strip().split()
            if len(parts) < 7:
                return None
            
            x = float(parts[0])
            y = float(parts[1])
            z = float(parts[2])
            r = self._calculate_r(x, y, z)
            
            # Parse cell (may have lattice info)
            cell, lattice_indices = self._parse_lattice_indices(parts[3])
            if cell is None:
                return None
            
            # Find surface and direction cosines
            surface = None
            direction_start = 4
            
            # Check if next field is a surface number
            if len(parts) > 4:
                try:
                    potential_surface = int(parts[4])
                    if abs(potential_surface) < 10000:  # Reasonable surface number
                        surface = potential_surface
                        direction_start = 5
                except ValueError:
                    pass
            
            # Parse direction cosines (should be last 3 fields)
            u = float(parts[-3])
            v = float(parts[-2])
            w = float(parts[-1])
            
            return ParticlePoint(
                x=x, y=y, z=z, r=r,
                cell=cell,
                lattice_indices=lattice_indices,
                surface=surface,
                u=u, v=v, w=w
            )
            
        except (ValueError, IndexError):
            return None
    
    def get_particle(self, nps: int) -> Optional[SourceParticle]:
        """Get data for a specific particle."""
        return self.particles.get(nps)
    
    def get_all_particles(self) -> List[int]:
        """Get list of all particle numbers."""
        return sorted(list(self.particles.keys()))
    
    def get_particles_in_cell(self, cell: int) -> List[SourceParticle]:
        """Get particles born in a specific cell."""
        result = []
        for particle in self.particles.values():
            if particle.birth_point and particle.birth_point.cell == cell:
                result.append(particle)
        return result
    
    def get_particle_birth_positions(self) -> List[Tuple[int, float, float, float, float]]:
        """Get birth positions for all particles as (nps, x, y, z, r)."""
        result = []
        for particle in self.particles.values():
            if particle.birth_point:
                bp = particle.birth_point
                result.append((particle.nps, bp.x, bp.y, bp.z, bp.r))
        return result
    
    def to_dict(self) -> Dict:
        """Convert parsed data to dictionary."""
        return {
            'particles': {
                nps: {
                    'nps': particle.nps,
                    'energy': particle.energy,
                    'weight': particle.weight,
                    'time': particle.time,
                    'points': [
                        {
                            'x': point.x,
                            'y': point.y,
                            'z': point.z,
                            'r': point.r,
                            'cell': point.cell,
                            'lattice_indices': point.lattice_indices,
                            'surface': point.surface,
                            'u': point.u,
                            'v': point.v,
                            'w': point.w
                        }
                        for point in particle.points
                    ]
                }
                for nps, particle in self.particles.items()
            }
        }


# Example usage:
if __name__ == "__main__":
    # Example lines from your MCNP output
    sample_lines = [
        " nps   x          y          z       cell lattice[i j k]       surface    u          v          w        energy     weight      time",
        "",
        "  1  1.489E+01 -1.331E+01  1.377E+02    1484                           -5.133E-01  8.532E-01  9.242E-02  1.355E+00  9.996E-01  0.000E+00",
        "     4.143E+00 -2.557E+00  1.377E+02    1483[   2    1    0]           -5.133E-01  8.532E-01  9.242E-02",
        "     4.143E+00 -2.557E+00  1.377E+02     232                           -5.133E-01  8.532E-01  9.242E-02",
        "     3.631E-01 -3.774E-02  1.377E+02      81[  12    7    0]           -5.133E-01  8.532E-01  9.242E-02",
        "     3.631E-01 -3.774E-02  1.377E+02      71                         0 -5.133E-01  8.532E-01  9.242E-02",
        "  2  1.683E+01 -1.560E+01  1.385E+02    1484                            6.958E-01  2.556E-01 -6.712E-01  1.466E+00  9.996E-01  0.000E+00",
        "     6.076E+00 -4.846E+00  1.385E+02    1483[   2    1    0]            6.958E-01  2.556E-01 -6.712E-01",
        "     6.076E+00 -4.846E+00  1.385E+02     232                            6.958E-01  2.556E-01 -6.712E-01",
        "    -2.231E-01  1.937E-01  1.385E+02      81[  14    5    0]            6.958E-01  2.556E-01 -6.712E-01",
        "    -2.231E-01  1.937E-01  1.385E+02      71                         0  6.958E-01  2.556E-01 -6.712E-01"
    ]
    
    parser = Table110Parser()
    particles = parser.parse_lines(sample_lines)
    
    print(f"Found {len(particles)} source particles:")
    
    for nps, particle in particles.items():
        print(f"\nParticle {nps}:")
        print(f"  Energy: {particle.energy:.3f} MeV")
        print(f"  Weight: {particle.weight:.3f}")
        print(f"  Geometry hierarchy ({len(particle.points)} levels):")
        
        for i, point in enumerate(particle.points):
            lattice_str = f"[{point.lattice_indices[0]:2d} {point.lattice_indices[1]:2d} {point.lattice_indices[2]:2d}]" if point.lattice_indices else ""
            surface_str = f" surf:{point.surface}" if point.surface is not None else ""
            print(f"    {i+1}: Cell {point.cell}{lattice_str}{surface_str}")
            print(f"       Position: ({point.x:.3f}, {point.y:.3f}, {point.z:.3f}) r={point.r:.3f}")
            print(f"       Direction: ({point.u:.3f}, {point.v:.3f}, {point.w:.3f})")
    
    # Test birth position extraction
    birth_positions = parser.get_particle_birth_positions()
    print(f"\nBirth positions:")
    for nps, x, y, z, r in birth_positions:
        print(f"  Particle {nps}: r={r:.3f}")