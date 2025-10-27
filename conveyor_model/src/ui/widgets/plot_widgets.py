from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QGroupBox, QFileDialog, QMessageBox, QApplication)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from ...visualization.plotter import ConveyorPlotter
from ...models.simulation_data import SimulationResults

class PlotWidget(QWidget):
    """Widget containing matplotlib plots"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Group box for plots
        group = QGroupBox("Simulation Results")
        group_layout = QVBoxLayout()
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.plotter = ConveyorPlotter(self.figure)
        
        group_layout.addWidget(self.canvas)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        export_button = QPushButton("Export Plots")
        export_button.clicked.connect(self.export_plots)
        button_layout.addWidget(export_button)
        
        clear_button = QPushButton("Clear Plots")
        clear_button.clicked.connect(self.clear_plots)
        button_layout.addWidget(clear_button)
        
        button_layout.addStretch()  # Push buttons to the left
        
        group_layout.addLayout(button_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        self.setLayout(layout)
    
    def update_plots(self, results: SimulationResults):
        """Update plots with new results"""
        self.plotter.plot_results(results)
        self.current_results = results
    
    def clear_plots(self):
        """Clear all plots"""
        self.plotter.clear_plots()
        self.current_results = None
    
    def export_plots(self):
        """
        Export plots to file with progress indication
        """
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Plots", "", "PNG Files (*.png);;All Files (*)"
            )
            if filename:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self.plotter.export_plots(filename)
                QApplication.restoreOverrideCursor()
                QMessageBox.information(self, "Success", "Plots exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export plots: {str(e)}")
        """Export plots to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Plots", "", 
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)"
        )
        
        if filename:
            try:
                self.plotter.export_plots(filename)
                from ..dialogs.error_dialog import ErrorDialog
                ErrorDialog.show_info(self, "Export Success", 
                                    f"Plots exported successfully to {filename}")
            except Exception as e:
                from ..dialogs.error_dialog import ErrorDialog
                ErrorDialog.show_error(self, "Export Error", 
                                     f"Failed to export plots: {str(e)}")
