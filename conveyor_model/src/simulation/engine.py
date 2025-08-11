import numpy as np
from typing import List, Tuple
from ..models.silo import Silo
from ..models.conveyor import Conveyor
from ..models.simulation_data import SimulationParameters, SimulationResults
from .calculator import MatrixCalculator
from .validator import SimulationValidator

class SimulationEngine:
    """Core simulation engine for conveyor blending model"""
    
    def __init__(self):
        self.calculator = MatrixCalculator()
        self.validator = SimulationValidator()
    
    def run_simulation(self, parameters: SimulationParameters) -> SimulationResults:
        """
        Run the complete simulation
        
        Args:
            parameters: Simulation parameters and configuration
            
        Returns:
            SimulationResults object containing all results
            
        Raises:
            ValidationError: If parameters are invalid
            SimulationError: If simulation fails
        """
        # Validate input parameters
        self.validator.validate_parameters(parameters)
        
        # Initialize simulation state
        conveyor = Conveyor(parameters.conveyor_velocity, parameters.conveyor_length)
        dt = parameters.resolution_size / conveyor.velocity
        n_steps = int(parameters.total_time / dt)
        n_segments = int(conveyor.length / parameters.resolution_size)
        n_materials = len(parameters.materials)
        
        # Initialize matrices
        material_matrix = np.zeros((n_materials, n_segments))
        flow_data = np.zeros((n_steps + 1, n_materials + 2))  # +2 for time and total
        
        # Run simulation loop
        time = 0.0
        counter = 0
        step_size = round((conveyor.velocity * dt) / parameters.resolution_size)
        
        while time <= parameters.total_time and counter <= n_steps:
            # Process all active silos
            for silo in parameters.silos:
                if silo.is_active_at_time(time):
                    quantity = silo.quantity_at_time(dt)
                    self._add_material_to_conveyor(
                        material_matrix, 
                        silo.material_position, 
                        silo.silo_position, 
                        quantity
                    )
            
            # Record current state
            material_flows = material_matrix[:, -1]  # Material at end of conveyor
            total_flow = np.sum(material_flows)
            flow_data[counter, :] = np.concatenate([material_flows, [time], [total_flow]])
            
            # Move materials along conveyor
            material_matrix = self.calculator.shift_matrix_right(material_matrix, step_size)
            
            # Update time and counter
            time += dt
            counter += 1
        
        # Trim unused rows
        flow_data = flow_data[:counter]
        
        # Calculate proportions
        proportion_data = self.calculator.calculate_proportions(flow_data)
        
        # Create results object
        results = SimulationResults(
            material_matrix=material_matrix,
            flow_data=flow_data,
            proportion_data=proportion_data,
            parameters=parameters,
            metadata={
                'dt': dt,
                'n_steps': counter,
                'step_size': step_size,
                'final_time': time - dt
            }
        )
        
        return results
    
    def _add_material_to_conveyor(self, matrix: np.ndarray, material_pos: int, 
                                  silo_pos: int, quantity: float) -> None:
        """Add material quantity to specific position on conveyor"""
        if (0 <= material_pos < matrix.shape[0] and 
            0 <= silo_pos < matrix.shape[1]):
            matrix[material_pos, silo_pos] += quantity