from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np
from .silo import Silo

@dataclass
class SimulationParameters:
    """
    Contains all parameters needed for running a conveyor system simulation.
    
    This class encapsulates all the necessary parameters for configuring and running
    a conveyor system simulation, including physical parameters, material properties,
    and operational settings.
    
    Attributes:
        total_time (float): Total simulation duration in seconds.
        conveyor_length (float): Length of the conveyor system in meters.
        resolution_size (float): Size of each discrete segment in meters.
        conveyor_velocity (float): Operating velocity of the conveyor in m/s.
        materials (List[str]): List of material names used in the simulation.
            Defaults to empty list.
        silos (List[Silo]): List of silo configurations for material discharge.
            Defaults to empty list.
        material_chemistry (Dict[str, Dict[str, float]]): Chemical composition data
            for each material. Format: {material_name: {element: percentage}}.
            Defaults to empty dict.
            
    Example:
        >>> params = SimulationParameters(
        ...     total_time=100.0,
        ...     conveyor_length=50.0,
        ...     resolution_size=1.0,
        ...     conveyor_velocity=2.0,
        ...     materials=['Iron Ore', 'Limestone'],
        ...     silos=[Silo(...), Silo(...)],
        ...     material_chemistry={'Iron Ore': {'Fe': 62.0, 'SiO2': 4.5}}
        ... )
    """
    total_time: float
    conveyor_length: float
    resolution_size: float
    conveyor_velocity: float
    materials: List[str] = field(default_factory=list)
    silos: List['Silo'] = field(default_factory=list)
    material_chemistry: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
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
    """
    Contains the complete results from a conveyor system simulation.
    
    This class stores all simulation results, including material distributions,
    flow rates, proportions, and optional chemical analysis data. It provides
    methods to access and analyze the simulation outcomes.
    
    Attributes:
        material_matrix (np.ndarray): 2D array of material distributions over time.
            Shape: (time_steps, spatial_positions).
        flow_data (np.ndarray): 2D array of material flow rates.
            Shape: (time_steps, n_materials + 2).
            Last two columns are rate and total.
        proportion_data (np.ndarray): 2D array of material proportions.
            Shape: (time_steps, n_materials).
        parameters (SimulationParameters): Original parameters used for simulation.
        metadata (Dict[str, Any]): Additional simulation metadata and statistics.
            Defaults to empty dict.
        chemistry_matrix (Optional[np.ndarray]): Chemical composition over time.
            Shape: (time_steps, n_elements, spatial_positions).
            None if chemistry tracking disabled.
        chemistry_trends (Optional[Dict[str, np.ndarray]]): Time series of chemical
            parameters. Format: {parameter_name: time_series_array}.
            Empty dict if chemistry tracking disabled.
            
    Example:
        >>> results = SimulationResults(
        ...     material_matrix=np.array(...),
        ...     flow_data=np.array(...),
        ...     proportion_data=np.array(...),
        ...     parameters=sim_params,
        ...     metadata={'duration': 120.5},
        ...     chemistry_matrix=np.array(...),
        ...     chemistry_trends={'Fe': np.array(...)}
        ... )
        >>> print(results.metadata['duration'])
        120.5
    """
    material_matrix: np.ndarray
    flow_data: np.ndarray
    proportion_data: np.ndarray
    parameters: SimulationParameters
    metadata: Dict[str, Any] = field(default_factory=dict)
    chemistry_matrix: Optional[np.ndarray] = None
    chemistry_trends: Optional[Dict[str, np.ndarray]] = field(default_factory=dict)
    
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
