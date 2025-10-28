import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from ..models.simulation_data import SimulationResults
from ..models.material import Material
from ..models.silo import Silo

from .base_visualizer import BaseVisualizer

class ConveyorPlotter(BaseVisualizer):
    """Handles all plotting functionality for conveyor simulation"""
    
    def __init__(self, figure: Optional[Figure] = None):
        super().__init__(figure)
        self._axes_grid = np.array([[None]])  # Default empty grid
        self.setup_subplots()
    
    def setup_subplots(self):
        """Initialize subplot layout"""
        if self.figure:
            self.figure.clear()
            axes_array = self.figure.subplots(2, 2)
            if isinstance(axes_array, np.ndarray):
                self._axes_grid = axes_array.reshape(2, 2)  # Store as ndarray
            else:
                self._axes_grid = np.array([[axes_array]])  # Single subplot case
            self.figure.tight_layout(pad=3.0)
    
    @property
    def axes_grid(self) -> np.ndarray:
        """Get axes grid array"""
        return self._axes_grid
    
    def plot_results(self, results: SimulationResults):
        """
        Plot all simulation results
        
        Args:
            results (SimulationResults): The simulation results to plot
        """
        if self.figure is None:
            return
            
        self.setup_subplots()  # Ensure we have axes setup
        
        # Clear previous plots
        for ax_row in self.axes_grid:
            for ax in ax_row:
                if ax is not None:
                    ax.clear()
        
        time_array = results.get_time_array()
        materials = results.parameters.materials
        
        # Get axes for each plot and convert data types as needed
        flows_ax = self.axes_grid[0, 0]
        props_ax = self.axes_grid[1, 0]
        total_ax = self.axes_grid[0, 1]
        silo_ax = self.axes_grid[1, 1]
        
        # Create Material objects from material names
        material_objects = [
            Material(name=material_name, density=1.0)  # Default density, as it's not used in plotting
            for material_name in materials
        ]
        
        if flows_ax is not None:
            self._plot_material_flows(flows_ax, time_array, results.flow_data, material_objects)
        
        if props_ax is not None:
            self._plot_material_proportions(props_ax, time_array, results.proportion_data, material_objects)
        
        if total_ax is not None:
            self._plot_total_flow(total_ax, time_array, results.flow_data)
        
        if silo_ax is not None:
            self._plot_silo_timeline(silo_ax, results.parameters.silos)
        
        self.update()  # Use base class method to update

    def _plot_material_flows(self, ax: Axes, time_array: np.ndarray, flow_data: np.ndarray, materials: List[Material]):
        """Plot individual material flows"""
        for i, material in enumerate(materials):
            if i < flow_data.shape[1] - 2:  # Exclude time and total columns
                ax.plot(time_array, flow_data[:len(time_array), i], 
                       label=material.name, linewidth=2)
        
        ax.set_xlabel('Time (s)', fontsize=10)
        ax.set_ylabel('Flow Rate (kg/s)', fontsize=10)
        ax.set_title('Material Flow Rates', fontsize=11)
        ax.legend(fontsize=8, loc='upper left', ncol=1)
        ax.tick_params(labelsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_array) if len(time_array) > 0 else 100)
    
    def _plot_material_proportions(self, ax: Axes, time_array: np.ndarray, proportion_data: np.ndarray, materials: List[Material]):
        """Plot material proportions as stacked area chart"""
        if len(materials) == 0 or proportion_data.size == 0:
            ax.text(0.5, 0.5, 'No data to display', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=10)
            return
        
        # Prepare data for stackplot
        data_to_plot = []
        labels_to_plot = []
        
        for i, material in enumerate(materials):
            if i < proportion_data.shape[1]:
                data_to_plot.append(proportion_data[:len(time_array), i])
                labels_to_plot.append(material.name)
        
        if data_to_plot:
            ax.stackplot(time_array, *data_to_plot, labels=labels_to_plot, alpha=0.7)
        
        ax.set_xlabel('Time (s)', fontsize=10)
        ax.set_ylabel('Proportion (%)', fontsize=10)
        ax.set_title('Material Composition', fontsize=11)
        ax.legend(fontsize=8, loc='upper left', ncol=1)
        ax.tick_params(labelsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_array) if len(time_array) > 0 else 100)
        ax.set_ylim(0, 100)
    
    def _plot_total_flow(self, ax: Axes, time_array: np.ndarray, flow_data: np.ndarray):
        """Plot total flow rate"""
        if flow_data.size == 0:
            ax.text(0.5, 0.5, 'No data to display',
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=10)
            return
        
        total_flow = flow_data[:len(time_array), -1]  # Last column is total
        ax.plot(time_array, total_flow, 'b-', linewidth=2, label='Total')
        
        ax.set_xlabel('Time (s)', fontsize=10)
        ax.set_ylabel('Total Flow Rate (kg/s)', fontsize=10)
        ax.set_title('Total Belt Flow Rate', fontsize=11)
        ax.legend(fontsize=8, loc='upper left')
        ax.tick_params(labelsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_array) if len(time_array) > 0 else 100)
    
    def _plot_silo_timeline(self, ax: Axes, silos: List[Silo]):
        """Plot silo operation timeline as Gantt chart"""
        if not silos:
            ax.text(0.5, 0.5, 'No silos defined',
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes)
            return
        
        # Create Gantt chart
        for i, silo in enumerate(silos):
            start_time = silo.start_time
            duration = silo.capacity / silo.flow_rate
            
            # Create bar for silo operation
            ax.barh(i, duration, left=start_time, height=0.6, 
                   alpha=0.7, label=silo.material)
            
            # Add text annotation
            mid_time = start_time + duration / 2
            # Simplificar a exibição do texto
            ax.text(mid_time, i, f'{silo.material}\n{silo.flow_rate:.0f} kg/s',
                   horizontalalignment='center', verticalalignment='center',
                   fontsize=8)
        
        ax.set_xlabel('Time (s)', fontsize=10)
        ax.set_ylabel('Silo Number', fontsize=10)
        ax.set_title('Operation Schedule', fontsize=11)
        ax.set_yticks(range(len(silos)))
        ax.set_yticklabels([f'Silo {i+1}' for i in range(len(silos))], fontsize=9)
        ax.tick_params(labelsize=9)
        ax.grid(True, alpha=0.3, axis='x')
    
    def clear_plots(self):
        """Clear all plots"""
        if self.figure is not None:
            for ax_row in self.axes_grid:
                for ax in ax_row:
                    if ax is not None:
                        ax.clear()
            self.update()
    
    def save_figure(self, filename: str, dpi: int = 300):
        """Save the current figure to a file
        
        Args:
            filename (str): Path where the figure should be saved
            dpi (int, optional): Resolution of the output image. Defaults to 300.
        """
        if self.figure is not None:
            self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')