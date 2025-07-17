# Galaxy Game Refactoring Implementation Plan

## Overview
Transform the Discord-dependent galaxy game into a standalone, portable game engine with pluggable UI interfaces.

---

## Phase 1: Foundation & Core Database (Week 1)

### Objectives
- Create standalone project structure
- Extract database schema without Discord fields
- Build core database management layer

### Tasks
1. **Create Project Structure**
   ```
   galaxy-core/
   ├── README.md
   ├── requirements.txt
   ├── setup.py
   ├── galaxy_core/
   │   ├── __init__.py
   │   ├── database/
   │   ├── models/
   │   ├── generators/
   │   ├── systems/
   │   └── interfaces/
   └── tests/
   ```

2. **Extract Database Schema**
   - [ ] Copy `database.py` to `galaxy_core/database/schema.py`
   - [ ] Remove Discord-specific columns (channel_id, guild_id, message_id)
   - [ ] Add abstract "location_ref" and "player_ref" fields
   - [ ] Create migration script for existing data

3. **Build Database Manager**
   - [ ] Implement `DatabaseManager` class (no Discord dependencies)
   - [ ] Add connection pooling for concurrent access
   - [ ] Create backup/restore functionality
   - [ ] Add database versioning system

### Deliverables
- Working database module
- Schema documentation
- Unit tests for database operations

### Verification
- Run demo script that creates/queries database
- Ensure no Discord imports in codebase

---

## Phase 2: Core Game Models (Week 1-2)

### Objectives
- Create pure Python models for all game entities
- Implement game logic without UI dependencies

### Tasks

1. **Location Model** (`models/location.py`)
   ```python
   class Location:
       - Properties: id, name, type, wealth, services, coordinates
       - Methods: get_available_services(), calculate_population()
       - Events: on_wealth_change, on_population_change
   ```

2. **Character Model** (`models/character.py`)
   ```python
   class Character:
       - Properties: id, name, stats, inventory, location
       - Methods: move_to(), add_credits(), take_damage()
       - Events: on_location_change, on_death
   ```

3. **NPC Models** (`models/npc.py`)
   ```python
   class StaticNPC:
       - Properties: location, personality, trade_goods
       - Methods: generate_dialogue(), offer_trade()
   
   class DynamicNPC:
       - Properties: current_location, destination, ship
       - Methods: update_position(), broadcast_radio()
   ```

4. **Ship Model** (`models/ship.py`)
   ```python
   class Ship:
       - Properties: hull, cargo, fuel, upgrades
       - Methods: add_cargo(), consume_fuel(), apply_damage()
   ```

### Deliverables
- All model classes with documentation
- Model interaction tests
- Event system for model changes

---

## Phase 3: Galaxy Generation System (Week 2)

### Objectives
- Port galaxy generation without Discord dependencies
- Create reusable generation modules

### Tasks

1. **Extract Generation Logic**
   - [ ] Copy `galaxy_generator.py` core logic
   - [ ] Remove Discord-specific code (embeds, interactions)
   - [ ] Create `GalaxyGenerator` class with progress callbacks

2. **Modular Generators**
   ```python
   generators/
   ├── galaxy_generator.py    # Main orchestrator
   ├── location_generator.py  # Location creation
   ├── corridor_generator.py  # Network generation
   ├── npc_generator.py      # NPC population
   └── history_generator.py  # Lore creation
   ```

3. **Generation Configuration**
   ```python
   class GalaxyConfig:
       - num_locations: int
       - location_distribution: Dict[str, float]
       - wealth_curve: str
       - corridor_density: float
       - npc_per_location: Tuple[int, int]
   ```

### Deliverables
- Standalone generation module
- Configuration system
- Generation progress reporting

### Verification
- Generate galaxies of various sizes
- Validate network connectivity
- Check distribution of location types

---

## Phase 4: Core Game Systems (Week 2-3)

### Objectives
- Implement game mechanics as independent systems
- Create clean APIs for each system

### Tasks

1. **Economy System** (`systems/economy_system.py`)
   - [ ] Job generation and lifecycle
   - [ ] Shop inventory management  
   - [ ] Price calculations based on supply/demand
   - [ ] Trade mechanics

2. **Travel System** (`systems/travel_system.py`)
   - [ ] Corridor navigation logic
   - [ ] Fuel consumption calculations
   - [ ] Travel time and encounters
   - [ ] Location arrival/departure events

3. **Time System** (`systems/time_system.py`)
   - [ ] Game calendar implementation
   - [ ] Time progression mechanics
   - [ ] Scheduled events (corridor shifts, etc.)
   - [ ] Time-based triggers

4. **Combat System** (`systems/combat_system.py`)
   - [ ] Turn management
   - [ ] Damage calculations
   - [ ] Combat state machine
   - [ ] Loot distribution

### Deliverables
- All system modules with APIs
- System interaction documentation
- Integration tests

---

## Phase 5: Game Engine Core (Week 3-4)

### Objectives
- Create central game engine that orchestrates all systems
- Implement save/load functionality

### Tasks

1. **Game Engine** (`game_engine.py`)
   ```python
   class GalaxyGameEngine:
       def __init__(self, db_path: str):
           self.db = DatabaseManager(db_path)
           self.economy = EconomySystem(self.db)
           self.travel = TravelSystem(self.db)
           self.time = TimeSystem(self.db)
           self.combat = CombatSystem(self.db)
       
       def tick(self):
           """Advance game state"""
       
       def process_action(self, action: GameAction):
           """Handle player/NPC actions"""
   ```

2. **Action System**
   ```python
   class GameAction:
       - action_type: str
       - actor_id: int
       - parameters: Dict
       - timestamp: datetime
   ```

3. **Save/Load System**
   - [ ] Export game state to JSON
   - [ ] Import saved games
   - [ ] Version compatibility
   - [ ] Auto-save functionality

### Deliverables
- Working game engine
- Action processing system
- Save/load functionality

---

## Phase 6: Interface Abstraction Layer (Week 4)

### Objectives
- Create clean separation between game logic and UI
- Define interface contracts

### Tasks

1. **Base Interface** (`interfaces/base_interface.py`)
   ```python
   class GameInterface(ABC):
       @abstractmethod
       def display_location(self, location: Location):
           pass
       
       @abstractmethod
       def display_character_stats(self, character: Character):
           pass
       
       @abstractmethod
       def get_user_action(self) -> GameAction:
           pass
   ```

2. **Event System**
   ```python
   class GameEventBus:
       - subscribe(event_type: str, handler: Callable)
       - publish(event: GameEvent)
       - Event types: location_update, combat_start, npc_message
   ```

3. **Terminal Interface** (`interfaces/terminal_ui.py`)
   - [ ] Basic text menus
   - [ ] Status display
   - [ ] Command parsing
   - [ ] Color support (optional)

### Deliverables
- Interface abstraction layer
- Working terminal UI
- Event documentation

---

## Phase 7: Testing & Migration (Week 5)

### Objectives
- Comprehensive testing suite
- Migration tools for existing Discord bot data

### Tasks

1. **Test Suite**
   - [ ] Unit tests for all models
   - [ ] Integration tests for systems
   - [ ] End-to-end game scenarios
   - [ ] Performance benchmarks

2. **Migration Tools**
   - [ ] Discord database → Core database converter
   - [ ] Character/location mapping
   - [ ] Progress preservation
   - [ ] Rollback capability

3. **Documentation**
   - [ ] API documentation
   - [ ] Integration guide
   - [ ] Migration guide
   - [ ] Example implementations

### Deliverables
- Complete test suite
- Migration tools
- Documentation package

---

## Phase 8: Advanced Features (Week 5-6)

### Objectives
- Add sophisticated game features
- Optimize performance

### Tasks

1. **Group/Party System**
   - [ ] Group formation mechanics
   - [ ] Shared resources
   - [ ] Group travel logic
   - [ ] Leadership system

2. **Quest System**
   - [ ] Quest generation
   - [ ] Progress tracking
   - [ ] Reward distribution
   - [ ] Quest chains

3. **Performance Optimization**
   - [ ] Database query optimization
   - [ ] Caching layer
   - [ ] Batch operations
   - [ ] Memory management

### Deliverables
- Advanced feature modules
- Performance metrics
- Optimization report

---

## Phase 9: GUI Options (Week 6+)

### Objectives
- Demonstrate UI flexibility
- Create reference implementations

### Tasks

1. **Web Interface** (Optional)
   ```python
   interfaces/web/
   ├── app.py          # Flask/FastAPI
   ├── static/         # JS/CSS
   ├── templates/      # HTML
   └── api/           # REST endpoints
   ```

2. **Desktop GUI** (Optional)
   ```python
   interfaces/desktop/
   ├── main_window.py  # PyQt/tkinter
   ├── widgets/        # Custom widgets
   └── resources/      # Images/sounds
   ```

3. **Discord Adapter** (Maintain compatibility)
   ```python
   interfaces/discord_adapter.py
   - Wraps core game engine
   - Translates Discord events → GameActions
   - Renders game state → Discord embeds
   ```

### Deliverables
- At least one GUI implementation
- Discord adapter for backward compatibility
- UI development guide

---

## Implementation Guidelines

### Code Standards
- **No Discord imports** in galaxy_core/
- **Type hints** for all public methods
- **Docstrings** for all classes/functions
- **Event-driven** architecture
- **Pure functions** where possible

### Testing Strategy
- Test each phase before moving forward
- Maintain both versions during transition
- Use feature flags for gradual rollout
- Keep Discord bot running throughout

### File Organization
```
galaxy-core/
├── galaxy_core/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── schema.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── location.py
│   │   ├── character.py
│   │   ├── npc.py
│   │   └── ship.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── galaxy.py
│   │   ├── location.py
│   │   └── npc.py
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── economy.py
│   │   ├── travel.py
│   │   ├── time.py
│   │   └── combat.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── terminal.py
│   └── game_engine.py
├── tests/
├── docs/
├── examples/
└── requirements.txt
```

### Success Metrics
- [ ] Core runs without Discord dependencies
- [ ] All game features preserved
- [ ] Performance equal or better
- [ ] Can run on phone/tablet/PC
- [ ] Multiple UI options demonstrated
- [ ] Existing players can migrate seamlessly

---

## Risk Mitigation

### Potential Issues & Solutions

1. **Data Migration Complexity**
   - Solution: Incremental migration with validation
   - Maintain mapping tables during transition

2. **Performance Degradation**
   - Solution: Profile before/after each phase
   - Implement caching early

3. **Feature Parity**
   - Solution: Create feature checklist from Discord bot
   - Test each feature in isolation

4. **Player Disruption**
   - Solution: Run both versions in parallel
   - Provide migration incentives

---

## Timeline Summary

- **Week 1**: Foundation & Models
- **Week 2**: Generation & Basic Systems  
- **Week 3**: Game Engine & Advanced Systems
- **Week 4**: Interface Layer & Terminal UI
- **Week 5**: Testing & Migration
- **Week 6+**: Advanced Features & GUIs

Total estimated time: 6-8 weeks for full refactor with basic GUI options.

---

## Next Steps

1. Set up new repository
2. Copy this plan to README.md
3. Create issue for each phase
4. Start with Phase 1: Database extraction
5. Set up CI/CD pipeline early

Remember: Each phase should produce working code that can be tested independently!