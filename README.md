# Conveyor Blending Model v1.0

A modular PyQt5 application for simulating material flow and blending on conveyor belts. This is a complete rewrite of the original single-file application with improved architecture, better maintainability, and enhanced features.

## Features

### Core Functionality
- **Multi-material simulation** with configurable properties
- **Flexible silo configuration** with individual flow rates and timing
- **Real-time visualization** with four specialized plot types:
  - Material Flow Rates: Individual material flow tracking
  - Material Composition: Proportional composition over time
  - Total Belt Flow Rate: Combined material flow
  - Operation Schedule: Silo operation timeline
- **Save/load functionality** for case management
- **Export capabilities** for results and plots

### User Interface
- **Enhanced table editing** with dropdowns and spinboxes
- **Input validation** with clear error messages
- **Progress tracking** for long simulations
- **Professional styling** with modern Qt widgets
- **Keyboard shortcuts** and menu system

### Technical Improvements
- **Modular architecture** for easy maintenance
- **Threaded simulations** to prevent UI freezing
- **Comprehensive error handling**
- **Configuration management**
- **Extensible design** for future enhancements

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Required packages:
  - PyQt5 >= 5.15.0 (GUI framework)
  - matplotlib >= 3.3.0 (Plotting)
  - numpy >= 1.20.0 (Numerical computations)
  - pandas >= 1.3.0 (Data handling)

### Install from Source
```bash
# Clone the repository
git clone (https://github.com/roberto144/conveyor_blend.git)
cd conveyor-blending-model

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Install as Package
```bash
# Install in development mode
pip install -e .

# Run from command line
conveyor-model
```

## Project Structure

```
conveyor_model/
├── main.py                   # Main application entry point
├── bf_integration.py         # Blast Furnace integration module
├── test.py                   # Testing module
├── setup.py                  # Package setup configuration
├── requirements.txt          # Project dependencies
├── User_Manual              # Comprehensive user documentation
├── src/
│   ├── main.py              # Secondary entry point
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   ├── conveyor.py      # Conveyor model
│   │   ├── material.py      # Material definitions
│   │   ├── silo.py         # Silo configurations
│   │   └── simulation_data.py # Simulation data structures
│   ├── simulation/          # Simulation engine
│   │   ├── __init__.py
│   │   ├── bf_bunker_viz.py           # BF bunker visualization
│   │   ├── bf_conveyor_bunker_integration.py  # BF integration
│   │   ├── calculator.py    # Mathematical computations
│   │   ├── engine.py       # Core simulation logic
│   │   └── validator.py    # Input validation
│   ├── ui/                 # User interface components
│   │   ├── __init__.py
│   │   ├── main_window.py  # Main application window
│   │   ├── dialogs/        # Dialog windows
│   │   │   ├── __init__.py
│   │   │   └── error_dialog.py
│   │   └── widgets/        # Custom UI widgets
│   │       ├── __init__.py
│   │       ├── bf_integration.py
│   │       ├── enhanced_bf_integration.py
│   │       ├── input_widgets.py
│   │       ├── plot_widgets.py
│   │       └── table_widgets.py
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   ├── config.py      # Configuration management
│   │   ├── exceptions.py  # Custom exceptions
│   │   └── file_handler.py # File operations
│   └── visualization/      # Plotting and visualization
│       ├── __init__.py
│       └── plotter.py     # Plot generation
└── config/                # Configuration files
    └── default_config.json  # Default settings
```

## Usage

### Basic Workflow

1. **Define Materials**
   - Add materials in the Materials table
   - Default materials for blast furnace operation are provided:
     - Lump Ore
     - Sinter
     - Pellet
     - Dolomite
     - Limestone
     - Nut Coke
     - Quartz

2. **Configure Silos**
   - Set capacity, flow rate, and timing for each silo
   - Choose material type and position on conveyor
   - Use enhanced table editing with dropdowns and spinboxes

3. **Set Simulation Parameters**
   - Total simulation time
   - Conveyor length and velocity
   - Resolution size for accuracy

4. **Run Simulation**
   - Click "Run Simulation" or press F5
   - Monitor progress in status bar
   - View results in real-time plots with:
     - Clear material-specific legends in upper left
     - Standardized units (s, kg/s, %)
     - Optimized font sizes for readability
     - Professional grid layout with 4 synchronized plots

5. **Save/Export Results**
   - Save complete cases for later analysis
   - Export plots as PNG, PDF, or SVG
   - Export data as CSV for external analysis

### Keyboard Shortcuts
- `Ctrl+N` - New case
- `Ctrl+O` - Open case
- `Ctrl+S` - Save case
- `Ctrl+Shift+S` - Save case as
- `F5` - Run simulation
- `Ctrl+Q` - Exit application

### File Formats
- **Case files**: JSON format with all parameters and results
- **Plot exports**: PNG, PDF, SVG formats supported
- **Data exports**: CSV format for spreadsheet analysis

## Configuration

The application uses JSON configuration files in the `config/` directory:

### `default_config.json`
```json
{
  "simulation": {
    "default_total_time": 100.0,
    "default_conveyor_length": 100.0,
    "default_resolution_size": 1.0,
    "default_conveyor_velocity": 2.0
  },
  "ui": {
    "window_width": 1400,
    "window_height": 800,
    "theme": "default"
  },
  "materials": {
    "default_materials": [
      "Steel", "Aluminum", "Concrete", "Sand", "Gravel", "Coal"
    ]
  }
}
```

## Development

### Setting up Development Environment
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Lint code
flake8 src/
```

### Architecture Overview

The application follows a modular Model-View-Controller (MVC) pattern:

- **Models** (`src/models/`): Data structures and business logic
- **Simulation** (`src/simulation/`): Core simulation algorithms
- **UI** (`src/ui/`): User interface components (Views)
- **Utils** (`src/utils/`): Utility functions and helpers

### Key Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Loose Coupling**: Modules interact through well-defined interfaces  
3. **High Cohesion**: Related functionality is grouped together
4. **Testability**: All components can be tested independently
5. **Extensibility**: New features can be added without modifying existing code

### Adding New Features

To add new features:

1. **New Material Models**: Add to `src/models/material.py`
2. **Simulation Algorithms**: Extend `src/simulation/engine.py`
3. **UI Components**: Add widgets to `src/ui/widgets/`
4. **Plot Types**: Extend `src/visualization/plotter.py`

## Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/

# Run specific test file
pytest tests/test_models.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes following the coding standards
4. Add tests for new functionality
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Coding Standards
- Use Black for code formatting
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write docstrings for public methods
- Maintain test coverage above 80%

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v1.0.0 (Current)
- Complete modular rewrite of original application
- Enhanced UI with improved table editing
- Threaded simulation execution
- Comprehensive error handling and validation
- Save/load functionality with JSON format
- Export capabilities for plots and data
- Configuration management system

### Previous Version (v0.5)
- Original single-file implementation
- Basic simulation functionality
- Simple matplotlib integration
- Limited error handling

## Support

For questions, bug reports, or feature requests:
- Open an issue on GitHub
- Contact: robertoabreu.alencar@hotmail.com

## Acknowledgments

- Original simulation algorithms developed for industrial conveyor systems
- PyQt5 community for excellent GUI framework
- matplotlib developers for plotting capabilities
