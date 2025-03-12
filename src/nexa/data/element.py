class Element:
    """Class to store element data.

    Data maintained as read-only properties.
    Properties:
        symbol: str - element symbol
        name: str - element name
        z: int - atomic number
        zaid: int - zaid (=z*1000)
        amu: float - atomic mass units
    """

    def __init__(self, symbol: str, name: str, z: int, amu: float):
        """
        All initialization is done in the constructor.  No updates are allowed.

        Element symbols are normalized to lower case and stripped of leading/trailing spaces.

        Args:
            symbol (str): element symbol
            name (str): element name
            z (int): atomic number
            amu (float): atomic mass [amu]
        """
        self._symbol: str = self.__normalize_key(symbol)
        self._name: str = name
        self._z: int = z
        self._amu: float = amu

    def __str__(self):
        return (
            f"symbol({self.symbol}) name({self.name}) z({self.z}) zaid({self.zaid}) amu({self.amu})"
        )

    # define readonly properties to disallow changes
    @property
    def symbol(self) -> str:
        """Element symbol"""
        return self._symbol

    @property
    def name(self) -> str:
        """Element name"""
        return self._name

    @property
    def z(self) -> int:
        """Atomic number"""
        return self._z

    @property
    def zaid(self) -> int:
        """ZA id"""
        return self._z * 1000

    @property
    def amu(self) -> float:
        """Atomic mass from MCNP6"""
        return self._amu

    def __normalize_key(self, key: str):
        return key.strip().lower()
