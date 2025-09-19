class ConveyorModelError(Exception):
    """Base exception for conveyor model"""
    pass

class ValidationError(ConveyorModelError):
    """Raised when input validation fails"""
    pass

class SimulationError(ConveyorModelError):
    """Raised when simulation fails"""
    pass

class FileHandlingError(ConveyorModelError):
    """Raised when file operations fail"""
    pass