"""
galaxy_core/models/npc.py
NPC models for static and dynamic non-player characters
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
from .base import BaseModel
from .character import Alignment, InventoryItem

class NPCPersonality(Enum):
    """NPC personality types"""
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    HOSTILE = "hostile"
    MYSTERIOUS = "mysterious"
    MERCHANT = "merchant"
    GUARD = "guard"
    CRIMINAL = "criminal"
    SCIENTIST = "scientist"
    PILOT = "pilot"

class NPCOccupation(Enum):
    """NPC occupations"""
    TRADER = "trader"
    BARTENDER = "bartender"
    MECHANIC = "mechanic"
    DOCTOR = "doctor"
    SECURITY = "security"
    MINER = "miner"
    SMUGGLER = "smuggler"
    PILOT = "pilot"
    RESEARCHER = "researcher"
    MERCENARY = "mercenary"

@dataclass
class DialogueOption:
    """Dialogue option for NPCs"""
    text: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)
    personality_match: List[NPCPersonality] = field(default_factory=list)
    
@dataclass
class TradeGood:
    """Item available for trade from NPC"""
    item_id: str
    name: str
    base_price: int
    quantity: int
    category: str = "general"
    rarity: str = "common"


class BaseNPC(BaseModel):
    """Base class for all NPCs"""
    
    def __init__(self,
                 npc_id: Optional[int] = None,
                 name: str = "",
                 age: int = 30,
                 alignment: Alignment = Alignment.NEUTRAL):
        
        super().__init__(npc_id)
        
        self.name = name
        self.age = age
        self.alignment = alignment
        self.hp = 100
        self.max_hp = 100
        self.combat_rating = 5
        self.is_alive = True
        self.credits = random.randint(100, 1000)
        
        # Track important fields
        self.track_field('is_alive')
        self.track_field('hp')
        self.track_field('alignment')
    
    def take_damage(self, damage: int) -> bool:
        """Apply damage to NPC"""
        if not self.is_alive:
            return False
        
        self.hp = max(0, self.hp - damage)
        
        if self.hp <= 0:
            self.is_alive = False
            self.publish_event("npc_died", {
                "npc_name": self.name,
                "npc_id": self.id
            })
        
        return True
    
    def heal(self, amount: int) -> int:
        """Heal NPC"""
        if not self.is_alive:
            return 0
        
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp


class StaticNPC(BaseNPC):
    """Static NPC that stays in one location"""
    
    def __init__(self,
                 npc_id: Optional[int] = None,
                 name: str = "",
                 age: int = 30,
                 alignment: Alignment = Alignment.NEUTRAL,
                 location_id: Optional[int] = None,
                 occupation: Optional[NPCOccupation] = None,
                 personality: NPCPersonality = NPCPersonality.NEUTRAL):
        
        super().__init__(npc_id, name, age, alignment)
        
        self.location_id = location_id
        self.occupation = occupation or NPCOccupation.TRADER
        self.personality = personality
        self.trade_specialty: Optional[str] = None
        
        # Dialogue system
        self._dialogue_options: List[DialogueOption] = []
        self._current_dialogue_state: str = "greeting"
        self._dialogue_history: List[str] = []
        
        # Trading
        self._trade_goods: List[TradeGood] = []
        self._price_modifier: float = 1.0
        self._last_restock: datetime = datetime.now()
        self._restock_interval: timedelta = timedelta(hours=24)
        
        # Relationships
        self._reputation_with_players: Dict[str, int] = {}
        
        # Initialize based on occupation
        self._initialize_by_occupation()
    
    def _initialize_by_occupation(self) -> None:
        """Set up NPC based on their occupation"""
        occupation_configs = {
            NPCOccupation.TRADER: {
                'trade_specialty': 'general_goods',
                'personality': NPCPersonality.MERCHANT,
                'base_inventory_size': 10
            },
            NPCOccupation.BARTENDER: {
                'trade_specialty': 'information',
                'personality': NPCPersonality.FRIENDLY,
                'base_inventory_size': 5
            },
            NPCOccupation.MECHANIC: {
                'trade_specialty': 'ship_parts',
                'personality': NPCPersonality.NEUTRAL,
                'base_inventory_size': 8
            },
            NPCOccupation.DOCTOR: {
                'trade_specialty': 'medical_supplies',
                'personality': NPCPersonality.FRIENDLY,
                'base_inventory_size': 6
            },
            NPCOccupation.SMUGGLER: {
                'trade_specialty': 'illegal_goods',
                'personality': NPCPersonality.MYSTERIOUS,
                'base_inventory_size': 4
            }
        }
        
        config = occupation_configs.get(self.occupation, {})
        if not self.trade_specialty:
            self.trade_specialty = config.get('trade_specialty', 'general_goods')
        
        # Generate initial trade goods
        self._generate_trade_goods(config.get('base_inventory_size', 5))
    
    def _generate_trade_goods(self, num_items: int) -> None:
        """Generate trade goods based on specialty"""
        specialty_items = {
            'general_goods': [
                ('food_ration', 'Food Ration', 10, 'consumable'),
                ('water_purifier', 'Water Purifier', 50, 'tool'),
                ('basic_toolkit', 'Basic Toolkit', 100, 'tool'),
                ('energy_cell', 'Energy Cell', 30, 'component')
            ],
            'ship_parts': [
                ('hull_plating', 'Hull Plating', 200, 'ship_component'),
                ('engine_booster', 'Engine Booster', 500, 'ship_upgrade'),
                ('shield_generator', 'Shield Generator', 800, 'ship_component'),
                ('fuel_injector', 'Fuel Injector', 300, 'ship_component')
            ],
            'medical_supplies': [
                ('medkit', 'Medkit', 75, 'medical'),
                ('stimpak', 'Stimpak', 150, 'medical'),
                ('antidote', 'Antidote', 100, 'medical'),
                ('trauma_kit', 'Trauma Kit', 300, 'medical')
            ],
            'illegal_goods': [
                ('contraband_data', 'Contraband Data', 1000, 'illegal'),
                ('weapon_mod', 'Illegal Weapon Mod', 600, 'illegal'),
                ('forged_permit', 'Forged Permit', 400, 'illegal'),
                ('encrypted_chip', 'Encrypted Chip', 800, 'illegal')
            ]
        }
        
        available_items = specialty_items.get(self.trade_specialty, specialty_items['general_goods'])
        
        for i in range(min(num_items, len(available_items))):
            item_data = available_items[i]
            trade_good = TradeGood(
                item_id=item_data[0],
                name=item_data[1],
                base_price=item_data[2],
                quantity=random.randint(1, 10),
                category=item_data[3],
                rarity='common' if item_data[2] < 100 else 'uncommon' if item_data[2] < 500 else 'rare'
            )
            self._trade_goods.append(trade_good)
    
    def generate_dialogue(self, player_karma: int = 0, player_alignment: Alignment = Alignment.NEUTRAL) -> str:
        """Generate contextual dialogue based on NPC personality and player stats"""
        
        # Base greetings by personality
        personality_greetings = {
            NPCPersonality.FRIENDLY: [
                f"Welcome, friend! I'm {self.name}. How can I help you today?",
                f"Good to see a new face! The name's {self.name}.",
                "Always happy to meet fellow travelers!"
            ],
            NPCPersonality.NEUTRAL: [
                f"Name's {self.name}. What do you need?",
                "Looking for something specific?",
                "State your business."
            ],
            NPCPersonality.HOSTILE: [
                "What do you want?",
                "Make it quick, I don't have all day.",
                f"You better not be wasting {self.name}'s time."
            ],
            NPCPersonality.MYSTERIOUS: [
                "Ah, another seeker of... unusual items?",
                f"They call me {self.name}. But names are just labels, aren't they?",
                "You have the look of someone searching for something..."
            ],
            NPCPersonality.MERCHANT: [
                f"{self.name}'s Goods - finest quality in the sector!",
                "Welcome to my humble shop! Everything's negotiable.",
                "Buying or selling? I deal in both!"
            ]
        }
        
        base_dialogues = personality_greetings.get(self.personality, personality_greetings[NPCPersonality.NEUTRAL])
        dialogue = random.choice(base_dialogues)
        
        # Modify based on alignment compatibility
        if self.alignment == player_alignment:
            dialogue += " I can tell we think alike."
        elif (self.alignment == Alignment.LOYAL and player_alignment == Alignment.BANDIT) or \
             (self.alignment == Alignment.BANDIT and player_alignment == Alignment.LOYAL):
            dialogue += " Though I'm not sure I trust your type."
        
        # Add occupation-specific flavor
        occupation_addons = {
            NPCOccupation.BARTENDER: " Pull up a seat and I'll pour you a drink.",
            NPCOccupation.MECHANIC: " Your ship looking a bit worse for wear?",
            NPCOccupation.DOCTOR: " You look like you could use a check-up.",
            NPCOccupation.PILOT: " Looking for fast transport?",
            NPCOccupation.SMUGGLER: " ...assuming you can keep a secret."
        }
        
        if self.occupation in occupation_addons:
            dialogue += occupation_addons[self.occupation]
        
        return dialogue
    
    def offer_trade(self, player_credits: int, player_reputation: int = 0) -> List[Tuple[TradeGood, int]]:
        """Get available trade goods with adjusted prices"""
        if not self.is_alive:
            return []
        
        # Check if restock needed
        if datetime.now() - self._last_restock > self._restock_interval:
            self._restock_goods()
        
        available_goods = []
        for good in self._trade_goods:
            if good.quantity > 0:
                # Calculate price with modifiers
                price = self._calculate_price(good, player_reputation)
                available_goods.append((good, price))
        
        return available_goods
    
    def _calculate_price(self, good: TradeGood, player_reputation: int) -> int:
        """Calculate adjusted price based on various factors"""
        base_price = good.base_price
        
        # Reputation modifier (-20 to +20%)
        rep_modifier = 1.0 - (player_reputation / 500.0)  # Max ±20% at ±100 reputation
        
        # Personality modifier
        personality_modifiers = {
            NPCPersonality.FRIENDLY: 0.95,
            NPCPersonality.MERCHANT: 1.0,
            NPCPersonality.HOSTILE: 1.15,
            NPCPersonality.MYSTERIOUS: 1.1
        }
        personality_mod = personality_modifiers.get(self.personality, 1.0)
        
        # Rarity modifier
        rarity_modifiers = {
            'common': 1.0,
            'uncommon': 1.3,
            'rare': 1.8,
            'legendary': 2.5
        }
        rarity_mod = rarity_modifiers.get(good.rarity, 1.0)
        
        # Calculate final price
        final_price = int(base_price * rep_modifier * personality_mod * rarity_mod * self._price_modifier)
        
        return max(1, final_price)  # Minimum price of 1
    
    def complete_trade(self, item_id: str, quantity: int, is_buying: bool) -> bool:
        """Complete a trade transaction"""
        for good in self._trade_goods:
            if good.item_id == item_id:
                if is_buying and good.quantity >= quantity:
                    good.quantity -= quantity
                    return True
                elif not is_buying:  # Selling to NPC
                    good.quantity += quantity
                    return True
        return False
    
    def _restock_goods(self) -> None:
        """Restock trade goods"""
        for good in self._trade_goods:
            # Random restock between 50% and 150% of base
            restock_percent = random.uniform(0.5, 1.5)
            good.quantity = int(5 * restock_percent)  # Base stock of 5
        
        self._last_restock = datetime.now()
        
        self.publish_event("npc_restocked", {
            "npc_name": self.name,
            "specialty": self.trade_specialty
        })
    
    def update_reputation(self, player_ref: str, change: int) -> int:
        """Update reputation with a specific player"""
        if player_ref not in self._reputation_with_players:
            self._reputation_with_players[player_ref] = 0
        
        self._reputation_with_players[player_ref] += change
        # Clamp between -100 and 100
        self._reputation_with_players[player_ref] = max(-100, min(100, self._reputation_with_players[player_ref]))
        
        return self._reputation_with_players[player_ref]
    
    def get_reputation(self, player_ref: str) -> int:
        """Get reputation with a specific player"""
        return self._reputation_with_players.get(player_ref, 0)
    
    def validate(self) -> bool:
        """Validate NPC state"""
        if not super().validate():
            return False
        
        if self.personality not in NPCPersonality:
            return False
        
        if self.occupation and self.occupation not in NPCOccupation:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        base_dict = {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'alignment': self.alignment.value,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'combat_rating': self.combat_rating,
            'is_alive': self.is_alive,
            'credits': self.credits,
            'location_id': self.location_id,
            'occupation': self.occupation.value if self.occupation else None,
            'personality': self.personality.value,
            'trade_specialty': self.trade_specialty,
            'trade_goods': [
                {
                    'item_id': good.item_id,
                    'name': good.name,
                    'base_price': good.base_price,
                    'quantity': good.quantity,
                    'category': good.category,
                    'rarity': good.rarity
                } for good in self._trade_goods
            ],
            'reputation_data': self._reputation_with_players,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        return base_dict


class DynamicNPC(BaseNPC):
    """Dynamic NPC that travels between locations"""
    
    def __init__(self,
                 npc_id: Optional[int] = None,
                 name: str = "",
                 age: int = 30,
                 alignment: Alignment = Alignment.NEUTRAL,
                 callsign: str = "",
                 ship_name: str = "",
                 ship_type: str = "freighter"):
        
        super().__init__(npc_id, name, age, alignment)
        
        self.callsign = callsign or f"Trader-{random.randint(100, 999)}"
        self.ship_name = ship_name or f"SS {name}"
        self.ship_type = ship_type
        
        # Location and travel
        self.current_location: Optional[int] = None
        self.destination_location: Optional[int] = None
        self.travel_start_time: Optional[datetime] = None
        self.travel_duration: Optional[timedelta] = None
        
        # Ship stats
        self.ship_hull = 100
        self.max_ship_hull = 100
        self.ship_fuel = 100
        self.max_ship_fuel = 100
        self.cargo_capacity = 100
        self.current_cargo: List[InventoryItem] = []
        
        # Radio broadcasts
        self._radio_messages: List[str] = []
        self._last_broadcast: Optional[datetime] = None
        self._broadcast_interval = timedelta(minutes=30)
        
        # AI behavior
        self.ai_behavior: str = "trader"  # trader, patrol, pirate, explorer
        self._behavior_state: Dict[str, Any] = {}
        
        self._initialize_radio_messages()
        
        # Track location changes
        self.track_field('current_location')
        self.track_field('destination_location')
    
    def _initialize_radio_messages(self) -> None:
        """Set up radio messages based on ship type and alignment"""
        if self.alignment == Alignment.BANDIT:
            self._radio_messages = [
                f"This is {self.callsign}. Stay out of my way.",
                "Valuable cargo coming through. Don't get any ideas.",
                f"{self.ship_name} to all ships - maintaining radio silence.",
                "...signal interference... *static* ...watch your six..."
            ]
        elif self.alignment == Alignment.LOYAL:
            self._radio_messages = [
                f"{self.callsign} here. Safe travels, everyone!",
                f"This is {self.ship_name}. Reporting clear skies ahead.",
                "Remember to check your fuel before long jumps, folks!",
                f"{self.callsign} to all ships - happy to provide escort if needed."
            ]
        else:  # Neutral
            self._radio_messages = [
                f"{self.callsign} passing through.",
                f"This is {self.ship_name}. Just another milk run.",
                "Anyone know the best prices for quantum cores these days?",
                f"{self.callsign} here. Everything nominal."
            ]
    
    def update_position(self, current_time: datetime) -> bool:
        """Update NPC position during travel"""
        if not self.is_alive or not self.destination_location:
            return False
        
        if not self.travel_start_time or not self.travel_duration:
            return False
        
        elapsed = current_time - self.travel_start_time
        
        if elapsed >= self.travel_duration:
            # Arrival
            old_location = self.current_location
            self.current_location = self.destination_location
            self.destination_location = None
            self.travel_start_time = None
            self.travel_duration = None
            
            self.publish_event("npc_arrived", {
                "npc_name": self.name,
                "callsign": self.callsign,
                "from_location": old_location,
                "to_location": self.current_location
            })
            
            return True
        
        return False
    
    def start_travel(self, destination_id: int, travel_time: timedelta) -> bool:
        """Start traveling to a new location"""
        if not self.is_alive or self.destination_location:
            return False  # Already traveling
        
        if self.ship_fuel < 10:  # Minimum fuel requirement
            return False
        
        self.destination_location = destination_id
        self.travel_start_time = datetime.now()
        self.travel_duration = travel_time
        
        # Consume fuel based on travel time
        fuel_cost = int(travel_time.total_seconds() / 60)  # 1 fuel per minute
        self.ship_fuel = max(0, self.ship_fuel - fuel_cost)
        
        self.publish_event("npc_departing", {
            "npc_name": self.name,
            "callsign": self.callsign,
            "from_location": self.current_location,
            "to_location": destination_id,
            "travel_time": travel_time.total_seconds()
        })
        
        return True
    
    def broadcast_radio(self, force: bool = False) -> Optional[str]:
        """Generate a radio broadcast message"""
        if not self.is_alive:
            return None
        
        current_time = datetime.now()
        
        # Check if enough time has passed
        if not force and self._last_broadcast:
            if current_time - self._last_broadcast < self._broadcast_interval:
                return None
        
        # Select message based on current state
        if self.destination_location and self.travel_duration:
            # In transit
            if self.travel_duration.total_seconds() > 600:  # Long journey
                message = f"{self.callsign}: Still got a ways to go. ETA {int(self.travel_duration.total_seconds() / 60)} minutes."
            else:
                message = random.choice(self._radio_messages)
        else:
            # At location
            location_messages = [
                f"{self.callsign}: Docked and resupplying.",
                f"This is {self.ship_name}. Anyone need transport?",
                f"{self.callsign} here. Prices are good at this station!"
            ]
            message = random.choice(location_messages)
        
        self._last_broadcast = current_time
        
        self.publish_event("radio_broadcast", {
            "npc_name": self.name,
            "callsign": self.callsign,
            "message": message,
            "location": self.current_location
        })
        
        return message
    
    def add_cargo(self, item: InventoryItem) -> bool:
        """Add item to cargo hold"""
        current_weight = sum(i.weight * i.quantity for i in self.current_cargo)
        if current_weight + item.weight > self.cargo_capacity:
            return False
        
        # Check if item already exists
        for cargo_item in self.current_cargo:
            if cargo_item.item_id == item.item_id:
                cargo_item.quantity += item.quantity
                return True
        
        self.current_cargo.append(item)
        return True
    
    def remove_cargo(self, item_id: str, quantity: int) -> bool:
        """Remove item from cargo"""
        for i, item in enumerate(self.current_cargo):
            if item.item_id == item_id:
                if item.quantity > quantity:
                    item.quantity -= quantity
                    return True
                elif item.quantity == quantity:
                    self.current_cargo.pop(i)
                    return True
        return False
    
    def calculate_cargo_value(self) -> int:
        """Calculate total value of cargo"""
        return sum(item.value * item.quantity for item in self.current_cargo)
    
    def refuel(self, amount: int) -> int:
        """Refuel the ship"""
        old_fuel = self.ship_fuel
        self.ship_fuel = min(self.max_ship_fuel, self.ship_fuel + amount)
        return self.ship_fuel - old_fuel
    
    def repair_ship(self, amount: int) -> int:
        """Repair ship hull"""
        old_hull = self.ship_hull
        self.ship_hull = min(self.max_ship_hull, self.ship_hull + amount)
        return self.ship_hull - old_hull
    
    def execute_ai_behavior(self, available_locations: List[int], current_time: datetime) -> Optional[Dict[str, Any]]:
        """Execute AI behavior and return action to take"""
        if not self.is_alive:
            return None
        
        # Update position first
        self.update_position(current_time)
        
        # If already traveling, no new action
        if self.destination_location:
            return None
        
        # Behavior-specific logic
        if self.ai_behavior == "trader":
            return self._trader_behavior(available_locations)
        elif self.ai_behavior == "patrol":
            return self._patrol_behavior(available_locations)
        elif self.ai_behavior == "pirate":
            return self._pirate_behavior(available_locations)
        elif self.ai_behavior == "explorer":
            return self._explorer_behavior(available_locations)
        
        return None
    
    def _trader_behavior(self, available_locations: List[int]) -> Optional[Dict[str, Any]]:
        """Trading AI behavior"""
        # Need fuel to travel
        if self.ship_fuel < 20:
            return {"action": "refuel", "amount": self.max_ship_fuel - self.ship_fuel}
        
        # Need repairs
        if self.ship_hull < self.max_ship_hull * 0.5:
            return {"action": "repair", "amount": self.max_ship_hull - self.ship_hull}
        
        # Pick a random destination for trading
        if available_locations and self.current_location:
            valid_destinations = [loc for loc in available_locations if loc != self.current_location]
            if valid_destinations:
                destination = random.choice(valid_destinations)
                travel_time = timedelta(minutes=random.randint(5, 30))
                return {"action": "travel", "destination": destination, "duration": travel_time}
        
        return None
    
    def _patrol_behavior(self, available_locations: List[int]) -> Optional[Dict[str, Any]]:
        """Patrol AI behavior - systematic movement"""
        if 'patrol_index' not in self._behavior_state:
            self._behavior_state['patrol_index'] = 0
        
        if self.ship_fuel < 30:
            return {"action": "refuel", "amount": self.max_ship_fuel - self.ship_fuel}
        
        if available_locations and self.current_location:
            # Move to next location in patrol route
            patrol_index = self._behavior_state['patrol_index']
            valid_locations = [loc for loc in available_locations if loc != self.current_location]
            
            if valid_locations:
                destination = valid_locations[patrol_index % len(valid_locations)]
                self._behavior_state['patrol_index'] = (patrol_index + 1) % len(valid_locations)
                travel_time = timedelta(minutes=random.randint(10, 20))
                return {"action": "travel", "destination": destination, "duration": travel_time}
        
        return None
    
    def _pirate_behavior(self, available_locations: List[int]) -> Optional[Dict[str, Any]]:
        """Pirate AI behavior - aggressive actions"""
        # Pirates prioritize repairs and fuel
        if self.ship_hull < self.max_ship_hull * 0.7:
            return {"action": "repair", "amount": self.max_ship_hull - self.ship_hull}
        
        if self.ship_fuel < 40:
            return {"action": "refuel", "amount": self.max_ship_fuel - self.ship_fuel}
        
        # Look for targets (simplified - just move randomly for now)
        if available_locations and self.current_location:
            valid_destinations = [loc for loc in available_locations if loc != self.current_location]
            if valid_destinations:
                destination = random.choice(valid_destinations)
                travel_time = timedelta(minutes=random.randint(3, 15))  # Pirates move faster
                return {"action": "travel", "destination": destination, "duration": travel_time}
        
        return None
    
    def _explorer_behavior(self, available_locations: List[int]) -> Optional[Dict[str, Any]]:
        """Explorer AI behavior - visit new locations"""
        if 'visited_locations' not in self._behavior_state:
            self._behavior_state['visited_locations'] = set()
        
        if self.current_location:
            self._behavior_state['visited_locations'].add(self.current_location)
        
        if self.ship_fuel < 50:  # Explorers need more fuel
            return {"action": "refuel", "amount": self.max_ship_fuel - self.ship_fuel}
        
        # Find unvisited locations
        if available_locations and self.current_location:
            unvisited = [loc for loc in available_locations 
                        if loc not in self._behavior_state['visited_locations'] and loc != self.current_location]
            
            if unvisited:
                destination = random.choice(unvisited)
            else:
                # All visited, pick randomly
                valid_destinations = [loc for loc in available_locations if loc != self.current_location]
                if valid_destinations:
                    destination = random.choice(valid_destinations)
                else:
                    return None
            
            travel_time = timedelta(minutes=random.randint(15, 45))  # Explorers take their time
            return {"action": "travel", "destination": destination, "duration": travel_time}
        
        return None
    
    def validate(self) -> bool:
        """Validate dynamic NPC state"""
        if not super().validate():
            return False
        
        if not self.callsign or not self.ship_name:
            return False
        
        if self.ship_fuel < 0 or self.ship_fuel > self.max_ship_fuel:
            return False
        
        if self.ship_hull < 0 or self.ship_hull > self.max_ship_hull:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        base_dict = {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'alignment': self.alignment.value,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'combat_rating': self.combat_rating,
            'is_alive': self.is_alive,
            'credits': self.credits,
            'callsign': self.callsign,
            'ship_name': self.ship_name,
            'ship_type': self.ship_type,
            'current_location': self.current_location,
            'destination_location': self.destination_location,
            'travel_start_time': self.travel_start_time.isoformat() if self.travel_start_time else None,
            'travel_duration': self.travel_duration.total_seconds() if self.travel_duration else None,
            'ship_hull': self.ship_hull,
            'max_ship_hull': self.max_ship_hull,
            'ship_fuel': self.ship_fuel,
            'max_ship_fuel': self.max_ship_fuel,
            'cargo_capacity': self.cargo_capacity,
            'current_cargo': [
                {
                    'item_id': item.item_id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'weight': item.weight,
                    'value': item.value,
                    'type': item.item_type
                } for item in self.current_cargo
            ],
            'ai_behavior': self.ai_behavior,
            'behavior_state': self._behavior_state,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DynamicNPC':
        """Create dynamic NPC from dictionary"""
        npc = cls(
            npc_id=data.get('id'),
            name=data['name'],
            age=data.get('age', 30),
            alignment=Alignment(data.get('alignment', 'neutral')),
            callsign=data.get('callsign', ''),
            ship_name=data.get('ship_name', ''),
            ship_type=data.get('ship_type', 'freighter')
        )
        
        # Set properties
        npc.hp = data.get('hp', 100)
        npc.max_hp = data.get('max_hp', 100)
        npc.combat_rating = data.get('combat_rating', 5)
        npc.is_alive = data.get('is_alive', True)
        npc.credits = data.get('credits', 1000)
        
        # Location and travel
        npc.current_location = data.get('current_location')
        npc.destination_location = data.get('destination_location')
        if data.get('travel_start_time'):
            npc.travel_start_time = datetime.fromisoformat(data['travel_start_time'])
        if data.get('travel_duration'):
            npc.travel_duration = timedelta(seconds=data['travel_duration'])
        
        # Ship stats
        npc.ship_hull = data.get('ship_hull', 100)
        npc.max_ship_hull = data.get('max_ship_hull', 100)
        npc.ship_fuel = data.get('ship_fuel', 100)
        npc.max_ship_fuel = data.get('max_ship_fuel', 100)
        npc.cargo_capacity = data.get('cargo_capacity', 100)
        
        # Load cargo
        if 'current_cargo' in data:
            for item_data in data['current_cargo']:
                item = InventoryItem(
                    item_id=item_data['item_id'],
                    name=item_data['name'],
                    quantity=item_data.get('quantity', 1),
                    weight=item_data.get('weight', 1.0),
                    value=item_data.get('value', 0),
                    item_type=item_data.get('type', 'misc')
                )
                npc.current_cargo.append(item)
        
        # AI behavior
        npc.ai_behavior = data.get('ai_behavior', 'trader')
        npc._behavior_state = data.get('behavior_state', {})
        
        return npc
    
    def __repr__(self) -> str:
        status = "traveling" if self.destination_location else "docked"
        return f"<DynamicNPC {self.id}: {self.name} ({self.callsign}) - {status}>"