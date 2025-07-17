"""
galaxy_demo.py
Minimal standalone galaxy generation demo
"""

import random
import math
from datetime import datetime
from typing import List, Dict, Tuple
import json

# Import our core database module
from galaxy_core.database.db_manager import DatabaseManager


class GalaxyGenerator:
    """Core galaxy generation logic without Discord dependencies"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        
        # Location name components
        self.prefixes = ["New", "Port", "Fort", "Station", "Haven", "Alpha", 
                        "Beta", "Gamma", "Delta", "Epsilon", "Outer", "Inner"]
        self.suffixes = ["Prime", "Major", "Minor", "Alpha", "Beta", "Gamma",
                        "Station", "Outpost", "Colony", "Hub", "Port", "Depot"]
        self.system_names = ["Sol", "Kepler", "Hawking", "Armstrong", "Galilei",
                           "Newton", "Einstein", "Sagan", "Asimov", "Clarke"]
    
    def generate_galaxy(self, num_locations: int = 50, galaxy_name: str = None, 
                       start_date: str = None) -> Dict:
        """Generate a complete galaxy"""
        
        # Set defaults if not provided
        if not galaxy_name:
            galaxy_name = f"Galaxy-{random.randint(1000, 9999)}"
        
        if not start_date:
            year = random.randint(2700, 2799)
            start_date = f"01-01-{year}"
        
        print(f"\n🌌 Generating {galaxy_name}...")
        print(f"📅 Start Date: {start_date}")
        print(f"🌍 Target Locations: {num_locations}")
        
        # Clear existing data
        self._clear_galaxy_data()
        
        # Store galaxy info
        self.db.execute_query(
            '''INSERT INTO galaxy_info (galaxy_id, galaxy_name, game_start_date)
               VALUES (1, ?, ?)''',
            (galaxy_name, start_date)
        )
        
        # Generate locations
        locations = self._generate_locations(num_locations)
        
        # Generate corridors
        corridors = self._generate_corridors(locations)
        
        # Generate NPCs
        npcs = self._generate_npcs(locations)
        
        # Generate some history
        history = self._generate_basic_history(locations, start_date)
        
        return {
            'galaxy_name': galaxy_name,
            'start_date': start_date,
            'locations': len(locations),
            'corridors': len(corridors),
            'npcs': len(npcs),
            'history_events': len(history)
        }
    
    def _clear_galaxy_data(self):
        """Clear existing galaxy data"""
        tables = ['galactic_history', 'jobs', 'dynamic_npcs', 'static_npcs', 
                 'corridors', 'locations', 'galaxy_info']
        for table in tables:
            self.db.execute_query(f"DELETE FROM {table}")
    
    def _generate_locations(self, num_locations: int) -> List[Dict]:
        """Generate locations with balanced types"""
        locations = []
        
        # Location type distribution
        colonies = int(num_locations * 0.40)
        stations = int(num_locations * 0.30)
        outposts = int(num_locations * 0.20)
        gates = num_locations - colonies - stations - outposts
        
        # Generate each type
        for i in range(colonies):
            locations.append(self._create_location('colony', i))
        
        for i in range(stations):
            locations.append(self._create_location('space_station', i))
        
        for i in range(outposts):
            locations.append(self._create_location('outpost', i))
        
        for i in range(gates):
            locations.append(self._create_location('gate', i))
        
        return locations
    
    def _create_location(self, loc_type: str, index: int) -> Dict:
        """Create a single location"""
        # Generate unique name
        if loc_type == 'gate':
            name = f"Gate {random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])}-{random.randint(100, 999)}"
        else:
            prefix = random.choice(self.prefixes)
            suffix = random.choice(self.suffixes)
            name = f"{prefix} {suffix}"
        
        # Generate coordinates (2D plane)
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(10, 100)
        x = distance * math.cos(angle)
        y = distance * math.sin(angle)
        
        # Wealth based on type and randomness
        wealth_ranges = {
            'colony': (2, 8),
            'space_station': (3, 9),
            'outpost': (1, 6),
            'gate': (5, 10)
        }
        wealth = random.randint(*wealth_ranges[loc_type])
        
        # Population
        pop_ranges = {
            'colony': (1000, 50000),
            'space_station': (500, 20000),
            'outpost': (50, 1000),
            'gate': (100, 5000)
        }
        population = random.randint(*pop_ranges[loc_type])
        
        # Services
        services = {
            'has_jobs': wealth >= 2,
            'has_shops': wealth >= 3,
            'has_medical': wealth >= 4,
            'has_repairs': wealth >= 3,
            'has_fuel': True,
            'has_upgrades': wealth >= 7,
            'has_black_market': wealth <= 3 and random.random() < 0.2,
            'has_federal_supplies': wealth >= 8 and random.random() < 0.3,
            'has_shipyard': loc_type == 'space_station' and wealth >= 6
        }
        
        # Insert into database
        location_id = self.db.execute_query(
            '''INSERT INTO locations (name, location_type, wealth_level, 
               population, x_coord, y_coord, system_name, has_jobs, has_shops,
               has_medical, has_repairs, has_fuel, has_upgrades, has_black_market,
               has_federal_supplies, has_shipyard)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name, loc_type, wealth, population, x, y, 
             random.choice(self.system_names),
             services['has_jobs'], services['has_shops'], services['has_medical'],
             services['has_repairs'], services['has_fuel'], services['has_upgrades'],
             services['has_black_market'], services['has_federal_supplies'],
             services['has_shipyard'])
        )
        
        return {
            'id': location_id,
            'name': name,
            'type': loc_type,
            'wealth': wealth,
            'x': x,
            'y': y
        }
    
    def _generate_corridors(self, locations: List[Dict]) -> List[Dict]:
        """Generate corridor network between locations"""
        corridors = []
        
        # Ensure connectivity - create a minimal spanning tree first
        connected = {locations[0]['id']}
        unconnected = {loc['id'] for loc in locations[1:]}
        
        while unconnected:
            # Find closest pair
            min_dist = float('inf')
            best_pair = None
            
            for conn_id in connected:
                conn_loc = next(l for l in locations if l['id'] == conn_id)
                
                for unconn_id in unconnected:
                    unconn_loc = next(l for l in locations if l['id'] == unconn_id)
                    
                    dist = math.sqrt((conn_loc['x'] - unconn_loc['x'])**2 + 
                                   (conn_loc['y'] - unconn_loc['y'])**2)
                    
                    if dist < min_dist:
                        min_dist = dist
                        best_pair = (conn_id, unconn_id)
            
            if best_pair:
                corridors.append(self._create_corridor(best_pair[0], best_pair[1], min_dist))
                connected.add(best_pair[1])
                unconnected.remove(best_pair[1])
        
        # Add some additional corridors for redundancy
        num_extra = len(locations) // 2
        for _ in range(num_extra):
            loc1, loc2 = random.sample(locations, 2)
            if loc1['id'] != loc2['id']:
                dist = math.sqrt((loc1['x'] - loc2['x'])**2 + (loc1['y'] - loc2['y'])**2)
                corridors.append(self._create_corridor(loc1['id'], loc2['id'], dist))
        
        return corridors
    
    def _create_corridor(self, origin_id: int, dest_id: int, distance: float) -> Dict:
        """Create a single corridor"""
        # Travel time based on distance
        base_time = int(distance * 10)  # seconds
        travel_time = random.randint(base_time, base_time * 2)
        
        # Fuel cost based on distance
        fuel_cost = int(distance * 0.5) + random.randint(5, 20)
        
        # Danger level
        danger = random.randint(1, 5)
        
        # Has gates (safer corridors)
        has_gates = random.random() < 0.3
        
        name = f"Corridor-{origin_id}-{dest_id}"
        
        corridor_id = self.db.execute_query(
            '''INSERT INTO corridors (name, origin_location, destination_location,
               travel_time, fuel_cost, danger_level, has_gates)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (name, origin_id, dest_id, travel_time, fuel_cost, danger, has_gates)
        )
        
        return {'id': corridor_id, 'origin': origin_id, 'dest': dest_id}
    
    def _generate_npcs(self, locations: List[Dict]) -> List[Dict]:
        """Generate NPCs for each location"""
        npcs = []
        
        first_names = ["Alex", "Jordan", "Sam", "Morgan", "Casey", "Riley", 
                      "Avery", "Quinn", "Blake", "Drew", "Sage", "Rowan"]
        last_names = ["Chen", "Patel", "Kim", "Singh", "Ivanov", "Mueller",
                     "Sato", "Rodriguez", "O'Brien", "Johansson"]
        
        occupations = {
            'colony': ["Farmer", "Engineer", "Medic", "Teacher", "Merchant"],
            'space_station': ["Dock Worker", "Flight Controller", "Technician"],
            'outpost': ["Monitor", "Researcher", "Security"],
            'gate': ["Transit Operator", "Gate Technician", "Coordinator"]
        }
        
        for loc in locations:
            # 2-5 NPCs per location
            num_npcs = random.randint(2, 5)
            
            for _ in range(num_npcs):
                name = f"{random.choice(first_names)} {random.choice(last_names)}"
                age = random.randint(25, 65)
                occupation = random.choice(occupations.get(loc['type'], ["Worker"]))
                
                # Alignment based on location wealth
                if loc['wealth'] <= 3:
                    alignment = random.choice(['bandit', 'neutral', 'neutral'])
                elif loc['wealth'] >= 7:
                    alignment = random.choice(['loyal', 'loyal', 'neutral'])
                else:
                    alignment = 'neutral'
                
                npc_id = self.db.execute_query(
                    '''INSERT INTO static_npcs (location_id, name, age, occupation,
                       personality, alignment, credits)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (loc['id'], name, age, occupation, 
                     "Hardworking", alignment, random.randint(50, 500))
                )
                
                npcs.append({'id': npc_id, 'name': name, 'location': loc['name']})
        
        return npcs
    
    def _generate_basic_history(self, locations: List[Dict], start_date: str) -> List[Dict]:
        """Generate some basic historical events"""
        history = []
        
        event_types = [
            "Founded as a mining outpost",
            "Established trade routes",
            "Survived pirate raids",
            "Discovered valuable resources",
            "Built defensive installations"
        ]
        
        figures = ["Captain Rivera", "Dr. Chen", "Commander Singh", 
                  "Ambassador Nakamura", "Engineer O'Brien"]
        
        # Generate 5-10 historical events
        for _ in range(random.randint(5, 10)):
            loc = random.choice(locations)
            event = random.choice(event_types)
            figure = random.choice(figures)
            
            history_id = self.db.execute_query(
                '''INSERT INTO galactic_history (location_id, event_title,
                   event_description, historical_figure, event_date)
                   VALUES (?, ?, ?, ?, ?)''',
                (loc['id'], event, f"{loc['name']} {event}", figure, start_date)
            )
            
            history.append({'id': history_id, 'location': loc['name'], 'event': event})
        
        return history


def print_galaxy_summary(db: DatabaseManager):
    """Print a summary of the generated galaxy"""
    print("\n" + "="*60)
    print("🌌 GALAXY SUMMARY")
    print("="*60)
    
    # Galaxy info
    galaxy = db.execute_query("SELECT * FROM galaxy_info WHERE galaxy_id = 1", fetch='one')
    if galaxy:
        print(f"Galaxy Name: {galaxy['galaxy_name']}")
        print(f"Start Date: {galaxy['game_start_date']}")
    
    # Location summary
    locations = db.execute_query("SELECT * FROM locations", fetch='all')
    print(f"\n📍 Total Locations: {len(locations)}")
    
    # Count by type
    types = {}
    for loc in locations:
        loc_type = loc['location_type']
        types[loc_type] = types.get(loc_type, 0) + 1
    
    for loc_type, count in types.items():
        print(f"  - {loc_type.replace('_', ' ').title()}: {count}")
    
    # Sample locations
    print("\n🏙️ Sample Locations:")
    for loc in random.sample(locations, min(5, len(locations))):
        print(f"  - {loc['name']} ({loc['location_type']}) - Wealth: {loc['wealth_level']}")
    
    # Corridor summary
    corridors = db.execute_query("SELECT COUNT(*) as count FROM corridors", fetch='one')
    print(f"\n🛤️ Total Corridors: {corridors['count']}")
    
    # NPC summary
    npcs = db.execute_query("SELECT COUNT(*) as count FROM static_npcs", fetch='one')
    print(f"\n👥 Total NPCs: {npcs['count']}")
    
    # History summary
    history = db.execute_query("SELECT COUNT(*) as count FROM galactic_history", fetch='one')
    print(f"\n📚 Historical Events: {history['count']}")
    
    print("\n" + "="*60)


def main():
    """Main demo program"""
    print("🚀 Galaxy Core - Standalone Demo")
    print("================================")
    
    # Initialize database
    db = DatabaseManager("demo_galaxy.db")
    
    # Create galaxy generator
    generator = GalaxyGenerator(db)
    
    # Generate a galaxy
    result = generator.generate_galaxy(
        num_locations=25,  # Small galaxy for demo
        galaxy_name="Demo Spiral",
        start_date="01-01-2750"
    )
    
    print(f"\n✅ Generation Complete!")
    print(f"  - Locations: {result['locations']}")
    print(f"  - Corridors: {result['corridors']}")
    print(f"  - NPCs: {result['npcs']}")
    print(f"  - History Events: {result['history_events']}")
    
    # Print detailed summary
    print_galaxy_summary(db)
    
    # Close database
    db.close()
    
    print("\n🎮 Demo complete! Database saved as 'demo_galaxy.db'")


if __name__ == "__main__":
    # Create the galaxy_core directory structure
    import os
    os.makedirs("galaxy_core/database", exist_ok=True)
    
    # Create __init__.py files
    open("galaxy_core/__init__.py", "w").close()
    open("galaxy_core/database/__init__.py", "w").close()
    
    # Save the database module
    with open("galaxy_core/database/db_manager.py", "w") as f:
        # Copy the DatabaseManager code from the first artifact
        f.write('"""\ngalaxy_core/database/db_manager.py\nCore database management without Discord dependencies\n"""\n\n')
        f.write('import sqlite3\nimport os\nfrom typing import Optional, List, Tuple, Dict, Any\nfrom datetime import datetime\n\n')
        f.write('class DatabaseManager:\n    # ... (full code from first artifact)\n')
    
    # Run the demo
    main()