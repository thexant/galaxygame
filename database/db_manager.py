"""
galaxy_core/database/db_manager.py
Core database management without Discord dependencies
"""

import sqlite3
import os
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
import json
import shutil
from contextlib import contextmanager


class DatabaseManager:
    """
    Core database manager for Galaxy game
    Handles all database operations without any Discord dependencies
    """
    
    def __init__(self, db_path: str = "galaxy.db", connection_pool_size: int = 5):
        """
        Initialize database manager
        
        Args:
            db_path: Path to the SQLite database file
            connection_pool_size: Number of connections to maintain in pool
        """
        self.db_path = db_path
        self.pool_size = connection_pool_size
        self._version = "1.0.0"
        
        # Initialize database
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Tuple = (), fetch: Optional[str] = None) -> Any:
        """
        Execute a database query
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            fetch: 'one', 'all', or None
            
        Returns:
            Query results based on fetch parameter
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'all':
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.lastrowid
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute multiple queries with different parameters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the database
        
        Returns:
            Path to the backup file
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"galaxy_backup_{timestamp}.db"
        
        shutil.copy2(self.db_path, backup_path)
        return backup_path
    
    def restore_database(self, backup_path: str) -> None:
        """Restore database from a backup"""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        shutil.copy2(backup_path, self.db_path)
    
    def get_database_version(self) -> str:
        """Get the current database schema version"""
        result = self.execute_query(
            "SELECT version FROM database_version ORDER BY applied_at DESC LIMIT 1",
            fetch='one'
        )
        return result[0] if result else "0.0.0"
    
    def set_database_version(self, version: str) -> None:
        """Set the database schema version"""
        self.execute_query(
            "INSERT INTO database_version (version) VALUES (?)",
            (version,)
        )
    
    def begin_transaction(self):
        """Start a new transaction and return connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN")
        return conn
    
    def commit_transaction(self, conn: sqlite3.Connection):
        """Commit a transaction"""
        conn.commit()
        conn.close()
    
    def rollback_transaction(self, conn: sqlite3.Connection):
        """Rollback a transaction"""
        conn.rollback()
        conn.close()
    
    def _init_database(self):
        """Initialize database schema"""
        # Core tables only - no Discord-specific fields
        tables = [
            '''CREATE TABLE IF NOT EXISTS galaxy_info (
                galaxy_id INTEGER PRIMARY KEY CHECK (galaxy_id = 1),
                galaxy_name TEXT NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                game_start_date TEXT NOT NULL,
                hours_per_day REAL DEFAULT 24.0,
                days_per_year INTEGER DEFAULT 365
            )''',
            
            '''CREATE TABLE IF NOT EXISTS locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location_type TEXT NOT NULL,
                description TEXT,
                wealth_level INTEGER DEFAULT 5,
                population INTEGER DEFAULT 100,
                x_coord REAL DEFAULT 0,
                y_coord REAL DEFAULT 0,
                system_name TEXT,
                has_jobs BOOLEAN DEFAULT 1,
                has_shops BOOLEAN DEFAULT 1,
                has_medical BOOLEAN DEFAULT 1,
                has_repairs BOOLEAN DEFAULT 1,
                has_fuel BOOLEAN DEFAULT 1,
                has_upgrades BOOLEAN DEFAULT 0,
                has_black_market BOOLEAN DEFAULT 0,
                has_federal_supplies BOOLEAN DEFAULT 0,
                has_shipyard BOOLEAN DEFAULT 0,
                is_derelict BOOLEAN DEFAULT 0,
                gate_status TEXT DEFAULT 'active',
                establishment_date TEXT,
                faction TEXT DEFAULT 'Independent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                location_ref TEXT UNIQUE
            )''',
            
            '''CREATE TABLE IF NOT EXISTS corridors (
                corridor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                origin_location INTEGER NOT NULL,
                destination_location INTEGER NOT NULL,
                travel_time INTEGER DEFAULT 300,
                fuel_cost INTEGER DEFAULT 20,
                danger_level INTEGER DEFAULT 3,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (origin_location) REFERENCES locations (location_id),
                FOREIGN KEY (destination_location) REFERENCES locations (location_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS characters (
                character_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_ref TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                current_location INTEGER,
                credits INTEGER DEFAULT 1000,
                ship_fuel INTEGER DEFAULT 50,
                ship_hull INTEGER DEFAULT 100,
                max_ship_hull INTEGER DEFAULT 100,
                karma INTEGER DEFAULT 0,
                wanted_level INTEGER DEFAULT 0,
                location_status TEXT DEFAULT 'docked',
                alignment TEXT DEFAULT 'neutral' CHECK(alignment IN ('loyal', 'neutral', 'bandit')),
                is_alive BOOLEAN DEFAULT 1,
                death_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_location) REFERENCES locations (location_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS ships (
                ship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                ship_type TEXT NOT NULL,
                cargo_capacity INTEGER DEFAULT 100,
                fuel_capacity INTEGER DEFAULT 100,
                hull_points INTEGER DEFAULT 100,
                max_hull_points INTEGER DEFAULT 100,
                engine_level INTEGER DEFAULT 1,
                shield_level INTEGER DEFAULT 0,
                weapon_level INTEGER DEFAULT 1,
                interior_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES characters (character_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS inventory (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                description TEXT,
                value INTEGER DEFAULT 0,
                metadata TEXT,
                FOREIGN KEY (owner_id) REFERENCES characters (character_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                reward_money INTEGER DEFAULT 100,
                required_skill TEXT,
                min_skill_level INTEGER DEFAULT 0,
                danger_level INTEGER DEFAULT 1,
                duration_minutes INTEGER DEFAULT 60,
                is_taken BOOLEAN DEFAULT 0,
                taken_by INTEGER,
                taken_at TIMESTAMP,
                expires_at TIMESTAMP,
                job_status TEXT DEFAULT 'available',
                destination_location_id INTEGER,
                karma_change INTEGER DEFAULT 0,
                FOREIGN KEY (location_id) REFERENCES locations (location_id),
                FOREIGN KEY (destination_location_id) REFERENCES locations (location_id),
                FOREIGN KEY (taken_by) REFERENCES characters (character_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                leader_id INTEGER NOT NULL,
                current_location INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (leader_id) REFERENCES characters (character_id),
                FOREIGN KEY (current_location) REFERENCES locations (location_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS group_members (
                membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                character_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups (group_id),
                FOREIGN KEY (character_id) REFERENCES characters (character_id),
                UNIQUE(group_id, character_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS static_npcs (
                npc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                occupation TEXT,
                personality TEXT,
                trade_specialty TEXT,
                alignment TEXT DEFAULT 'neutral' CHECK(alignment IN ('loyal', 'neutral', 'bandit')),
                hp INTEGER DEFAULT 100,
                max_hp INTEGER DEFAULT 100,
                combat_rating INTEGER DEFAULT 5,
                is_alive BOOLEAN DEFAULT 1,
                credits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (location_id) REFERENCES locations (location_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS dynamic_npcs (
                npc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                callsign TEXT UNIQUE NOT NULL,
                age INTEGER NOT NULL,
                ship_name TEXT NOT NULL,
                ship_type TEXT NOT NULL,
                current_location INTEGER,
                destination_location INTEGER,
                travel_start_time TIMESTAMP,
                travel_duration INTEGER,
                alignment TEXT DEFAULT 'neutral' CHECK(alignment IN ('loyal', 'neutral', 'bandit')),
                hp INTEGER DEFAULT 100,
                max_hp INTEGER DEFAULT 100,
                combat_rating INTEGER DEFAULT 5,
                is_alive BOOLEAN DEFAULT 1,
                credits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_location) REFERENCES locations (location_id),
                FOREIGN KEY (destination_location) REFERENCES locations (location_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS database_version (
                version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        ]
        
        # Execute all table creation queries
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table_query in tables:
                cursor.execute(table_query)
            conn.commit()
        
        # Set initial version if not exists
        if self.get_database_version() == "0.0.0":
            self.set_database_version(self._version)
    
    def close(self):
        """Close database connections (placeholder for connection pool)"""
        pass