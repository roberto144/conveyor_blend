from dataclasses import dataclass
from typing import Optional

@dataclass
class Material:
    """
    Represents a material with its physical and descriptive properties.
    
    This class encapsulates the properties of a material used in the conveyor
    system, including its name, density, and optional description.
    
    Attributes:
        name (str): The unique identifier/name of the material.
        density (float): The material's density in kg/m³. Must be positive.
        description (Optional[str]): Optional description of the material.
            Defaults to None.
            
    Raises:
        ValueError: If density is not positive or name is empty/whitespace.
        
    Example:
        >>> iron_ore = Material("Iron Ore", 5200, "High-grade iron ore")
        >>> print(iron_ore.density)
        5200
    """
    name: str
    density: float
    description: Optional[str] = None
    
    def __post_init__(self):
        """
        Validates the material's properties after initialization.
        
        Raises:
            ValueError: If density is not positive or name is empty.
        """
        if self.density <= 0:
            raise ValueError("Density must be positive")
        if not self.name.strip():
            raise ValueError("Material name cannot be empty")