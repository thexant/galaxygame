"""
galaxy_core/database/db_manager.py
Core database management without Discord dependencies
"""

import sqlite3
import os
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path: str = "galaxy_game.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self._connection = None
        self._ensure_connection()
        self._init_database()
    
    def _ensure_connection(self):
        """Ensure database connection is active"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=NORMAL")
    
    def execute_query(self, query: str, params: Tuple = None, fetch: str = None) -> Any:
        """Execute a database query"""
        self._ensure_connection()
        cursor = self._connection.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'all':
                return cursor.fetchall()
            else:
                self._connection.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def begin_transaction(self) -> sqlite3.Connection:
        """Begin a transaction"""
        conn = sqlite3.connect(self.db_path)
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                has_gates BOOLEAN DEFAULT 0,
                last_shift TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                next_shift TIMESTAMP,
                FOREIGN KEY (origin_location) REFERENCES locations (location_id),
                FOREIGN KEY (destination_location) REFERENCES locations (location_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS static_npcs (
                npc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                occupation TEXT,
                personality TEXT,
                trade_specialty TEXT,
                alignment TEXT DEFAULT 'neutral',
                hp INTEGER DEFAULT 100,
                max_hp INTEGER DEFAULT 100,
                combat_rating INTEGER DEFAULT 5,
                credits INTEGER DEFAULT 0,
                is_alive BOOLEAN DEFAULT 1,
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
                alignment TEXT DEFAULT 'neutral',
                hp INTEGER DEFAULT 100,
                max_hp INTEGER DEFAULT 100,
                combat_rating INTEGER DEFAULT 5,
                credits INTEGER DEFAULT 0,
                is_alive BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_location) REFERENCES locations (location_id),
                FOREIGN KEY (destination_location) REFERENCES locations (location_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS characters (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                current_location INTEGER NOT NULL,
                credits INTEGER DEFAULT 100,
                fuel INTEGER DEFAULT 100,
                max_fuel INTEGER DEFAULT 100,
                health INTEGER DEFAULT 100,
                max_health INTEGER DEFAULT 100,
                is_alive BOOLEAN DEFAULT 1,
                alignment TEXT DEFAULT 'neutral',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_location) REFERENCES locations (location_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS ships (
                ship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                hull_points INTEGER DEFAULT 100,
                max_hull_points INTEGER DEFAULT 100,
                cargo_capacity INTEGER DEFAULT 50,
                fuel_efficiency REAL DEFAULT 1.0,
                speed_modifier REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES characters (user_id)
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
                FOREIGN KEY (location_id) REFERENCES locations (location_id),
                FOREIGN KEY (taken_by) REFERENCES characters (user_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS galactic_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER,
                event_title TEXT NOT NULL,
                event_description TEXT NOT NULL,
                historical_figure TEXT,
                event_date TEXT NOT NULL,
                event_type TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (location_id) REFERENCES locations (location_id)
            )'''
        ]
        
        for table in tables:
            try:
                self.execute_query(table)
            except sqlite3.OperationalError as e:
                if "already exists" not in str(e):
                    raise
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None