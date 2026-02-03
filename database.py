"""
Database management for Assistive Literacy Learning System
Handles all SQLite operations for student progress tracking
"""

import sqlite3
import time
from datetime import datetime
import config

class Database:
    def __init__(self, db_name=config.DATABASE_NAME):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Create and return a database connection"""
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Student progress table
        c.execute('''CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            module TEXT NOT NULL,
            score INTEGER,
            gems_earned INTEGER,
            time_spent REAL,
            timestamp TEXT
        )''')
        
        # Student stats table
        c.execute('''CREATE TABLE IF NOT EXISTS student_stats (
            student_id TEXT PRIMARY KEY,
            total_gems INTEGER DEFAULT 0,
            phonics_completed INTEGER DEFAULT 0,
            summit_completed INTEGER DEFAULT 0,
            story_completed INTEGER DEFAULT 0,
            summit_unlocked INTEGER DEFAULT 0,
            story_unlocked INTEGER DEFAULT 0
        )''')
        
        # Session tracking
        c.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            duration REAL
        )''')
        
        conn.commit()
        conn.close()
    
    def log_progress(self, student_id, module, score, gems_earned, time_spent):
        """Log student progress for a module"""
        conn = self.get_connection()
        c = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("""INSERT INTO progress (student_id, module, score, gems_earned, time_spent, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (student_id, module, score, gems_earned, time_spent, timestamp))
        
        # Update student stats
        self.update_student_stats(student_id, module, gems_earned)
        
        conn.commit()
        conn.close()
    
    def update_student_stats(self, student_id, module, gems_earned):
        """Update cumulative student statistics"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Check if student exists
        c.execute("SELECT * FROM student_stats WHERE student_id = ?", (student_id,))
        if not c.fetchone():
            c.execute("INSERT INTO student_stats (student_id) VALUES (?)", (student_id,))
        
        # Update gems
        c.execute("UPDATE student_stats SET total_gems = total_gems + ? WHERE student_id = ?",
                  (gems_earned, student_id))
        
        # Update module completion counts
        if module == 'Phonics Forest':
            c.execute("UPDATE student_stats SET phonics_completed = phonics_completed + 1 WHERE student_id = ?",
                      (student_id,))
        elif module == 'Sentence Summit':
            c.execute("UPDATE student_stats SET summit_completed = summit_completed + 1 WHERE student_id = ?",
                      (student_id,))
        elif module == 'Story Sea':
            c.execute("UPDATE student_stats SET story_completed = story_completed + 1 WHERE student_id = ?",
                      (student_id,))
        
        conn.commit()
        conn.close()
    
    def get_student_stats(self, student_id):
        """Get statistics for a specific student"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM student_stats WHERE student_id = ?", (student_id,))
        result = c.fetchone()
        
        conn.close()
        
        if result:
            return {
                'student_id': result[0],
                'total_gems': result[1],
                'phonics_completed': result[2],
                'summit_completed': result[3],
                'story_completed': result[4],
                'summit_unlocked': result[5],
                'story_unlocked': result[6]
            }
        else:
            # Return default stats
            return {
                'student_id': student_id,
                'total_gems': 0,
                'phonics_completed': 0,
                'summit_completed': 0,
                'story_completed': 0,
                'summit_unlocked': 0,
                'story_unlocked': 0
            }
    
    def unlock_zone(self, student_id, zone):
        """Unlock a zone for a student"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Ensure student exists
        c.execute("SELECT * FROM student_stats WHERE student_id = ?", (student_id,))
        if not c.fetchone():
            c.execute("INSERT INTO student_stats (student_id) VALUES (?)", (student_id,))
        
        if zone == 'summit':
            c.execute("UPDATE student_stats SET summit_unlocked = 1 WHERE student_id = ?", (student_id,))
        elif zone == 'story':
            c.execute("UPDATE student_stats SET story_unlocked = 1 WHERE student_id = ?", (student_id,))
        
        conn.commit()
        conn.close()
    
    def start_session(self, student_id):
        """Start a new session"""
        conn = self.get_connection()
        c = conn.cursor()
        
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO sessions (student_id, start_time) VALUES (?, ?)",
                  (student_id, start_time))
        session_id = c.lastrowid
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def end_session(self, session_id, duration):
        """End a session"""
        conn = self.get_connection()
        c = conn.cursor()
        
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("UPDATE sessions SET end_time = ?, duration = ? WHERE id = ?",
                  (end_time, duration, session_id))
        
        conn.commit()
        conn.close()
    
    def get_all_progress(self):
        """Get all progress records for teacher dashboard"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM progress ORDER BY timestamp DESC LIMIT 100")
        results = c.fetchall()
        
        conn.close()
        return results
    
    def get_student_progress(self, student_id):
        """Get progress records for a specific student"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM progress WHERE student_id = ? ORDER BY timestamp DESC",
                  (student_id,))
        results = c.fetchall()
        
        conn.close()
        return results
    
    def generate_report(self):
        """Generate a summary report for teachers"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Get all student stats
        c.execute("SELECT * FROM student_stats")
        students = c.fetchall()
        
        # Get total sessions
        c.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = c.fetchone()[0]
        
        # Get average time spent
        c.execute("SELECT AVG(time_spent) FROM progress")
        avg_time = c.fetchone()[0] or 0
        
        conn.close()
        
        report = {
            'students': students,
            'total_sessions': total_sessions,
            'avg_time_per_module': avg_time,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return report
