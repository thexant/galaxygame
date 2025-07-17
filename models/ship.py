"""
galaxy_core/models/ship.py
Ship model representing spacecraft in the game
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from .base import BaseModel
from .character import InventoryItem

class ShipType(Enum):
    """Types of ships available"""
    SHUTTLE = "shuttle"
    FIGHTER = "fighter"
    FREIGHTER = "freighter"
    EXPLORER = "explorer"
    CORVETTE = "corvette"
    CRUISER = "cruiser"
    CARRIER = "carrier"
    SPECIAL = "special"

class ShipUpgradeType(Enum):
    """Types of ship upgrades"""
    ENGINE = "engine"
    SHIELD = "shield"
    WEAPON = "weapon"
    CARGO = "cargo"
    FUEL = "fuel"
    HULL = "hull"
    SCANNER = "scanner"
    SPECIAL = "special"

@dataclass
class ShipUpgrade:
    """Ship upgrade/modification"""
    upgrade_id: str
    name: str
    upgrade_type: ShipUpgradeType
    level: int = 1
    bonus_value: float = 0.0
    description: str = ""
    power_requirement: int = 0
    mass: float = 0.0

@dataclass
class ShipStats:
    """Ship statistics and capabilities"""
    # Movement
    max_speed: int = 100
    acceleration: int = 50
    maneuverability: int = 50
    
    # Combat
    shield_strength: int = 0
    weapon_power: int = 10
    targeting_accuracy: int = 70
    
    # Utility
    scanner_range: int = 100
    stealth_rating: int = 0
    power_generation: int = 100


class Ship(BaseModel):
    """Represents a ship in the game"""
    
    def __init__(self,
                 ship_id: Optional[int] = None,
                 owner_id: int = 0,
                 name: str = "Unnamed Ship",
                 ship_type: ShipType = ShipType.SHUTTLE):
        
        super().__init__(ship_id)
        
        # Basic properties
        self.owner_id = owner_id
        self.name = name
        self.ship_type = ship_type
        
        # Initialize stats based on ship type
        self._initialize_ship_stats()
        
        # Hull and fuel
        self.hull_points = self.max_hull_points
        self.fuel = self.fuel_capacity
        
        # Cargo management
        self._cargo_bay: List[InventoryItem] = []
        
        # Upgrades
        self._upgrades: Dict[str, ShipUpgrade] = {}
        self.engine_level = 1
        self.shield_level = 0
        self.weapon_level = 1
        
        # Ship systems
        self.power_available = 100
        self.power_used = 0
        
        # Location and status
        self.docked_at_location: Optional[int] = None
        self.is_active = True
        self.interior_description: Optional[str] = None
        
        # Damage and wear
        self.damage_report: Dict[str, float] = {
            "hull": 0.0,
            "engine": 0.0,
            "weapons": 0.0,
            "shields": 0.0,
            "life_support": 0.0
        }
        
        # Track important fields
        self.track_field('hull_points')
        self.track_field('fuel')
        self.track_field('docked_at_location')
        self.track_field('is_active')
    
    def _initialize_ship_stats(self) -> None:
        """Initialize ship stats based on type"""
        ship_configs = {
            ShipType.SHUTTLE: {
                'cargo_capacity': 50,
                'fuel_capacity': 80,
                'max_hull_points': 50,
                'base_stats': ShipStats(max_speed=80, maneuverability=70)
            },
            ShipType.FIGHTER: {
                'cargo_capacity': 20,
                'fuel_capacity': 100,
                'max_hull_points': 80,
                'base_stats': ShipStats(max_speed=150, maneuverability=90, weapon_power=30)
            },
            ShipType.FREIGHTER: {
                'cargo_capacity': 200,
                'fuel_capacity': 150,
                'max_hull_points': 150,
                'base_stats': ShipStats(max_speed=60, maneuverability=30, shield_strength=20)
            },
            ShipType.EXPLORER: {
                'cargo_capacity': 100,
                'fuel_capacity': 200,
                'max_hull_points': 100,
                'base_stats': ShipStats(scanner_range=200, fuel_efficiency=1.5)
            },
            ShipType.CORVETTE: {
                'cargo_capacity': 80,
                'fuel_capacity': 120,
                'max_hull_points': 120,
                'base_stats': ShipStats(max_speed=120, weapon_power=25, shield_strength=15)
            },
            ShipType.CRUISER: {
                'cargo_capacity': 150,
                'fuel_capacity': 180,
                'max_hull_points': 200,
                'base_stats': ShipStats(weapon_power=40, shield_strength=30, power_generation=150)
            },
            ShipType.CARRIER: {
                'cargo_capacity': 300,
                'fuel_capacity': 250,
                'max_hull_points': 300,
                'base_stats': ShipStats(max_speed=40, shield_strength=50, power_generation=200)
            }
        }
        
        config = ship_configs.get(self.ship_type, ship_configs[ShipType.SHUTTLE])
        
        self.cargo_capacity = config['cargo_capacity']
        self.fuel_capacity = config['fuel_capacity']
        self.max_hull_points = config['max_hull_points']
        self.base_stats = config['base_stats']
        
        # Set initial interior description
        self._generate_interior_description()
    
    def _generate_interior_description(self) -> None:
        """Generate interior description based on ship type"""
        descriptions = {
            ShipType.SHUTTLE: "A cramped but functional shuttle interior with basic controls and minimal amenities.",
            ShipType.FIGHTER: "A tight cockpit filled with combat systems, targeting computers, and weapon controls.",
            ShipType.FREIGHTER: "A spacious cargo hold dominates the interior, with living quarters tucked into the corners.",
            ShipType.EXPLORER: "Advanced sensor arrays line the walls, with comfortable quarters for long journeys.",
            ShipType.CORVETTE: "A military-style bridge with multiple stations and reinforced bulkheads.",
            ShipType.CRUISER: "An impressive command center with tactical displays and crew stations.",
            ShipType.CARRIER: "A massive hangar bay with multiple decks and launch facilities."
        }
        
        self.interior_description = descriptions.get(self.ship_type, "A functional spacecraft interior.")
    
    def add_cargo(self, item: InventoryItem) -> bool:
        """Add item to cargo bay"""
        current_weight = self.get_cargo_weight()
        if current_weight + item.weight > self.cargo_capacity:
            return False
        
        # Try to stack with existing items
        for cargo_item in self._cargo_bay:
            if cargo_item.item_id == item.item_id:
                cargo_item.quantity += item.quantity
                self.publish_event("cargo_added", {
                    "item": item.name,
                    "quantity": item.quantity,
                    "total_weight": self.get_cargo_weight()
                })
                return True
        
        # Add as new item
        self._cargo_bay.append(item)
        self.publish_event("cargo_added", {
            "item": item.name,
            "quantity": item.quantity,
            "total_weight": self.get_cargo_weight()
        })
        return True
    
    def remove_cargo(self, item_id: str, quantity: int = 1) -> Optional[InventoryItem]:
        """Remove item from cargo bay"""
        for i, cargo_item in enumerate(self._cargo_bay):
            if cargo_item.item_id == item_id:
                if cargo_item.quantity > quantity:
                    cargo_item.quantity -= quantity
                    removed = InventoryItem(
                        item_id=item_id,
                        name=cargo_item.name,
                        quantity=quantity,
                        weight=cargo_item.weight,
                        value=cargo_item.value,
                        item_type=cargo_item.item_type
                    )
                    self.publish_event("cargo_removed", {
                        "item": cargo_item.name,
                        "quantity": quantity
                    })
                    return removed
                elif cargo_item.quantity == quantity:
                    removed = self._cargo_bay.pop(i)
                    self.publish_event("cargo_removed", {
                        "item": removed.name,
                        "quantity": quantity
                    })
                    return removed
        return None
    
    def get_cargo_weight(self) -> float:
        """Calculate total cargo weight"""
        return sum(item.weight * item.quantity for item in self._cargo_bay)
    
    def get_cargo_list(self) -> List[InventoryItem]:
        """Get list of cargo items"""
        return list(self._cargo_bay)
    
    def consume_fuel(self, amount: int) -> bool:
        """Consume fuel for operations"""
        if self.fuel < amount:
            return False
        
        self.fuel -= amount
        
        # Warning events
        fuel_percentage = self.fuel / self.fuel_capacity
        if fuel_percentage <= 0.1:
            self.publish_event("fuel_critical", {
                "fuel_remaining": self.fuel,
                "percentage": fuel_percentage * 100
            })
        elif fuel_percentage <= 0.25:
            self.publish_event("fuel_low", {
                "fuel_remaining": self.fuel,
                "percentage": fuel_percentage * 100
            })
        
        return True
    
    def refuel(self, amount: int) -> int:
        """Add fuel to ship"""
        old_fuel = self.fuel
        self.fuel = min(self.fuel_capacity, self.fuel + amount)
        actual_refueled = self.fuel - old_fuel
        
        if actual_refueled > 0:
            self.publish_event("ship_refueled", {
                "amount": actual_refueled,
                "fuel_level": self.fuel,
                "capacity": self.fuel_capacity
            })
        
        return actual_refueled
    
    def apply_damage(self, damage: int, damage_type: str = "general") -> int:
        """Apply damage to ship"""
        # Calculate actual damage after shields
        actual_damage = damage
        
        if self.shield_level > 0 and damage_type != "bypass":
            shield_absorption = min(damage, self.shield_level * 10)
            actual_damage = damage - shield_absorption
            
            if shield_absorption > 0:
                self.publish_event("shields_hit", {
                    "absorbed": shield_absorption,
                    "remaining_damage": actual_damage
                })
        
        # Apply damage to hull
        if actual_damage > 0:
            old_hull = self.hull_points
            self.hull_points = max(0, self.hull_points - actual_damage)
            
            # System damage based on hull percentage
            hull_percentage = self.hull_points / self.max_hull_points
            if hull_percentage < 0.5:
                self._apply_system_damage(damage_type)
            
            # Critical damage event
            if self.hull_points == 0:
                self.is_active = False
                self.publish_event("ship_destroyed", {
                    "final_damage": actual_damage,
                    "damage_type": damage_type
                })
            elif hull_percentage < 0.2:
                self.publish_event("hull_critical", {
                    "hull_remaining": self.hull_points,
                    "percentage": hull_percentage * 100
                })
        
        return actual_damage
    
    def _apply_system_damage(self, damage_type: str) -> None:
        """Apply damage to ship systems"""
        import random
        
        # Determine which system takes damage
        if damage_type == "general":
            system = random.choice(list(self.damage_report.keys()))
        elif damage_type in self.damage_report:
            system = damage_type
        else:
            system = "hull"
        
        # Increase system damage
        damage_amount = random.uniform(0.05, 0.15)
        self.damage_report[system] = min(1.0, self.damage_report[system] + damage_amount)
        
        if self.damage_report[system] > 0.5:
            self.publish_event("system_damaged", {
                "system": system,
                "damage_level": self.damage_report[system] * 100
            })
    
    def repair(self, amount: int, system: Optional[str] = None) -> int:
        """Repair ship hull or specific system"""
        if system and system in self.damage_report:
            # Repair specific system
            old_damage = self.damage_report[system]
            self.damage_report[system] = max(0, self.damage_report[system] - (amount / 100.0))
            repair_amount = old_damage - self.damage_report[system]
            
            self.publish_event("system_repaired", {
                "system": system,
                "repair_amount": repair_amount * 100,
                "remaining_damage": self.damage_report[system] * 100
            })
            
            return int(repair_amount * 100)
        else:
            # Repair hull
            old_hull = self.hull_points
            self.hull_points = min(self.max_hull_points, self.hull_points + amount)
            actual_repaired = self.hull_points - old_hull
            
            if actual_repaired > 0:
                # Also reduce system damage slightly
                for sys in self.damage_report:
                    self.damage_report[sys] = max(0, self.damage_report[sys] - 0.1)
                
                self.publish_event("ship_repaired", {
                    "amount": actual_repaired,
                    "hull_points": self.hull_points,
                    "max_hull": self.max_hull_points
                })
            
            return actual_repaired
    
    def add_upgrade(self, upgrade: ShipUpgrade) -> bool:
        """Add or replace an upgrade"""
        # Check power requirements
        if self.power_used + upgrade.power_requirement > self.power_available:
            return False
        
        # Remove old upgrade of same type if exists
        old_upgrade = None
        for up_id, up in self._upgrades.items():
            if up.upgrade_type == upgrade.upgrade_type:
                old_upgrade = up
                break
        
        if old_upgrade:
            self.remove_upgrade(old_upgrade.upgrade_id)
        
        # Add new upgrade
        self._upgrades[upgrade.upgrade_id] = upgrade
        self.power_used += upgrade.power_requirement
        
        # Update relevant stats
        if upgrade.upgrade_type == ShipUpgradeType.ENGINE:
            self.engine_level = max(self.engine_level, upgrade.level)
        elif upgrade.upgrade_type == ShipUpgradeType.SHIELD:
            self.shield_level = max(self.shield_level, upgrade.level)
        elif upgrade.upgrade_type == ShipUpgradeType.WEAPON:
            self.weapon_level = max(self.weapon_level, upgrade.level)
        elif upgrade.upgrade_type == ShipUpgradeType.CARGO:
            self.cargo_capacity += int(upgrade.bonus_value)
        elif upgrade.upgrade_type == ShipUpgradeType.FUEL:
            self.fuel_capacity += int(upgrade.bonus_value)
        
        self.publish_event("upgrade_installed", {
            "upgrade_name": upgrade.name,
            "upgrade_type": upgrade.upgrade_type.value,
            "level": upgrade.level
        })
        
        return True
    
    def remove_upgrade(self, upgrade_id: str) -> Optional[ShipUpgrade]:
        """Remove an upgrade"""
        if upgrade_id not in self._upgrades:
            return None
        
        upgrade = self._upgrades.pop(upgrade_id)
        self.power_used -= upgrade.power_requirement
        
        # Revert stat changes
        if upgrade.upgrade_type == ShipUpgradeType.CARGO:
            self.cargo_capacity -= int(upgrade.bonus_value)
        elif upgrade.upgrade_type == ShipUpgradeType.FUEL:
            self.fuel_capacity -= int(upgrade.bonus_value)
        
        # Recalculate levels
        self._recalculate_upgrade_levels()
        
        self.publish_event("upgrade_removed", {
            "upgrade_name": upgrade.name,
            "upgrade_type": upgrade.upgrade_type.value
        })
        
        return upgrade
    
    def _recalculate_upgrade_levels(self) -> None:
        """Recalculate upgrade levels after removal"""
        self.engine_level = 1
        self.shield_level = 0
        self.weapon_level = 1
        
        for upgrade in self._upgrades.values():
            if upgrade.upgrade_type == ShipUpgradeType.ENGINE:
                self.engine_level = max(self.engine_level, upgrade.level)
            elif upgrade.upgrade_type == ShipUpgradeType.SHIELD:
                self.shield_level = max(self.shield_level, upgrade.level)
            elif upgrade.upgrade_type == ShipUpgradeType.WEAPON:
                self.weapon_level = max(self.weapon_level, upgrade.level)
    
    def get_upgrades(self) -> List[ShipUpgrade]:
        """Get list of installed upgrades"""
        return list(self._upgrades.values())
    
    def calculate_fuel_efficiency(self) -> float:
        """Calculate fuel efficiency based on upgrades and damage"""
        base_efficiency = 1.0
        
        # Engine upgrades improve efficiency
        engine_bonus = self.engine_level * 0.1
        
        # Engine damage reduces efficiency
        engine_penalty = self.damage_report.get("engine", 0) * 0.5
        
        # Ship type modifier
        type_modifiers = {
            ShipType.SHUTTLE: 1.1,
            ShipType.FIGHTER: 0.9,
            ShipType.FREIGHTER: 0.8,
            ShipType.EXPLORER: 1.3,
            ShipType.CRUISER: 0.7,
            ShipType.CARRIER: 0.6
        }
        type_modifier = type_modifiers.get(self.ship_type, 1.0)
        
        efficiency = base_efficiency + engine_bonus - engine_penalty
        efficiency *= type_modifier
        
        return max(0.1, efficiency)  # Minimum 10% efficiency
    
    def calculate_combat_power(self) -> int:
        """Calculate total combat power"""
        base_power = self.base_stats.weapon_power
        
        # Weapon upgrades
        weapon_bonus = self.weapon_level * 10
        
        # Weapon damage penalty
        weapon_penalty = int(self.damage_report.get("weapons", 0) * base_power * 0.5)
        
        # Hull integrity affects accuracy
        hull_modifier = self.hull_points / self.max_hull_points
        
        total_power = int((base_power + weapon_bonus - weapon_penalty) * hull_modifier)
        
        return max(1, total_power)
    
    def dock_at(self, location_id: int) -> None:
        """Dock ship at a location"""
        old_location = self.docked_at_location
        self.docked_at_location = location_id
        
        self.publish_event("ship_docked", {
            "location_id": location_id,
            "previous_location": old_location
        })
    
    def undock(self) -> None:
        """Undock ship from current location"""
        if self.docked_at_location:
            old_location = self.docked_at_location
            self.docked_at_location = None
            
            self.publish_event("ship_undocked", {
                "from_location": old_location
            })
    
    def validate(self) -> bool:
        """Validate ship state"""
        if not self.name:
            return False
        
        if self.hull_points < 0 or self.hull_points > self.max_hull_points:
            return False
        
        if self.fuel < 0 or self.fuel > self.fuel_capacity:
            return False
        
        if self.cargo_capacity < 0:
            return False
        
        if self.power_used > self.power_available:
            return False
        
        if self.ship_type not in ShipType:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ship to dictionary"""
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'ship_type': self.ship_type.value,
            'cargo_capacity': self.cargo_capacity,
            'fuel_capacity': self.fuel_capacity,
            'hull_points': self.hull_points,
            'max_hull_points': self.max_hull_points,
            'fuel': self.fuel,
            'engine_level': self.engine_level,
            'shield_level': self.shield_level,
            'weapon_level': self.weapon_level,
            'interior_description': self.interior_description,
            'docked_at_location': self.docked_at_location,
            'is_active': self.is_active,
            'cargo_bay': [
                {
                    'item_id': item.item_id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'weight': item.weight,
                    'value': item.value,
                    'type': item.item_type
                } for item in self._cargo_bay
            ],
            'upgrades': [
                {
                    'upgrade_id': up.upgrade_id,
                    'name': up.name,
                    'type': up.upgrade_type.value,
                    'level': up.level,
                    'bonus_value': up.bonus_value,
                    'description': up.description,
                    'power_requirement': up.power_requirement,
                    'mass': up.mass
                } for up in self._upgrades.values()
            ],
            'damage_report': self.damage_report,
            'power_available': self.power_available,
            'power_used': self.power_used,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ship':
        """Create ship from dictionary"""
        ship = cls(
            ship_id=data.get('id'),
            owner_id=data.get('owner_id', 0),
            name=data.get('name', 'Unnamed Ship'),
            ship_type=ShipType(data.get('ship_type', 'shuttle'))
        )
        
        # Set properties
        ship.cargo_capacity = data.get('cargo_capacity', ship.cargo_capacity)
        ship.fuel_capacity = data.get('fuel_capacity', ship.fuel_capacity)
        ship.hull_points = data.get('hull_points', ship.hull_points)
        ship.max_hull_points = data.get('max_hull_points', ship.max_hull_points)
        ship.fuel = data.get('fuel', ship.fuel)
        ship.engine_level = data.get('engine_level', 1)
        ship.shield_level = data.get('shield_level', 0)
        ship.weapon_level = data.get('weapon_level', 1)
        ship.interior_description = data.get('interior_description')
        ship.docked_at_location = data.get('docked_at_location')
        ship.is_active = data.get('is_active', True)
        
        # Load cargo
        if 'cargo_bay' in data:
            for item_data in data['cargo_bay']:
                item = InventoryItem(
                    item_id=item_data['item_id'],
                    name=item_data['name'],
                    quantity=item_data.get('quantity', 1),
                    weight=item_data.get('weight', 1.0),
                    value=item_data.get('value', 0),
                    item_type=item_data.get('type', 'misc')
                )
                ship._cargo_bay.append(item)
        
        # Load upgrades
        if 'upgrades' in data:
            for up_data in data['upgrades']:
                upgrade = ShipUpgrade(
                    upgrade_id=up_data['upgrade_id'],
                    name=up_data['name'],
                    upgrade_type=ShipUpgradeType(up_data['type']),
                    level=up_data.get('level', 1),
                    bonus_value=up_data.get('bonus_value', 0.0),
                    description=up_data.get('description', ''),
                    power_requirement=up_data.get('power_requirement', 0),
                    mass=up_data.get('mass', 0.0)
                )
                ship._upgrades[upgrade.upgrade_id] = upgrade
        
        # Load damage report
        if 'damage_report' in data:
            ship.damage_report = data['damage_report']
        
        # Power systems
        ship.power_available = data.get('power_available', 100)
        ship.power_used = data.get('power_used', 0)
        
        return ship
    
    def __repr__(self) -> str:
        return f"<Ship {self.id}: {self.name} ({self.ship_type.value})>"