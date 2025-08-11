import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from typing import List, Optional
from ..models.simulation_data import SimulationResults

class ConveyorPlotter:
    """Handles all plotting functionality for conveyor simulation"""
    
    def __init__(self, figure: Figure):
        self.figure = figure
        self.axes = None
        self.setup_subplots()
    
    def setup_subplots(self):
        """Initialize subplot layout"""
        self.figure.clear()
        self.axes = self.figure.subplots(2, 2)
        self.figure.tight_layout(pad=3.0)
    
    def plot_results(self, results: SimulationResults):
        """
        Plot all simulation results
        
        Args:
            results: SimulationResults object containing data to plot
        """
        if self.axes is None:
            self.setup_subplots()
        
        # Clear previous plots
        for ax_row in self.axes:
            for ax in ax_row:
                ax.clear()
        
        time_array = results.get_time_array()
        materials = results.parameters.materials
        
        # Plot 1: Material flows over time
        self._plot_material_flows(
            self.axes[0, 0], time_array, results.flow_data, materials
        )
        
        # Plot 2: Material proportions (stacked area)
        self._plot_material_proportions(
            self.axes[1, 0], time_array, results.proportion_data, materials
        )
        
        # Plot 3: Total flow rate
        self._plot_total_flow(
            self.axes[0, 1], time_array, results.flow_data
        )
        
        # Plot 4: Silo operation timeline
        self._plot_silo_timeline(
            self.axes[1, 1], results.parameters.silos
        )
        
        self.figure.canvas.draw()
    
    def _plot_material_flows(self, ax, time_array, flow_data, materials):
        """Plot individual material flows"""
        for i, material in enumerate(materials):
            if i < flow_data.shape[1] - 2:  # Exclude time and total columns
                ax.plot(time_array, flow_data[:len(time_array), i], 
                       label=material, linewidth=2)
        
        ax.set_xlabel('Time [s]')
        ax.set_ylabel('Material Flow [kg/s]')
        ax.set_title('Material Flows at Conveyor End')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_array) if len(time_array) > 0 else 100)
    
    def _plot_material_proportions(self, ax, time_array, proportion_data, materials):
        """Plot material proportions as stacked area chart"""
        if len(materials) == 0 or proportion_data.size == 0:
            ax.text(0.5, 0.5, 'No data to display', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes)
            return
        
        # Prepare data for stackplot
        data_to_plot = []
        labels_to_plot = []
        
        for i, material in enumerate(materials):
            if i < proportion_data.shape[1]:
                data_to_plot.append(proportion_data[:len(time_array), i])
                labels_to_plot.append(material)
        
        if data_to_plot:
            ax.stackplot(time_array, *data_to_plot, labels=labels_to_plot, alpha=0.7)
        
        ax.set_xlabel('Time [s]')
        ax.set_ylabel('Material Proportion [%]')
        ax.set_title('Material Proportions in Conveyor Belt')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_array) if len(time_array) > 0 else 100)
        ax.set_ylim(0, 100)
    
    def _plot_total_flow(self, ax, time_array, flow_data):
        """Plot total flow rate"""
        if flow_data.size == 0:
            ax.text(0.5, 0.5, 'No data to display',
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes)
            return
        
        total_flow = flow_data[:len(time_array), -1]  # Last column is total
        ax.plot(time_array, total_flow, 'b-', linewidth=2, label='Total Flow')
        
        ax.set_xlabel('Time [s]')
        ax.set_ylabel('Total Flow [kg/s]')
        ax.set_title('Total Flow Rate on Conveyor Belt')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_array) if len(time_array) > 0 else 100)
    
    def _plot_silo_timeline(self, ax, silos):
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
                   alpha=0.7, label=f'{silo.material}')
            
            # Add text annotation
            mid_time = start_time + duration / 2
            ax.text(mid_time, i, f'{silo.material}\n{silo.flow_rate:.1f} kg/s',
                   horizontalalignment='center', verticalalignment='center',
                   fontsize=8)
        
        ax.set_xlabel('Time [s]')
        ax.set_ylabel('Silo Number')
        ax.set_title('Silo Operation Timeline')
        ax.set_yticks(range(len(silos)))
        ax.set_yticklabels([f'Silo {i+1}' for i in range(len(silos))])
        ax.grid(True, alpha=0.3, axis='x')
    
    def clear_plots(self):
        """Clear all plots"""
        if self.axes is not None:
            for ax_row in self.axes:
                for ax in ax_row:
                    ax.clear()
            self.figure.canvas.draw()
    
    def export_plots(self, filename: str, dpi: int = 300):
        """Export current plots to file"""
        self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')