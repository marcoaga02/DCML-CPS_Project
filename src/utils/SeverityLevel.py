from enum import Enum

class SeverityLevel(Enum):
    """
    Enumeration to represent the severity alert of the system.
    The scale goes from 1 to 5 where 1 indicates a critical severity while 5 is the lowest and indicates that the system is not in danger.
    """
    LEVEL_1 = "Critical"
    LEVEL_2 = "Severe"
    LEVEL_3 = "Caution"
    LEVEL_4 = "Under Observation"
    LEVEL_5 = "Informational"
