"""
galaxy_core/models/character.py
Character model representing players and their state
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from .base import BaseModel

class Alignment(Enum):
    """Character alignment types"""
    LOYAL = "loyal"
    NEUTRAL = "neutral"
    BANDIT = "bandit"

class LocationStatus(Enum):
    """Character's status at their location"""
    DOCKED = "docked"
    TRAVELING = "traveling"
    IN_COMBAT = "in_combat"
    IN_SHIP = "in_ship"
    EXPLORING = "exploring"

@dataclass
class CharacterStats:
    """Character statistics"""
    strength: int = 10
    agility: int = 10
    intelligence: int = 10
    charisma: int = 10
    endurance: int = 10
    
    def get_modifier(self, stat_name: str) -> int:
        """Get modifier for a stat (D&D style)"""
        stat_value = getattr(self, stat_name, 10)
        return (stat_value - 10) // 2

@dataclass
class InventoryItem:
    """Item in character inventory"""
    item_id: str
    name: str
    quantity: int = 1
    weight: float = 1.0
    value: int = 0
    item_type: str = "misc"
    metadata: Dict[str, Any] = field(default_factory=dict)


class Character(BaseModel):
    """Represents a player character in the game"""
    
    def __init__(self,
                 character_id: Optional[int] = None,
                 player_ref: str = "",
                 name: str = "",
                 current_location: Optional[int] = None,
                 credits: int = 1000):
        
        super().__init__(character_id)
        
        # Basic properties
        self.player_ref = player_ref  # Reference to player (abstract, not Discord)
        self.name = name
        self.current_location = current_location
        self.credits = credits
        
        # Ship-related stats
        self.ship_fuel = 50
        self.ship_hull = 100
        self.max_ship_hull = 100
        self.current_ship_id: Optional[int] = None
        
        # Character stats
        self.stats = CharacterStats()
        self.karma = 0
        self.wanted_level = 0
        self.alignment = Alignment.NEUTRAL
        
        # Status
        self.location_status = LocationStatus.DOCKED
        self.is_alive = True
        self.death_count = 0
        self.last_death_time: Optional[datetime] = None
        
        # Inventory
        self._inventory: List[InventoryItem] = []
        self.max_inventory_weight = 100.0
        
        # Experience and skills
        self.experience = 0
        self.level = 1
        self.skills: Dict[str, int] = {
            "piloting": 1,
            "combat": 1,
            "trading": 1,
            "engineering": 1,
            "diplomacy": 1
        }
        
        # Track important fields
        self.track_field('current_location')
        self.track_field('credits')
        self.track_field('is_alive')
        self.track_field('karma')
        self.track_field('alignment')
        self.track_field('wanted_level')
    
    def move_to(self, location_id: int, travel_time: Optional[int] = None) -> bool:
        """Move character to a new location"""
        if not self.is_alive:
            return False
        
        old_location = self.current_location
        self.current_location = location_id
        
        # Publish movement event (field tracking handles basic event)
        self.publish_event("character_moved", {
            "from_location": old_location,
            "to_location": location_id,
            "travel_time": travel_time
        })
        
        return True
    
    def add_credits(self, amount: int) -> bool:
        """Add credits to character (can be negative for spending)"""
        if amount < 0 and self.credits + amount < 0:
            return False  # Not enough credits
        
        self.credits += amount
        
        # Additional event for significant transactions
        if abs(amount) > 1000:
            self.publish_event("major_transaction", {
                "amount": amount,
                "new_balance": self.credits
            })
        
        return True
    
    def take_damage(self, damage: int, source: Optional[str] = None) -> bool:
        """Apply damage to character"""
        if not self.is_alive:
            return False
        
        self.ship_hull = max(0, self.ship_hull - damage)
        
        self.publish_event("damage_taken", {
            "damage": damage,
            "remaining_hull": self.ship_hull,
            "source": source
        })
        
        if self.ship_hull <= 0:
            self._handle_death(source)
        
        return True
    
    def heal(self, amount: int) -> int:
        """Heal character's ship hull"""
        if not self.is_alive:
            return 0
        
        old_hull = self.ship_hull
        self.ship_hull = min(self.max_ship_hull, self.ship_hull + amount)
        actual_healed = self.ship_hull - old_hull
        
        if actual_healed > 0:
            self.publish_event("healed", {
                "amount": actual_healed,
                "new_hull": self.ship_hull
            })
        
        return actual_healed
    
    def _handle_death(self, cause: Optional[str] = None) -> None:
        """Handle character death"""
        self.is_alive = False
        self.death_count += 1
        self.last_death_time = datetime.now()
        
        # Death penalty
        credits_lost = int(self.credits * 0.1)  # Lose 10% of credits
        self.credits = max(0, self.credits - credits_lost)
        
        # Reset ship
        self.ship_hull = 0
        self.ship_fuel = 0
        
        # Event is published by field tracking, but add detailed death event
        self.publish_event("character_died", {
            "cause": cause,
            "death_count": self.death_count,
            "credits_lost": credits_lost,
            "location": self.current_location
        })
    
    def respawn(self, respawn_location: int) -> None:
        """Respawn character after death"""
        if self.is_alive:
            return
        
        self.is_alive = True
        self.current_location = respawn_location
        self.ship_hull = int(self.max_ship_hull * 0.5)  # Respawn with 50% hull
        self.ship_fuel = 25  # Minimal fuel
        self.location_status = LocationStatus.DOCKED
        
        self.publish_event("character_respawned", {
            "location": respawn_location,
            "death_count": self.death_count
        })
    
    def update_alignment(self, karma_change: int) -> None:
        """Update karma and potentially change alignment"""
        old_alignment = self.alignment
        self.karma += karma_change
        
        # Determine new alignment based on karma
        if self.karma >= 50:
            self.alignment = Alignment.LOYAL
        elif self.karma <= -50:
            self.alignment = Alignment.BANDIT
        else:
            self.alignment = Alignment.NEUTRAL
        
        if old_alignment != self.alignment:
            self.publish_event("alignment_changed", {
                "old_alignment": old_alignment.value,
                "new_alignment": self.alignment.value,
                "karma": self.karma
            })
    
    def add_experience(self, amount: int, skill: Optional[str] = None) -> None:
        """Add experience and potentially level up"""
        self.experience += amount
        
        # Check for level up
        xp_for_next_level = self.level * 1000
        if self.experience >= xp_for_next_level:
            self.level += 1
            self.experience -= xp_for_next_level
            
            # Increase stats on level up
            self.stats.strength += 1
            self.stats.agility += 1
            self.stats.intelligence += 1
            self.stats.charisma += 1
            self.stats.endurance += 1
            
            self.publish_event("level_up", {
                "new_level": self.level,
                "stats": self.stats
            })
        
        # Increase specific skill if provided
        if skill and skill in self.skills:
            self.skills[skill] = min(100, self.skills[skill] + 1)
    
    # Inventory Management
    def add_item(self, item: InventoryItem) -> bool:
        """Add item to inventory"""
        current_weight = self.get_inventory_weight()
        if current_weight + item.weight > self.max_inventory_weight:
            return False
        
        # Check if item already exists and stack it
        for inv_item in self._inventory:
            if inv_item.item_id == item.item_id:
                inv_item.quantity += item.quantity
                self.publish_event("item_added", {
                    "item": item.name,
                    "quantity": item.quantity,
                    "total": inv_item.quantity
                })
                return True
        
        # Add new item
        self._inventory.append(item)
        self.publish_event("item_added", {
            "item": item.name,
            "quantity": item.quantity
        })
        return True
    
    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Remove item from inventory"""
        for i, item in enumerate(self._inventory):
            if item.item_id == item_id:
                if item.quantity > quantity:
                    item.quantity -= quantity
                    self.publish_event("item_removed", {
                        "item": item.name,
                        "quantity": quantity,
                        "remaining": item.quantity
                    })
                    return True
                elif item.quantity == quantity:
                    removed_item = self._inventory.pop(i)
                    self.publish_event("item_removed", {
                        "item": removed_item.name,
                        "quantity": quantity,
                        "remaining": 0
                    })
                    return True
        return False
    
    def get_inventory(self) -> List[InventoryItem]:
        """Get current inventory"""
        return list(self._inventory)
    
    def get_inventory_weight(self) -> float:
        """Calculate total inventory weight"""
        return sum(item.weight * item.quantity for item in self._inventory)
    
    def get_item(self, item_id: str) -> Optional[InventoryItem]:
        """Get specific item from inventory"""
        for item in self._inventory:
            if item.item_id == item_id:
                return item
        return None
    
    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if character has an item"""
        item = self.get_item(item_id)
        return item is not None and item.quantity >= quantity
    
    def validate(self) -> bool:
        """Validate character state"""
        if not self.name or not self.player_ref:
            return False
        
        if self.credits < 0:
            return False
        
        if self.ship_fuel < 0 or self.ship_fuel > 100:
            return False
        
        if self.ship_hull < 0 or self.ship_hull > self.max_ship_hull:
            return False
        
        if self.alignment not in Alignment:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary"""
        return {
            'id': self.id,
            'player_ref': self.player_ref,
            'name': self.name,
            'current_location': self.current_location,
            'credits': self.credits,
            'ship_fuel': self.ship_fuel,
            'ship_hull': self.ship_hull,
            'max_ship_hull': self.max_ship_hull,
            'current_ship_id': self.current_ship_id,
            'stats': {
                'strength': self.stats.strength,
                'agility': self.stats.agility,
                'intelligence': self.stats.intelligence,
                'charisma': self.stats.charisma,
                'endurance': self.stats.endurance
            },
            'karma': self.karma,
            'wanted_level': self.wanted_level,
            'alignment': self.alignment.value,
            'location_status': self.location_status.value,
            'is_alive': self.is_alive,
            'death_count': self.death_count,
            'last_death_time': self.last_death_time.isoformat() if self.last_death_time else None,
            'inventory': [
                {
                    'item_id': item.item_id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'weight': item.weight,
                    'value': item.value,
                    'type': item.item_type,
                    'metadata': item.metadata
                } for item in self._inventory
            ],
            'experience': self.experience,
            'level': self.level,
            'skills': self.skills,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Create character from dictionary"""
        character = cls(
            character_id=data.get('id'),
            player_ref=data['player_ref'],
            name=data['name'],
            current_location=data.get('current_location'),
            credits=data.get('credits', 1000)
        )
        
        # Set ship stats
        character.ship_fuel = data.get('ship_fuel', 50)
        character.ship_hull = data.get('ship_hull', 100)
        character.max_ship_hull = data.get('max_ship_hull', 100)
        character.current_ship_id = data.get('current_ship_id')
        
        # Set character stats
        if 'stats' in data:
            stats_data = data['stats']
            character.stats = CharacterStats(
                strength=stats_data.get('strength', 10),
                agility=stats_data.get('agility', 10),
                intelligence=stats_data.get('intelligence', 10),
                charisma=stats_data.get('charisma', 10),
                endurance=stats_data.get('endurance', 10)
            )
        
        # Set other properties
        character.karma = data.get('karma', 0)
        character.wanted_level = data.get('wanted_level', 0)
        character.alignment = Alignment(data.get('alignment', 'neutral'))
        character.location_status = LocationStatus(data.get('location_status', 'docked'))
        character.is_alive = data.get('is_alive', True)
        character.death_count = data.get('death_count', 0)
        
        if data.get('last_death_time'):
            character.last_death_time = datetime.fromisoformat(data['last_death_time'])
        
        # Load inventory
        if 'inventory' in data:
            for item_data in data['inventory']:
                item = InventoryItem(
                    item_id=item_data['item_id'],
                    name=item_data['name'],
                    quantity=item_data.get('quantity', 1),
                    weight=item_data.get('weight', 1.0),
                    value=item_data.get('value', 0),
                    item_type=item_data.get('type', 'misc'),
                    metadata=item_data.get('metadata', {})
                )
                character._inventory.append(item)
        
        # Set experience and skills
        character.experience = data.get('experience', 0)
        character.level = data.get('level', 1)
        character.skills = data.get('skills', character.skills)
        
        return character
    
    def __repr__(self) -> str:
        return f"<Character {self.id}: {self.name} ({self.alignment.value})>"