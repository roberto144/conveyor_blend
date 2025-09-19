# src/simulation/engine.py
import numpy as np
from typing import List, Tuple, Dict
from ..models.silo import Silo
from ..models.conveyor import Conveyor
from ..models.simulation_data import SimulationParameters, SimulationResults
from .calculator import MatrixCalculator
from .validator import SimulationValidator
from ..utils.exceptions import SimulationError

class SimulationEngine:
    """Enhanced simulation engine for conveyor blending model with BF support"""
    
    def __init__(self):
        self.calculator = MatrixCalculator()
        self.validator = SimulationValidator()
        self.bf_initialized = False
        self.chemistry_data = {}
        
    def initialize_blast_furnace(self):
        """Initialize blast furnace specific components"""
        self.bf_initialized = True
        self.chemistry_data = {}
        print("Blast furnace mode initialized")
        
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
        
        # Initialize chemistry tracking if BF mode
        chemistry_matrix = None
        if self.bf_initialized and hasattr(parameters, 'material_chemistry'):
            chemistry_matrix = self._initialize_chemistry_tracking(
                n_materials, n_segments, parameters.material_chemistry
            )
        
        # Run simulation loop
        time = 0.0
        counter = 0
        step_size = max(1, round((conveyor.velocity * dt) / parameters.resolution_size))
        
        print(f"Starting simulation: {n_steps} steps, step_size={step_size}")
        
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
                    
                    # Add chemistry data if BF mode
                    if chemistry_matrix is not None:
                        self._add_chemistry_to_conveyor(
                            chemistry_matrix,
                            silo.material_position,
                            silo.silo_position,
                            quantity,
                            parameters.material_chemistry
                        )
            
            # Record current state
            material_flows = material_matrix[:, -1]  # Material at end of conveyor
            total_flow = np.sum(material_flows)
            flow_data[counter, :] = np.concatenate([material_flows, [time], [total_flow]])
            
            # Move materials along conveyor
            material_matrix = self.calculator.shift_matrix_right(material_matrix, step_size)
            if chemistry_matrix is not None:
                chemistry_matrix = self._shift_chemistry_matrix(chemistry_matrix, step_size)
            
            # Update time and counter
            time += dt
            counter += 1
        
        # Trim unused rows
        flow_data = flow_data[:counter]
        
        # Calculate proportions
        proportion_data = self.calculator.calculate_proportions(flow_data)
        
        # Calculate mass balance
        mass_balance = self.calculator.calculate_mass_balance(flow_data)
        
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
                'final_time': time - dt,
                'mass_balance': mass_balance,
                'bf_mode': self.bf_initialized
            }
        )
        
        # Add chemistry results if BF mode
        if chemistry_matrix is not None:
            results.chemistry_matrix = chemistry_matrix
            results.chemistry_trends = self._calculate_chemistry_trends(
                chemistry_matrix, flow_data, parameters
            )
        
        return results
    
    def run_bf_simulation(self, parameters: SimulationParameters) -> SimulationResults:
        """
        Run blast furnace specific simulation
        """
        if not self.bf_initialized:
            self.initialize_blast_furnace()
        
        # Run standard simulation with BF enhancements
        results = self.run_simulation(parameters)
        
        # Add BF-specific post-processing
        if hasattr(parameters, 'material_chemistry'):
            results = self._enhance_bf_results(results, parameters)
        
        return results
    
    def _initialize_chemistry_tracking(self, n_materials: int, n_segments: int, 
                                     material_chemistry: Dict) -> np.ndarray:
        """Initialize chemistry tracking matrix for BF mode"""
        # Chemistry matrix: [materials x segments x chemistry_components]
        # Chemistry components: Fe, SiO2, CaO, MgO, Al2O3
        chemistry_components = 5
        chemistry_matrix = np.zeros((n_materials, n_segments, chemistry_components))
        return chemistry_matrix
    
    def _add_chemistry_to_conveyor(self, chemistry_matrix: np.ndarray, 
                                 material_pos: int, silo_pos: int, quantity: float,
                                 material_chemistry: Dict) -> None:
        """Add chemistry data when material is added to conveyor"""
        if (0 <= material_pos < chemistry_matrix.shape[0] and 
            0 <= silo_pos < chemistry_matrix.shape[1]):
            
            # Get material name from position
            materials = list(material_chemistry.keys())
            if material_pos < len(materials):
                material_name = materials[material_pos]
                chemistry = material_chemistry[material_name]['chemistry']
                
                # Add weighted chemistry values
                weight = quantity / max(quantity, 1e-10)  # Normalize by quantity
                chemistry_matrix[material_pos, silo_pos, 0] += chemistry.get('Fe', 0) * weight
                chemistry_matrix[material_pos, silo_pos, 1] += chemistry.get('SiO2', 0) * weight
                chemistry_matrix[material_pos, silo_pos, 2] += chemistry.get('CaO', 0) * weight
                chemistry_matrix[material_pos, silo_pos, 3] += chemistry.get('MgO', 0) * weight
                chemistry_matrix[material_pos, silo_pos, 4] += chemistry.get('Al2O3', 0) * weight
    
    def _shift_chemistry_matrix(self, chemistry_matrix: np.ndarray, steps: int) -> np.ndarray:
        """Shift chemistry matrix along with material matrix"""
        if steps <= 0:
            return chemistry_matrix.copy()
        
        materials, segments, components = chemistry_matrix.shape
        shifted_matrix = np.zeros_like(chemistry_matrix)
        
        if steps < segments:
            shifted_matrix[:, steps:, :] = chemistry_matrix[:, :-steps, :]
        
        return shifted_matrix
    
    def _calculate_chemistry_trends(self, chemistry_matrix: np.ndarray, 
                                  flow_data: np.ndarray,
                                  parameters: SimulationParameters) -> Dict:
        """Calculate chemistry trends over time at conveyor discharge point"""
        trends = {
            'fe_trend': [],
            'sio2_trend': [],
            'cao_trend': [],
            'mgo_trend': [],
            'al2o3_trend': [],
            'basicity_trend': [],
            'time_points': []
        }
        
        if not hasattr(parameters, 'material_chemistry'):
            return trends
        
        chemistry_data = parameters.material_chemistry
        materials = list(chemistry_data.keys())
        
        # Calculate weighted average chemistry at discharge point for each time step
        for i in range(flow_data.shape[0]):
            total_flow = flow_data[i, -1]  # Last column is total flow
            time_point = flow_data[i, -2]  # Second to last is time
            
            if total_flow > 1e-6:  # Only calculate if there's significant flow
                # Calculate weighted average chemistry based on material flows
                weighted_fe = 0
                weighted_sio2 = 0
                weighted_cao = 0
                weighted_mgo = 0
                weighted_al2o3 = 0
                
                for mat_idx, material_name in enumerate(materials):
                    if mat_idx < flow_data.shape[1] - 2:  # Check bounds
                        material_flow = flow_data[i, mat_idx]
                        if material_flow > 0:
                            weight = material_flow / total_flow
                            chemistry = chemistry_data[material_name]['chemistry']
                            
                            weighted_fe += chemistry.get('Fe', 0) * weight
                            weighted_sio2 += chemistry.get('SiO2', 0) * weight
                            weighted_cao += chemistry.get('CaO', 0) * weight
                            weighted_mgo += chemistry.get('MgO', 0) * weight
                            weighted_al2o3 += chemistry.get('Al2O3', 0) * weight
                
                # Calculate basicity (B2)
                basicity_b2 = weighted_cao / max(weighted_sio2, 0.1) if weighted_sio2 > 0.1 else 0
                
                # Store the weighted averages
                trends['fe_trend'].append(weighted_fe)
                trends['sio2_trend'].append(weighted_sio2)
                trends['cao_trend'].append(weighted_cao)
                trends['mgo_trend'].append(weighted_mgo)
                trends['al2o3_trend'].append(weighted_al2o3)
                trends['basicity_trend'].append(basicity_b2)
                trends['time_points'].append(time_point)
        
        return trends
    
    def _enhance_bf_results(self, results: SimulationResults, 
                          parameters: SimulationParameters) -> SimulationResults:
        """Add BF-specific enhancements to results"""
        # Calculate discharge chemistry statistics
        if hasattr(results, 'chemistry_trends'):
            trends = results.chemistry_trends
            
            # Add statistical analysis
            if trends['fe_trend']:
                results.metadata['avg_fe_content'] = np.mean(trends['fe_trend'])
                results.metadata['fe_std'] = np.std(trends['fe_trend'])
                results.metadata['avg_basicity'] = np.mean(trends['basicity_trend'])
                results.metadata['basicity_std'] = np.std(trends['basicity_trend'])
                
                # Quality indicators
                results.metadata['fe_stability'] = 'Good' if np.std(trends['fe_trend']) < 2.0 else 'Poor'
                basicity_target = 1.1
                basicity_deviation = abs(np.mean(trends['basicity_trend']) - basicity_target)
                results.metadata['basicity_quality'] = 'Good' if basicity_deviation < 0.1 else 'Poor'
        
        return results
    
    def _add_material_to_conveyor(self, matrix: np.ndarray, material_pos: int, 
                                  silo_pos: int, quantity: float) -> None:
        """Add material quantity to specific position on conveyor"""
        if (0 <= material_pos < matrix.shape[0] and 
            0 <= silo_pos < matrix.shape[1]):
            matrix[material_pos, silo_pos] += quantity
    
    def calculate_bunker_chemistry(self, bunker_data: Dict) -> Dict:
        """Calculate chemistry for bunker discharge - BF specific feature"""
        if not self.bf_initialized:
            raise SimulationError("BF mode not initialized")
        
        # This would integrate with the bunker visualization
        # For now, return placeholder
        return {
            'Fe': 60.0,
            'SiO2': 5.0,
            'CaO': 8.0,
            'MgO': 1.0,
            'Al2O3': 2.0,
            'B2': 1.6
        }
    
    def validate_bf_chemistry(self, chemistry_data: Dict) -> bool:
        """Validate BF chemistry parameters"""
        required_elements = ['Fe', 'SiO2', 'CaO', 'MgO', 'Al2O3']
        
        for element in required_elements:
            if element not in chemistry_data:
                return False
            if not isinstance(chemistry_data[element], (int, float)):
                return False
            if chemistry_data[element] < 0:
                return False
        
        # Check reasonable ranges
        if chemistry_data['Fe'] > 70:  # Fe content too high
            return False
        if chemistry_data['SiO2'] > 50:  # SiO2 content too high for most materials
            return False
        
        return True