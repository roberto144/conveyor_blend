"""Integration module for blast furnace bunker visualization"""

import os
import sys
from pathlib import Path
module_path = str(Path(__file__).resolve().parents[3])  # Add project root to path
sys.path.append(module_path)

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar

from src.visualization.bunker_visualizer import BunkerVisualizer
from src.simulation.bf_bunker_viz import BlastFurnaceBunker

class BunkerVisualizationWidget(QWidget):
    """Widget for embedding bunker visualization in Qt"""
    
    def __init__(self, bunker: BlastFurnaceBunker, parent=None):
        super().__init__(parent)
        self.bunker = bunker
        self.viz = None
        self.canvas = None
        self.toolbar = None
        self._layout = None  # Use different name to avoid conflict
        self.setup_ui()
        self.setup_visualization()
    
    def setup_ui(self):
        """Initialize widget layout"""
        layout = QVBoxLayout()  # Local variable
        self.setLayout(layout)
        self._layout = layout  # Store reference if needed
    
    def setup_visualization(self):
        """Set up bunker visualization"""
        try:
            # Create figure and visualizer
            fig = Figure(figsize=(12, 8))
            self.viz = BunkerVisualizer(self.bunker, fig)
            
            # Create canvas and toolbar
            self.canvas = FigureCanvas(self.viz.figure)
            self.toolbar = NavigationToolbar(self.canvas, self)
            
            # Add to layout
            layout = self.layout()  # Get current layout
            if layout:
                layout.addWidget(self.toolbar)
                layout.addWidget(self.canvas)
            
            # Initial plots
            self.update_plots()
            
        except Exception as e:
            QMessageBox.critical(self, "Visualization Error", 
                               f"Failed to initialize visualization: {str(e)}")
            
    def update_plots(self):
        """Update all plots"""
        if not self.viz or not self.canvas:
            return
            
        try:
            self.viz.plot_bunker()
            self.viz.plot_chemistry()
            self.viz.plot_timeline()
            self.canvas.draw()
        except Exception as e:
            QMessageBox.warning(self, "Update Error",
                              f"Failed to update plots: {str(e)}")
    
    def clear_plots(self):
        """Clear all plots"""
        if self.viz:
            self.viz.clear()
            if self.canvas:
                self.canvas.draw()
                
    def save_figure(self, filename: str, dpi: int = 300):
        """Save current figure to file"""
        if self.viz and self.viz.figure:
            self.viz.figure.savefig(filename, dpi=dpi, bbox_inches='tight')