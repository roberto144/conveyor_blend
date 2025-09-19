# src/simulation/bf_conveyor_bunker_integration.py
"""
Enhanced Blast Furnace Integration Module
Connects conveyor discharge to bunker charging sequence for realistic BF operation
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from ..models.simulation_data import SimulationResults, SimulationParameters
from .bf_bunker_viz import BlastFurnaceBunker, MaterialLayer

@dataclass
class TransferBin:
    """Represents the transfer bin between conveyor and bunker"""
    bin_id: str
    capacity: float  # m³
    current_volume: float = 0.0
    material_layers: List[Dict] = field(default_factory=list)
    
    def add_material(self, material_name: str, volume: float, chemistry: Dict[str, float], timestamp: float):
        """Add material from conveyor discharge to transfer bin"""
        if self.current_volume + volume > self.capacity:
            # Handle overflow - either reject or discharge to make space
            excess = (self.current_volume + volume) - self.capacity
            print(f"Warning: Transfer bin overflow of {excess:.2f} m³")
            volume = self.capacity - self.current_volume
        
        if volume > 0:
            self.material_layers.append({
                'material_name': material_name,
                'volume': volume,
                'chemistry': chemistry,
                'timestamp': timestamp
            })
            self.current_volume += volume
    
    def discharge_material(self, volume_to_discharge: float) -> List[Dict]:
        """Discharge material from transfer bin (FIFO - first in, first out)"""
        discharged_materials = []
        remaining_discharge = volume_to_discharge
        
        while remaining_discharge > 0 and self.material_layers:
            layer = self.material_layers[0]
            
            if layer['volume'] <= remaining_discharge:
                # Discharge entire layer
                discharged_materials.append(layer.copy())
                remaining_discharge -= layer['volume']
                self.current_volume -= layer['volume']
                self.material_layers.pop(0)
            else:
                # Discharge partial layer
                partial_layer = layer.copy()
                partial_layer['volume'] = remaining_discharge
                discharged_materials.append(partial_layer)
                
                # Update remaining layer
                layer['volume'] -= remaining_discharge
                self.current_volume -= remaining_discharge
                remaining_discharge = 0
        
        return discharged_materials

@dataclass
class ConveyorToBunkerSystem:
    """Manages the complete conveyor-to-bunker material flow system"""
    transfer_bin: TransferBin
    bunker: BlastFurnaceBunker
    conveyor_results: Optional[SimulationResults] = None
    material_chemistry_db: Dict = field(default_factory=dict)
    
    # Operating parameters
    bin_discharge_rate: float = 50.0  # m³/h standard discharge rate
    auto_discharge_enabled: bool = True
    bin_level_high_trigger: float = 0.8  # Discharge when 80% full
    bin_level_low_trigger: float = 0.2   # Stop discharge when 20% full
    
    def process_conveyor_discharge(self, simulation_results: SimulationResults):
        """Process conveyor simulation results and feed to transfer bin"""
        self.conveyor_results = simulation_results
        
        if not hasattr(simulation_results.parameters, 'material_chemistry'):
            raise ValueError("BF mode required - material chemistry data missing")
        
        self.material_chemistry_db = simulation_results.parameters.material_chemistry
        
        # Process each time step of conveyor discharge
        time_array = simulation_results.get_time_array()
        flow_data = simulation_results.flow_data
        
        print(f"Processing {len(time_array)} time steps of conveyor discharge...")
        
        for i, time_point in enumerate(time_array):
            if i >= flow_data.shape[0]:
                break
            
            # Get material flows at conveyor discharge point
            material_flows = flow_data[i, :-2]  # Exclude time and total columns
            total_flow = flow_data[i, -1]
            
            if total_flow > 1e-6:  # Significant flow
                # Calculate time step
                dt = time_array[1] - time_array[0] if len(time_array) > 1 else 1.0
                
                # Convert mass flow to volume and add to transfer bin
                self._add_conveyor_materials_to_bin(material_flows, dt, time_point)
            
            # Check if automatic discharge should occur
            if self.auto_discharge_enabled:
                self._check_auto_discharge(time_point)
    
    def _add_conveyor_materials_to_bin(self, material_flows: np.ndarray, dt: float, timestamp: float):
        """Add materials from conveyor discharge to transfer bin"""
        materials = list(self.material_chemistry_db.keys())
        
        for i, flow_rate in enumerate(material_flows):
            if flow_rate > 0 and i < len(materials):
                material_name = materials[i]
                
                # Convert mass flow to volume flow
                density = self.material_chemistry_db[material_name].get('density', 2000)  # kg/m³
                mass_added = flow_rate * dt  # kg
                volume_added = mass_added / density  # m³
                
                # Get chemistry data
                chemistry = self.material_chemistry_db[material_name]['chemistry']
                
                # Add to transfer bin
                self.transfer_bin.add_material(material_name, volume_added, chemistry, timestamp)
    
    def _check_auto_discharge(self, current_time: float):
        """Check if automatic discharge should occur based on bin level"""
        fill_ratio = self.transfer_bin.current_volume / self.transfer_bin.capacity
        
        if fill_ratio >= self.bin_level_high_trigger:
            # Discharge material to bunker
            discharge_volume = (fill_ratio - self.bin_level_low_trigger) * self.transfer_bin.capacity
            self.discharge_to_bunker(discharge_volume, current_time)
    
    def discharge_to_bunker(self, volume: float, timestamp: float):
        """Discharge material from transfer bin to bunker"""
        discharged_materials = self.transfer_bin.discharge_material(volume)
        
        for material_data in discharged_materials:
            self.bunker.add_material_layer(
                material_name=material_data['material_name'],
                volume=material_data['volume'],
                chemistry=material_data['chemistry'],
                timestamp=timestamp
            )
        
        print(f"Discharged {volume:.2f} m³ to bunker at time {timestamp:.1f}s")
    
    def manual_discharge_to_bunker(self, volume: float, timestamp: float):
        """Manually discharge specified volume to bunker"""
        if volume > self.transfer_bin.current_volume:
            volume = self.transfer_bin.current_volume
            print(f"Warning: Requested volume exceeds bin contents. Discharging {volume:.2f} m³")
        
        self.discharge_to_bunker(volume, timestamp)
    
    def get_bin_status(self) -> Dict:
        """Get current transfer bin status"""
        fill_percentage = (self.transfer_bin.current_volume / self.transfer_bin.capacity) * 100
        
        # Calculate current chemistry if materials present
        current_chemistry = None
        if self.transfer_bin.material_layers:
            current_chemistry = self._calculate_bin_chemistry()
        
        return {
            'current_volume': self.transfer_bin.current_volume,
            'capacity': self.transfer_bin.capacity,
            'fill_percentage': fill_percentage,
            'layer_count': len(self.transfer_bin.material_layers),
            'current_chemistry': current_chemistry,
            'can_discharge': self.transfer_bin.current_volume > 0
        }
    
    def _calculate_bin_chemistry(self) -> Dict[str, float]:
        """Calculate weighted average chemistry of materials in bin"""
        if not self.transfer_bin.material_layers:
            return {}
        
        total_volume = sum(layer['volume'] for layer in self.transfer_bin.material_layers)
        if total_volume == 0:
            return {}
        
        chemistry_sum = {'Fe': 0, 'SiO2': 0, 'CaO': 0, 'MgO': 0, 'Al2O3': 0}
        
        for layer in self.transfer_bin.material_layers:
            weight = layer['volume'] / total_volume
            for element in chemistry_sum.keys():
                chemistry_sum[element] += layer['chemistry'].get(element, 0) * weight
        
        # Calculate basicity
        chemistry_sum['B2'] = chemistry_sum['CaO'] / max(chemistry_sum['SiO2'], 0.1)
        chemistry_sum['B4'] = ((chemistry_sum['CaO'] + chemistry_sum['MgO']) / 
                              max((chemistry_sum['SiO2'] + chemistry_sum['Al2O3']), 0.1))
        
        return chemistry_sum
    
    def get_bunker_charging_sequence(self) -> List[Dict]:
        """Get the sequence of materials charged to bunker"""
        return [
            {
                'material': layer.material_name,
                'volume': layer.volume,
                'timestamp': layer.timestamp,
                'chemistry': {
                    'Fe': layer.fe_content,
                    'SiO2': layer.sio2_content,
                    'CaO': layer.cao_content,
                    'MgO': layer.mgo_content,
                    'Al2O3': layer.al2o3_content
                }
            }
            for layer in self.bunker.layers
        ]
    
    def export_material_flow_report(self, filename: str):
        """Export comprehensive material flow report"""
        import csv
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header section
            writer.writerow(['=== BLAST FURNACE MATERIAL FLOW REPORT ==='])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # System configuration
            writer.writerow(['=== SYSTEM CONFIGURATION ==='])
            writer.writerow(['Component', 'Parameter', 'Value', 'Unit'])
            writer.writerow(['Transfer Bin', 'Capacity', f"{self.transfer_bin.capacity:.1f}", 'm³'])
            writer.writerow(['Transfer Bin', 'Current Volume', f"{self.transfer_bin.current_volume:.1f}", 'm³'])
            writer.writerow(['Transfer Bin', 'Fill Level', f"{(self.transfer_bin.current_volume/self.transfer_bin.capacity)*100:.1f}", '%'])
            writer.writerow(['Bunker', 'Diameter', f"{self.bunker.diameter:.1f}", 'm'])
            writer.writerow(['Bunker', 'Height', f"{self.bunker.height:.1f}", 'm'])
            writer.writerow(['Bunker', 'Layer Count', f"{len(self.bunker.layers)}", '-'])
            writer.writerow([])
            
            # Conveyor discharge summary
            if self.conveyor_results:
                writer.writerow(['=== CONVEYOR DISCHARGE SUMMARY ==='])
                total_mass = np.sum(self.conveyor_results.flow_data[:, :-2]) * \
                           (self.conveyor_results.get_time_array()[1] - self.conveyor_results.get_time_array()[0] 
                            if len(self.conveyor_results.get_time_array()) > 1 else 1.0)
                writer.writerow(['Total Mass Discharged', f"{total_mass:.1f}", 'kg'])
                writer.writerow(['Simulation Duration', f"{self.conveyor_results.parameters.total_time:.1f}", 's'])
                writer.writerow([])
            
            # Transfer bin material layers
            writer.writerow(['=== TRANSFER BIN CONTENTS ==='])
            writer.writerow(['Layer', 'Material', 'Volume (m³)', 'Fe%', 'SiO2%', 'CaO%', 'Timestamp'])
            for i, layer in enumerate(self.transfer_bin.material_layers):
                writer.writerow([
                    i+1,
                    layer['material_name'],
                    f"{layer['volume']:.2f}",
                    f"{layer['chemistry'].get('Fe', 0):.2f}",
                    f"{layer['chemistry'].get('SiO2', 0):.2f}",
                    f"{layer['chemistry'].get('CaO', 0):.2f}",
                    f"{layer['timestamp']:.1f}"
                ])
            writer.writerow([])
            
            # Bunker charging sequence
            writer.writerow(['=== BUNKER CHARGING SEQUENCE ==='])
            writer.writerow(['Charge', 'Material', 'Volume (m³)', 'Fe%', 'SiO2%', 'CaO%', 'B2', 'Timestamp'])
            for i, layer in enumerate(self.bunker.layers):
                b2 = layer.cao_content / max(layer.sio2_content, 0.1)
                writer.writerow([
                    i+1,
                    layer.material_name,
                    f"{layer.volume:.2f}",
                    f"{layer.fe_content:.2f}",
                    f"{layer.sio2_content:.2f}",
                    f"{layer.cao_content:.2f}",
                    f"{b2:.3f}",
                    f"{layer.timestamp:.1f}"
                ])

class ConveyorBunkerVisualization:
    """Visualization for the complete conveyor-to-bunker system"""
    
    def __init__(self, system: ConveyorToBunkerSystem):
        self.system = system
        self.fig = None
        
    def create_system_visualization(self, figsize=(16, 10)):
        """Create comprehensive system visualization"""
        self.fig = plt.figure(figsize=figsize)
        
        # Create 2x3 subplot layout
        gs = self.fig.add_gridspec(2, 3, height_ratios=[1, 1], width_ratios=[1, 1, 1])
        
        # Conveyor discharge flow
        self.ax_conveyor = self.fig.add_subplot(gs[0, 0])
        self.ax_conveyor.set_title('Conveyor Discharge Flow')
        
        # Transfer bin status
        self.ax_bin = self.fig.add_subplot(gs[0, 1])
        self.ax_bin.set_title('Transfer Bin Status')
        
        # Bunker layers
        self.ax_bunker = self.fig.add_subplot(gs[0, 2])
        self.ax_bunker.set_title('Bunker Material Layers')
        
        # Chemistry trends
        self.ax_chemistry = self.fig.add_subplot(gs[1, :])
        self.ax_chemistry.set_title('Material Flow Chemistry Evolution')
        
        plt.tight_layout()
        
    def update_visualization(self):
        """Update all visualization components"""
        if not self.fig:
            self.create_system_visualization()
        
        self._update_conveyor_plot()
        self._update_bin_plot()
        self._update_bunker_plot()
        self._update_chemistry_plot()
        
        self.fig.canvas.draw() if hasattr(self.fig, 'canvas') else None
    
    def _update_conveyor_plot(self):
        """Update conveyor discharge plot"""
        self.ax_conveyor.clear()
        
        if not self.system.conveyor_results:
            self.ax_conveyor.text(0.5, 0.5, 'No conveyor data available', 
                                ha='center', va='center', transform=self.ax_conveyor.transAxes)
            return
        
        time_array = self.system.conveyor_results.get_time_array()
        flow_data = self.system.conveyor_results.flow_data
        materials = self.system.conveyor_results.parameters.materials
        
        # Plot material flows
        for i, material in enumerate(materials):
            if i < flow_data.shape[1] - 2:
                self.ax_conveyor.plot(time_array, flow_data[:len(time_array), i], 
                                    label=material, linewidth=2)
        
        self.ax_conveyor.set_xlabel('Time (s)')
        self.ax_conveyor.set_ylabel('Flow Rate (kg/s)')
        self.ax_conveyor.legend()
        self.ax_conveyor.grid(True, alpha=0.3)
    
    def _update_bin_plot(self):
        """Update transfer bin status plot"""
        self.ax_bin.clear()
        
        status = self.system.get_bin_status()
        
        # Bin fill level visualization
        fill_height = status['fill_percentage'] / 100 * 10  # Scale to 10 units height
        
        # Draw bin outline
        bin_rect = plt.Rectangle((0, 0), 4, 10, fill=False, edgecolor='black', linewidth=2)
        self.ax_bin.add_patch(bin_rect)
        
        # Draw fill level
        if fill_height > 0:
            fill_rect = plt.Rectangle((0, 0), 4, fill_height, 
                                    facecolor='lightblue', alpha=0.7)
            self.ax_bin.add_patch(fill_rect)
        
        # Add text information
        self.ax_bin.text(2, 11, f"Fill: {status['fill_percentage']:.1f}%", 
                        ha='center', fontsize=12, weight='bold')
        self.ax_bin.text(2, -1, f"Volume: {status['current_volume']:.1f}/{status['capacity']:.1f} m³", 
                        ha='center', fontsize=10)
        self.ax_bin.text(2, -1.5, f"Layers: {status['layer_count']}", 
                        ha='center', fontsize=10)
        
        # Draw trigger levels
        high_level = self.system.bin_level_high_trigger * 10
        low_level = self.system.bin_level_low_trigger * 10
        
        self.ax_bin.axhline(y=high_level, color='red', linestyle='--', alpha=0.7, label='High trigger')
        self.ax_bin.axhline(y=low_level, color='orange', linestyle='--', alpha=0.7, label='Low trigger')
        
        self.ax_bin.set_xlim(-1, 5)
        self.ax_bin.set_ylim(-2, 12)
        self.ax_bin.set_aspect('equal')
        
    def _update_bunker_plot(self):
        """Update bunker layers plot"""
        self.ax_bunker.clear()
        
        bunker = self.system.bunker
        
        # Draw bunker outline
        bunker_rect = plt.Rectangle((0, 0), bunker.diameter, bunker.height, 
                                  fill=False, edgecolor='black', linewidth=2)
        self.ax_bunker.add_patch(bunker_rect)
        
        # Draw material layers
        colors = ['#8B4513', '#CD853F', '#A0522D', '#D3D3D3', '#C0C0C0', '#2F4F4F', '#FFE4B5']
        
        for i, layer in enumerate(bunker.layers):
            color = colors[i % len(colors)]
            layer_rect = plt.Rectangle((0, layer.position), bunker.diameter, layer.height,
                                     facecolor=color, alpha=0.8, edgecolor='black')
            self.ax_bunker.add_patch(layer_rect)
            
            # Add material label
            if layer.height > bunker.height * 0.05:
                self.ax_bunker.text(bunker.diameter/2, layer.position + layer.height/2,
                                  f"{layer.material_name[:8]}\n{layer.volume:.1f}m³",
                                  ha='center', va='center', fontsize=8, color='white', weight='bold')
        
        self.ax_bunker.set_xlim(-0.5, bunker.diameter + 0.5)
        self.ax_bunker.set_ylim(0, bunker.height * 1.1)
        self.ax_bunker.set_xlabel('Width (m)')
        self.ax_bunker.set_ylabel('Height (m)')
        self.ax_bunker.set_aspect('equal')
    
    def _update_chemistry_plot(self):
        """Update chemistry evolution plot"""
        self.ax_chemistry.clear()
        
        # Plot bin chemistry if available
        bin_status = self.system.get_bin_status()
        if bin_status['current_chemistry']:
            chemistry = bin_status['current_chemistry']
            elements = ['Fe', 'SiO2', 'CaO', 'MgO', 'Al2O3']
            values = [chemistry.get(elem, 0) for elem in elements]
            
            bars = self.ax_chemistry.bar(elements, values, alpha=0.7)
            
            # Color code bars
            colors = ['red', 'blue', 'green', 'purple', 'orange']
            for bar, color in zip(bars, colors):
                bar.set_color(color)
            
            self.ax_chemistry.set_ylabel('Content (%)')
            self.ax_chemistry.set_title('Current Transfer Bin Chemistry')
            
            # Add basicity information
            if 'B2' in chemistry:
                self.ax_chemistry.text(0.7, 0.9, f"Basicity B2: {chemistry['B2']:.3f}", 
                                     transform=self.ax_chemistry.transAxes, 
                                     bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        else:
            self.ax_chemistry.text(0.5, 0.5, 'No chemistry data available', 
                                 ha='center', va='center', transform=self.ax_chemistry.transAxes)
        
        self.ax_chemistry.grid(True, alpha=0.3)