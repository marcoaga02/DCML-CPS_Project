from enum import Enum

class SystemState(Enum):
    """
    Enumeration to represent the state of the system
    """
    NORMAL = "normal"
    UNDER_INJECTION = "under_injection"
