from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ruamel.yaml import YAML


class classproperty:
    """A descriptor that behaves like a read-only property at the class level."""

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, instance, owner):
        # 'owner' is the class; 'instance' is ignored for class access
        return self.fget(owner)


@dataclass(frozen=True)
class McnpParticleType:
    """Dataclass to store MCNP particle data."""

    ipt: int
    name: str
    symbol: str
    rest_mass_MeV: float
    cutoff_min_MeV: float
    cutoff_default_MeV: float
    lifetime_mcnp_s: str
    lifetime_actual_s: str


class McnpParticleTypes:
    """Class to store MCNP particle type data.

    Disallows instantiation. Use class methods only.
    """

    _particles: Dict[str, McnpParticleType] = {}
    p = Path(__file__).resolve().parent.parent.parent / "resources" / "tblMcnpParticle.yaml"
    yaml = YAML()
    raw_dict: Dict[int, List[Any]] = yaml.load(p)
    # Store particle data
    for key, entry in raw_dict.items():
        symbol = str(entry[1])
        val = McnpParticleType(
            ipt=int(key),
            name=str(entry[0]),
            symbol=symbol,
            rest_mass_MeV=float(entry[2]),
            cutoff_min_MeV=float(entry[3]),
            cutoff_default_MeV=float(entry[4]),
            lifetime_mcnp_s=str(entry[5]),
            lifetime_actual_s=str(entry[6]) if len(entry) > 6 else "",
        )
        _particles[symbol] = val

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} cannot be instantiated")

    @classmethod
    def particle_by_symbol(cls, symbol: str) -> McnpParticleType:
        """Get the particle by its symbol."""
        try:
            # strings are immutable so this doesn't affect calling scope
            symbol = symbol.strip().upper()
            return cls._particles[symbol]
        except AttributeError:
            raise KeyError(f"Invalid particle symbol: {symbol}")
        except KeyError:
            raise KeyError(f"Particle symbol not found: {symbol}")

    @classmethod
    def particle_by_ipt(cls, ipt: int) -> McnpParticleType:
        """Get the particle by its IPT number."""
        for particle in cls._particles.values():
            if particle.ipt == ipt:
                return particle
        raise KeyError(f"Particle IPT not found: {ipt}")

    @classproperty
    def num_particles(cls) -> int:
        """Get the number of defined MCNP particles."""
        return len(cls._particles)


if __name__ == "__main__":
    for sym in ["N", "p", "E", "|", "%"]:
        try:
            particle = McnpParticleTypes.particle_by_symbol(sym)
            print(f"Particle symbol: {sym} -> {particle}")
        except KeyError as e:
            print(e)
    print(f"Total MCNP particles defined: {McnpParticleTypes.num_particles}")
