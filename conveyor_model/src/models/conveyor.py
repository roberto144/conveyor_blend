from dataclasses import dataclass

@dataclass
class Conveyor:
    """Represents a conveyor belt with its properties"""
    velocity: float  # m/s
    length: float   # m
    
    def __post_init__(self):
        if self.velocity <= 0:
            raise ValueError("Velocity must be positive")
        if self.length <= 0:
            raise ValueError("Length must be positive")
    
    def travel_time(self) -> float:
        """Time for material to travel the full length"""
        return self.length / self.velocity