"""
galaxy_core/database/schema.py
Database schema definitions for Galaxy Core
No Discord-specific fields - uses abstract references
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class LocationSchema:
    """Schema for location entities"""
    location_id: Optional[int] = None
    name: str = ""
    location_type: str = ""
    description: Optional[str] = None
    wealth_level: int = 5
    population: int = 100
    x_coord: float = 0.0
    y_coord: float = 0.0
    system_name: Optional[str] = None
    has_jobs: bool = True
    has_shops: bool = True
    has_medical: bool = True
    has_repairs: bool = True
    has_fuel: bool = True
    has_upgrades: bool = False
    has_black_market: bool = False
    has_federal_supplies: bool = False
    has_shipyard: bool = False
    is_derelict: bool = False
    gate_status: str = "active"
    establishment_date: Optional[str] = None
    faction: str = "Independent"
    created_at: Optional[datetime] = None
    location_ref: Optional[str] = None  # Abstract reference for external systems


@dataclass
class CharacterSchema:
    """Schema for character entities"""
    character_id: Optional[int] = None
    player_ref: str = ""  # Abstract reference instead of Discord user_id
    name: str = ""
    current_location: Optional[int] = None
    credits: int = 1000
    ship_fuel: int = 50
    ship_hull: int = 100
    max_ship_hull: int = 100
    karma: int = 0
    wanted_level: int = 0
    location_status: str = "docked"
    alignment: str = "neutral"
    is_alive: bool = True
    death_count: int = 0
    created_at: Optional[datetime] = None


@dataclass
class ShipSchema:
    """Schema for ship entities"""
    ship_id: Optional[int] = None
    owner_id: int = 0
    name: str = ""
    ship_type: str = ""
    cargo_capacity: int = 100
    fuel_capacity: int = 100
    hull_points: int = 100
    max_hull_points: int = 100
    engine_level: int = 1
    shield_level: int = 0
    weapon_level: int = 1
    interior_description: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class CorridorSchema:
    """Schema for corridor entities"""
    corridor_id: Optional[int] = None
    name: str = ""
    origin_location: int = 0
    destination_location: int = 0
    travel_time: int = 300
    fuel_cost: int = 20
    danger_level: int = 3
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class JobSchema:
    """Schema for job entities"""
    job_id: Optional[int] = None
    location_id: int = 0
    title: str = ""
    description: Optional[str] = None
    reward_money: int = 100
    required_skill: Optional[str] = None
    min_skill_level: int = 0
    danger_level: int = 1
    duration_minutes: int = 60
    is_taken: bool = False
    taken_by: Optional[int] = None
    taken_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    job_status: str = "available"
    destination_location_id: Optional[int] = None
    karma_change: int = 0


@dataclass
class GroupSchema:
    """Schema for group entities"""
    group_id: Optional[int] = None
    name: Optional[str] = None
    leader_id: int = 0
    current_location: Optional[int] = None
    status: str = "active"
    created_at: Optional[datetime] = None


@dataclass
class NPCSchema:
    """Base schema for NPC entities"""
    npc_id: Optional[int] = None
    name: str = ""
    age: int = 0
    alignment: str = "neutral"
    hp: int = 100
    max_hp: int = 100
    combat_rating: int = 5
    is_alive: bool = True
    credits: int = 0
    created_at: Optional[datetime] = None


@dataclass
class StaticNPCSchema(NPCSchema):
    """Schema for static NPC entities"""
    location_id: int = 0
    occupation: Optional[str] = None
    personality: Optional[str] = None
    trade_specialty: Optional[str] = None


@dataclass
class DynamicNPCSchema(NPCSchema):
    """Schema for dynamic NPC entities"""
    callsign: str = ""
    ship_name: str = ""
    ship_type: str = ""
    current_location: Optional[int] = None
    destination_location: Optional[int] = None
    travel_start_time: Optional[datetime] = None
    travel_duration: Optional[int] = None


class SchemaManager:
    """Manages database schema operations"""
    
    @staticmethod
    def location_to_dict(location: LocationSchema) -> Dict[str, Any]:
        """Convert location schema to dictionary for database operations"""
        return {
            'name': location.name,
            'location_type': location.location_type,
            'description': location.description,
            'wealth_level': location.wealth_level,
            'population': location.population,
            'x_coord': location.x_coord,
            'y_coord': location.y_coord,
            'system_name': location.system_name,
            'has_jobs': location.has_jobs,
            'has_shops': location.has_shops,
            'has_medical': location.has_medical,
            'has_repairs': location.has_repairs,
            'has_fuel': location.has_fuel,
            'has_upgrades': location.has_upgrades,
            'has_black_market': location.has_black_market,
            'has_federal_supplies': location.has_federal_supplies,
            'has_shipyard': location.has_shipyard,
            'is_derelict': location.is_derelict,
            'gate_status': location.gate_status,
            'establishment_date': location.establishment_date,
            'faction': location.faction,
            'location_ref': location.location_ref
        }
    
    @staticmethod
    def character_to_dict(character: CharacterSchema) -> Dict[str, Any]:
        """Convert character schema to dictionary for database operations"""
        return {
            'player_ref': character.player_ref,
            'name': character.name,
            'current_location': character.current_location,
            'credits': character.credits,
            'ship_fuel': character.ship_fuel,
            'ship_hull': character.ship_hull,
            'max_ship_hull': character.max_ship_hull,
            'karma': character.karma,
            'wanted_level': character.wanted_level,
            'location_status': character.location_status,
            'alignment': character.alignment,
            'is_alive': character.is_alive,
            'death_count': character.death_count
        }
    
    @staticmethod
    def ship_to_dict(ship: ShipSchema) -> Dict[str, Any]:
        """Convert ship schema to dictionary for database operations"""
        return {
            'owner_id': ship.owner_id,
            'name': ship.name,
            'ship_type': ship.ship_type,
            'cargo_capacity': ship.cargo_capacity,
            'fuel_capacity': ship.fuel_capacity,
            'hull_points': ship.hull_points,
            'max_hull_points': ship.max_hull_points,
            'engine_level': ship.engine_level,
            'shield_level': ship.shield_level,
            'weapon_level': ship.weapon_level,
            'interior_description': ship.interior_description
        }