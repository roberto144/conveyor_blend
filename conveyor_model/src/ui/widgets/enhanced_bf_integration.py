# src/ui/widgets/enhanced_bf_integration.py
"""
Enhanced Blast Furnace UI Integration
Connects conveyor simulation results directly to bunker charging system
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QComboBox, QDoubleSpinBox, QSpinBox,
                             QSplitter, QLabel, QProgressBar, QTextEdit,
                             QTabWidget, QCheckBox, QSlider, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from typing import Dict, List, Optional

# Import the enhanced BF system
from ...simulation.bf_conveyor_bunker_integration import (
    ConveyorToBunkerSystem, TransferBin, ConveyorBunkerVisualization
)
from ...simulation.bf_bunker_viz import BlastFurnaceBunker
from ...models.simulation_data import SimulationResults

class ConveyorToBunkerControlWidget(QWidget):
    """Main control widget for conveyor-to-bunker system"""
    
    # Signals
    system_updated = pyqtSignal()
    material_transferred = pyqtSignal(float)  # volume transferred
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.system = None
        self.auto_update_timer = QTimer()
        self.auto_update_timer.timeout.connect(self.update_displays)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # System Configuration Group
        config_group = QGroupBox("System Configuration")
        config_layout = QVBoxLayout()
        
        # Transfer Bin Parameters
        bin_layout = QHBoxLayout()
        bin_layout.addWidget(QLabel("Transfer Bin Capacity:"))
        self.bin_capacity_spin = QDoubleSpinBox()
        self.bin_capacity_spin.setRange(10.0, 1000.0)
        self.bin_capacity_spin.setValue(100.0)
        self.bin_capacity_spin.setSuffix(" m³")
        self.bin_capacity_spin.valueChanged.connect(self.update_bin_capacity)
        bin_layout.addWidget(self.bin_capacity_spin)
        
        bin_layout.addWidget(QLabel("Discharge Rate:"))
        self.discharge_rate_spin = QDoubleSpinBox()
        self.discharge_rate_spin.setRange(1.0, 200.0)
        self.discharge_rate_spin.setValue(50.0)
        self.discharge_rate_spin.setSuffix(" m³/h")
        self.discharge_rate_spin.valueChanged.connect(self.update_discharge_rate)
        bin_layout.addWidget(self.discharge_rate_spin)
        
        config_layout.addLayout(bin_layout)
        
        # Bunker Parameters
        bunker_layout = QHBoxLayout()
        bunker_layout.addWidget(QLabel("Bunker Diameter:"))
        self.bunker_diameter_spin = QDoubleSpinBox()
        self.bunker_diameter_spin.setRange(3.0, 15.0)
        self.bunker_diameter_spin.setValue(8.0)
        self.bunker_diameter_spin.setSuffix(" m")
        self.bunker_diameter_spin.valueChanged.connect(self.update_bunker_params)
        bunker_layout.addWidget(self.bunker_diameter_spin)
        
        bunker_layout.addWidget(QLabel("Bunker Height:"))
        self.bunker_height_spin = QDoubleSpinBox()
        self.bunker_height_spin.setRange(10.0, 50.0)
        self.bunker_height_spin.setValue(25.0)
        self.bunker_height_spin.setSuffix(" m")
        self.bunker_height_spin.valueChanged.connect(self.update_bunker_params)
        bunker_layout.addWidget(self.bunker_height_spin)
        
        config_layout.addLayout(bunker_layout)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Operating Controls Group
        controls_group = QGroupBox("Operating Controls")
        controls_layout = QVBoxLayout()
        
        # Auto-discharge controls
        auto_layout = QHBoxLayout()
        self.auto_discharge_check = QCheckBox("Auto Discharge Enabled")
        self.auto_discharge_check.setChecked(True)
        self.auto_discharge_check.toggled.connect(self.toggle_auto_discharge)
        auto_layout.addWidget(self.auto_discharge_check)
        
        auto_layout.addWidget(QLabel("High Trigger:"))
        self.high_trigger_spin = QDoubleSpinBox()
        self.high_trigger_spin.setRange(0.1, 1.0)
        self.high_trigger_spin.setSingleStep(0.05)
        self.high_trigger_spin.setValue(0.8)
        self.high_trigger_spin.setDecimals(2)
        self.high_trigger_spin.valueChanged.connect(self.update_triggers)
        auto_layout.addWidget(self.high_trigger_spin)
        
        auto_layout.addWidget(QLabel("Low Trigger:"))
        self.low_trigger_spin = QDoubleSpinBox()
        self.low_trigger_spin.setRange(0.0, 0.9)
        self.low_trigger_spin.setSingleStep(0.05)
        self.low_trigger_spin.setValue(0.2)
        self.low_trigger_spin.setDecimals(2)
        self.low_trigger_spin.valueChanged.connect(self.update_triggers)
        auto_layout.addWidget(self.low_trigger_spin)
        
        controls_layout.addLayout(auto_layout)
        
        # Manual control buttons
        manual_layout = QHBoxLayout()
        
        self.load_conveyor_btn = QPushButton("Load Conveyor Results")
        self.load_conveyor_btn.clicked.connect(self.load_conveyor_results)
        manual_layout.addWidget(self.load_conveyor_btn)
        
        self.process_discharge_btn = QPushButton("Process Conveyor Discharge")
        self.process_discharge_btn.clicked.connect(self.process_conveyor_discharge)
        self.process_discharge_btn.setEnabled(False)
        manual_layout.addWidget(self.process_discharge_btn)
        
        manual_layout.addWidget(QLabel("Manual Discharge:"))
        self.manual_volume_spin = QDoubleSpinBox()
        self.manual_volume_spin.setRange(0.1, 100.0)
        self.manual_volume_spin.setValue(10.0)
        self.manual_volume_spin.setSuffix(" m³")
        manual_layout.addWidget(self.manual_volume_spin)
        
        self.manual_discharge_btn = QPushButton("Discharge to Bunker")
        self.manual_discharge_btn.clicked.connect(self.manual_discharge)
        self.manual_discharge_btn.setEnabled(False)
        manual_layout.addWidget(self.manual_discharge_btn)
        
        controls_layout.addLayout(manual_layout)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Status Display Group
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        
        # Status labels
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        
        # Progress bars
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Bin Fill:"))
        self.bin_fill_progress = QProgressBar()
        self.bin_fill_progress.setRange(0, 100)
        progress_layout.addWidget(self.bin_fill_progress)
        
        progress_layout.addWidget(QLabel("Bunker Fill:"))
        self.bunker_fill_progress = QProgressBar()
        self.bunker_fill_progress.setRange(0, 100)
        progress_layout.addWidget(self.bunker_fill_progress)
        
        status_layout.addLayout(progress_layout)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Export Controls
        export_layout = QHBoxLayout()
        self.export_report_btn = QPushButton("Export Material Flow Report")
        self.export_report_btn.clicked.connect(self.export_report)
        self.export_report_btn.setEnabled(False)
        export_layout.addWidget(self.export_report_btn)
        
        self.clear_system_btn = QPushButton("Clear System")
        self.clear_system_btn.clicked.connect(self.clear_system)
        export_layout.addWidget(self.clear_system_btn)
        
        layout.addLayout(export_layout)
        
        self.setLayout(layout)
        self.initialize_system()
    
    def initialize_system(self):
        """Initialize the conveyor-to-bunker system"""
        # Create transfer bin
        transfer_bin = TransferBin(
            bin_id="MAIN_TRANSFER_BIN",
            capacity=self.bin_capacity_spin.value()
        )
        
        # Create bunker
        bunker = BlastFurnaceBunker(
            bunker_id="BF1_TOP_BUNKER",
            diameter=self.bunker_diameter_spin.value(),
            height=self.bunker_height_spin.value()
        )
        
        # Create system
        self.system = ConveyorToBunkerSystem(
            transfer_bin=transfer_bin,
            bunker=bunker
        )
        
        # Configure operating parameters
        self.system.auto_discharge_enabled = self.auto_discharge_check.isChecked()
        self.system.bin_level_high_trigger = self.high_trigger_spin.value()
        self.system.bin_level_low_trigger = self.low_trigger_spin.value()
        self.system.bin_discharge_rate = self.discharge_rate_spin.value()
        
        self.update_status()
    
    def load_conveyor_results(self):
        """Load conveyor simulation results - this would be connected to main application"""
        # This would typically be called from the main window with actual results
        # For now, we'll emit a signal that the main window can connect to
        self.system_updated.emit()
        
        # Enable processing button
        self.process_discharge_btn.setEnabled(True)
        self.update_status("Conveyor results loaded. Ready to process discharge.")
    
    def set_conveyor_results(self, results: SimulationResults):
        """Set conveyor results from main application"""
        if self.system:
            self.system.conveyor_results = results
            if hasattr(results.parameters, 'material_chemistry'):
                self.system.material_chemistry_db = results.parameters.material_chemistry
                self.update_status("Conveyor results loaded with chemistry data.")
                self.process_discharge_btn.setEnabled(True)
                self.export_report_btn.setEnabled(True)
            else:
                self.update_status("Warning: Conveyor results loaded but no chemistry data found.")
    
    def process_conveyor_discharge(self):
        """Process the conveyor discharge into transfer bin"""
        if not self.system or not self.system.conveyor_results:
            QMessageBox.warning(self, "No Data", "Please load conveyor results first.")
            return
        
        try:
            self.update_status("Processing conveyor discharge...")
            self.system.process_conveyor_discharge(self.system.conveyor_results)
            self.manual_discharge_btn.setEnabled(True)
            self.update_status("Conveyor discharge processed successfully.")
            self.update_displays()
            
            # Start auto-update timer for real-time monitoring
            if not self.auto_update_timer.isActive():
                self.auto_update_timer.start(1000)  # Update every second
                
        except Exception as e:
            QMessageBox.critical(self, "Processing Error", f"Error processing discharge: {str(e)}")
            self.update_status(f"Error: {str(e)}")
    
    def manual_discharge(self):
        """Manually discharge material to bunker"""
        if not self.system:
            return
        
        volume = self.manual_volume_spin.value()
        
        try:
            self.system.manual_discharge_to_bunker(volume, 0.0)  # timestamp = 0 for manual
            self.update_status(f"Manually discharged {volume:.1f} m³ to bunker.")
            self.update_displays()
            self.material_transferred.emit(volume)
        except Exception as e:
            QMessageBox.warning(self, "Discharge Error", f"Error during discharge: {str(e)}")
    
    def update_bin_capacity(self):
        """Update transfer bin capacity"""
        if self.system:
            self.system.transfer_bin.capacity = self.bin_capacity_spin.value()
            self.update_displays()
    
    def update_discharge_rate(self):
        """Update discharge rate"""
        if self.system:
            self.system.bin_discharge_rate = self.discharge_rate_spin.value()
    
    def update_bunker_params(self):
        """Update bunker parameters"""
        if self.system:
            self.system.bunker.diameter = self.bunker_diameter_spin.value()
            self.system.bunker.height = self.bunker_height_spin.value()
            self.update_displays()
    
    def toggle_auto_discharge(self, checked):
        """Toggle automatic discharge"""
        if self.system:
            self.system.auto_discharge_enabled = checked
            status = "enabled" if checked else "disabled"
            self.update_status(f"Auto discharge {status}.")
    
    def update_triggers(self):
        """Update discharge trigger levels"""
        if self.system:
            self.system.bin_level_high_trigger = self.high_trigger_spin.value()
            self.system.bin_level_low_trigger = self.low_trigger_spin.value()
    
    def update_displays(self):
        """Update all displays with current system status"""
        if not self.system:
            return
        
        # Update progress bars
        bin_status = self.system.get_bin_status()
        self.bin_fill_progress.setValue(int(bin_status['fill_percentage']))
        
        # Calculate bunker fill percentage
        bunker_fill = sum(layer.height for layer in self.system.bunker.layers)
        bunker_fill_percent = min(100, (bunker_fill / self.system.bunker.height) * 100)
        self.bunker_fill_progress.setValue(int(bunker_fill_percent))
        
        # Update status text
        status_info = [
            f"Transfer Bin: {bin_status['current_volume']:.1f}/{bin_status['capacity']:.1f} m³ ({bin_status['fill_percentage']:.1f}%)",
            f"Bin Layers: {bin_status['layer_count']}",
            f"Bunker Layers: {len(self.system.bunker.layers)}",
            f"Bunker Fill: {bunker_fill:.1f}/{self.system.bunker.height:.1f} m ({bunker_fill_percent:.1f}%)"
        ]
        
        # Add chemistry information if available
        if bin_status['current_chemistry']:
            chem = bin_status['current_chemistry']
            status_info.append(f"Bin Chemistry - Fe: {chem['Fe']:.1f}%, SiO2: {chem['SiO2']:.1f}%, B2: {chem['B2']:.3f}")
        
        self.update_status("\n".join(status_info))
    
    def update_status(self, message: str = None):
        """Update status display"""
        if message:
            current_text = self.status_text.toPlainText()
            timestamp = QTimer().time().toString("hh:mm:ss")
            new_line = f"[{timestamp}] {message}"
            
            if current_text:
                updated_text = f"{current_text}\n{new_line}"
            else:
                updated_text = new_line
            
            self.status_text.setPlainText(updated_text)
            
            # Auto-scroll to bottom
            cursor = self.status_text.textCursor()
            cursor.movePosition(cursor.End)
            self.status_text.setTextCursor(cursor)
    
    def export_report(self):
        """Export material flow report"""
        if not self.system:
            return
        
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Material Flow Report", 
            "material_flow_report.csv", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                self.system.export_material_flow_report(filename)
                QMessageBox.information(self, "Export Complete", 
                                      f"Material flow report exported to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export report: {str(e)}")
    
    def clear_system(self):
        """Clear all materials from the system"""
        reply = QMessageBox.question(
            self, "Clear System",
            "Are you sure you want to clear all materials from the transfer bin and bunker?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.system:
                self.system.transfer_bin.material_layers.clear()
                self.system.transfer_bin.current_volume = 0.0
                self.system.bunker.layers.clear()
                self.update_displays()
                self.update_status("System cleared.")

class EnhancedBFIntegrationWidget(QWidget):
    """Enhanced BF integration widget with conveyor-to-bunker flow"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conveyor_results = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Conveyor-to-bunker control
        self.control_widget = ConveyorToBunkerControlWidget()
        left_layout.addWidget(self.control_widget)
        
        left_panel.setLayout(left_layout)
        
        # Right panel - Visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Visualization tabs
        self.viz_tabs = QTabWidget()
        
        # System overview tab
        self.system_canvas_widget = QWidget()
        self.system_canvas_layout = QVBoxLayout()
        self.system_canvas_widget.setLayout(self.system_canvas_layout)
        self.viz_tabs.addTab(self.system_canvas_widget, "System Overview")
        
        # Detailed bunker tab
        self.bunker_canvas_widget = QWidget()
        self.bunker_canvas_layout = QVBoxLayout()
        self.bunker_canvas_widget.setLayout(self.bunker_canvas_layout)
        self.viz_tabs.addTab(self.bunker_canvas_widget, "Bunker Details")
        
        right_layout.addWidget(self.viz_tabs)
        right_panel.setLayout(right_layout)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Connect signals
        self.control_widget.system_updated.connect(self.update_visualization)
        self.control_widget.material_transferred.connect(self.on_material_transferred)
        
        # Initialize visualization
        self.setup_visualization()
    
    def setup_visualization(self):
        """Setup the visualization components"""
        if self.control_widget.system:
            # Create system visualization
            self.system_viz = ConveyorBunkerVisualization(self.control_widget.system)
            self.system_viz.create_system_visualization(figsize=(12, 8))
            
            # Add to canvas
            if hasattr(self.system_viz, 'fig'):
                self.system_canvas = FigureCanvas(self.system_viz.fig)
                self.system_canvas_layout.addWidget(self.system_canvas)
                
                # Add toolbar
                self.system_toolbar = NavigationToolbar(self.system_canvas, self)
                self.system_canvas_layout.addWidget(self.system_toolbar)
    
    def set_conveyor_results(self, results: SimulationResults):
        """Set conveyor simulation results"""
        self.conveyor_results = results
        self.control_widget.set_conveyor_results(results)
        self.update_visualization()
    
    def update_visualization(self):
        """Update all visualizations"""
        if hasattr(self, 'system_viz') and self.system_viz:
            self.system_viz.update_visualization()
    
    def on_material_transferred(self, volume: float):
        """Handle material transfer event"""
        self.update_visualization()
        print(f"Material transferred: {volume:.1f} m³")

# Integration with main window
class EnhancedMainWindowIntegration:
    """Helper class to integrate enhanced BF features into main window"""
    
    @staticmethod
    def add_enhanced_bf_features(main_window):
        """Add enhanced BF features to existing main window"""
        
        # Store reference to enhanced widget
        main_window.enhanced_bf_widget = None
        
        # Modify the show_bf_bunker_visualization method
        original_show_bf_bunker = main_window.show_bf_bunker_visualization
        
        def enhanced_show_bf_bunker_visualization():
            """Enhanced bunker visualization with conveyor integration"""
            if not main_window.bf_mode_enabled:
                QMessageBox.warning(
                    main_window,
                    "BF Mode Required",
                    "Please enable Blast Furnace Mode first."
                )
                return
            
            # Create or show the enhanced BF window
            if not main_window.enhanced_bf_widget:
                main_window.enhanced_bf_widget = EnhancedBFIntegrationWidget()
                main_window.enhanced_bf_widget.setWindowTitle(
                    'Enhanced Blast Furnace: Conveyor to Bunker Integration'
                )
                main_window.enhanced_bf_widget.resize(1400, 900)
                
                # Connect to simulation results
                if hasattr(main_window, 'current_results') and main_window.current_results:
                    main_window.enhanced_bf_widget.set_conveyor_results(main_window.current_results)
            
            main_window.enhanced_bf_widget.show()
            main_window.enhanced_bf_widget.raise_()
            main_window.enhanced_bf_widget.activateWindow()
        
        # Replace the method
        main_window.show_bf_bunker_visualization = enhanced_show_bf_bunker_visualization
        
        # Modify the simulation completion handler
        original_on_simulation_finished = main_window.on_simulation_finished
        
        def enhanced_on_simulation_finished(results):
            """Enhanced simulation completion handler"""
            # Call original handler
            original_on_simulation_finished(results)
            
            # Update enhanced BF widget if open and in BF mode
            if (main_window.bf_mode_enabled and 
                main_window.enhanced_bf_widget and 
                main_window.enhanced_bf_widget.isVisible()):
                main_window.enhanced_bf_widget.set_conveyor_results(results)
        
        # Replace the method
        main_window.on_simulation_finished = enhanced_on_simulation_finished
        
        # Add menu item for enhanced features
        bf_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == '&Blast Furnace':
                bf_menu = action.menu()
                break
        
        if bf_menu:
            bf_menu.addSeparator()
            
            enhanced_action = bf_menu.addAction('&Enhanced Conveyor-Bunker Integration')
            enhanced_action.setShortcut('Ctrl+Shift+B')
            enhanced_action.triggered.connect(enhanced_show_bf_bunker_visualization)
            enhanced_action.setEnabled(main_window.bf_mode_enabled)
            
            # Store reference for enabling/disabling
            main_window.enhanced_bf_action = enhanced_action
            
            # Update the toggle_bf_mode method to handle enhanced features
            original_toggle_bf_mode = main_window.toggle_bf_mode
            
            def enhanced_toggle_bf_mode(checked):
                """Enhanced BF mode toggle"""
                original_toggle_bf_mode(checked)
                
                # Enable/disable enhanced features
                if hasattr(main_window, 'enhanced_bf_action'):
                    main_window.enhanced_bf_action.setEnabled(checked)
                
                # Close enhanced widget if disabling BF mode
                if not checked and main_window.enhanced_bf_widget:
                    main_window.enhanced_bf_widget.close()
                    main_window.enhanced_bf_widget = None
            
            main_window.toggle_bf_mode = enhanced_toggle_bf_mode

# Usage example for integration
def integrate_enhanced_bf_features(main_window_instance):
    """
    Function to integrate enhanced BF features into existing main window
    Call this after main window initialization
    """
    EnhancedMainWindowIntegration.add_enhanced_bf_features(main_window_instance)
    print("Enhanced BF features integrated successfully!")
    print("New menu item: Blast Furnace → Enhanced Conveyor-Bunker Integration")
    print("Hotkey: Ctrl+Shift+B")