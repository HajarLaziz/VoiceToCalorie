# backend/database/db_manager.py
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

class DatabaseManager:
    def __init__(self, db_path: str = "voice_nutrition.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # Table des repas (avec source vocale)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                text_description TEXT NOT NULL,
                voice_text TEXT,
                calories REAL DEFAULT 0,
                proteines REAL DEFAULT 0,
                glucides REAL DEFAULT 0,
                lipides REAL DEFAULT 0,
                method TEXT DEFAULT 'spaCy',
                is_voice BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des performances
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT,
                extraction_time REAL,
                voice_duration REAL,
                foods_detected INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def save_meal(self, text: str, nutrition: Dict, method: str, is_voice: bool = False, voice_text: str = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO meals (date, text_description, voice_text, calories, proteines, glucides, lipides, method, is_voice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            text,
            voice_text or text,
            nutrition.get("calories", 0),
            nutrition.get("proteines", 0),
            nutrition.get("glucides", 0),
            nutrition.get("lipides", 0),
            method,
            1 if is_voice else 0
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def log_performance(self, method: str, extraction_time: float, voice_duration: float, foods_detected: int):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO performance (method, extraction_time, voice_duration, foods_detected)
            VALUES (?, ?, ?, ?)
        """, (method, extraction_time, voice_duration, foods_detected))
        self.conn.commit()
    
    def get_all_meals(self, limit: int = 100) -> List[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM meals ORDER BY date DESC LIMIT ?", (limit,))
        return cursor.fetchall()
    
    def get_daily_totals(self, days: int = 30) -> List[Tuple]:
        cursor = self.conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute("""
            SELECT date(date), SUM(calories), SUM(proteines), SUM(glucides), SUM(lipides)
            FROM meals WHERE date >= ? GROUP BY date(date) ORDER BY date(date)
        """, (cutoff,))
        return cursor.fetchall()
    
    def get_statistics(self) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM meals")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(calories), AVG(proteines), AVG(glucides), AVG(lipides) FROM meals")
        avg = cursor.fetchone()
        cursor.execute("SELECT method, COUNT(*) FROM meals GROUP BY method")
        methods = dict(cursor.fetchall())
        cursor.execute("SELECT COUNT(*) FROM meals WHERE is_voice = 1")
        voice_count = cursor.fetchone()[0]
        
        return {
            "total_meals": total,
            "voice_meals": voice_count,
            "text_meals": total - voice_count,
            "avg_calories": avg[0] if avg[0] else 0,
            "avg_proteines": avg[1] if avg[1] else 0,
            "avg_glucides": avg[2] if avg[2] else 0,
            "avg_lipides": avg[3] if avg[3] else 0,
            "methods": methods
        }
    
    def delete_all(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM meals")
        cursor.execute("DELETE FROM performance")
        self.conn.commit()
    
    def close(self):
        self.conn.close()