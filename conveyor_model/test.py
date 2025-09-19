"""
Blast Furnace Stock House Conveyor Belt Simulation
Specialized for ferrous material flow modeling and optimization
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json

class FerrusMaterialType(Enum):
    """Blast furnace ferrous material types"""
    IRON_ORE_PELLETS = "iron_ore_pellets"
    IRON_ORE_SINTER = "iron_ore_sinter"
    IRON_ORE_LUMP = "iron_ore_lump"
    COKE = "coke"
    COAL = "coal"
    LIMESTONE = "limestone"
    DOLOMITE = "dolomite"
    QUARTZITE = "quartzite"
    # Mixed materials
    PELLET_SINTER_MIX = "pellet_sinter_mix"
    ORE_FLUX_MIX = "ore_flux_mix"

@dataclass
class BlastFurnaceMaterial:
    """Blast furnace specific material properties"""
    material_type: FerrusMaterialType
    name: str
    
    # Physical properties for volumetric calculations
    bulk_density: float  # kg/m³ (typical stockpile density)
    packed_density: float  # kg/m³ (compacted in bunkers)
    angle_of_repose: float  # degrees
    moisture_content: float = 0.0  # % moisture (affects flow and density)
    
    # Chemical composition (affects blast furnace performance)
    fe_content: float = 0.0  # % Iron content
    sio2_content: float = 0.0  # % Silica
    al2o3_content: float = 0.0  # % Alumina
    cao_content: float = 0.0  # % Lime
    mgo_content: float = 0.0  # % Magnesia
    s_content: float = 0.0  # % Sulfur
    p_content: float = 0.0  # % Phosphorus
    
    # Blast furnace specific properties
    reducibility_index: float = 0.0  # RDI (reduction degradation index)
    tumbler_index: float = 0.0  # TI (mechanical strength)
    abrasion_index: float = 0.0  # AI (abrasion resistance)
    porosity: float = 0.0  # % porosity
    
    # Flow characteristics
    flowability_coefficient: float = 0.8  # Material flow coefficient (0-1)
    segregation_tendency: float = 0.0  # Tendency to segregate during transport (0-1)
    degradation_rate: float = 0.0  # Material breakdown during handling (% per transfer)
    
    # Size distribution
    size_distribution: Dict[str, float] = field(default_factory=dict)  # mm -> %
    
    @property
    def basicity_index_B2(self) -> float:
        """Calculate basicity index (CaO)/(SiO2)"""
        acid_oxides = self.sio2_content
        basic_oxides = self.cao_content
        return basic_oxides / acid_oxides if acid_oxides > 0 else 0.0
    
    @property
    def effective_bulk_density(self) -> float:
        """Calculate effective bulk density considering moisture"""
        moisture_factor = 1 + (self.moisture_content / 100) * 0.15
        return self.bulk_density * moisture_factor
    
    def calculate_compaction_factor(self, loading_pressure: float) -> float:
        """Calculate compaction factor based on material properties and pressure"""
        # Empirical relationship for iron ore materials
        if self.material_type in [FerrusMaterialType.IRON_ORE_PELLETS]:
            base_compaction = 0.1  # Pellets resist compaction
        elif self.material_type in [FerrusMaterialType.COKE, FerrusMaterialType.COAL]:
            base_compaction = 0.3  # Carbonaceous materials compress more
        else:
            base_compaction = 0.2  # Default for ores and fluxes
        
        pressure_factor = min(loading_pressure / 100.0, 1.0)  # Normalize to 100 kPa
        return base_compaction * pressure_factor
    
    def calculate_flow_rate_factor(self, particle_size_mm: float, 
                                  outlet_diameter_mm: float) -> float:
        """Calculate flow rate modification factor based on Jenike theory"""
        # Critical diameter ratio for flow
        critical_ratio = max(5.0, 20.0 - self.flowability_coefficient * 10)
        diameter_ratio = outlet_diameter_mm / particle_size_mm
        
        if diameter_ratio < critical_ratio:
            return 0.1  # Poor flow
        else:
            flow_factor = min(1.0, (diameter_ratio - critical_ratio) / critical_ratio)
            return 0.1 + 0.9 * flow_factor

# Material database for blast furnace materials
BLAST_FURNACE_MATERIALS = {
    "iron_ore_pellets": BlastFurnaceMaterial(
        material_type=FerrusMaterialType.IRON_ORE_PELLETS,
        name="Iron Ore Pellets",
        bulk_density=2200.0,  # kg/m³
        packed_density=2400.0,
        angle_of_repose=28.0,
        fe_content=65.0,
        sio2_content=4.5,
        al2o3_content=0.8,
        cao_content=0.5,
        reducibility_index=45.0,
        tumbler_index=95.0,
        flowability_coefficient=0.85,
        segregation_tendency=0.1,
        size_distribution={"9-16": 85.0, "6.3-9": 10.0, "<6.3": 5.0}
    ),
    
    "iron_ore_sinter": BlastFurnaceMaterial(
        material_type=FerrusMaterialType.IRON_ORE_SINTER,
        name="Iron Ore Sinter",
        bulk_density=1900.0,
        packed_density=2100.0,
        angle_of_repose=35.0,
        fe_content=57.0,
        sio2_content=9.8,
        al2o3_content=1.8,
        cao_content=9.5,
        mgo_content=1.2,
        reducibility_index=65.0,
        tumbler_index=65.0,
        flowability_coefficient=0.75,
        segregation_tendency=0.3,
        degradation_rate=0.5,
        size_distribution={"10-40": 70.0, "5-10": 20.0, "<5": 10.0}
    ),
    
    "coke": BlastFurnaceMaterial(
        material_type=FerrusMaterialType.COKE,
        name="Metallurgical Coke",
        bulk_density=500.0,
        packed_density=650.0,
        angle_of_repose=40.0,
        fe_content=0.0,
        sio2_content=5.5,
        al2o3_content=2.8,
        s_content=0.65,
        porosity=48.0,
        flowability_coefficient=0.9,
        segregation_tendency=0.4,
        degradation_rate=1.0,
        size_distribution={"25-80": 85.0, "15-25": 10.0, "<15": 5.0}
    ),
    
    "limestone": BlastFurnaceMaterial(
        material_type=FerrusMaterialType.LIMESTONE,
        name="Limestone Flux",
        bulk_density=1600.0,
        packed_density=1750.0,
        angle_of_repose=32.0,
        cao_content=52.0,
        mgo_content=2.5,
        sio2_content=2.0,
        al2o3_content=0.8,
        flowability_coefficient=0.8,
        segregation_tendency=0.2,
        size_distribution={"10-30": 80.0, "5-10": 15.0, "<5": 5.0}
    )
}

@dataclass
class StockHouseBunker:
    """Stock house bunker (destination silo) for blast furnace materials"""
    bunker_id: str
    material_designation: FerrusMaterialType
    
    # Geometric properties
    capacity_volume: float  # m³ total geometric capacity
    usable_volume: float   # m³ usable capacity (accounting for discharge cone, etc.)
    cross_sectional_area: float  # m² at widest point
    outlet_diameter: float  # m discharge outlet diameter
    height: float  # m total height
    
    # Current state
    current_volume: float = 0.0  # m³ currently stored
    current_mass: float = 0.0    # kg currently stored
    material_composition: Dict[str, float] = field(default_factory=dict)  # material -> volume
    
    # Operational parameters
    max_fill_rate: float = 2.0  # m³/s maximum filling rate
    target_fill_level: float = 0.85  # Target fill level (85% of usable capacity)
    min_operating_level: float = 0.15  # Minimum level for continuous operation
    
    # Quality tracking
    average_fe_content: float = 0.0
    average_basicity: float = 0.0
    last_quality_update: float = 0.0
    
    # Charging sequence info (for blast furnace charging)
    charging_sequence_position: int = 0  # Position in BF charging sequence
    target_charge_weight: float = 0.0  # kg per charge to blast furnace
    
    @property
    def fill_percentage(self) -> float:
        """Current fill percentage"""
        return (self.current_volume / self.usable_volume) * 100.0
    
    @property
    def available_volume(self) -> float:
        """Available volume for additional material"""
        return max(0.0, self.usable_volume - self.current_volume)
    
    @property
    def is_ready_for_charging(self) -> bool:
        """Check if bunker has sufficient material for blast furnace charging"""
        return self.fill_percentage >= self.min_operating_level * 100
    
    @property
    def needs_filling(self) -> bool:
        """Check if bunker needs to be filled"""
        return self.fill_percentage < self.target_fill_level * 100
    
    def calculate_discharge_flow_rate(self, material_props: BlastFurnaceMaterial) -> float:
        """Calculate maximum discharge flow rate based on material and bunker properties"""
        # Orifice flow calculation for granular materials
        g = 9.81  # m/s²
        
        # Effective outlet diameter considering material flow properties
        effective_diameter = self.outlet_diameter * material_props.flowability_coefficient
        
        # Beverloo equation for granular flow
        flow_coefficient = 0.58  # Typical for well-designed outlets
        particle_size = 0.015  # m (assumed average particle size)
        
        # Volumetric flow rate
        volumetric_flow = (flow_coefficient * 
                          (effective_diameter - 1.4 * particle_size) ** 2.5 * 
                          np.sqrt(g * material_props.effective_bulk_density))
        
        # Convert to m³/s and apply material-specific corrections
        flow_rate = volumetric_flow / material_props.effective_bulk_density
        
        # Apply degradation and caking factors
        if material_props.moisture_content > 5.0:
            flow_rate *= 0.8  # Reduce flow for high moisture
        
        return min(flow_rate, self.max_fill_rate)  # Don't exceed design limit
    
    def add_material(self, material_name: str, volume: float, 
                    material_props: BlastFurnaceMaterial):
        """Add material to bunker and update composition"""
        if volume <= 0 or volume > self.available_volume:
            return False
            
        # Update volumes
        if material_name not in self.material_composition:
            self.material_composition[material_name] = 0.0
        
        self.material_composition[material_name] += volume
        self.current_volume += volume
        
        # Update mass
        mass_added = volume * material_props.effective_bulk_density
        self.current_mass += mass_added
        
        # Update quality parameters (weighted average)
        if self.current_mass > 0:
            weight_factor = mass_added / self.current_mass
            self.average_fe_content = (self.average_fe_content * (1 - weight_factor) + 
                                     material_props.fe_content * weight_factor)
            self.average_basicity = (self.average_basicity * (1 - weight_factor) + 
                                   material_props.basicity_index * weight_factor)
        
        return True
    
    def calculate_charging_readiness_score(self) -> float:
        """Calculate readiness score for blast furnace charging (0-1)"""
        # Fill level component
        fill_score = min(self.fill_percentage / 85.0, 1.0)  # Target 85% fill
        
        # Quality consistency component (simplified)
        quality_score = 1.0  # Would be based on Fe content variability, etc.
        
        # Material age component (fresher material is better)
        age_score = 1.0  # Would be based on residence time
        
        # Weighted score
        readiness = 0.5 * fill_score + 0.3 * quality_score + 0.2 * age_score
        return readiness

@dataclass
class StockHouseConveyor:
    """Main ferrous conveyor belt in blast furnace stock house"""
    conveyor_id: str
    
    # Physical parameters
    length: float  # m
    width: float   # m
    velocity: float  # m/s
    inclination_angle: float = 0.0  # degrees from horizontal
    
    # Capacity parameters
    max_material_height: float = 0.3  # m maximum material pile height
    design_capacity: float = 1000.0   # t/h design capacity
    
    # Belt properties
    belt_type: str = "steel_cord"  # steel_cord, fabric, etc.
    pulley_diameter: float = 1.6   # m drive pulley diameter
    belt_tension: float = 200.0    # kN belt tension
    
    # Operational state
    current_speed: float = None    # m/s current operating speed
    is_running: bool = True
    total_operating_hours: float = 0.0
    
    # Material distribution along belt
    position_resolution: float = 1.0  # m resolution for material tracking
    material_distribution: Dict[int, Dict[str, float]] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.current_speed is None:
            self.current_speed = self.velocity
        
        # Initialize position tracking
        self.n_positions = int(self.length / self.position_resolution) + 1
        self.positions = np.linspace(0, self.length, self.n_positions)
    
    @property
    def cross_sectional_area(self) -> float:
        """Calculate cross-sectional area of material on belt"""
        # Trapezoidal cross-section approximation
        base_width = self.width * 0.9  # Effective width (accounting for belt edges)
        return base_width * self.max_material_height / 2  # Triangular approximation
    
    @property
    def volumetric_capacity_per_position(self) -> float:
        """Volume capacity per position segment"""
        return self.cross_sectional_area * self.position_resolution
    
    @property
    def theoretical_capacity_tph(self) -> float:
        """Calculate theoretical capacity in tonnes per hour"""
        volume_per_second = self.cross_sectional_area * self.current_speed
        # Assume average bulk density of 1800 kg/m³ for mixed ferrous materials
        mass_per_second = volume_per_second * 1800
        return mass_per_second * 3600 / 1000  # Convert to t/h
    
    def calculate_power_requirement(self, total_material_mass: float) -> float:
        """Calculate power requirement in kW"""
        # Simplified power calculation
        # P = (belt resistance + material lifting + acceleration) forces × velocity
        
        # Empty belt power
        empty_belt_power = 0.5 * self.length * self.width * self.current_speed  # kW approximation
        
        # Material lifting power (if inclined)
        if self.inclination_angle > 0:
            lifting_power = (total_material_mass * 9.81 * 
                           np.sin(np.radians(self.inclination_angle)) * 
                           self.current_speed / 1000)  # kW
        else:
            lifting_power = 0.0
        
        # Material acceleration power
        acceleration_power = total_material_mass * self.current_speed**2 / 2000  # kW approximation
        
        return empty_belt_power + lifting_power + acceleration_power
    
    def check_belt_loading(self) -> Dict[str, float]:
        """Check belt loading conditions and return status"""
        total_volume = sum(
            sum(materials.values()) 
            for materials in self.material_distribution.values()
        )
        
        max_volume = self.n_positions * self.volumetric_capacity_per_position
        loading_percentage = (total_volume / max_volume) * 100 if max_volume > 0 else 0
        
        # Calculate load distribution evenness
        position_loads = [
            sum(materials.values()) / self.volumetric_capacity_per_position * 100
            for materials in self.material_distribution.values()
        ]
        load_std = np.std(position_loads) if position_loads else 0
        
        return {
            "total_loading_percentage": loading_percentage,
            "load_distribution_std": load_std,
            "overloaded_positions": sum(1 for load in position_loads if load > 90),
            "max_position_load": max(position_loads) if position_loads else 0
        }

class BlastFurnaceConveyorSimulation:
    """Main simulation engine for blast furnace stock house conveyors"""
    
    def __init__(self):
        self.conveyors: List[StockHouseConveyor] = []
        self.bunkers: List[StockHouseBunker] = []
        self.materials_db = BLAST_FURNACE_MATERIALS
        
        # Simulation parameters
        self.time_step = 1.0  # seconds
        self.current_time = 0.0
        self.total_simulation_time = 3600.0  # 1 hour default
        
        # Results tracking
        self.results = {
            "time_series": [],
            "bunker_levels": [],
            "conveyor_loads": [],
            "material_quality": [],
            "power_consumption": [],
            "charging_readiness": [],
            "mass_balance": []
        }
    
    def add_conveyor(self, conveyor: StockHouseConveyor):
        """Add conveyor to simulation"""
        self.conveyors.append(conveyor)
    
    def add_bunker(self, bunker: StockHouseBunker):
        """Add bunker to simulation"""
        self.bunkers.append(bunker)
    
    def run_simulation(self, total_time: float = 3600.0):
        """Run the blast furnace stock house simulation"""
        self.total_simulation_time = total_time
        self.current_time = 0.0
        
        while self.current_time < self.total_simulation_time:
            # Update material transport on all conveyors
            self._update_conveyor_transport()
            
            # Process material transfer to bunkers
            self._process_bunker_filling()
            
            # Update bunker states and quality
            self._update_bunker_quality()
            
            # Check charging readiness
            self._evaluate_charging_readiness()
            
            # Record results
            self._record_timestep_results()
            
            # Advance time
            self.current_time += self.time_step
        
        return self._generate_final_results()
    
    def _update_conveyor_transport(self):
        """Update material movement on conveyors"""
        for conveyor in self.conveyors:
            if not conveyor.is_running:
                continue
                
            # Transport materials along belt
            new_distribution = {}
            distance_per_timestep = conveyor.current_speed * self.time_step
            
            for pos_index, materials in conveyor.material_distribution.items():
                current_position = conveyor.positions[pos_index]
                new_position = current_position + distance_per_timestep
                
                if new_position >= conveyor.length:
                    # Material reaches end - transfer to bunkers
                    self._queue_for_bunker_transfer(materials, conveyor)
                else:
                    # Material continues on belt
                    new_pos_index = int(new_position / conveyor.position_resolution)
                    if new_pos_index not in new_distribution:
                        new_distribution[new_pos_index] = {}
                    
                    for material, volume in materials.items():
                        if material not in new_distribution[new_pos_index]:
                            new_distribution[new_pos_index][material] = 0.0
                        new_distribution[new_pos_index][material] += volume
            
            conveyor.material_distribution = new_distribution
    
    def _queue_for_bunker_transfer(self, materials: Dict[str, float], 
                                   conveyor: StockHouseConveyor):
        """Queue materials for transfer to appropriate bunkers"""
        for material_name, volume in materials.items():
            if material_name in self.materials_db:
                material_props = self.materials_db[material_name]
                target_bunker = self._find_target_bunker(material_props.material_type)
                
                if target_bunker and target_bunker.available_volume >= volume:
                    target_bunker.add_material(material_name, volume, material_props)
    
    def _find_target_bunker(self, material_type: FerrusMaterialType) -> Optional[StockHouseBunker]:
        """Find appropriate bunker for material type"""
        compatible_bunkers = [
            bunker for bunker in self.bunkers 
            if bunker.material_designation == material_type and bunker.needs_filling
        ]
        
        if not compatible_bunkers:
            return None
        
        # Choose bunker with lowest fill level
        return min(compatible_bunkers, key=lambda b: b.fill_percentage)
    
    def _update_bunker_quality(self):
        """Update quality parameters for all bunkers"""
        for bunker in self.bunkers:
            bunker.last_quality_update = self.current_time
            # Quality updates would be based on material composition
    
    def _evaluate_charging_readiness(self):
        """Evaluate blast furnace charging readiness"""
        charging_scores = {}
        for bunker in self.bunkers:
            charging_scores[bunker.bunker_id] = bunker.calculate_charging_readiness_score()
    
    def _record_timestep_results(self):
        """Record simulation results for current timestep"""
        self.results["time_series"].append(self.current_time)
        
        # Bunker levels
        bunker_data = {}
        for bunker in self.bunkers:
            bunker_data[bunker.bunker_id] = {
                "fill_percentage": bunker.fill_percentage,
                "current_mass": bunker.current_mass,
                "fe_content": bunker.average_fe_content,
                "charging_ready": bunker.is_ready_for_charging
            }
        self.results["bunker_levels"].append(bunker_data)
        
        # Conveyor loads
        conveyor_data = {}
        for conveyor in self.conveyors:
            loading_status = conveyor.check_belt_loading()
            conveyor_data[conveyor.conveyor_id] = loading_status
        self.results["conveyor_loads"].append(conveyor_data)
    
    def _generate_final_results(self):
        """Generate final simulation results"""
        return {
            "simulation_summary": {
                "total_time": self.total_simulation_time,
                "time_step": self.time_step,
                "n_conveyors": len(self.conveyors),
                "n_bunkers": len(self.bunkers)
            },
            "results": self.results,
            "final_state": {
                "bunker_states": [
                    {
                        "id": b.bunker_id,
                        "fill_level": b.fill_percentage,
                        "material_mass": b.current_mass,
                        "charging_ready": b.is_ready_for_charging
                    }
                    for b in self.bunkers
                ],
                "conveyor_states": [
                    {
                        "id": c.conveyor_id,
                        "loading": c.check_belt_loading()["total_loading_percentage"],
                        "power_kw": c.calculate_power_requirement(1000)  # Assume 1000 kg total
                    }
                    for c in self.conveyors
                ]
            }
        }

# Example usage for blast furnace stock house
def create_blast_furnace_example():
    """Create example blast furnace stock house configuration"""
    
    # Create simulation
    sim = BlastFurnaceConveyorSimulation()
    
    # Main ferrous conveyor
    main_conveyor = StockHouseConveyor(
        conveyor_id="MAIN_FERROUS_001",
        length=150.0,  # 150m long
        width=2.0,     # 2m wide
        velocity=2.5,  # 2.5 m/s
        inclination_angle=12.0,  # 12° incline to bunkers
        max_material_height=0.4,  # 40cm max pile height
        design_capacity=1500.0   # 1500 t/h design capacity
    )
    sim.add_conveyor(main_conveyor)
    
    # Iron ore pellet bunkers
    for i in range(4):  # 4 pellet bunkers
        bunker = StockHouseBunker(
            bunker_id=f"PELLET_BUNKER_{i+1:02d}",
            material_designation=FerrusMaterialType.IRON_ORE_PELLETS,
            capacity_volume=200.0,  # 200 m³
            usable_volume=170.0,    # 170 m³ usable
            cross_sectional_area=25.0,  # 25 m²
            outlet_diameter=1.2,    # 1.2m outlet
            height=12.0,           # 12m height
            max_fill_rate=3.0,     # 3 m³/s fill rate
            charging_sequence_position=i+1
        )
        sim.add_bunker(bunker)
    
    # Sinter bunkers
    for i in range(3):  # 3 sinter bunkers
        bunker = StockHouseBunker(
            bunker_id=f"SINTER_BUNKER_{i+1:02d}",
            material_designation=FerrusMaterialType.IRON_ORE_SINTER,
            capacity_volume=180.0,
            usable_volume=150.0,
            cross_sectional_area=22.0,
            outlet_diameter=1.0,
            height=10.0,
            max_fill_rate=2.5,
            charging_sequence_position=i+5  # After pellets
        )
        sim.add_bunker(bunker)
    
    # Coke bunkers
    for i in range(2):  # 2 coke bunkers
        bunker = StockHouseBunker(
            bunker_id=f"COKE_BUNKER_{i+1:02d}",
            material_designation=FerrusMaterialType.COKE,
            capacity_volume=250.0,  # Larger volume due to lower density
            usable_volume=220.0,
            cross_sectional_area=30.0,
            outlet_diameter=1.5,    # Larger outlet for coke
            height=15.0,
            max_fill_rate=4.0,
            charging_sequence_position=i+8  # After iron ore materials
        )
        sim.add_bunker(bunker)
    
    return sim

if __name__ == "__main__":
    # Demonstrate blast furnace stock house simulation
    simulation = create_blast_furnace_example()
    print("Blast Furnace Stock House Simulation Created")
    print(f"Conveyors: {len(simulation.conveyors)}")
    print(f"Bunkers: {len(simulation.bunkers)}")
    
    # Show material properties
    print("\nMaterial Properties:")
    for name, material in BLAST_FURNACE_MATERIALS.items():
        print(f"{material.name}: {material.bulk_density} kg/m³, Fe: {material.fe_content}%")