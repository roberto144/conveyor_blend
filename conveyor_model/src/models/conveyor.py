from dataclasses import dataclass

@dataclass
class Conveyor:
    """
    Represents a conveyor belt with its physical properties and operational parameters.
    
    This class models a conveyor belt system with its basic physical characteristics,
    including velocity and length. It provides methods to calculate material transit times
    and validates the physical constraints of the system.
    
    Attributes:
        velocity (float): Operating velocity of the conveyor in meters per second (m/s).
            Must be positive.
        length (float): Total length of the conveyor in meters (m).
            Must be positive.
            
    Raises:
        ValueError: If velocity or length is not positive.
        
    Example:
        >>> conveyor = Conveyor(velocity=2.0, length=100.0)
        >>> print(conveyor.travel_time())
        50.0  # Time in seconds
    """
    velocity: float  # m/s
    length: float   # m
    
    def __post_init__(self):
        """
        Validates the conveyor's physical parameters after initialization.
        
        Raises:
            ValueError: If velocity or length is not positive.
        """
        if self.velocity <= 0:
            raise ValueError("Velocity must be positive")
        if self.length <= 0:
            raise ValueError("Length must be positive")
    
    def travel_time(self) -> float:
        """
        Calculate the time required for material to travel the full length of the conveyor.
        
        Returns:
            float: Transit time in seconds.
            
        Note:
            This calculation assumes constant velocity and no material slippage.
        """
        return self.length / self.velocity