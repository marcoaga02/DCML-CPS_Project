from enum import Enum

class SeverityLevel(Enum):
    """
    Enumeration to represent the severity alert of the system.
    The scale goes from 1 to 5 where 1 indicates a critical severity while 5 is the lowest and indicates that the system is not in danger.
    """
    LEVEL_1 = "Critical"
    LEVEL_2 = "High"
    LEVEL_3 = "Medium"
    LEVEL_4 = "Low"
    LEVEL_5 = "Informational"
