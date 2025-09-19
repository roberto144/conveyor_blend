from dataclasses import dataclass
from typing import Optional

@dataclass
class Material:
    """Represents a material with its properties"""
    name: str
    density: float
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.density <= 0:
            raise ValueError("Density must be positive")
        if not self.name.strip():
            raise ValueError("Material name cannot be empty")