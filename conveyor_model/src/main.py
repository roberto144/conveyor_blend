# Standard library imports
import os
import sys

# Third-party imports
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.main_window import MainWindow
from src.utils.config import ConfigManager

def main():
    """Main application entry point"""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Conveyor Blending Model")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Roberto Abreu Alencar")
    
    # Set application style
    app.setStyle('Fusion')  # Modern cross-platform style
    
    # Load configuration
    config = ConfigManager()
    
    # Create and show main window
    try:
        main_window = MainWindow()
        
        # Set window size from config
        width = config.get('ui.window_width', 1400)
        height = config.get('ui.window_height', 800)
        main_window.resize(width, height)
        
        main_window.show()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()



