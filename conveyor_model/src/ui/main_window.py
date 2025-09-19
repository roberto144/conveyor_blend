# src/ui/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QMessageBox, QProgressBar, QStatusBar, QMenuBar, 
                             QAction, QApplication, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import traceback
import numpy as np

from typing import Dict
from datetime import datetime

from .widgets.input_widgets import InputPanel
from .widgets.table_widgets import SiloTable, MaterialTable  
from .widgets.plot_widgets import PlotWidget
from .dialogs.error_dialog import ErrorDialog
from ..simulation.engine import SimulationEngine
from ..models.simulation_data import SimulationParameters, SimulationResults
from ..utils.file_handler import FileHandler
from ..utils.exceptions import ValidationError, SimulationError

# FIXED: Correct import paths for BF integration
from .widgets.bf_integration import BlastFurnaceBunkerWidget, BlastFurnaceMaterialWidget
from ..simulation.bf_bunker_viz import BlastFurnaceBunker, BunkerVisualization
# Add these imports after your existing ones
try:
    from .widgets.enhanced_bf_integration import (
        EnhancedBFIntegrationWidget, 
        EnhancedMainWindowIntegration
    )
    ENHANCED_BF_AVAILABLE = True
except ImportError:
    print("Enhanced BF integration not available")
    ENHANCED_BF_AVAILABLE = False

class SimulationWorker(QThread):
    """Worker thread for running simulations"""
    finished = pyqtSignal(object)  # SimulationResults
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, parameters: SimulationParameters, use_bf_mode: bool = False):
        super().__init__()
        self.parameters = parameters
        self.use_bf_mode = use_bf_mode
        self.engine = SimulationEngine()
    
    def run(self):
        try:
            if self.use_bf_mode:
                # Initialize blast furnace integration
                self.engine.initialize_blast_furnace()
                # Add BF-specific processing here
                results = self.engine.run_bf_simulation(self.parameters)
            else:
                results = self.engine.run_simulation(self.parameters)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """Main application window with full BF integration"""
    
    def __init__(self):
        super().__init__()
        
        self.bf_mode_enabled = False
        self.bf_bunker_window = None
        self.enhanced_bf_widget = None

        self.setWindowTitle('Conveyor Blending Model - v1.1')
        self.setGeometry(100, 100, 1400, 800)
        
        # Initialize components
        self.file_handler = FileHandler()
        self.current_results = None
        self.simulation_worker = None

        # Setup UI
        self.setup_ui()
        self.setup_menus()
        self.setup_status_bar()
        self.setup_connections()

    def setup_ui(self):
        """Initialize the main UI components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Create tabbed interface for mode switching
        self.left_tabs = QTabWidget()
        
        # Standard mode panel
        self.standard_panel = self.create_standard_panel()
        self.left_tabs.addTab(self.standard_panel, "Standard Mode")
        
        # Blast furnace mode panel
        self.bf_panel = self.create_bf_panel()
        self.bf_panel.setEnabled(False)
        self.left_tabs.addTab(self.bf_panel, "Blast Furnace Mode")
        
        # Connect tab change signal
        self.left_tabs.currentChanged.connect(self.on_mode_tab_changed)
        
        main_splitter.addWidget(self.left_tabs)
        
        # Right panel for results and plots
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 1000])
        
        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(main_splitter)
        central_widget.setLayout(layout)

        #integrate enhanced BF features
        if ENHANCED_BF_AVAILABLE:
            EnhancedMainWindowIntegration.add_enhanced_bf_features(self)
    
    def create_standard_panel(self) -> QWidget:
        """Create the standard mode input panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Input fields for simulation parameters
        self.input_panel = InputPanel()
        layout.addWidget(self.input_panel)
        
        # Material table
        self.material_table = MaterialTable()
        layout.addWidget(self.material_table)
        
        # Silo table
        self.silo_table = SiloTable()
        layout.addWidget(self.silo_table)
        
        panel.setLayout(layout)
        return panel
    
    def create_bf_panel(self) -> QWidget:
        """Create the blast furnace mode panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # BF-specific input panel
        self.bf_input_panel = InputPanel()
        layout.addWidget(self.bf_input_panel)
        
        # BF materials with chemistry
        self.bf_material_widget = BlastFurnaceMaterialWidget()
        layout.addWidget(self.bf_material_widget)
        
        # Modified silo table for BF bunkers
        self.bf_silo_table = SiloTable()
        # Customize column headers for BF
        self.bf_silo_table.table.setHorizontalHeaderLabels(
            ['Material', 'Bunker Volume [m³]', 'Flow [t/h]', 
             'Material Position', 'Bunker Position', 'Start Time [s]']
        )
        layout.addWidget(self.bf_silo_table)
        
        panel.setLayout(layout)
        return panel

    def create_right_panel(self) -> QWidget:
        """Create the right results panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Tabbed plot widget for different visualizations
        self.plot_tabs = QTabWidget()
        
        # Standard plot widget
        self.plot_widget = PlotWidget()
        self.plot_tabs.addTab(self.plot_widget, "Flow Analysis")
        
        # BF chemistry plots widget
        self.bf_chemistry_widget = QWidget()
        self.setup_bf_chemistry_widget()
        self.plot_tabs.addTab(self.bf_chemistry_widget, "Chemistry Trends")
        
        layout.addWidget(self.plot_tabs)
        
        panel.setLayout(layout)
        return panel
    
    def setup_bf_chemistry_widget(self):
        """Setup the BF chemistry visualization widget"""
        if not hasattr(self, 'bf_chemistry_widget'):
            print("Debug: Creating bf_chemistry_widget")  # ADD DEBUG
            return
            
        layout = QVBoxLayout()
        
        # Placeholder for BF chemistry plots
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        
        self.bf_figure = Figure(figsize=(10, 6))
        self.bf_canvas = FigureCanvas(self.bf_figure)
        layout.addWidget(self.bf_canvas)
        
        self.bf_chemistry_widget.setLayout(layout)
        print("Debug: bf_chemistry_widget setup complete")  # ADD DEBUG

    def setup_menus(self):
        """Setup application menus with BF additions"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        new_action = QAction('&New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_case)
        file_menu.addAction(new_action)
        
        open_action = QAction('&Open...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_case)
        file_menu.addAction(open_action)
        
        save_action = QAction('&Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_case)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save &As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_case_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Simulation menu
        sim_menu = menubar.addMenu('&Simulation')
        
        run_action = QAction('&Run Simulation', self)
        run_action.setShortcut('F5')
        run_action.triggered.connect(self.run_simulation)
        sim_menu.addAction(run_action)
        
        # Blast Furnace menu
        bf_menu = menubar.addMenu('&Blast Furnace')
        if ENHANCED_BF_AVAILABLE:
            bf_menu.addSeparator()

            self.enhanced_bf_action = QAction('&Enhanced Conveyor-Bunker Integration', self)
            self.enhanced_bf_action.setShortcut("Ctrl+Shift+B")
            self.enhanced_bf_action.triggered.connect(self.show_enhanced_bf_integration)
            self.enhanced_bf_action.setEnabled(False)
            bf_menu.addAction(self.enhanced_bf_action)


        # Enable/Disable BF Mode
        self.bf_mode_action = QAction('&Enable BF Mode', self)
        self.bf_mode_action.setCheckable(True)
        self.bf_mode_action.setChecked(False)
        self.bf_mode_action.triggered.connect(self.toggle_bf_mode)
        bf_menu.addAction(self.bf_mode_action)
        
        bf_menu.addSeparator()
        
        # Open Bunker Visualization
        bf_bunker_action = QAction('&Bunker Chemistry Visualization', self)
        bf_bunker_action.setShortcut('Ctrl+B')
        bf_bunker_action.triggered.connect(self.show_bf_bunker_visualization)
        bf_bunker_action.setEnabled(False)
        self.bf_bunker_action = bf_bunker_action
        bf_menu.addAction(bf_bunker_action)
        
        # Load BF Material Presets
        bf_presets_action = QAction('&Load BF Material Presets', self)
        bf_presets_action.triggered.connect(self.load_bf_presets)
        bf_presets_action.setEnabled(False)
        self.bf_presets_action = bf_presets_action
        bf_menu.addAction(bf_presets_action)
        
        # Export Chemistry Report
        bf_export_action = QAction('&Export Chemistry Report', self)
        bf_export_action.triggered.connect(self.export_bf_chemistry)
        bf_export_action.setEnabled(False)
        self.bf_export_action = bf_export_action
        bf_menu.addAction(bf_export_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        bf_help_action = QAction('&BF Mode Guide', self)
        bf_help_action.triggered.connect(self.show_bf_help)
        help_menu.addAction(bf_help_action)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')
    
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Standard mode connections
        self.material_table.materials_changed.connect(
            self.silo_table.update_material_options
        )
        self.input_panel.run_requested.connect(self.run_simulation)
        
        # BF mode connections
        if hasattr(self, 'bf_material_widget'):
            self.bf_material_widget.materials_updated.connect(
                self.on_bf_materials_updated
            )
        
        if hasattr(self, 'bf_input_panel'):
            self.bf_input_panel.run_requested.connect(self.run_simulation)
    
    def toggle_bf_mode(self, checked):
        """Toggle between standard and blast furnace modes"""
        self.bf_mode_enabled = checked
        
        if checked:
            # Enable BF mode
            self.bf_panel.setEnabled(True)
            self.left_tabs.setCurrentIndex(1)  # Switch to BF tab
            
            # Enable BF menu items
            self.bf_bunker_action.setEnabled(True)
            self.bf_presets_action.setEnabled(True)
            self.bf_export_action.setEnabled(True)
            
            # Update status
            self.status_bar.showMessage('Blast Furnace Mode Enabled')
            
            # Update window title
            self.setWindowTitle('Conveyor Blending Model - v1.0 [BLAST FURNACE MODE]')
            
            # Load default BF materials
            if hasattr(self, 'bf_material_widget'):
                self.bf_material_widget.load_default_materials()

            self.update_enhanced_bf_menu_state()
            
        else:
            # Disable BF mode
            self.bf_panel.setEnabled(False)
            self.left_tabs.setCurrentIndex(0)  # Switch to standard tab
            
            # Disable BF menu items
            self.bf_bunker_action.setEnabled(False)
            self.bf_presets_action.setEnabled(False)
            self.bf_export_action.setEnabled(False)
            
            # Close BF visualization window if open
            if self.bf_bunker_window:
                self.bf_bunker_window.close()
                self.bf_bunker_window = None
            
            # Update status
            self.status_bar.showMessage('Standard Mode')
            
            # Reset window title
            self.setWindowTitle('Conveyor Blending Model - v1.0')

            if hasattr(self, 'enhanced_bf_widget') and self.enhanced_bf_widget:
                self.enhanced_bf_widget.close()
                self.enhanced_bf_widget = None
        
            self.update_enhanced_bf_menu_state()
    
    def on_mode_tab_changed(self, index):
        """Handle tab change between modes"""
        if index == 1 and not self.bf_mode_enabled:
            # User clicked BF tab but mode not enabled
            QMessageBox.information(
                self, 
                "Blast Furnace Mode", 
                "Please enable Blast Furnace Mode from the menu first.\n"
                "Go to: Blast Furnace → Enable BF Mode"
            )
            self.left_tabs.setCurrentIndex(0)
    
    def show_bf_bunker_visualization(self):
        """Show the blast furnace bunker visualization window"""
        if not self.bf_mode_enabled:
            QMessageBox.warning(
                self,
                "BF Mode Required",
                "Please enable Blast Furnace Mode first."
            )
            return
        
        # Create or show the BF bunker window
        if not self.bf_bunker_window:
            self.bf_bunker_window = QWidget()
            self.bf_bunker_window.setWindowTitle('Blast Furnace Bunker Chemistry Visualization')
            self.bf_bunker_window.resize(1200, 800)
            
            layout = QVBoxLayout()
            self.bf_bunker_widget = BlastFurnaceBunkerWidget()
            
            # Connect BF materials to bunker widget
            if hasattr(self, 'bf_material_widget'):
                self.bf_bunker_widget.materials_widget = self.bf_material_widget
            
            layout.addWidget(self.bf_bunker_widget)
            self.bf_bunker_window.setLayout(layout)
        
        self.bf_bunker_window.show()
        self.bf_bunker_window.raise_()
        self.bf_bunker_window.activateWindow()
    
    def load_bf_presets(self):
        """Load blast furnace material presets"""
        if hasattr(self, 'bf_material_widget'):
            self.bf_material_widget.load_default_materials()
            QMessageBox.information(
                self,
                "Presets Loaded",
                "Blast furnace material presets have been loaded:\n"
                "- Pellets (65.5% Fe)\n"
                "- Sinter (57.2% Fe)\n"
                "- Lump Ore (62.0% Fe)\n"
                "- Coke\n"
                "- Limestone (flux)\n"
                "- Dolomite (flux)\n"
                "- Quartzite"
            )
    
    def export_bf_chemistry(self):
        """Export blast furnace chemistry report"""
        if not self.current_results:
            QMessageBox.warning(
                self,
                "No Results",
                "Please run a simulation first."
            )
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export BF Chemistry Report",
                "",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if filename:
                self._export_bf_chemistry_data(filename)
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Chemistry report exported to:\n{filename}"
                )
        except Exception as e:
            ErrorDialog.show_error(self, "Export Error", str(e))
    
    def _export_bf_chemistry_data(self, filename):
        """Helper method to export BF chemistry data including time series"""
        import csv
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Section 1: Material Chemistry Definitions
            writer.writerow(['=== MATERIAL CHEMISTRY DEFINITIONS ==='])
            writer.writerow(['Material', 'Fe%', 'SiO2%', 'CaO%', 'MgO%', 'Al2O3%', 'Density (kg/m³)', 'Basicity_B2'])
            
            if hasattr(self.current_results.parameters, 'material_chemistry'):
                for material, data in self.current_results.parameters.material_chemistry.items():
                    chem = data.get('chemistry', {})
                    density = data.get('density', 0)
                    basicity = chem.get('CaO', 0) / max(chem.get('SiO2', 1), 0.1)
                    
                    writer.writerow([
                        material,
                        f"{chem.get('Fe', 0):.2f}",
                        f"{chem.get('SiO2', 0):.2f}",
                        f"{chem.get('CaO', 0):.2f}",
                        f"{chem.get('MgO', 0):.2f}",
                        f"{chem.get('Al2O3', 0):.2f}",
                        f"{density:.1f}",
                        f"{basicity:.3f}"
                    ])
            
            writer.writerow([])  # Empty row
            
            # Section 2: Chemistry Time Series at Conveyor Discharge
            writer.writerow(['=== CHEMISTRY TIME SERIES AT CONVEYOR DISCHARGE ==='])
            writer.writerow(['Time (s)', 'Weighted_Fe%', 'Weighted_SiO2%', 'Weighted_CaO%', 
                           'Weighted_MgO%', 'Weighted_Al2O3%', 'Basicity_B2', 'Total_Flow (kg/s)'])
            
            # Calculate chemistry time series
            chemistry_trends = self._calculate_chemistry_time_series(self.current_results)
            
            for i, time_point in enumerate(chemistry_trends['time_points']):
                writer.writerow([
                    f"{time_point:.1f}",
                    f"{chemistry_trends['fe_trend'][i]:.2f}" if i < len(chemistry_trends['fe_trend']) else "0.00",
                    f"{chemistry_trends['sio2_trend'][i]:.2f}" if i < len(chemistry_trends['sio2_trend']) else "0.00",
                    f"{chemistry_trends['cao_trend'][i]:.2f}" if i < len(chemistry_trends['cao_trend']) else "0.00",
                    f"{chemistry_trends['mgo_trend'][i]:.2f}" if i < len(chemistry_trends['mgo_trend']) else "0.00",
                    f"{chemistry_trends['al2o3_trend'][i]:.2f}" if i < len(chemistry_trends['al2o3_trend']) else "0.00",
                    f"{chemistry_trends['basicity_trend'][i]:.3f}" if i < len(chemistry_trends['basicity_trend']) else "0.000",
                    f"{self.current_results.flow_data[i, -1]:.2f}" if i < len(self.current_results.flow_data) else "0.00"
                ])
            
            writer.writerow([])  # Empty row
            
            # Section 3: Statistical Summary
            writer.writerow(['=== STATISTICAL SUMMARY ==='])
            writer.writerow(['Parameter', 'Average', 'Std Dev', 'Min', 'Max', 'Target', 'Quality'])
            
            if chemistry_trends['fe_trend']:
                fe_avg = np.mean(chemistry_trends['fe_trend'])
                fe_std = np.std(chemistry_trends['fe_trend'])
                fe_min = np.min(chemistry_trends['fe_trend'])
                fe_max = np.max(chemistry_trends['fe_trend'])
                fe_quality = 'Good' if fe_std < 2.0 else 'Poor'
                writer.writerow(['Fe%', f"{fe_avg:.2f}", f"{fe_std:.2f}", f"{fe_min:.2f}", f"{fe_max:.2f}", "58-66%", fe_quality])
                
                sio2_avg = np.mean(chemistry_trends['sio2_trend'])
                sio2_std = np.std(chemistry_trends['sio2_trend'])
                sio2_min = np.min(chemistry_trends['sio2_trend'])
                sio2_max = np.max(chemistry_trends['sio2_trend'])
                writer.writerow(['SiO2%', f"{sio2_avg:.2f}", f"{sio2_std:.2f}", f"{sio2_min:.2f}", f"{sio2_max:.2f}", "4-8%", "-"])
                
                cao_avg = np.mean(chemistry_trends['cao_trend'])
                cao_std = np.std(chemistry_trends['cao_trend'])
                cao_min = np.min(chemistry_trends['cao_trend'])
                cao_max = np.max(chemistry_trends['cao_trend'])
                writer.writerow(['CaO%', f"{cao_avg:.2f}", f"{cao_std:.2f}", f"{cao_min:.2f}", f"{cao_max:.2f}", "6-12%", "-"])
                
                b2_avg = np.mean(chemistry_trends['basicity_trend'])
                b2_std = np.std(chemistry_trends['basicity_trend'])
                b2_min = np.min(chemistry_trends['basicity_trend'])
                b2_max = np.max(chemistry_trends['basicity_trend'])
                b2_quality = 'Good' if abs(b2_avg - 1.1) < 0.1 else 'Poor'
                writer.writerow(['Basicity B2', f"{b2_avg:.3f}", f"{b2_std:.3f}", f"{b2_min:.3f}", f"{b2_max:.3f}", "1.0-1.2", b2_quality])
            
            writer.writerow([])  # Empty row
            
            # Section 4: Simulation Parameters
            writer.writerow(['=== SIMULATION PARAMETERS ==='])
            writer.writerow(['Parameter', 'Value', 'Unit'])
            writer.writerow(['Total Time', f"{self.current_results.parameters.total_time:.1f}", 'seconds'])
            writer.writerow(['Conveyor Length', f"{self.current_results.parameters.conveyor_length:.1f}", 'meters'])
            writer.writerow(['Conveyor Velocity', f"{self.current_results.parameters.conveyor_velocity:.2f}", 'm/s'])
            writer.writerow(['Resolution Size', f"{self.current_results.parameters.resolution_size:.2f}", 'meters'])
            writer.writerow(['Number of Materials', f"{len(self.current_results.parameters.materials)}", '-'])
            writer.writerow(['Number of Silos', f"{len(self.current_results.parameters.silos)}", '-'])
            writer.writerow(['Time Steps', f"{self.current_results.time_steps}", '-'])
            
            # Mass balance information
            if 'mass_balance' in self.current_results.metadata:
                mb = self.current_results.metadata['mass_balance']
                writer.writerow(['Mass Balance Error', f"{mb.get('balance_error_percent', 0):.3f}", '%'])
            
            writer.writerow([])
            writer.writerow(['Export completed at:', str(datetime.now())])
            
    def show_simulation_summary(self, results: SimulationResults):
        """Enhanced simulation summary with BF-specific information"""
        mode_info = ""
        chemistry_info = ""
        
        if self.bf_mode_enabled:
            mode_info = "\nBF Mode: Chemistry tracking enabled"
            
            # Add chemistry quality summary if available
            if hasattr(results, 'chemistry_trends') and results.chemistry_trends:
                trends = results.chemistry_trends
                if trends.get('fe_trend'):
                    fe_avg = np.mean(trends['fe_trend'])
                    fe_std = np.std(trends['fe_trend'])
                    b2_avg = np.mean(trends['basicity_trend'])
                    
                    chemistry_info = f"""
                    Chemistry Quality Summary:
                    - Average Fe Content: {fe_avg:.2f}% (±{fe_std:.2f})
                    - Average Basicity: {b2_avg:.3f}
                    - Fe Stability: {'Good' if fe_std < 2.0 else 'Poor'}
                    - Basicity Target: {'Good' if abs(b2_avg - 1.1) < 0.1 else 'Poor'}"""
        
        # Mass balance information
        mass_balance_info = ""
        if 'mass_balance' in results.metadata:
            mb = results.metadata['mass_balance']
            mass_balance_info = f"\nMass Balance Error: {mb.get('balance_error_percent', 0):.3f}%"
        
        summary = f"""
        Simulation completed successfully!{mode_info}

        Time steps: {results.time_steps}
        Materials: {results.material_count}
        Total simulation time: {results.parameters.total_time:.1f} s
        Final time reached: {results.metadata.get('final_time', 0):.1f} s{mass_balance_info}{chemistry_info}
        """
        
        QMessageBox.information(self, "Simulation Complete", summary)
    
    def show_bf_help(self):
        """Show blast furnace mode help"""
        help_text = """
        <h3>Blast Furnace Mode Guide</h3>

        <h4>Overview</h4>
        <p>Blast Furnace Mode provides specialized features for simulating material flow 
        in blast furnace stock house operations, with focus on chemical composition tracking.</p>

        <h4>Key Features:</h4>
        <ul>
        <li><b>Material Chemistry:</b> Track Fe%, SiO2%, CaO%, MgO%, Al2O3% for each material</li>
        <li><b>Bunker Visualization:</b> See material stratification in the bunker</li>
        <li><b>Basicity Control:</b> Monitor CaO/SiO2 ratio (target ~1.1)</li>
        <li><b>Discharge Prediction:</b> Predict chemistry of materials entering the furnace</li>
        </ul>

        <h4>How to Use:</h4>
        <ol>
        <li>Enable BF Mode from the Blast Furnace menu</li>
        <li>Define materials with their chemical compositions</li>
        <li>Set up bunker charging sequence</li>
        <li>Open Bunker Chemistry Visualization to see stratification</li>
        <li>Run simulation to analyze material flow and chemistry trends</li>
        </ol>

        <h4>Important Parameters:</h4>
        <ul>
        <li><b>Basicity (B2):</b> CaO/SiO2 ratio, should be 1.0-1.2 for optimal operation</li>
        <li><b>Fe Content:</b> Iron content should be consistent (±2%) for stable furnace operation</li>
        <li><b>Bunker Level:</b> Maintain 30-85% fill for continuous operation</li>
        </ul>
        """
        QMessageBox.about(self, "Blast Furnace Mode Guide", help_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>Conveyor Blending Model v1.0</h3>
        <p>A modular application for simulating material flow and blending on conveyor belts.</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Multiple material simulation</li>
        <li>Configurable silo parameters</li>
        <li>Real-time visualization</li>
        <li>Save/load functionality</li>
        <li>Blast Furnace Mode with chemistry tracking</li>
        </ul>
        <p>Built with PyQt5 and matplotlib</p>
        """
        QMessageBox.about(self, "About", about_text)
    
    def run_simulation(self):
        """Run simulation with mode detection"""
        try:
            # Collect parameters based on mode
            if self.bf_mode_enabled:
                parameters = self.collect_bf_simulation_parameters()
            else:
                parameters = self.collect_simulation_parameters()
            
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            mode_text = " (BF Mode)" if self.bf_mode_enabled else ""
            self.status_bar.showMessage(f'Running simulation{mode_text}...')
            
            # Start simulation in worker thread with mode flag
            self.simulation_worker = SimulationWorker(parameters, self.bf_mode_enabled)
            self.simulation_worker.finished.connect(self.on_simulation_finished)
            self.simulation_worker.error.connect(self.on_simulation_error)
            self.simulation_worker.start()
            
        except ValidationError as e:
            ErrorDialog.show_error(self, "Validation Error", str(e))
        except Exception as e:
            ErrorDialog.show_error(self, "Error", f"Failed to start simulation: {str(e)}")
    
    def collect_bf_simulation_parameters(self) -> SimulationParameters:
        """Collect blast furnace specific parameters"""
        # Get basic parameters from BF input panel
        basic_params = self.bf_input_panel.get_parameters()
        
        # Get BF materials with chemistry
        materials = list(self.bf_material_widget.materials_db.keys())
        if not materials:
            raise ValidationError("At least one material must be defined")
        
        # Get BF bunkers/silos
        silos = self.bf_silo_table.get_silos()
        if not silos:
            raise ValidationError("At least one bunker must be defined")
        
        # Create parameters object
        params = SimulationParameters(
            total_time=basic_params['total_time'],
            conveyor_length=basic_params['conveyor_length'],
            resolution_size=basic_params['resolution_size'],
            conveyor_velocity=basic_params['conveyor_velocity'],
            materials=materials,
            silos=silos
        )
        
        # Attach chemistry data
        params.material_chemistry = self.bf_material_widget.materials_db
        
        return params
    
    def collect_simulation_parameters(self) -> SimulationParameters:
        """Collect standard simulation parameters"""
        basic_params = self.input_panel.get_parameters()
        materials = self.material_table.get_materials()
        if not materials:
            raise ValidationError("At least one material must be defined")
        silos = self.silo_table.get_silos()
        if not silos:
            raise ValidationError("At least one silo must be defined")
        
        return SimulationParameters(
            total_time=basic_params['total_time'],
            conveyor_length=basic_params['conveyor_length'],
            resolution_size=basic_params['resolution_size'],
            conveyor_velocity=basic_params['conveyor_velocity'],
            materials=materials,
            silos=silos
        )
    
    def on_simulation_finished(self, results: SimulationResults):
        """Handle simulation completion"""
        self.current_results = results
        self.progress_bar.setVisible(False)
        
        # Update plots based on mode
        if self.bf_mode_enabled and self.enhanced_bf_widget:
            self.enhanced_bf_widget.set_conveyor_results(results)
            self.update_bf_plots(results)
        else:
            self.plot_widget.update_plots(results)
        
        # Show summary
        self.show_simulation_summary(results)
        self.status_bar.showMessage('Simulation completed successfully')
        
        if (self.bf_mode_enabled and 
            hasattr(self, 'enhanced_bf_widget') and 
            self.enhanced_bf_widget and 
            self.enhanced_bf_widget.isVisible()):
            self.enhanced_bf_widget.set_conveyor_results(results)
    
    def update_bf_plots(self, results: SimulationResults):
        """Update BF-specific plots"""
        print("Debug: update_bf_plots called")  # ADD DEBUG
        
        # Update standard plots
        self.plot_widget.update_plots(results)
        
        # Update BF chemistry plots
        if hasattr(results.parameters, 'material_chemistry'):
            print("Debug: Calling update_bf_chemistry_plots")  # ADD DEBUG
            self.update_bf_chemistry_plots(results)
        else:
            print("Debug: No material_chemistry found in results")  # ADD DEBUG 
    
    def update_bf_chemistry_plots(self, results: SimulationResults):
        """Update blast furnace chemistry plots with time-based weighted averages"""
        print("Debug: update_bf_chemistry_plots called")  # ADD THIS DEBUG LINE
        
        # Check if BF chemistry widget exists
        if not hasattr(self, 'bf_chemistry_widget') or not self.bf_chemistry_widget:
            print("Debug: bf_chemistry_widget not found")  # ADD THIS DEBUG LINE
            return
        
        # Check if we have the figure and canvas
        if not hasattr(self, 'bf_figure') or not hasattr(self, 'bf_canvas'):
            print("Debug: bf_figure or bf_canvas not found")  # ADD THIS DEBUG LINE
            return
        
        self.bf_figure.clear()
        
        # Create 2x3 subplot layout for better organization
        ax1 = self.bf_figure.add_subplot(2, 3, 1)
        ax2 = self.bf_figure.add_subplot(2, 3, 2)
        ax3 = self.bf_figure.add_subplot(2, 3, 3)
        ax4 = self.bf_figure.add_subplot(2, 3, 4)
        ax5 = self.bf_figure.add_subplot(2, 3, 5)
        ax6 = self.bf_figure.add_subplot(2, 3, 6)
        
        # Calculate weighted average chemistry over time
        chemistry_trends = self._calculate_chemistry_time_series(results)
        
        print(f"Debug: chemistry_trends time_points: {len(chemistry_trends['time_points'])}")  # ADD DEBUG
        
        if not chemistry_trends['time_points']:
            # No data available - show placeholder
            for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
                ax.text(0.5, 0.5, 'No chemistry data available\nCheck BF mode and materials', 
                    ha='center', va='center', transform=ax.transAxes, fontsize=12)
            self.bf_figure.tight_layout()
            self.bf_canvas.draw()
            return
        
        time_points = chemistry_trends['time_points']
        
        # Fe content over time
        if chemistry_trends['fe_trend']:
            ax1.plot(time_points, chemistry_trends['fe_trend'], 'r-', linewidth=2, label='Fe Content')
            ax1.set_title('Fe Content Over Time')
            ax1.set_ylabel('Fe (%)')
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, max(chemistry_trends['fe_trend']) * 1.1 if chemistry_trends['fe_trend'] else 70)
            
            # Add target range for Fe content (typical: 58-66%)
            ax1.axhspan(58, 66, alpha=0.2, color='green', label='Target Range')
            ax1.legend()
        
        # SiO2 content over time
        if chemistry_trends['sio2_trend']:
            ax2.plot(time_points, chemistry_trends['sio2_trend'], 'b-', linewidth=2, label='SiO2 Content')
            ax2.set_title('SiO2 Content Over Time')
            ax2.set_ylabel('SiO2 (%)')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, max(chemistry_trends['sio2_trend']) * 1.1 if chemistry_trends['sio2_trend'] else 15)
            
            # Add target range for SiO2 (typical: 4-8%)
            ax2.axhspan(4, 8, alpha=0.2, color='blue', label='Target Range')
            ax2.legend()
        
        # CaO content over time
        if chemistry_trends['cao_trend']:
            ax3.plot(time_points, chemistry_trends['cao_trend'], 'g-', linewidth=2, label='CaO Content')
            ax3.set_title('CaO Content Over Time')
            ax3.set_ylabel('CaO (%)')
            ax3.grid(True, alpha=0.3)
            ax3.set_ylim(0, max(chemistry_trends['cao_trend']) * 1.1 if chemistry_trends['cao_trend'] else 15)
            
            # Add target range for CaO (varies with basicity target)
            ax3.axhspan(6, 12, alpha=0.2, color='green', label='Typical Range')
            ax3.legend()
        
        # MgO content over time
        if chemistry_trends['mgo_trend']:
            ax4.plot(time_points, chemistry_trends['mgo_trend'], 'm-', linewidth=2, label='MgO Content')
            ax4.set_title('MgO Content Over Time')
            ax4.set_ylabel('MgO (%)')
            ax4.set_xlabel('Time (s)')
            ax4.grid(True, alpha=0.3)
            ax4.set_ylim(0, max(chemistry_trends['mgo_trend']) * 1.1 if chemistry_trends['mgo_trend'] else 5)
            
            # Add target range for MgO (typical: 0.5-3%)
            ax4.axhspan(0.5, 3, alpha=0.2, color='purple', label='Target Range')
            ax4.legend()
        
        # Al2O3 content over time
        if chemistry_trends['al2o3_trend']:
            ax5.plot(time_points, chemistry_trends['al2o3_trend'], 'orange', linewidth=2, label='Al2O3 Content')
            ax5.set_title('Al2O3 Content Over Time')
            ax5.set_ylabel('Al2O3 (%)')
            ax5.set_xlabel('Time (s)')
            ax5.grid(True, alpha=0.3)
            ax5.set_ylim(0, max(chemistry_trends['al2o3_trend']) * 1.1 if chemistry_trends['al2o3_trend'] else 5)
            
            # Add target range for Al2O3 (typical: 1-3%)
            ax5.axhspan(1, 3, alpha=0.2, color='orange', label='Target Range')
            ax5.legend()
        
        # Basicity (B2) over time with enhanced features
        if chemistry_trends['basicity_trend']:
            ax6.plot(time_points, chemistry_trends['basicity_trend'], 'purple', linewidth=2, label='Basicity (B2)')
            ax6.axhline(y=1.1, color='red', linestyle='--', linewidth=2, label='Target B2 = 1.1')
            ax6.axhspan(1.0, 1.2, alpha=0.2, color='red', label='Acceptable Range')
            ax6.set_title('Basicity (CaO/SiO2) Over Time')
            ax6.set_ylabel('Basicity (B2)')
            ax6.set_xlabel('Time (s)')
            ax6.grid(True, alpha=0.3)
            ax6.legend()
            
            # Set reasonable y-limits for basicity
            basicity_values = chemistry_trends['basicity_trend']
            if basicity_values:
                y_min = max(0, min(basicity_values) * 0.9)
                y_max = min(3.0, max(basicity_values) * 1.1)
                ax6.set_ylim(y_min, y_max)
        
        # Set common x-axis limits
        if time_points:
            x_min, x_max = 0, max(time_points)
            for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
                ax.set_xlim(x_min, x_max)
                ax.set_xlabel('Time (s)')
        
        self.bf_figure.tight_layout()
        self.bf_canvas.draw()

        def _calculate_chemistry_time_series(self, results: SimulationResults) -> Dict:
            """Calculate weighted average chemistry at conveyor discharge over time"""
        print("Debug: _calculate_chemistry_time_series called")  # ADD DEBUG
        
        trends = {
            'fe_trend': [],
            'sio2_trend': [],
            'cao_trend': [],
            'mgo_trend': [],
            'al2o3_trend': [],
            'basicity_trend': [],
            'time_points': []
        }
        
        # Check if we have chemistry data
        if not hasattr(results.parameters, 'material_chemistry'):
            print("Debug: No material_chemistry in results.parameters")  # ADD DEBUG
            return trends
        
        chemistry_data = results.parameters.material_chemistry
        materials = list(chemistry_data.keys())
        flow_data = results.flow_data
        time_array = results.get_time_array()
        
        print(f"Debug: Found {len(materials)} materials: {materials}")  # ADD DEBUG
        print(f"Debug: Flow data shape: {flow_data.shape}")  # ADD DEBUG
        print(f"Debug: Time array length: {len(time_array)}")  # ADD DEBUG
        
        # Calculate weighted averages for each time step
        for i in range(len(time_array)):
            if i >= flow_data.shape[0]:
                break
            
            # Get material flows at this time step
            material_flows = flow_data[i, :-2]  # Exclude time and total columns
            total_flow = np.sum(material_flows)
            
            if total_flow > 1e-6:  # Only calculate if there's significant flow
                # Calculate weighted chemistry
                weighted_fe = 0
                weighted_sio2 = 0
                weighted_cao = 0
                weighted_mgo = 0
                weighted_al2o3 = 0
                
                for mat_idx, material_name in enumerate(materials):
                    if mat_idx < len(material_flows):
                        material_flow = material_flows[mat_idx]
                        if material_flow > 0 and material_name in chemistry_data:
                            weight = material_flow / total_flow
                            chemistry = chemistry_data[material_name]['chemistry']
                            
                            weighted_fe += chemistry.get('Fe', 0) * weight
                            weighted_sio2 += chemistry.get('SiO2', 0) * weight
                            weighted_cao += chemistry.get('CaO', 0) * weight
                            weighted_mgo += chemistry.get('MgO', 0) * weight
                            weighted_al2o3 += chemistry.get('Al2O3', 0) * weight
                
                # Calculate basicity
                basicity = weighted_cao / max(weighted_sio2, 0.1) if weighted_sio2 > 0.1 else 0
                
                # Store results
                trends['fe_trend'].append(weighted_fe)
                trends['sio2_trend'].append(weighted_sio2)
                trends['cao_trend'].append(weighted_cao)
                trends['mgo_trend'].append(weighted_mgo)
                trends['al2o3_trend'].append(weighted_al2o3)
                trends['basicity_trend'].append(basicity)
                trends['time_points'].append(time_array[i])
        
        print(f"Debug: Generated {len(trends['time_points'])} trend points")  # ADD DEBUG
        return trends
    
    def show_simulation_summary(self, results: SimulationResults):
        """Show a summary of simulation results"""
        mode_info = ""
        if self.bf_mode_enabled:
            mode_info = "\nBF Mode: Chemistry tracking enabled"
        
        summary = f"""
        Simulation completed successfully!{mode_info}

        Time steps: {results.time_steps}
        Materials: {results.material_count}
        Total simulation time: {results.parameters.total_time:.1f} s
        Final time reached: {results.metadata.get('final_time', 0):.1f} s
        """
        
        QMessageBox.information(self, "Simulation Complete", summary)
    
    def on_simulation_error(self, error_message: str):
        """Handle simulation error"""
        self.progress_bar.setVisible(False)
        ErrorDialog.show_error(self, "Simulation Error", error_message)
        self.status_bar.showMessage('Simulation failed')
    
    def on_bf_materials_updated(self, materials_db):
        """Handle BF materials update"""
        # Update BF silo table with new materials
        material_names = list(materials_db.keys())
        self.bf_silo_table.update_material_options(material_names)
        
        # If bunker window is open, update it
        if self.bf_bunker_window and hasattr(self, 'bf_bunker_widget'):
            self.bf_bunker_widget.charging_widget.update_material_options(materials_db)
    
    # File management methods
    def new_case(self):
        """Create a new case"""
        reply = QMessageBox.question(
            self, 'New Case', 
            'Are you sure you want to create a new case?\nUnsaved changes will be lost.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.input_panel.clear()
            self.material_table.clear()
            self.silo_table.clear()
            self.plot_widget.clear()
            
            if self.bf_mode_enabled:
                self.bf_input_panel.clear()
                self.bf_material_widget.load_default_materials()
                self.bf_silo_table.clear()
            
            self.current_results = None
            self.status_bar.showMessage('New case created')
    
    def open_case(self):
        """Open a saved case"""
        try:
            data = self.file_handler.load_case()
            if data:
                self.load_case_data(data)
                self.status_bar.showMessage('Case loaded successfully')
        except Exception as e:
            ErrorDialog.show_error(self, "Load Error", f"Failed to load case: {str(e)}")
    
    def save_case(self):
        """Save current case"""
        try:
            case_data = self.collect_case_data()
            self.file_handler.save_case(case_data)
            self.status_bar.showMessage('Case saved successfully')
        except Exception as e:
            ErrorDialog.show_error(self, "Save Error", f"Failed to save case: {str(e)}")
    
    def save_case_as(self):
        """Save case with new filename"""
        try:
            case_data = self.collect_case_data()
            self.file_handler.save_case_as(case_data)
            self.status_bar.showMessage('Case saved successfully')
        except Exception as e:
            ErrorDialog.show_error(self, "Save Error", f"Failed to save case: {str(e)}")
    
    def collect_case_data(self):
        """Collect all case data for saving"""
        case_data = {
            'version': '1.0',
            'mode': 'bf' if self.bf_mode_enabled else 'standard',
            'parameters': self.input_panel.get_parameters(),
            'materials': self.material_table.get_materials(),
            'silos': [silo.__dict__ for silo in self.silo_table.get_silos()]
        }
        
        if self.bf_mode_enabled:
            case_data['bf_parameters'] = self.bf_input_panel.get_parameters()
            case_data['bf_materials'] = self.bf_material_widget.materials_db
            case_data['bf_silos'] = [silo.__dict__ for silo in self.bf_silo_table.get_silos()]
        
        return case_data
    
    def load_case_data(self, data):
        """Load case data from file"""
        mode = data.get('mode', 'standard')
        
        # Load basic parameters
        if 'parameters' in data:
            self.input_panel.set_parameters(data['parameters'])
        
        # Load materials
        if 'materials' in data:
            self.material_table.set_materials(data['materials'])
        
        # Load silos
        if 'silos' in data:
            self.silo_table.set_silos(data['silos'])
        
        # Load BF mode data if available
        if mode == 'bf' and 'bf_materials' in data:
            # Enable BF mode
            self.bf_mode_action.setChecked(True)
            self.toggle_bf_mode(True)
            
            # Load BF parameters
            if 'bf_parameters' in data:
                self.bf_input_panel.set_parameters(data['bf_parameters'])
            
            # Load BF materials
            self.bf_material_widget.materials_db = data['bf_materials']
            self.bf_material_widget.update_materials_db()
            
            # Load BF silos
            if 'bf_silos' in data:
                self.bf_silo_table.set_silos(data['bf_silos'])
    
    def show_enhanced_bf_integration(self):
        """Show enhanced BF integration window"""
        if not self.bf_mode_enabled:
            QMessageBox.warning(
                self,
                "BF Mode Required",
                "Please enable Blast Furnace Mode first."
            )
        return
    
        # Create or show the enhanced BF window
        if not self.enhanced_bf_widget:
            self.enhanced_bf_widget = EnhancedBFIntegrationWidget()
            self.enhanced_bf_widget.setWindowTitle(
            'Enhanced Blast Furnace: Conveyor to Bunker Integration'
            )
            self.enhanced_bf_widget.resize(1400, 900)
        
        # Connect to simulation results if available
            if hasattr(self, 'current_results') and self.current_results:
                self.enhanced_bf_widget.set_conveyor_results(self.current_results)
    
        self.enhanced_bf_widget.show()
        self.enhanced_bf_widget.raise_()
        self.enhanced_bf_widget.activateWindow()

    def update_enhanced_bf_menu_state(self):
        """Update enhanced BF menu item state based on BF mode"""
        if hasattr(self, 'enhanced_bf_action'):
            self.enhanced_bf_action.setEnabled(self.bf_mode_enabled)