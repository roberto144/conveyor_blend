from typing import List
from ..models.simulation_data import SimulationParameters
from ..utils.exceptions import ValidationError

class SimulationValidator:
    """Validates simulation parameters and inputs"""
    
    def validate_parameters(self, params: SimulationParameters) -> None:
        """
        Validate all simulation parameters
        
        Args:
            params: Parameters to validate
            
        Raises:
            ValidationError: If any parameter is invalid
        """
        self._validate_basic_parameters(params)
        self._validate_materials(params)
        self._validate_silos(params)
        self._validate_physical_constraints(params)
    
    def _validate_basic_parameters(self, params: SimulationParameters) -> None:
        """Validate basic numerical parameters"""
        if params.total_time <= 0:
            raise ValidationError("Simulation time must be positive")
        
        if params.conveyor_length <= 0:
            raise ValidationError("Conveyor length must be positive")
        
        if params.resolution_size <= 0:
            raise ValidationError("Resolution size must be positive")
        
        if params.conveyor_velocity <= 0:
            raise ValidationError("Conveyor velocity must be positive")
        
        if params.resolution_size > params.conveyor_length:
            raise ValidationError("Resolution size cannot exceed conveyor length")
    
    def _validate_materials(self, params: SimulationParameters) -> None:
        """Validate material definitions"""
        if not params.materials:
            raise ValidationError("At least one material must be defined")
        
        if len(set(params.materials)) != len(params.materials):
            raise ValidationError("Material names must be unique")
    
    def _validate_silos(self, params: SimulationParameters) -> None:
        """Validate silo configurations"""
        if not params.silos:
            raise ValidationError("At least one silo must be defined")
        
        n_segments = int(params.conveyor_length / params.resolution_size)
        n_materials = len(params.materials)
        
        for i, silo in enumerate(params.silos):
            if silo.silo_position >= n_segments:
                raise ValidationError(f"Silo {i+1}: Position exceeds conveyor length")
            
            if silo.material_position >= n_materials:
                raise ValidationError(f"Silo {i+1}: Material position exceeds material count")
            
            if silo.start_time > params.total_time:
                raise ValidationError(f"Silo {i+1}: Start time exceeds simulation time")
    
    def _validate_physical_constraints(self, params: SimulationParameters) -> None:
        """Validate physical feasibility"""
        # Check if any silo will finish after simulation ends
        for i, silo in enumerate(params.silos):
            end_time = silo.end_time()
            if end_time > params.total_time * 1.5:  # Allow some buffer
                raise ValidationError(
                    f"Silo {i+1}: Will not empty within reasonable time "
                    f"(ends at {end_time:.1f}s, simulation runs for {params.total_time:.1f}s)"
                )
