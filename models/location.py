"""
galaxy_core/models/location.py
Location model representing places in the galaxy
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from .base import BaseModel

class LocationType(Enum):
    """Types of locations in the galaxy"""
    COLONY = "colony"
    SPACE_STATION = "space_station"
    OUTPOST = "outpost"
    GATE = "gate"
    DERELICT = "derelict"
    HIDDEN = "hidden"

class Service(Enum):
    """Available services at locations"""
    JOBS = "jobs"
    SHOPS = "shops"
    MEDICAL = "medical"
    REPAIRS = "repairs"
    FUEL = "fuel"
    UPGRADES = "upgrades"
    BLACK_MARKET = "black_market"
    FEDERAL_SUPPLIES = "federal_supplies"
    SHIPYARD = "shipyard"
    BANK = "bank"
    COMMS = "comms"
    HOMES = "homes"

@dataclass
class Coordinates:
    """3D coordinates in space"""
    x: float
    y: float
    z: float = 0.0
    
    def distance_to(self, other: 'Coordinates') -> float:
        """Calculate euclidean distance to another coordinate"""
        return ((self.x - other.x) ** 2 + 
                (self.y - other.y) ** 2 + 
                (self.z - other.z) ** 2) ** 0.5


class Location(BaseModel):
    """Represents a location in the galaxy"""
    
    def __init__(self, 
                 location_id: Optional[int] = None,
                 name: str = "",
                 location_type: LocationType = LocationType.OUTPOST,
                 coordinates: Optional[Coordinates] = None,
                 wealth_level: int = 5,
                 population: int = 1000,
                 description: Optional[str] = None):
        
        super().__init__(location_id)
        
        # Basic properties
        self.name = name
        self.location_type = location_type
        self.coordinates = coordinates or Coordinates(0, 0, 0)
        self.wealth_level = wealth_level
        self.population = population
        self.description = description or f"A {location_type.value} in the galaxy"
        
        # Service availability
        self._services: Set[Service] = set()
        self._initialize_services()
        
        # Additional properties
        self.system_name: Optional[str] = None
        self.faction: str = "Independent"
        self.is_derelict: bool = False
        self.gate_status: str = "active"  # For gate locations
        self.establishment_date: Optional[str] = None
        
        # Economic factors
        self.base_price_modifier: float = 1.0
        self.supply_demand_factors: Dict[str, float] = {}
        
        # Track important fields for events
        self.track_field('wealth_level')
        self.track_field('population')
        self.track_field('is_derelict')
        self.track_field('gate_status')
    
    def _initialize_services(self) -> None:
        """Initialize available services based on location type and wealth"""
        # All locations have basic services
        if self.location_type != LocationType.DERELICT:
            self._services.add(Service.JOBS)
            self._services.add(Service.COMMS)
        
        # Wealth-based services
        if self.wealth_level >= 3:
            self._services.add(Service.SHOPS)
            self._services.add(Service.FUEL)
        
        if self.wealth_level >= 5:
            self._services.add(Service.MEDICAL)
            self._services.add(Service.REPAIRS)
        
        if self.wealth_level >= 7:
            self._services.add(Service.UPGRADES)
            self._services.add(Service.BANK)
        
        # Type-specific services
        if self.location_type == LocationType.COLONY:
            self._services.add(Service.HOMES)
            if self.wealth_level >= 6:
                self._services.add(Service.SHIPYARD)
        
        elif self.location_type == LocationType.SPACE_STATION:
            self._services.add(Service.REPAIRS)
            self._services.add(Service.FUEL)
            if self.wealth_level >= 8:
                self._services.add(Service.FEDERAL_SUPPLIES)
        
        elif self.location_type == LocationType.OUTPOST:
            if self.wealth_level <= 4:
                self._services.add(Service.BLACK_MARKET)
    
    def get_available_services(self) -> List[Service]:
        """Get list of available services at this location"""
        return list(self._services)
    
    def has_service(self, service: Service) -> bool:
        """Check if a specific service is available"""
        return service in self._services
    
    def add_service(self, service: Service) -> None:
        """Add a service to the location"""
        if service not in self._services:
            self._services.add(service)
            self.publish_event("service_added", {"service": service.value})
    
    def remove_service(self, service: Service) -> None:
        """Remove a service from the location"""
        if service in self._services:
            self._services.remove(service)
            self.publish_event("service_removed", {"service": service.value})
    
    def calculate_population(self) -> int:
        """Calculate population based on various factors"""
        base_population = self.population
        
        # Wealth modifier
        wealth_modifier = 1 + (self.wealth_level - 5) * 0.1
        
        # Type modifier
        type_modifiers = {
            LocationType.COLONY: 1.5,
            LocationType.SPACE_STATION: 1.2,
            LocationType.OUTPOST: 0.8,
            LocationType.GATE: 0.5,
            LocationType.DERELICT: 0.0,
            LocationType.HIDDEN: 0.3
        }
        type_modifier = type_modifiers.get(self.location_type, 1.0)
        
        # Service modifier (more services = more population)
        service_modifier = 1 + (len(self._services) * 0.05)
        
        # Calculate final population
        calculated_pop = int(base_population * wealth_modifier * type_modifier * service_modifier)
        
        # Derelict locations have no population
        if self.is_derelict:
            calculated_pop = 0
        
        return max(0, calculated_pop)
    
    def update_wealth(self, change: int) -> None:
        """Update wealth level with bounds checking"""
        old_wealth = self.wealth_level
        self.wealth_level = max(1, min(10, self.wealth_level + change))
        
        if old_wealth != self.wealth_level:
            # Reinitialize services based on new wealth
            self._services.clear()
            self._initialize_services()
            
            # Event is automatically published by tracked field
    
    def update_population(self, change: int) -> None:
        """Update population with bounds checking"""
        self.population = max(0, self.population + change)
        # Event is automatically published by tracked field
    
    def set_derelict(self, is_derelict: bool = True) -> None:
        """Mark location as derelict or restore it"""
        self.is_derelict = is_derelict
        
        if is_derelict:
            # Remove all services except basic comms
            services_to_remove = list(self._services)
            for service in services_to_remove:
                if service != Service.COMMS:
                    self.remove_service(service)
            
            # Set population to 0
            self.population = 0
            
            # Update description
            if "derelict" not in self.description.lower():
                self.description = f"Abandoned {self.description}"
        else:
            # Restore services based on type and wealth
            self._initialize_services()
    
    def get_price_modifier(self, item_category: str = "general") -> float:
        """Get price modifier for items at this location"""
        # Base modifier from location
        modifier = self.base_price_modifier
        
        # Wealth adjustment (poor locations have higher prices)
        wealth_adjustment = 1.0 + (5 - self.wealth_level) * 0.05
        modifier *= wealth_adjustment
        
        # Supply/demand for specific categories
        if item_category in self.supply_demand_factors:
            modifier *= self.supply_demand_factors[item_category]
        
        # Location type modifiers
        type_modifiers = {
            LocationType.COLONY: 0.95,  # Colonies have better prices
            LocationType.SPACE_STATION: 1.05,  # Stations slightly higher
            LocationType.OUTPOST: 1.1,  # Outposts more expensive
            LocationType.GATE: 1.15,  # Gates most expensive
            LocationType.DERELICT: 2.0,  # If anyone's selling here...
            LocationType.HIDDEN: 0.9  # Hidden locations have good deals
        }
        
        modifier *= type_modifiers.get(self.location_type, 1.0)
        
        return max(0.5, min(3.0, modifier))  # Clamp between 50% and 300%
    
    def validate(self) -> bool:
        """Validate location data"""
        if not self.name:
            return False
        
        if self.wealth_level < 1 or self.wealth_level > 10:
            return False
        
        if self.population < 0:
            return False
        
        if self.location_type not in LocationType:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert location to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.location_type.value,
            'coordinates': {
                'x': self.coordinates.x,
                'y': self.coordinates.y,
                'z': self.coordinates.z
            },
            'wealth_level': self.wealth_level,
            'population': self.population,
            'description': self.description,
            'services': [s.value for s in self._services],
            'system_name': self.system_name,
            'faction': self.faction,
            'is_derelict': self.is_derelict,
            'gate_status': self.gate_status,
            'establishment_date': self.establishment_date,
            'base_price_modifier': self.base_price_modifier,
            'supply_demand_factors': self.supply_demand_factors,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Location':
        """Create location from dictionary"""
        # Parse coordinates
        coord_data = data.get('coordinates', {})
        coordinates = Coordinates(
            x=coord_data.get('x', 0),
            y=coord_data.get('y', 0),
            z=coord_data.get('z', 0)
        )
        
        # Create location
        location = cls(
            location_id=data.get('id'),
            name=data['name'],
            location_type=LocationType(data['type']),
            coordinates=coordinates,
            wealth_level=data.get('wealth_level', 5),
            population=data.get('population', 1000),
            description=data.get('description')
        )
        
        # Set additional properties
        location.system_name = data.get('system_name')
        location.faction = data.get('faction', 'Independent')
        location.is_derelict = data.get('is_derelict', False)
        location.gate_status = data.get('gate_status', 'active')
        location.establishment_date = data.get('establishment_date')
        location.base_price_modifier = data.get('base_price_modifier', 1.0)
        location.supply_demand_factors = data.get('supply_demand_factors', {})
        
        # Set services
        if 'services' in data:
            location._services = {Service(s) for s in data['services']}
        
        return location
    
    def __repr__(self) -> str:
        return f"<Location {self.id}: {self.name} ({self.location_type.value})>"