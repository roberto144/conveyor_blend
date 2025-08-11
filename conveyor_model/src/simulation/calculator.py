import numpy as np
from typing import Union

class MatrixCalculator:
    """Handles matrix operations for simulation"""
    
    @staticmethod
    def shift_matrix_right(matrix: np.ndarray, steps: int) -> np.ndarray:
        """
        Shift matrix contents to the right by specified steps
        
        Args:
            matrix: Input matrix to shift
            steps: Number of positions to shift
            
        Returns:
            Shifted matrix with same dimensions
        """
        if steps <= 0:
            return matrix.copy()
        
        rows, cols = matrix.shape
        shifted_matrix = np.zeros_like(matrix)
        
        # Vectorized shifting - much faster than loops
        if steps < cols:
            shifted_matrix[:, steps:] = matrix[:, :-steps]
        
        return shifted_matrix
    
    @staticmethod
    def calculate_proportions(flow_data: np.ndarray) -> np.ndarray:
        """
        Calculate material proportions as percentages
        
        Args:
            flow_data: Matrix with material flows and totals
            
        Returns:
            Matrix with proportions as percentages
        """
        if flow_data.shape[1] < 3:
            raise ValueError("Flow data must have at least 3 columns")
        
        # Extract material data (all columns except last 2)
        materials = flow_data[:, :-2]
        totals = flow_data[:, -1]  # Last column is total
        
        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            proportions = np.divide(materials, totals[:, np.newaxis]) * 100
            # Replace NaN and inf with 0
            proportions[~np.isfinite(proportions)] = 0
        
        return proportions
    
    @staticmethod
    def calculate_mass_balance(flow_data: np.ndarray) -> dict:
        """Calculate mass balance statistics"""
        total_input = np.sum(flow_data[:, :-2])  # Sum all material flows
        total_output = np.sum(flow_data[:, -1])  # Sum total flows
        
        return {
            'total_input': total_input,
            'total_output': total_output,
            'balance_error': abs(total_input - total_output),
            'balance_error_percent': abs(total_input - total_output) / max(total_input, 1e-10) * 100
        }