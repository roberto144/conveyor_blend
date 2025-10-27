"""Bunker visualization module using the base visualizer"""

import numpy as np
from typing import List, Optional, Dict
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from datetime import datetime
from matplotlib.patches import Rectangle

from .base_visualizer import BaseVisualizer
from ..models.material import Material
from ..simulation.bf_bunker_viz import BlastFurnaceBunker, MaterialLayer

class BunkerVisualizer(BaseVisualizer):
    """Visualizer for blast furnace bunker data"""
    
    def __init__(self, bunker: BlastFurnaceBunker, figure: Optional[Figure] = None):
        """Initialize bunker visualizer
        
        Args:
            bunker (BlastFurnaceBunker): The bunker to visualize
            figure (Optional[Figure], optional): Matplotlib figure. Defaults to None.
        """
        super().__init__(figure)
        self.bunker = bunker
        self._init_plot()
    
    def _init_plot(self, figsize: tuple = (12, 8)) -> None:
        """Initialize the plot layout and axes
        
        Args:
            figsize (tuple, optional): Figure size. Defaults to (12, 8).
        """
        self.setup_figure(figsize)
        
        if self.figure is None:
            return
            
        grid = GridSpec(2, 2, figure=self.figure)
        
        # Assign axes
        self.axes = {
            'bunker': self.figure.add_subplot(grid[0, 0]),  # Bunker shape
            'chemistry': self.figure.add_subplot(grid[0, 1]),  # Chemistry profile
            'timeline': self.figure.add_subplot(grid[1, :])  # Material timeline
        }
        
        self.figure.tight_layout(pad=3.0)
    
    def plot_bunker(self):
        """Draw the current state of the bunker"""
        if not self.figure or 'bunker' not in self._axes:
            return
            
        ax = self._axes['bunker']
        ax.clear()
        
        # Draw bunker outline
        radius = self.bunker.diameter / 2
        height = self.bunker.height
        
        # Outer shell
        ax.add_patch(Rectangle((-radius, 0), self.bunker.diameter, height, 
                                fill=False, color='black'))
        
        # Draw layers
        current_height = 0
        for layer in self.bunker.layers:
            ax.add_patch(Rectangle((-radius, current_height),
                                    self.bunker.diameter, layer.height,
                                    alpha=0.5,
                                    label=layer.material_name))
            current_height += layer.height
            
        ax.set_xlim(-radius*1.2, radius*1.2)
        ax.set_ylim(0, height*1.1)
        ax.set_title('Bunker Content')
        ax.legend()
        ax.grid(True)
        
    def plot_chemistry(self):
        """Plot chemical composition profile"""
        if not self.figure or 'chemistry' not in self._axes:
            return
            
        ax = self._axes['chemistry']
        ax.clear()
        
        if not self.bunker.layers:
            ax.text(0.5, 0.5, 'No data available',
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes)
            return
            
        # Prepare data
        heights = [layer.position + layer.height/2 for layer in self.bunker.layers]
        fe_content = [layer.fe_content for layer in self.bunker.layers]
        b2 = [layer.basicity_b2 for layer in self.bunker.layers]
        b4 = [layer.basicity_b4 for layer in self.bunker.layers]
        
        # Plot profiles
        ax.plot(fe_content, heights, 'b-', label='Fe%')
        ax.plot(b2, heights, 'r-', label='B2')
        ax.plot(b4, heights, 'g-', label='B4')
        
        ax.set_title('Chemical Profile')
        ax.set_xlabel('Content %')
        ax.set_ylabel('Height (m)')
        ax.legend()
        ax.grid(True)
        
    def plot_timeline(self):
        """Plot material addition timeline"""
        if not self.figure or 'timeline' not in self._axes:
            return
            
        ax = self._axes['timeline']
        ax.clear()
        
        if not self.bunker.layers:
            ax.text(0.5, 0.5, 'No data available',
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes)
            return
            
        # Convert timestamps to datetime and normalize
        base_time = min(layer.timestamp for layer in self.bunker.layers)
        times = [(layer.timestamp - base_time)/3600 for layer in self.bunker.layers]
        
        # Plot material additions
        materials = list(set(layer.material_name for layer in self.bunker.layers))
        for i, material in enumerate(materials):
            material_times = [t for t, layer in zip(times, self.bunker.layers)
                           if layer.material_name == material]
            material_volumes = [layer.volume for layer in self.bunker.layers 
                             if layer.material_name == material]
            
            ax.scatter(material_times, [i]*len(material_times),
                      s=np.array(material_volumes)*50, # Scale marker size with volume
                      alpha=0.6,
                      label=material)
            
        ax.set_title('Material Addition Timeline')
        ax.set_xlabel('Time (hours)')
        ax.set_yticks(range(len(materials)))
        ax.set_yticklabels(materials)
        ax.grid(True)
        
    def update(self):
        """Update all plots"""
        self.plot_bunker()
        self.plot_chemistry()
        self.plot_timeline()
        super().update()