import json
import os
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import numpy as np
from .exceptions import FileHandlingError

class FileHandler:
    """Handles saving and loading of case files"""
    
    def __init__(self):
        self.current_filename = None
        self.default_extension = ".json"
        self.file_filter = "JSON Files (*.json);;All Files (*)"
    
    def save_case(self, data: Dict[str, Any], filename: str = None) -> bool:
        """
        Save case data to file
        
        Args:
            data: Case data to save
            filename: Optional filename, uses current if not provided
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            FileHandlingError: If save operation fails
        """
        if filename is None:
            filename = self.current_filename
        
        if filename is None:
            return self.save_case_as(data)
        
        try:
            # Convert numpy arrays to lists for JSON serialization
            serializable_data = self._make_json_serializable(data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            self.current_filename = filename
            return True
            
        except Exception as e:
            raise FileHandlingError(f"Failed to save file: {str(e)}")
    
    def save_case_as(self, data: Dict[str, Any]) -> bool:
        """
        Save case data with file dialog
        
        Args:
            data: Case data to save
            
        Returns:
            True if successful, False if cancelled
        """
        filename, _ = QFileDialog.getSaveFileName(
            None, "Save Case", "", self.file_filter
        )
        
        if filename:
            if not filename.endswith(self.default_extension):
                filename += self.default_extension
            
            return self.save_case(data, filename)
        
        return False
    
    def load_case(self, filename: str = None) -> Optional[Dict[str, Any]]:
        """
        Load case data from file
        
        Args:
            filename: Optional filename, shows dialog if not provided
            
        Returns:
            Loaded data or None if cancelled
            
        Raises:
            FileHandlingError: If load operation fails
        """
        if filename is None:
            filename, _ = QFileDialog.getOpenFileName(
                None, "Open Case", "", self.file_filter
            )
        
        if not filename:
            return None
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_filename = filename
            return data
            
        except FileNotFoundError:
            raise FileHandlingError(f"File not found: {filename}")
        except json.JSONDecodeError as e:
            raise FileHandlingError(f"Invalid JSON file: {str(e)}")
        except Exception as e:
            raise FileHandlingError(f"Failed to load file: {str(e)}")
    
    def _make_json_serializable(self, data: Any) -> Any:
        """Convert data to JSON-serializable format"""
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, dict):
            return {key: self._make_json_serializable(value) 
                   for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._make_json_serializable(item) for item in data]
        else:
            return data
    
    def export_results_csv(self, results, filename: str = None) -> bool:
        """Export simulation results to CSV"""
        if filename is None:
            filename, _ = QFileDialog.getSaveFileName(
                None, "Export Results", "", "CSV Files (*.csv);;All Files (*)"
            )
        
        if not filename:
            return False
        
        try:
            import pandas as pd
            
            # Create DataFrame with results
            time_array = results.get_time_array()
            df_data = {}
            
            # Add time column
            df_data['Time [s]'] = time_array
            
            # Add material flow columns
            for i, material in enumerate(results.parameters.materials):
                df_data[f'{material} Flow [kg/s]'] = results.flow_data[:len(time_array), i]
            
            # Add total flow
            df_data['Total Flow [kg/s]'] = results.flow_data[:len(time_array), -1]
            
            # Add proportion columns
            for i, material in enumerate(results.parameters.materials):
                df_data[f'{material} Proportion [%]'] = results.proportion_data[:len(time_array), i]
            
            df = pd.DataFrame(df_data)
            df.to_csv(filename, index=False)
            return True
            
        except ImportError:
            # Fallback without pandas
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                header = ['Time [s]']
                for material in results.parameters.materials:
                    header.extend([f'{material} Flow [kg/s]', f'{material} Proportion [%]'])
                header.append('Total Flow [kg/s]')
                writer.writerow(header)
                
                # Write data
                time_array = results.get_time_array()
                for i in range(len(time_array)):
                    row = [time_array[i]]
                    for j in range(len(results.parameters.materials)):
                        row.extend([
                            results.flow_data[i, j],
                            results.proportion_data[i, j]
                        ])
                    row.append(results.flow_data[i, -1])
                    writer.writerow(row)
            
            return True
            
        except Exception as e:
            raise FileHandlingError(f"Failed to export CSV: {str(e)}")
