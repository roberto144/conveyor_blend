# src/ui/widgets/bf_integration.py
"""
Integration module to connect blast furnace bunker visualization 
with existing PyQt5 conveyor simulation application
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QComboBox, QDoubleSpinBox, QSpinBox,
                             QSplitter, QLabel, QAction, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from typing import Dict, List
import sys
import os

# Ensure proper import of BF visualization module
try:
    from ...simulation.bf_bunker_viz import BlastFurnaceBunker, BunkerVisualization
except ImportError:
    print("Warning: BF bunker visualization module not found. Using placeholder.")
    
    # Placeholder classes if import fails
    class BlastFurnaceBunker:
        def __init__(self, bunker_id, diameter, height):
            self.bunker_id = bunker_id
            self.diameter = diameter
            self.height = height
            self.layers = []
        
        def add_material_layer(self, material_name, volume, chemistry, timestamp):
            pass
    
    class BunkerVisualization:
        def __init__(self, bunker):
            self.bunker = bunker
            self.fig = plt.figure(figsize=(12, 8))
        
        def create_visualization(self, figsize=(12, 8)):
            pass
        
        def update_all(self):
            pass

class BlastFurnaceMaterialWidget(QWidget):
    """Widget for defining blast furnace materials with chemistry"""
    
    materials_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.materials_db = {}
        self.setup_ui()
        self.load_default_materials()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Materials table with chemistry
        group = QGroupBox("Blast Furnace Materials")
        group_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        headers = ['Material', 'Fe%', 'SiO2%', 'CaO%', 'MgO%', 'Al2O3%', 
                  'Bulk Density\n(kg/m³)', 'Color']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Connect table changes to update function
        self.table.itemChanged.connect(self.on_table_changed)
        
        group_layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Material")
        add_btn.clicked.connect(self.add_material)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_material)
        button_layout.addWidget(remove_btn)
        
        load_defaults_btn = QPushButton("Load BF Defaults")
        load_defaults_btn.clicked.connect(self.load_default_materials)
        button_layout.addWidget(load_defaults_btn)
        
        group_layout.addLayout(button_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        self.setLayout(layout)
    
    def on_table_changed(self, item):
        """Handle table cell changes"""
        self.update_materials_db()
    
    def load_default_materials(self):
        """Load typical blast furnace materials"""
        defaults = [
            ['Pellets', 65.5, 4.2, 0.5, 0.3, 0.8, 2200, '#8B4513'],
            ['Sinter', 57.2, 9.8, 9.5, 1.2, 1.8, 1900, '#CD853F'],
            ['Lump Ore', 62.0, 6.5, 0.2, 0.1, 2.1, 2500, '#A0522D'],
            ['Coke', 0.5, 5.5, 0.3, 0.1, 2.8, 500, '#2F4F4F'],
            ['Limestone', 0.5, 2.0, 52.0, 2.5, 0.8, 1600, '#D3D3D3'],
            ['Dolomite', 0.3, 1.5, 30.0, 20.0, 0.5, 1700, '#C0C0C0'],
            ['Quartzite', 0.2, 95.0, 0.5, 0.1, 2.0, 1650, '#FFE4B5']
        ]
        
        self.table.setRowCount(0)
        for material_data in defaults:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, value in enumerate(material_data):
                if isinstance(value, (int, float)):
                    item = QTableWidgetItem(f"{value:.1f}")
                else:
                    item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)
        
        self.update_materials_db()
    
    def add_material(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Set default values
        defaults = [f"Material_{row+1}", 60.0, 5.0, 1.0, 0.5, 1.0, 2000, '#808080']
        for col, value in enumerate(defaults):
            if isinstance(value, (int, float)):
                item = QTableWidgetItem(f"{value:.1f}")
            else:
                item = QTableWidgetItem(str(value))
            self.table.setItem(row, col, item)
        self.update_materials_db()
    
    def remove_material(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
            self.update_materials_db()
    
    def update_materials_db(self):
        """Update materials database from table"""
        self.materials_db = {}
        for row in range(self.table.rowCount()):
            try:
                name = self.table.item(row, 0).text() if self.table.item(row, 0) else f"Material_{row}"
                
                chemistry = {}
                chemistry['Fe'] = float(self.table.item(row, 1).text()) if self.table.item(row, 1) else 0.0
                chemistry['SiO2'] = float(self.table.item(row, 2).text()) if self.table.item(row, 2) else 0.0
                chemistry['CaO'] = float(self.table.item(row, 3).text()) if self.table.item(row, 3) else 0.0
                chemistry['MgO'] = float(self.table.item(row, 4).text()) if self.table.item(row, 4) else 0.0
                chemistry['Al2O3'] = float(self.table.item(row, 5).text()) if self.table.item(row, 5) else 0.0
                
                density = float(self.table.item(row, 6).text()) if self.table.item(row, 6) else 2000.0
                color = self.table.item(row, 7).text() if self.table.item(row, 7) else '#808080'
                
                self.materials_db[name] = {
                    'chemistry': chemistry,
                    'density': density,
                    'color': color
                }
            except (ValueError, AttributeError) as e:
                print(f"Error processing row {row}: {e}")
                continue
        
        self.materials_updated.emit(self.materials_db)
    
    def get_material_names(self) -> List[str]:
        return list(self.materials_db.keys())
    
    def get_material_chemistry(self, material_name: str) -> Dict[str, float]:
        if material_name in self.materials_db:
            return self.materials_db[material_name]['chemistry']
        return {}

class BunkerChargingWidget(QWidget):
    """Widget for simulating bunker charging operations"""
    
    charging_updated = pyqtSignal(dict)
    
    def __init__(self, materials_widget: BlastFurnaceMaterialWidget):
        super().__init__()
        self.materials_widget = materials_widget
        self.charging_sequence = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        group = QGroupBox("Charging Sequence")
        group_layout = QVBoxLayout()
        
        # Add charge controls
        charge_layout = QHBoxLayout()
        
        charge_layout.addWidget(QLabel("Material:"))
        self.material_combo = QComboBox()
        self.material_combo.setMinimumWidth(100)
        charge_layout.addWidget(self.material_combo)
        
        charge_layout.addWidget(QLabel("Volume (m³):"))
        self.volume_spin = QDoubleSpinBox()
        self.volume_spin.setRange(1.0, 100.0)
        self.volume_spin.setValue(25.0)
        self.volume_spin.setSuffix(" m³")
        charge_layout.addWidget(self.volume_spin)
        
        add_charge_btn = QPushButton("Add to Sequence")
        add_charge_btn.clicked.connect(self.add_charge)
        charge_layout.addWidget(add_charge_btn)
        
        group_layout.addLayout(charge_layout)
        
        # Charging sequence table
        self.sequence_table = QTableWidget()
        self.sequence_table.setColumnCount(4)
        self.sequence_table.setHorizontalHeaderLabels(['Step', 'Material', 'Volume (m³)', 'Time (s)'])
        self.sequence_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        group_layout.addWidget(self.sequence_table)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Sequence")
        clear_btn.clicked.connect(self.clear_sequence)
        button_layout.addWidget(clear_btn)
        
        run_btn = QPushButton("Run Charging")
        run_btn.clicked.connect(self.run_charging_sequence)
        button_layout.addWidget(run_btn)
        
        group_layout.addLayout(button_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        self.setLayout(layout)
        
        # Update material combo when materials change
        self.materials_widget.materials_updated.connect(self.update_material_options)
    
    def update_material_options(self, materials_db):
        """Update material dropdown options"""
        current_text = self.material_combo.currentText()
        self.material_combo.clear()
        self.material_combo.addItems(list(materials_db.keys()))
        
        # Try to restore previous selection
        index = self.material_combo.findText(current_text)
        if index >= 0:
            self.material_combo.setCurrentIndex(index)
    
    def add_charge(self):
        """Add a charge to the sequence"""
        material = self.material_combo.currentText()
        volume = self.volume_spin.value()
        
        if material:
            row = self.sequence_table.rowCount()
            self.sequence_table.insertRow(row)
            
            self.sequence_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.sequence_table.setItem(row, 1, QTableWidgetItem(material))
            self.sequence_table.setItem(row, 2, QTableWidgetItem(f"{volume:.1f}"))
            self.sequence_table.setItem(row, 3, QTableWidgetItem(f"{row * 30}"))  # 30s intervals
            
            self.charging_sequence.append({
                'material': material,
                'volume': volume,
                'time': row * 30
            })
    
    def clear_sequence(self):
        """Clear the charging sequence"""
        self.sequence_table.setRowCount(0)
        self.charging_sequence = []
    
    def run_charging_sequence(self):
        """Execute the charging sequence"""
        if self.charging_sequence:
            self.charging_updated.emit({
                'sequence': self.charging_sequence,
                'timestamp': 0
            })
        else:
            QMessageBox.warning(self, "No Sequence", "Please add some charges to the sequence first.")
    
    def get_sequence(self) -> List[Dict]:
        return self.charging_sequence

class BlastFurnaceBunkerWidget(QWidget):
    """Main widget integrating bunker visualization with PyQt5"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bunker = None
        self.viz = None
        self.canvas = None
        self.toolbar = None
        self.setup_ui()
        self.create_bunker()
        
    def setup_ui(self):
        main_layout = QHBoxLayout()
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Materials definition
        self.materials_widget = BlastFurnaceMaterialWidget()
        left_layout.addWidget(self.materials_widget)
        
        # Charging sequence
        self.charging_widget = BunkerChargingWidget(self.materials_widget)
        self.charging_widget.charging_updated.connect(self.execute_charging)
        left_layout.addWidget(self.charging_widget)
        
        # Bunker parameters
        params_group = QGroupBox("Bunker Parameters")
        params_layout = QVBoxLayout()
        
        diameter_layout = QHBoxLayout()
        diameter_layout.addWidget(QLabel("Diameter:"))
        self.diameter_spin = QDoubleSpinBox()
        self.diameter_spin.setRange(3.0, 10.0)
        self.diameter_spin.setValue(6.0)
        self.diameter_spin.setSuffix(" m")
        self.diameter_spin.valueChanged.connect(self.update_bunker_params)
        diameter_layout.addWidget(self.diameter_spin)
        params_layout.addLayout(diameter_layout)
        
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(10.0, 30.0)
        self.height_spin.setValue(20.0)
        self.height_spin.setSuffix(" m")
        self.height_spin.valueChanged.connect(self.update_bunker_params)
        height_layout.addWidget(self.height_spin)
        params_layout.addLayout(height_layout)
        
        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # Right panel - Visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Control buttons for visualization
        viz_controls = QHBoxLayout()
        
        self.update_btn = QPushButton("Update Visualization")
        self.update_btn.clicked.connect(self.update_visualization)
        viz_controls.addWidget(self.update_btn)
        
        self.clear_btn = QPushButton("Clear Bunker")
        self.clear_btn.clicked.connect(self.clear_bunker)
        viz_controls.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("Export Chemistry")
        self.export_btn.clicked.connect(self.export_chemistry_data)
        viz_controls.addWidget(self.export_btn)
        
        right_layout.addLayout(viz_controls)
        
        # Matplotlib canvas placeholder
        self.canvas_widget = QWidget()
        self.canvas_layout = QVBoxLayout()
        self.canvas_widget.setLayout(self.canvas_layout)
        right_layout.addWidget(self.canvas_widget)
        
        right_panel.setLayout(right_layout)
        
        # Add panels to splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def create_bunker(self):
        """Create the blast furnace bunker"""
        try:
            self.bunker = BlastFurnaceBunker(
                bunker_id="BF1_BUNKER_01",
                diameter=self.diameter_spin.value(),
                height=self.height_spin.value()
            )
            
            self.viz = BunkerVisualization(self.bunker)
            self.viz.create_visualization(figsize=(12, 8))
            
            # Embed matplotlib figure in PyQt5
            if self.canvas:
                self.canvas_layout.removeWidget(self.canvas)
                self.canvas.deleteLater()
            
            if self.toolbar:
                self.canvas_layout.removeWidget(self.toolbar)
                self.toolbar.deleteLater()
            
            self.canvas = FigureCanvas(self.viz.fig)
            self.canvas_layout.addWidget(self.canvas)
            
            # Add navigation toolbar
            self.toolbar = NavigationToolbar(self.canvas, self)
            self.canvas_layout.addWidget(self.toolbar)
            
        except Exception as e:
            print(f"Error creating bunker visualization: {e}")
            # Create fallback simple visualization
            self._create_fallback_visualization()
    
    def _create_fallback_visualization(self):
        """Create a simple fallback visualization if BF module fails"""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Bunker Visualization\n(BF Module Loading)', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=16)
        ax.set_title('Blast Furnace Bunker')
        
        if self.canvas:
            self.canvas_layout.removeWidget(self.canvas)
            self.canvas.deleteLater()
        
        self.canvas = FigureCanvas(fig)
        self.canvas_layout.addWidget(self.canvas)
        
        if self.toolbar:
            self.canvas_layout.removeWidget(self.toolbar)
            self.toolbar.deleteLater()
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.canvas_layout.addWidget(self.toolbar)
    
    def update_bunker_params(self):
        """Update bunker parameters"""
        if self.bunker:
            self.bunker.diameter = self.diameter_spin.value()
            self.bunker.height = self.height_spin.value()
            self.update_visualization()
    
    def execute_charging(self, charging_data):
        """Execute charging sequence from the charging widget"""
        if not self.bunker:
            QMessageBox.warning(self, "No Bunker", "Bunker not initialized properly.")
            return
        
        sequence = charging_data['sequence']
        
        try:
            for i, charge in enumerate(sequence):
                material_name = charge['material']
                volume = charge['volume']
                time = charge['time']
                
                # Get chemistry from materials database
                chemistry = self.materials_widget.get_material_chemistry(material_name)
                
                if chemistry:
                    self.bunker.add_material_layer(
                        material_name=material_name,
                        volume=volume,
                        chemistry=chemistry,
                        timestamp=time
                    )
            
            self.update_visualization()
            QMessageBox.information(self, "Charging Complete", 
                                  f"Added {len(sequence)} charges to bunker.")
        except Exception as e:
            QMessageBox.critical(self, "Charging Error", f"Error during charging: {str(e)}")
    
    def update_visualization(self):
        """Update the bunker visualization"""
        try:
            if self.viz and hasattr(self.viz, 'update_all'):
                self.viz.update_all()
                self.canvas.draw()
            else:
                print("Visualization not available - using fallback")
                self._update_fallback_visualization()
        except Exception as e:
            print(f"Error updating visualization: {e}")
            self._update_fallback_visualization()
    
    def _update_fallback_visualization(self):
        """Update fallback visualization with basic bunker info"""
        if not self.canvas:
            return
        
        fig = self.canvas.figure
        fig.clear()
        
        ax = fig.add_subplot(111)
        
        # Draw simple bunker representation
        bunker_height = self.height_spin.value()
        bunker_width = self.diameter_spin.value()
        
        # Bunker outline
        bunker_rect = plt.Rectangle((0, 0), bunker_width, bunker_height, 
                                   fill=False, edgecolor='black', linewidth=2)
        ax.add_patch(bunker_rect)
        
        # Show material layers if bunker exists
        if self.bunker and hasattr(self.bunker, 'layers'):
            current_height = 0
            colors = ['#8B4513', '#CD853F', '#A0522D', '#D3D3D3', '#C0C0C0', '#2F4F4F', '#FFE4B5']
            
            for i, layer in enumerate(self.bunker.layers):
                color = colors[i % len(colors)]
                layer_rect = plt.Rectangle((0, current_height), bunker_width, layer.height,
                                         facecolor=color, alpha=0.7, edgecolor='black')
                ax.add_patch(layer_rect)
                
                # Add label
                if layer.height > bunker_height * 0.05:
                    ax.text(bunker_width/2, current_height + layer.height/2,
                           f"{layer.material_name}\n{layer.volume:.1f} m³",
                           ha='center', va='center', fontsize=8)
                
                current_height += layer.height
        
        ax.set_xlim(-0.5, bunker_width + 0.5)
        ax.set_ylim(0, bunker_height * 1.1)
        ax.set_xlabel('Width (m)')
        ax.set_ylabel('Height (m)')
        ax.set_title('Bunker Material Layers')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        self.canvas.draw()
    
    def clear_bunker(self):
        """Clear all materials from bunker"""
        if self.bunker:
            self.bunker.layers = []
            self.update_visualization()
            QMessageBox.information(self, "Bunker Cleared", "All materials removed from bunker.")
    
    def export_chemistry_data(self):
        """Export chemistry data to CSV"""
        if not self.bunker or not hasattr(self.bunker, 'layers') or not self.bunker.layers:
            QMessageBox.warning(self, "No Data", "No material layers to export.")
            return
        
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Chemistry Data", "", "CSV Files (*.csv);;All Files (*)"
            )
            
            if filename:
                self._write_chemistry_csv(filename)
                QMessageBox.information(self, "Export Complete", 
                                      f"Chemistry data exported to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def _write_chemistry_csv(self, filename):
        """Write chemistry data to CSV file"""
        import csv
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['Layer', 'Material', 'Height (m)', 'Volume (m³)', 
                           'Fe%', 'SiO2%', 'CaO%', 'MgO%', 'Al2O3%', 
                           'Basicity B2', 'Basicity B4'])
            
            # Data
            for i, layer in enumerate(self.bunker.layers):
                if hasattr(layer, 'basicity_b2'):
                    b2 = layer.basicity_b2
                    b4 = layer.basicity_b4
                else:
                    # Calculate basicity if not available
                    b2 = layer.cao_content / max(layer.sio2_content, 0.1)
                    basic = layer.cao_content + layer.mgo_content
                    acidic = layer.sio2_content + layer.al2o3_content
                    b4 = basic / max(acidic, 0.1)
                
                writer.writerow([
                    i + 1,
                    layer.material_name,
                    f"{layer.height:.2f}",
                    f"{layer.volume:.2f}",
                    f"{layer.fe_content:.2f}",
                    f"{layer.sio2_content:.2f}",
                    f"{layer.cao_content:.2f}",
                    f"{layer.mgo_content:.2f}",
                    f"{layer.al2o3_content:.2f}",
                    f"{b2:.3f}",
                    f"{b4:.3f}"
                ])
            
            # Add discharge prediction
            writer.writerow([])
            writer.writerow(['Discharge Chemistry Prediction (next 10 charges)'])
            writer.writerow(['Charge', 'Fe%', 'SiO2%', 'CaO%', 'Basicity B2'])
            
            if hasattr(self.bunker, 'calculate_discharge_chemistry'):
                for charge_num in range(1, 11):
                    chemistry = self.bunker.calculate_discharge_chemistry(charge_volume=20)
                    if chemistry:
                        writer.writerow([
                            charge_num,
                            f"{chemistry.get('Fe', 0):.2f}",
                            f"{chemistry.get('SiO2', 0):.2f}",
                            f"{chemistry.get('CaO', 0):.2f}",
                            f"{chemistry.get('B2', 0):.3f}"
                        ])

# Integration helper functions
def integrate_bf_mode_into_main_window():
    """
    Helper function to show how to integrate BF mode into existing main window.
    This demonstrates the integration pattern.
    """
    integration_guide = """
    # Integration Steps for Blast Furnace Mode:
    
    1. Import the BF widgets in main_window.py:
       from .widgets.bf_integration import BlastFurnaceBunkerWidget, BlastFurnaceMaterialWidget
    
    2. Add BF mode toggle in setup_menus():
       bf_menu = menubar.addMenu('&Blast Furnace')
       bf_mode_action = QAction('&Enable BF Mode', self)
       bf_mode_action.setCheckable(True)
       bf_mode_action.triggered.connect(self.toggle_bf_mode)
    
    3. Create BF panel in setup_ui():
       self.bf_panel = self.create_bf_panel()
       self.left_tabs.addTab(self.bf_panel, "Blast Furnace Mode")
    
    4. Implement toggle_bf_mode():
       def toggle_bf_mode(self, checked):
           self.bf_mode_enabled = checked
           self.bf_panel.setEnabled(checked)
           # Update UI elements accordingly
    
    5. Modify run_simulation() to handle BF mode:
       if self.bf_mode_enabled:
           parameters = self.collect_bf_simulation_parameters()
       else:
           parameters = self.collect_simulation_parameters()
    
    6. Add BF-specific result handling:
       def update_bf_plots(self, results):
           # Update chemistry plots
           # Update bunker visualization
    """
    return integration_guide

# Error dialog for missing dependencies
class ErrorDialog:
    @staticmethod
    def show_error(parent, title, message):
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_info(parent, title, message):
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_warning(parent, title, message):
        QMessageBox.warning(parent, title, message)

# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create main widget
    widget = BlastFurnaceBunkerWidget()
    widget.setWindowTitle("Blast Furnace Bunker Chemistry Visualization")
    widget.resize(1200, 800)
    widget.show()
    
    sys.exit(app.exec_())