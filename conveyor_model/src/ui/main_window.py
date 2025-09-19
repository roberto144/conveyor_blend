# src/ui/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QMessageBox, QProgressBar, QStatusBar, QMenuBar, 
                             QAction, QApplication, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import traceback

from .widgets.input_widgets import InputPanel
from .widgets.table_widgets import SiloTable, MaterialTable  
from .widgets.plot_widgets import PlotWidget
from .dialogs.error_dialog import ErrorDialog
from ..simulation.engine import SimulationEngine
from ..models.simulation_data import SimulationParameters, SimulationResults
from ..utils.file_handler import FileHandler
from ..utils.exceptions import ValidationError, SimulationError

class SimulationWorker(QThread):
    """Worker thread for running simulations"""
    finished = pyqtSignal(object)  # SimulationResults
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, parameters: SimulationParameters):
        super().__init__()
        self.parameters = parameters
        self.engine = SimulationEngine()
    
    def run(self):
        try:
            results = self.engine.run_simulation(self.parameters)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Conveyor Blending Model - v1.0')
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
        
        # Left panel for inputs
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel for results and plots
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 1000])
        
        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(main_splitter)
        central_widget.setLayout(layout)
    
    def create_left_panel(self) -> QWidget:
        """Create the left input panel"""
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
    
    def create_right_panel(self) -> QWidget:
        """Create the right results panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Plot widget
        self.plot_widget = PlotWidget()
        layout.addWidget(self.plot_widget)
        
        panel.setLayout(layout)
        return panel
    
    def setup_menus(self):
        """Setup application menus"""
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
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')
    
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Connect material table changes to silo table
        self.material_table.materials_changed.connect(
            self.silo_table.update_material_options
        )
        
        # Connect run button to simulation
        self.input_panel.run_requested.connect(self.run_simulation)
    
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
    
    def run_simulation(self):
        """Run the simulation"""
        try:
            # Collect parameters
            parameters = self.collect_simulation_parameters()
            
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_bar.showMessage('Running simulation...')
            
            # Start simulation in worker thread
            self.simulation_worker = SimulationWorker(parameters)
            self.simulation_worker.finished.connect(self.on_simulation_finished)
            self.simulation_worker.error.connect(self.on_simulation_error)
            self.simulation_worker.start()
            
        except ValidationError as e:
            ErrorDialog.show_error(self, "Validation Error", str(e))
        except Exception as e:
            ErrorDialog.show_error(self, "Error", f"Failed to start simulation: {str(e)}")
    
    def on_simulation_finished(self, results: SimulationResults):
        """Handle simulation completion"""
        self.current_results = results
        self.progress_bar.setVisible(False)
        
        # Update plots
        self.plot_widget.update_plots(results)
        
        # Show summary
        self.show_simulation_summary(results)
        self.status_bar.showMessage('Simulation completed successfully')
    
    def on_simulation_error(self, error_message: str):
        """Handle simulation error"""
        self.progress_bar.setVisible(False)
        ErrorDialog.show_error(self, "Simulation Error", error_message)
        self.status_bar.showMessage('Simulation failed')
    
    def collect_simulation_parameters(self) -> SimulationParameters:
        """Collect all simulation parameters from UI"""
        # Get basic parameters
        basic_params = self.input_panel.get_parameters()
        
        # Get materials
        materials = self.material_table.get_materials()
        if not materials:
            raise ValidationError("At least one material must be defined")
        
        # Get silos
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
    
    def collect_case_data(self) -> dict:
        """Collect all case data for saving"""
        return {
            'parameters': self.input_panel.get_parameters(),
            'materials': self.material_table.get_materials(),
            'silos': [silo.__dict__ for silo in self.silo_table.get_silos()],
            'results': self.current_results.__dict__ if self.current_results else None
        }
    
    def load_case_data(self, data: dict):
        """Load case data into UI"""
        # Load parameters
        if 'parameters' in data:
            self.input_panel.set_parameters(data['parameters'])
        
        # Load materials
        if 'materials' in data:
            self.material_table.set_materials(data['materials'])
        
        # Load silos
        if 'silos' in data:
            self.silo_table.set_silos(data['silos'])
        
        # Load results if available
        if 'results' in data and data['results']:
            # You could reload and display previous results here
            pass
    
    def show_simulation_summary(self, results: SimulationResults):
        """Show a summary of simulation results"""
        summary = f"""
Simulation completed successfully!

Time steps: {results.time_steps}
Materials: {results.material_count}
Total simulation time: {results.parameters.total_time:.1f} s
Final time reached: {results.metadata.get('final_time', 0):.1f} s

Mass balance check:
- Balance error: {results.metadata.get('balance_error', 'N/A')}%
"""
        
        QMessageBox.information(self, "Simulation Complete", summary)
    
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
</ul>
<p>Built with PyQt5 and matplotlib</p>
"""
        QMessageBox.about(self, "About", about_text)
    
    def closeEvent(self, event):
        """Handle application close event"""
        if self.simulation_worker and self.simulation_worker.isRunning():
            reply = QMessageBox.question(
                self, 'Close Application', 
                'Simulation is running. Do you want to close anyway?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            else:
                self.simulation_worker.terminate()
                self.simulation_worker.wait()
        
        event.accept()