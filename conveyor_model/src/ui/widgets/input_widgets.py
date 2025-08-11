from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QDoubleSpinBox, QLabel, QGroupBox)
from PyQt5.QtCore import pyqtSignal
from ...utils.exceptions import ValidationError

class InputPanel(QWidget):
    """Panel for basic simulation parameters"""
    
    run_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Group box for parameters
        group = QGroupBox("Simulation Parameters")
        form_layout = QFormLayout()
        
        # Total time input
        self.total_time_input = QDoubleSpinBox()
        self.total_time_input.setRange(0.1, 86400.0)  # Up to 24 hours
        self.total_time_input.setValue(100.0)
        self.total_time_input.setSuffix(" s")
        self.total_time_input.setDecimals(1)
        form_layout.addRow("Simulation Time:", self.total_time_input)
        
        # Conveyor length
        self.length_input = QDoubleSpinBox()
        self.length_input.setRange(1.0, 10000.0)
        self.length_input.setValue(100.0)
        self.length_input.setSuffix(" m")
        self.length_input.setDecimals(1)
        form_layout.addRow("Conveyor Length:", self.length_input)
        
        # Resolution size
        self.resolution_input = QDoubleSpinBox()
        self.resolution_input.setRange(0.1, 10.0)
        self.resolution_input.setValue(1.0)
        self.resolution_input.setSuffix(" m")
        self.resolution_input.setDecimals(2)
        form_layout.addRow("Resolution Size:", self.resolution_input)
        
        # Conveyor velocity
        self.velocity_input = QDoubleSpinBox()
        self.velocity_input.setRange(0.1, 50.0)
        self.velocity_input.setValue(2.0)
        self.velocity_input.setSuffix(" m/s")
        self.velocity_input.setDecimals(2)
        form_layout.addRow("Conveyor Velocity:", self.velocity_input)
        
        group.setLayout(form_layout)
        layout.addWidget(group)
        
        # Run button
        self.run_button = QPushButton("Run Simulation")
        self.run_button.clicked.connect(self.run_requested.emit)
        layout.addWidget(self.run_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_parameters(self) -> dict:
        """Get current parameter values"""
        return {
            'total_time': self.total_time_input.value(),
            'conveyor_length': self.length_input.value(),
            'resolution_size': self.resolution_input.value(),
            'conveyor_velocity': self.velocity_input.value()
        }
    
    def set_parameters(self, params: dict):
        """Set parameter values"""
        if 'total_time' in params:
            self.total_time_input.setValue(float(params['total_time']))
        if 'conveyor_length' in params:
            self.length_input.setValue(float(params['conveyor_length']))
        if 'resolution_size' in params:
            self.resolution_input.setValue(float(params['resolution_size']))
        if 'conveyor_velocity' in params:
            self.velocity_input.setValue(float(params['conveyor_velocity']))
    
    def clear(self):
        """Reset to default values"""
        self.total_time_input.setValue(100.0)
        self.length_input.setValue(100.0)
        self.resolution_input.setValue(1.0)
        self.velocity_input.setValue(2.0)