from dataclasses import dataclass
from typing import Union

@dataclass
class Silo:
    """Represents a silo with its operational parameters"""
    material: str
    capacity: float  # kg
    flow_rate: float  # kg/s
    material_position: int  # position in material matrix
    silo_position: int  # position on conveyor
    start_time: float  # seconds
    
    def __post_init__(self):
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate silo parameters"""
        if self.capacity <= 0:
            raise ValueError("Capacity must be positive")
        if self.flow_rate <= 0:
            raise ValueError("Flow rate must be positive")
        if self.material_position < 0:
            raise ValueError("Material position must be non-negative")
        if self.silo_position < 0:
            raise ValueError("Silo position must be non-negative")
        if self.start_time < 0:
            raise ValueError("Start time must be non-negative")
    
    def quantity_at_time(self, dt: float) -> float:
        """Calculate quantity discharged in time dt"""
        return self.flow_rate * dt
    
    def end_time(self) -> float:
        """Calculate when silo will be empty"""
        return self.start_time + (self.capacity / self.flow_rate)
    
    def is_active_at_time(self, time: float) -> bool:
        """Check if silo is discharging at given time"""
        return self.start_time <= time <= self.end_time()