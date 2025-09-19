"""
Blast Furnace Bunker Visualization Module
Focuses on chemical composition tracking and material layering visualization
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import matplotlib.gridspec as gridspec
from datetime import datetime

@dataclass
class MaterialLayer:
    """Represents a layer of material in the bunker"""
    material_name: str
    volume: float  # m³
    height: float  # m height of this layer
    position: float  # m from bottom of bunker
    timestamp: float  # when deposited
    
    # Chemical composition
    fe_content: float  # % Iron
    sio2_content: float  # % Silica  
    cao_content: float  # % Lime
    mgo_content: float  # % Magnesia
    al2o3_content: float  # % Alumina
    
    @property
    def basicity_b2(self) -> float:
        """Calculate binary basicity CaO/SiO2"""
        return self.cao_content / self.sio2_content if self.sio2_content > 0 else 0
    
    @property
    def basicity_b4(self) -> float:
        """Calculate quaternary basicity (CaO+MgO)/(SiO2+Al2O3)"""
        basic = self.cao_content + self.mgo_content
        acidic = self.sio2_content + self.al2o3_content
        return basic / acidic if acidic > 0 else 0

@dataclass
class BlastFurnaceBunker:
    """Simplified bunker focused on material layering and chemistry"""
    bunker_id: str
    diameter: float  # m - assuming cylindrical bunker
    height: float  # m - total height
    
    # Material layers (bottom to top)
    layers: List[MaterialLayer] = field(default_factory=list)
    
    # Discharge parameters
    discharge_diameter: float = 1.2  # m
    discharge_angle: float = 60.0  # degrees - cone angle
    
    def add_material_layer(self, material_name: str, volume: float, 
                          chemistry: Dict[str, float], timestamp: float):
        """Add a new material layer on top"""
        # Calculate layer height based on volume and diameter
        cross_section = np.pi * (self.diameter / 2) ** 2
        layer_height = volume / cross_section
        
        # Determine position (on top of existing layers)
        current_top = sum(layer.height for layer in self.layers)
        
        if current_top + layer_height > self.height:
            # Bunker overflow protection
            layer_height = self.height - current_top
            volume = layer_height * cross_section
        
        layer = MaterialLayer(
            material_name=material_name,
            volume=volume,
            height=layer_height,
            position=current_top,
            timestamp=timestamp,
            fe_content=chemistry.get('Fe', 0),
            sio2_content=chemistry.get('SiO2', 0),
            cao_content=chemistry.get('CaO', 0),
            mgo_content=chemistry.get('MgO', 0),
            al2o3_content=chemistry.get('Al2O3', 0)
        )
        
        self.layers.append(layer)
    
    def get_discharge_sequence(self, discharge_volume: float) -> List[Tuple[MaterialLayer, float]]:
        """
        Get the sequence of materials that will be discharged
        Returns list of (layer, volume_from_layer) tuples
        """
        if not self.layers:
            return []
        
        discharge_sequence = []
        remaining_volume = discharge_volume
        
        # Discharge from bottom up
        for layer in self.layers:
            if remaining_volume <= 0:
                break
                
            layer_volume = min(layer.volume, remaining_volume)
            discharge_sequence.append((layer, layer_volume))
            remaining_volume -= layer_volume
        
        return discharge_sequence
    
    def calculate_discharge_chemistry(self, discharge_volume: float) -> Dict[str, float]:
        """Calculate the blended chemistry of discharged material"""
        sequence = self.get_discharge_sequence(discharge_volume)
        
        if not sequence:
            return {}
        
        # Weighted average of chemistry
        total_volume = sum(vol for _, vol in sequence)
        chemistry = {
            'Fe': 0, 'SiO2': 0, 'CaO': 0, 'MgO': 0, 'Al2O3': 0
        }
        
        for layer, volume in sequence:
            weight = volume / total_volume
            chemistry['Fe'] += layer.fe_content * weight
            chemistry['SiO2'] += layer.sio2_content * weight
            chemistry['CaO'] += layer.cao_content * weight
            chemistry['MgO'] += layer.mgo_content * weight
            chemistry['Al2O3'] += layer.al2o3_content * weight
        
        # Calculate basicity of blend
        chemistry['B2'] = chemistry['CaO'] / chemistry['SiO2'] if chemistry['SiO2'] > 0 else 0
        chemistry['B4'] = ((chemistry['CaO'] + chemistry['MgO']) / 
                          (chemistry['SiO2'] + chemistry['Al2O3']) 
                          if (chemistry['SiO2'] + chemistry['Al2O3']) > 0 else 0)
        
        return chemistry

class BunkerVisualization:
    """Visualization for bunker material layers and chemistry trends"""
    
    def __init__(self, bunker: BlastFurnaceBunker):
        self.bunker = bunker
        self.fig = None
        self.axes = None
        
    def create_visualization(self, figsize=(15, 10)):
        """Create the main visualization figure"""
        self.fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(2, 3, figure=self.fig, height_ratios=[2, 1])
        
        # Main bunker cross-section view
        self.ax_bunker = self.fig.add_subplot(gs[0, 0])
        self.ax_bunker.set_title('Bunker Material Layers', fontsize=12, fontweight='bold')
        
        # Chemistry profile along height
        self.ax_chemistry = self.fig.add_subplot(gs[0, 1])
        self.ax_chemistry.set_title('Chemistry vs Height', fontsize=12, fontweight='bold')
        
        # Basicity profile
        self.ax_basicity = self.fig.add_subplot(gs[0, 2])
        self.ax_basicity.set_title('Basicity Profile', fontsize=12, fontweight='bold')
        
        # Time series of discharge chemistry
        self.ax_fe_trend = self.fig.add_subplot(gs[1, 0])
        self.ax_fe_trend.set_title('Fe Content Trend', fontsize=10)
        
        self.ax_sio2_trend = self.fig.add_subplot(gs[1, 1])
        self.ax_sio2_trend.set_title('SiO2 Content Trend', fontsize=10)
        
        self.ax_basicity_trend = self.fig.add_subplot(gs[1, 2])
        self.ax_basicity_trend.set_title('Basicity (B2) Trend', fontsize=10)
        
        plt.tight_layout()
        
    def update_bunker_view(self):
        """Update the bunker cross-section visualization"""
        self.ax_bunker.clear()
        
        # Draw bunker outline
        bunker_width = self.bunker.diameter
        bunker_height = self.bunker.height
        
        # Bunker walls
        self.ax_bunker.plot([0, 0], [0, bunker_height], 'k-', linewidth=2)
        self.ax_bunker.plot([bunker_width, bunker_width], [0, bunker_height], 'k-', linewidth=2)
        
        # Draw discharge cone
        cone_height = (bunker_width - self.bunker.discharge_diameter) / 2 * np.tan(np.radians(self.bunker.discharge_angle))
        self.ax_bunker.plot([0, bunker_width/2 - self.bunker.discharge_diameter/2], [0, cone_height], 'k-', linewidth=1)
        self.ax_bunker.plot([bunker_width, bunker_width/2 + self.bunker.discharge_diameter/2], [0, cone_height], 'k-', linewidth=1)
        
        # Color map for different materials
        material_colors = {
            'Pellets': '#8B4513',      # Brown
            'Sinter': '#CD853F',       # Peru
            'Lump Ore': '#A0522D',     # Sienna
            'Limestone': '#D3D3D3',    # Light gray
            'Dolomite': '#C0C0C0',     # Silver
            'Coke': '#2F4F4F',         # Dark slate gray
            'Quartzite': '#FFE4B5'     # Moccasin
        }
        
        # Draw material layers
        for layer in self.bunker.layers:
            color = material_colors.get(layer.material_name.split('_')[0], '#808080')
            
            rect = Rectangle((0, layer.position), bunker_width, layer.height,
                           facecolor=color, edgecolor='black', linewidth=0.5,
                           alpha=0.8)
            self.ax_bunker.add_patch(rect)
            
            # Add material label if layer is thick enough
            if layer.height > bunker_height * 0.03:
                label_text = f"{layer.material_name[:8]}\nFe:{layer.fe_content:.1f}%"
                self.ax_bunker.text(bunker_width/2, layer.position + layer.height/2,
                                   label_text, ha='center', va='center',
                                   fontsize=8, color='white', weight='bold')
        
        # Add fill level indicator
        fill_height = sum(layer.height for layer in self.bunker.layers)
        fill_percent = (fill_height / bunker_height) * 100
        self.ax_bunker.text(bunker_width + 0.5, fill_height, f'{fill_percent:.1f}%',
                          ha='left', va='center', fontsize=10)
        
        self.ax_bunker.set_xlim(-0.5, bunker_width + 2)
        self.ax_bunker.set_ylim(0, bunker_height * 1.1)
        self.ax_bunker.set_xlabel('Width (m)')
        self.ax_bunker.set_ylabel('Height (m)')
        self.ax_bunker.grid(True, alpha=0.3)
        self.ax_bunker.set_aspect('equal')
        
    def update_chemistry_profile(self):
        """Update the chemistry vs height profile"""
        self.ax_chemistry.clear()
        
        if not self.bunker.layers:
            return
        
        heights = []
        fe_values = []
        sio2_values = []
        cao_values = []
        
        for layer in self.bunker.layers:
            # Sample at bottom and top of each layer
            heights.extend([layer.position, layer.position + layer.height])
            fe_values.extend([layer.fe_content, layer.fe_content])
            sio2_values.extend([layer.sio2_content, layer.sio2_content])
            cao_values.extend([layer.cao_content, layer.cao_content])
        
        self.ax_chemistry.plot(fe_values, heights, 'r-', linewidth=2, label='Fe')
        self.ax_chemistry.plot(sio2_values, heights, 'b-', linewidth=2, label='SiO2')
        self.ax_chemistry.plot(cao_values, heights, 'g-', linewidth=2, label='CaO')
        
        self.ax_chemistry.set_xlabel('Content (%)')
        self.ax_chemistry.set_ylabel('Height (m)')
        self.ax_chemistry.legend(loc='best')
        self.ax_chemistry.grid(True, alpha=0.3)
        self.ax_chemistry.set_xlim(0, max(max(fe_values, default=1), max(sio2_values, default=1), 
                                         max(cao_values, default=1)) * 1.1)
        
    def update_basicity_profile(self):
        """Update the basicity profile"""
        self.ax_basicity.clear()
        
        if not self.bunker.layers:
            return
        
        heights = []
        b2_values = []
        b4_values = []
        
        for layer in self.bunker.layers:
            heights.extend([layer.position, layer.position + layer.height])
            b2_values.extend([layer.basicity_b2, layer.basicity_b2])
            b4_values.extend([layer.basicity_b4, layer.basicity_b4])
        
        self.ax_basicity.plot(b2_values, heights, 'm-', linewidth=2, label='B2 (CaO/SiO2)')
        self.ax_basicity.plot(b4_values, heights, 'c-', linewidth=2, label='B4')
        
        # Add target basicity lines
        self.ax_basicity.axvline(x=1.1, color='gray', linestyle='--', alpha=0.5, label='Target B2')
        
        self.ax_basicity.set_xlabel('Basicity')
        self.ax_basicity.set_ylabel('Height (m)')
        self.ax_basicity.legend(loc='best')
        self.ax_basicity.grid(True, alpha=0.3)
        self.ax_basicity.set_xlim(0, 2.0)
        
    def simulate_discharge_trends(self, n_charges: int = 20, charge_volume: float = 50):
        """Simulate discharge chemistry over multiple charges"""
        time_points = []
        fe_trends = []
        sio2_trends = []
        basicity_trends = []
        
        for i in range(n_charges):
            chemistry = self.bunker.calculate_discharge_chemistry(charge_volume)
            if chemistry:
                time_points.append(i)
                fe_trends.append(chemistry['Fe'])
                sio2_trends.append(chemistry['SiO2'])
                basicity_trends.append(chemistry['B2'])
        
        # Plot trends
        if time_points:
            self.ax_fe_trend.clear()
            self.ax_fe_trend.plot(time_points, fe_trends, 'r-o', markersize=4)
            self.ax_fe_trend.set_xlabel('Charge Number')
            self.ax_fe_trend.set_ylabel('Fe (%)')
            self.ax_fe_trend.grid(True, alpha=0.3)
            
            self.ax_sio2_trend.clear()
            self.ax_sio2_trend.plot(time_points, sio2_trends, 'b-o', markersize=4)
            self.ax_sio2_trend.set_xlabel('Charge Number')
            self.ax_sio2_trend.set_ylabel('SiO2 (%)')
            self.ax_sio2_trend.grid(True, alpha=0.3)
            
            self.ax_basicity_trend.clear()
            self.ax_basicity_trend.plot(time_points, basicity_trends, 'm-o', markersize=4)
            self.ax_basicity_trend.axhline(y=1.1, color='gray', linestyle='--', alpha=0.5)
            self.ax_basicity_trend.set_xlabel('Charge Number')
            self.ax_basicity_trend.set_ylabel('Basicity (B2)')
            self.ax_basicity_trend.grid(True, alpha=0.3)
    
    def update_all(self):
        """Update all visualization components"""
        self.update_bunker_view()
        self.update_chemistry_profile()
        self.update_basicity_profile()
        self.simulate_discharge_trends()
        plt.draw()

# Integration with existing UI
class BunkerChemistryWidget:
    """PyQt5 widget for bunker chemistry visualization"""
    
    def __init__(self, parent=None):
        """This would be integrated into your existing PyQt5 UI"""
        self.bunkers = {}  # bunker_id -> BlastFurnaceBunker
        self.visualizations = {}  # bunker_id -> BunkerVisualization
        
    def add_bunker(self, bunker_id: str, diameter: float, height: float):
        """Add a new bunker to track"""
        bunker = BlastFurnaceBunker(bunker_id, diameter, height)
        self.bunkers[bunker_id] = bunker
        self.visualizations[bunker_id] = BunkerVisualization(bunker)
        
    def add_material_to_bunker(self, bunker_id: str, material_name: str, 
                               volume: float, chemistry: Dict[str, float], 
                               timestamp: float):
        """Add material layer to bunker"""
        if bunker_id in self.bunkers:
            self.bunkers[bunker_id].add_material_layer(
                material_name, volume, chemistry, timestamp
            )
            
    def update_visualization(self, bunker_id: str):
        """Update visualization for specific bunker"""
        if bunker_id in self.visualizations:
            viz = self.visualizations[bunker_id]
            if viz.fig is None:
                viz.create_visualization()
            viz.update_all()
            return viz.fig
        return None

# Example usage and testing
def example_blast_furnace_charging():
    """Example of blast furnace bunker filling and discharge"""
    
    # Create a bunker
    bunker = BlastFurnaceBunker(
        bunker_id="BF1_BUNKER_01",
        diameter=6.0,  # 6m diameter
        height=20.0    # 20m height
    )
    
    # Simulate filling with different materials over time
    # Morning shift - Pellets base
    bunker.add_material_layer(
        "Pellets_A",
        volume=30,
        chemistry={'Fe': 65.5, 'SiO2': 4.2, 'CaO': 0.5, 'MgO': 0.3, 'Al2O3': 0.8},
        timestamp=0
    )
    
    # Add sinter layer
    bunker.add_material_layer(
        "Sinter_B", 
        volume=25,
        chemistry={'Fe': 57.2, 'SiO2': 9.8, 'CaO': 9.5, 'MgO': 1.2, 'Al2O3': 1.8},
        timestamp=1
    )
    
    # Add limestone for basicity control
    bunker.add_material_layer(
        "Limestone",
        volume=8,
        chemistry={'Fe': 0.5, 'SiO2': 2.0, 'CaO': 52.0, 'MgO': 2.5, 'Al2O3': 0.8},
        timestamp=2
    )
    
    # Another pellet layer
    bunker.add_material_layer(
        "Pellets_B",
        volume=28,
        chemistry={'Fe': 64.8, 'SiO2': 4.5, 'CaO': 0.6, 'MgO': 0.3, 'Al2O3': 0.9},
        timestamp=3
    )
    
    # Mixed burden layer
    bunker.add_material_layer(
        "Lump_Ore",
        volume=20,
        chemistry={'Fe': 62.0, 'SiO2': 6.5, 'CaO': 0.2, 'MgO': 0.1, 'Al2O3': 2.1},
        timestamp=4
    )
    
    # Create visualization
    viz = BunkerVisualization(bunker)
    viz.create_visualization()
    viz.update_all()
    
    # Simulate discharge analysis
    print("\nDischarge Chemistry Analysis:")
    print("=" * 50)
    for charge_num in range(1, 6):
        chemistry = bunker.calculate_discharge_chemistry(charge_volume=15)
        print(f"Charge {charge_num}:")
        print(f"  Fe: {chemistry['Fe']:.2f}%")
        print(f"  SiO2: {chemistry['SiO2']:.2f}%")
        print(f"  CaO: {chemistry['CaO']:.2f}%")
        print(f"  Basicity (B2): {chemistry['B2']:.3f}")
        print(f"  Basicity (B4): {chemistry['B4']:.3f}")
        print()
    
    plt.show()
    return bunker, viz

if __name__ == "__main__":
    bunker, viz = example_blast_furnace_charging()