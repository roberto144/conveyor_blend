"""Base visualization module for common plotting functionality"""

from matplotlib.figure import Figure
import numpy as np
from typing import List, Optional, Dict, Any

class BaseVisualizer:
    """Base class for all visualization components"""
    
    def __init__(self, figure: Optional[Figure] = None):
        self._figure = figure
        self._axes = {}
    
    @property
    def figure(self) -> Optional[Figure]:
        """Get current figure"""
        return self._figure
    
    @figure.setter
    def figure(self, fig: Optional[Figure]):
        """Set current figure"""
        self._figure = fig
    
    @property
    def axes(self) -> Dict[str, Any]:
        """Get axes dictionary"""
        return self._axes
    
    @axes.setter
    def axes(self, axes_dict: Dict[str, Any]):
        """Set axes dictionary"""
        self._axes = axes_dict
    
    def setup_figure(self, figsize: tuple = (12, 8)):
        """Initialize or reset figure"""
        if self._figure is not None:
            self._figure.clear()
        else:
            self._figure = Figure(figsize=figsize)
    
    def clear(self):
        """Clear all axes"""
        for ax in self._axes.values():
            if ax is not None:
                ax.clear()
    
    def update(self):
        """Update all plots"""
        if self._figure and hasattr(self._figure, 'canvas'):
            self._figure.canvas.draw()
    
    def export(self, filename: str, dpi: int = 300):
        """Export figure to file"""
        if self.figure:
            self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')
    
    def _setup_grid(self, alpha: float = 0.3):
        """Apply standard grid to all axes"""
        for ax in self.axes.values():
            if ax is not None:
                ax.grid(True, alpha=alpha)
                
    def _format_axis(self, ax, title: str, xlabel: str, ylabel: str):
        """Apply standard formatting to axis"""
        if ax is not None:
            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.grid(True, alpha=0.3)