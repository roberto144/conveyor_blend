from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np

@dataclass
class SimulationParameters:
    """Contains all parameters needed for simulation"""
    total_time: float
    conveyor_length: float
    resolution_size: float
    conveyor_velocity: float
    materials: List[str] = field(default_factory=list)
    silos: List['Silo'] = field(default_factory=list)
    
    def __post_init__(self):
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate simulation parameters"""
        if self.total_time <= 0:
            raise ValueError("Total time must be positive")
        if self.conveyor_length <= 0:
            raise ValueError("Conveyor length must be positive")
        if self.resolution_size <= 0:
            raise ValueError("Resolution size must be positive")
        if self.conveyor_velocity <= 0:
            raise ValueError("Conveyor velocity must be positive")
        if self.resolution_size > self.conveyor_length:
            raise ValueError("Resolution size cannot be larger than conveyor length")

@dataclass
class SimulationResults:
    """Contains results from simulation"""
    material_matrix: np.ndarray
    flow_data: np.ndarray
    proportion_data: np.ndarray
    parameters: SimulationParameters
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def time_steps(self) -> int:
        """Number of time steps in simulation"""
        return self.flow_data.shape[0] if self.flow_data.size > 0 else 0
    
    @property
    def material_count(self) -> int:
        """Number of different materials"""
        return len(self.parameters.materials)
    
    def get_time_array(self) -> np.ndarray:
        """Get array of time values"""
        if self.time_steps == 0:
            return np.array([])
        
        dt = self.parameters.resolution_size / self.parameters.conveyor_velocity
        return np.arange(0, self.parameters.total_time + dt, dt)[:self.time_steps]
