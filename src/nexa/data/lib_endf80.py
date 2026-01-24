from pathlib import Path
from typing import Dict, Optional, Tuple

from ruamel.yaml import YAML


class LibEndf80:
    """Class to store and retrieve ENDF/B-VIII.0 S(a,b) SABIDs and library extensions.

    Disallows instantiation. Use class methods only.
    """

    _endf80_sabid: Dict[str, Tuple[float, float]] = {}
    p = Path(__file__).resolve().parent.parent / "resources" / "tblEndf80SaB.yaml"
    yaml = YAML()
    raw_dict: Dict[str, Tuple[float, float]] = yaml.load(p)
    # Store sabids
    for key, entry in raw_dict.items():
        val = tuple(entry)
        _endf80_sabid[key.strip().lower()] = val

    _endf80_ext: Dict[str, float] = {
        "00c": 293.6,
        "01c": 600.0,
        "02c": 900.0,
        "03c": 1200.0,
        "04c": 2500.0,
        "05c": 0.1,
        "06c": 250.0,
    }
    _endf80_ext = sorted(((ext, temp) for ext, temp in _endf80_ext.items()), key=lambda x: x[1])

    _missing_zaid = [
        12023,
        17034,
        36088,
        38091,
        38092,
        39086,
        39087,
        39088,
        39092,
        39093,
        40089,
        40097,
        41091,
        41098,
        41099,
        42091,
        42101,
        45106,
        45107,
        45108,
        45109,
        45110,
        45111,
        46111,
        46112,
        47106,
        47110,
        48115,
        49116,
        49117,
        49118,
        49119,
        49120,
        49121,
        50121,
        51127,
        52527, # breaks Origen
        52529, # breaks Origen
        57141,
        57142,
        59145,
        61548, # breaks Origen
        64150,
        67164,
        67166,
        69166,
        69167,
        88227,
        89228,
    ]

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} cannot be instantiated")

    @classmethod
    def ext_by_tempK(cls, tempK: float) -> float:
        """Get ENDF/B-VIII.1 thermal extension factor by temperature in K."""

        prev_ext = cls._endf80_ext[0][0]
        for ext, temp in cls._endf80_ext:
            if tempK == temp:
                return ext
            elif temp > tempK:
                return prev_ext
            prev_ext = ext
        return prev_ext

    @classmethod
    def ext_by_tempC(cls, tempC: float) -> float:
        """Get ENDF/B-VIII.1 thermal extension factor by temperature in C."""

        tempK = tempC + 273.15
        return cls.ext_by_tempK(tempK)

    @classmethod
    def sabid_by_tempMeV(cls, base: str, tempMeV: float) -> Optional[str]:
        """Get SABID by temperature in MeV."""

        filtered = sorted(
            ((sabid, vals[0]) for sabid, vals in cls._endf80_sabid.items() if base in sabid),
            key=lambda x: x[1],
        )
        if len(filtered) == 0:
            raise KeyError(f"No SABID found with base '{base}'")

        prev_sabid = filtered[0][0]
        for sabid, temp in filtered:
            if temp == tempMeV:
                return sabid
            elif temp > tempMeV:
                return prev_sabid
            prev_sabid = sabid
        return prev_sabid

    @classmethod
    def sabid_by_tempK(cls, base: str, tempK: float) -> Optional[str]:
        """Get SABID by temperature in K."""

        filtered = sorted(
            ((sabid, vals[1]) for sabid, vals in cls._endf80_sabid.items() if base in sabid),
            key=lambda x: x[1],
        )
        if len(filtered) == 0:
            raise KeyError(f"No SABID found with base '{base}'")

        prev_sabid = filtered[0][0]
        for sabid, temp in filtered:
            if temp == tempK:
                return sabid
            elif temp > tempK:
                return prev_sabid
            prev_sabid = sabid
        return prev_sabid

    @classmethod
    def sabid_by_tempC(cls, base: str, temp: float) -> Optional[str]:
        """Get SABID by temperature in C."""

        tempK = temp + 273.15
        return cls.sabid_by_tempK(base, tempK)

    @classmethod
    def is_missing_zaid(cls, zaid) -> bool:
        """Check if ZAID is missing from ENDF/B-VIII.1."""

        return zaid in cls._missing_zaid

if __name__ == "__main__":
    print(LibEndf80.sabid_by_tempMeV("h-h2o", 2.53e-08))
    print(LibEndf80.sabid_by_tempK("h-h2o", 293.6))
    print(LibEndf80.sabid_by_tempC("h-h2o", 20))
    print(LibEndf80.ext_by_tempK(293.6))
    print(LibEndf80.ext_by_tempK(400.0))
    print(LibEndf80.ext_by_tempK(1000.0))
