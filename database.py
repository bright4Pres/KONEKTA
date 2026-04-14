# database file
# handles all the saving and loading stuff

import sqlite3
import json
from datetime import datetime
import config

# dev footnotes / db brain dump:
# - this is the single source for writes, pls keep it boring + predictable.
# - sqlite lock issues happen if we nest writes on separate conns; keep txn flow clean.
# - custom_questions is now the content source for games (no config hardcode fallback).
# - report methods are teacher-facing, so shape changes there can break dashboard rendering.
# - if leaderboard looks wrong, inspect record_game_result first.

class Database:
    """sqlite helper wrapper.

    Personal notes:
    - All SQL is centralized here so state files stay UI-focused.
    - Keep methods tiny-ish and explicit; hidden side effects get messy fast.
    - Yes it's simple, and that's on purpose.
    """
    def __init__(self, db_name=config.DATABASE_NAME):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """connect to db"""
        return sqlite3.connect(self.db_name, timeout=10)
    
    def init_database(self):
        """make the tables if they dont exist"""
        # schema bootstrapping runs every launch; CREATE IF NOT EXISTS keeps it cheap.
        conn = self.get_connection()
        c = conn.cursor()
        
        # table for storing scores and stuff
        c.execute('''CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            module TEXT NOT NULL,
            score INTEGER,
            gems_earned INTEGER,
            time_spent REAL,
            timestamp TEXT
        )''')
        
        # student info table
        c.execute('''CREATE TABLE IF NOT EXISTS student_stats (
            student_id TEXT PRIMARY KEY,
            total_gems INTEGER DEFAULT 0,
            phonics_completed INTEGER DEFAULT 0,
            summit_completed INTEGER DEFAULT 0,
            story_completed INTEGER DEFAULT 0,
            summit_unlocked INTEGER DEFAULT 0,
            story_unlocked INTEGER DEFAULT 0
        )''')

        # profile registry (used by menu profile picker + teacher account manager)
        c.execute('''CREATE TABLE IF NOT EXISTS student_profiles (
            student_id TEXT PRIMARY KEY,
            created_at TEXT
        )''')
        
        # for tracking how long they play
        c.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            duration REAL
        )''')

        # arcade leaderboard entries (one row per score submission)
        c.execute('''CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            module TEXT NOT NULL,
            score INTEGER NOT NULL,
            max_score INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            language TEXT,
            timestamp TEXT
        )''')

        # teacher-made question bank (generic shape for all games)
        c.execute('''CREATE TABLE IF NOT EXISTS custom_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_key TEXT NOT NULL,
            language TEXT NOT NULL,
            difficulty_mode TEXT NOT NULL DEFAULT 'General',
            prompt_text TEXT,
            question_text TEXT NOT NULL,
            choices_json TEXT NOT NULL,
            correct_index INTEGER NOT NULL,
            created_at TEXT
        )''')

        # teacher-managed difficulty labels (ex: Grade 1, Intermediate, etc.)
        c.execute('''CREATE TABLE IF NOT EXISTS difficulty_modes (
            mode_name TEXT PRIMARY KEY,
            created_at TEXT
        )''')

        # active difficulty per game+language slot, set in Teacher Mode only
        c.execute('''CREATE TABLE IF NOT EXISTS teacher_difficulty_slots (
            game_key TEXT NOT NULL,
            language TEXT NOT NULL,
            difficulty_mode TEXT NOT NULL,
            updated_at TEXT,
            PRIMARY KEY (game_key, language)
        )''')

        # keep default profile + backfill profile table from existing activity rows.
        self._ensure_profile_cursor(c, config.DEFAULT_STUDENT_ID)
        self._sync_profiles_cursor(c)
        self._ensure_question_difficulty_schema(c)
        
        conn.commit()
        conn.close()

    def _ensure_profile_cursor(self, cursor, student_id):
        """insert profile if missing using existing transaction"""
        sid = str(student_id).strip()
        if not sid:
            return
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            """INSERT OR IGNORE INTO student_profiles (student_id, created_at)
               VALUES (?, ?)""",
            (sid, created_at)
        )

    def _sync_profiles_cursor(self, cursor):
        """migrate profile ids seen in activity tables into student_profiles"""
        cursor.execute(
            """SELECT DISTINCT student_id FROM (
                   SELECT student_id FROM student_stats
                   UNION SELECT student_id FROM progress
                   UNION SELECT student_id FROM sessions
                   UNION SELECT student_id FROM leaderboard
               )
               WHERE student_id IS NOT NULL AND TRIM(student_id) <> ''"""
        )
        for row in cursor.fetchall():
            self._ensure_profile_cursor(cursor, row[0])

    @staticmethod
    def _normalize_difficulty_mode(mode_name):
        """normalize and validate teacher difficulty labels"""
        clean = ' '.join(str(mode_name).strip().split())
        if not clean:
            raise ValueError('Difficulty mode cannot be blank.')
        return clean[:40]

    @staticmethod
    def _has_column(cursor, table_name, column_name):
        """check if a sqlite table already has a column"""
        cursor.execute(f"PRAGMA table_info({table_name})")
        return any(row[1] == column_name for row in cursor.fetchall())

    def _ensure_difficulty_mode_cursor(self, cursor, mode_name):
        """insert a difficulty mode if missing using existing transaction"""
        mode = self._normalize_difficulty_mode(mode_name)
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            """INSERT OR IGNORE INTO difficulty_modes (mode_name, created_at)
               VALUES (?, ?)""",
            (mode, created_at)
        )
        return mode

    def _ensure_any_difficulty_mode_cursor(self, cursor):
        """guarantee at least one available difficulty mode"""
        cursor.execute(
            """SELECT mode_name
               FROM difficulty_modes
               ORDER BY mode_name COLLATE NOCASE
               LIMIT 1"""
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        return self._ensure_difficulty_mode_cursor(cursor, 'General')

    def _ensure_question_difficulty_schema(self, cursor):
        """lightweight migration path for difficulty-aware question bank"""
        if not self._has_column(cursor, 'custom_questions', 'difficulty_mode'):
            cursor.execute(
                """ALTER TABLE custom_questions
                   ADD COLUMN difficulty_mode TEXT NOT NULL DEFAULT 'General'"""
            )

        fallback_mode = self._ensure_any_difficulty_mode_cursor(cursor)

        cursor.execute(
            """UPDATE custom_questions
               SET difficulty_mode = ?
               WHERE difficulty_mode IS NULL OR TRIM(difficulty_mode) = ''""",
            (fallback_mode,)
        )

        cursor.execute(
            """SELECT DISTINCT difficulty_mode
               FROM custom_questions
               WHERE difficulty_mode IS NOT NULL AND TRIM(difficulty_mode) <> ''"""
        )
        for row in cursor.fetchall():
            self._ensure_difficulty_mode_cursor(cursor, row[0])

        now_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            """UPDATE teacher_difficulty_slots
               SET difficulty_mode = ?, updated_at = ?
               WHERE difficulty_mode IS NULL OR TRIM(difficulty_mode) = ''""",
            (fallback_mode, now_stamp)
        )

        cursor.execute("SELECT game_key, language, difficulty_mode FROM teacher_difficulty_slots")
        for game_key, language, difficulty_mode in cursor.fetchall():
            cursor.execute(
                "SELECT 1 FROM difficulty_modes WHERE mode_name = ? LIMIT 1",
                (difficulty_mode,)
            )
            if not cursor.fetchone():
                cursor.execute(
                    """UPDATE teacher_difficulty_slots
                       SET difficulty_mode = ?, updated_at = ?
                       WHERE game_key = ? AND language = ?""",
                    (fallback_mode, now_stamp, game_key, language)
                )
    
    def log_progress(self, student_id, module, score, gems_earned, time_spent):
        """save what the student did"""
        # write progress + stats in one transaction so sqlite doesnt randomly lock up.
        conn = self.get_connection()
        c = conn.cursor()

        self._ensure_profile_cursor(c, student_id)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("""INSERT INTO progress (student_id, module, score, gems_earned, time_spent, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (student_id, module, score, gems_earned, time_spent, timestamp))
        
        # update stats in the same transaction to avoid sqlite write locks
        self._update_student_stats_cursor(c, student_id, module, gems_earned)
        
        conn.commit()
        conn.close()

    def _update_student_stats_cursor(self, cursor, student_id, module, gems_earned):
        """update student stats using an existing cursor/transaction"""
        # this method intentionally does not open/close its own connection.
        # add them if they're new
        cursor.execute("SELECT * FROM student_stats WHERE student_id = ?", (student_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO student_stats (student_id) VALUES (?)", (student_id,))

        # add gems
        cursor.execute(
            "UPDATE student_stats SET total_gems = total_gems + ? WHERE student_id = ?",
            (gems_earned, student_id)
        )

        # module completion counters
        if module in ('Phonics Forest', 'Barangay Captain Simulator'):
            cursor.execute(
                "UPDATE student_stats SET phonics_completed = phonics_completed + 1 WHERE student_id = ?",
                (student_id,)
            )
        elif module in ('Sentence Summit', 'Recipe Game'):
            cursor.execute(
                "UPDATE student_stats SET summit_completed = summit_completed + 1 WHERE student_id = ?",
                (student_id,)
            )
        elif module in ('Story Sea', 'Word Match Game'):
            cursor.execute(
                "UPDATE student_stats SET story_completed = story_completed + 1 WHERE student_id = ?",
                (student_id,)
            )

    def update_student_stats(self, student_id, module, gems_earned):
        """update the totals for the student"""
        conn = self.get_connection()
        c = conn.cursor()
        self._update_student_stats_cursor(c, student_id, module, gems_earned)
        
        conn.commit()
        conn.close()
    
    def get_student_stats(self, student_id):
        """get the students info"""
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
            # return all zeros if student doesnt exist yet
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
        """unlock a zone for the student"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # make sure student is in db first
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
        """start tracking a session"""
        conn = self.get_connection()
        c = conn.cursor()

        self._ensure_profile_cursor(c, student_id)
        
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO sessions (student_id, start_time) VALUES (?, ?)",
                  (student_id, start_time))
        session_id = c.lastrowid
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def end_session(self, session_id, duration):
        """stop tracking the session"""
        conn = self.get_connection()
        c = conn.cursor()
        
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("UPDATE sessions SET end_time = ?, duration = ? WHERE id = ?",
                  (end_time, duration, session_id))
        
        conn.commit()
        conn.close()
    
    def get_all_progress(self):
        """get all the progress for the teacher dashboard"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM progress ORDER BY timestamp DESC LIMIT 100")
        results = c.fetchall()
        
        conn.close()
        return results
    
    def get_student_progress(self, student_id):
        """get one students progress"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM progress WHERE student_id = ? ORDER BY timestamp DESC",
                  (student_id,))
        results = c.fetchall()
        
        conn.close()
        return results

    # --- arcade score + leaderboard ---

    # scoreboard pipeline note:
    # game states call record_game_result -> this writes progress + leaderboard entry.
    # keep this glue path stable or post-game flow will feel broken to users.

    def record_game_result(self, student_id, module, score, max_score, language, time_spent):
        """save one completed game to both progress + leaderboard"""
        max_score = max(1, int(max_score))
        score = max(0, min(int(score), max_score))
        ratio = score / max_score
        gems_earned = int(round(ratio * 5))

        self.log_progress(student_id, module, score, gems_earned, float(time_spent))
        self.log_leaderboard_entry(student_id, module, score, max_score, language)

    def log_leaderboard_entry(self, student_id, module, score, max_score, language):
        """save a leaderboard entry"""
        conn = self.get_connection()
        c = conn.cursor()

        self._ensure_profile_cursor(c, student_id)

        max_score = max(1, int(max_score))
        score = max(0, min(int(score), max_score))
        accuracy = round((score / max_score) * 100.0, 2)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        c.execute(
            """INSERT INTO leaderboard
               (student_id, module, score, max_score, accuracy, language, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (student_id, module, score, max_score, accuracy, language, timestamp)
        )

        conn.commit()
        conn.close()

    def create_profile(self, student_id):
        """create a profile id if it doesnt exist"""
        sid = str(student_id).strip()
        if not sid:
            raise ValueError('Profile id cannot be blank.')

        conn = self.get_connection()
        c = conn.cursor()
        self._ensure_profile_cursor(c, sid)
        c.execute("INSERT OR IGNORE INTO student_stats (student_id) VALUES (?)", (sid,))
        conn.commit()
        conn.close()
        return sid

    def get_profiles(self):
        """list all known profiles"""
        conn = self.get_connection()
        c = conn.cursor()
        self._ensure_profile_cursor(c, config.DEFAULT_STUDENT_ID)
        self._sync_profiles_cursor(c)
        conn.commit()

        c.execute(
            """SELECT student_id, created_at
               FROM student_profiles
               ORDER BY student_id COLLATE NOCASE"""
        )
        rows = c.fetchall()
        conn.close()

        return [
            {
                'student_id': row[0],
                'created_at': row[1] or '',
            }
            for row in rows
        ]

    def rename_profile(self, old_student_id, new_student_id):
        """rename a profile id across all related tables"""
        old_id = str(old_student_id).strip()
        new_id = str(new_student_id).strip()

        if not old_id:
            raise ValueError('Old profile id is required.')
        if not new_id:
            raise ValueError('New profile id is required.')
        if old_id == new_id:
            return new_id

        conn = self.get_connection()
        c = conn.cursor()

        c.execute(
            """SELECT 1 FROM (
                   SELECT student_id FROM student_profiles
                   UNION SELECT student_id FROM student_stats
                   UNION SELECT student_id FROM progress
                   UNION SELECT student_id FROM sessions
                   UNION SELECT student_id FROM leaderboard
               ) WHERE student_id = ? LIMIT 1""",
            (new_id,)
        )
        if c.fetchone():
            conn.close()
            raise ValueError('That profile id already exists.')

        c.execute("UPDATE student_profiles SET student_id = ? WHERE student_id = ?", (new_id, old_id))
        if c.rowcount == 0:
            self._ensure_profile_cursor(c, new_id)

        c.execute("UPDATE student_stats SET student_id = ? WHERE student_id = ?", (new_id, old_id))
        c.execute("UPDATE progress SET student_id = ? WHERE student_id = ?", (new_id, old_id))
        c.execute("UPDATE sessions SET student_id = ? WHERE student_id = ?", (new_id, old_id))
        c.execute("UPDATE leaderboard SET student_id = ? WHERE student_id = ?", (new_id, old_id))

        conn.commit()
        conn.close()
        return new_id

    def delete_profile(self, student_id):
        """delete a profile and all associated activity rows"""
        sid = str(student_id).strip()
        if not sid:
            raise ValueError('Profile id is required.')
        if sid == config.DEFAULT_STUDENT_ID:
            raise ValueError('Cannot delete the default profile.')

        conn = self.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM leaderboard WHERE student_id = ?", (sid,))
        c.execute("DELETE FROM progress WHERE student_id = ?", (sid,))
        c.execute("DELETE FROM sessions WHERE student_id = ?", (sid,))
        c.execute("DELETE FROM student_stats WHERE student_id = ?", (sid,))
        c.execute("DELETE FROM student_profiles WHERE student_id = ?", (sid,))
        conn.commit()
        conn.close()

    def get_student_profiles_with_metrics(self):
        """profile list with leaderboard-focused metrics for teacher kiosk"""
        conn = self.get_connection()
        c = conn.cursor()
        self._ensure_profile_cursor(c, config.DEFAULT_STUDENT_ID)
        self._sync_profiles_cursor(c)
        conn.commit()

        c.execute(
            """SELECT p.student_id,
                      COUNT(l.id) AS games_played,
                      AVG(l.accuracy) AS avg_accuracy,
                      MAX(l.accuracy) AS best_accuracy,
                      SUM(l.score) AS total_points,
                      MAX(l.timestamp) AS last_played,
                      COALESCE(s.total_gems, 0) AS total_gems
               FROM student_profiles p
               LEFT JOIN leaderboard l ON l.student_id = p.student_id
               LEFT JOIN student_stats s ON s.student_id = p.student_id
               GROUP BY p.student_id, s.total_gems
               ORDER BY games_played DESC,
                        avg_accuracy DESC,
                        p.student_id COLLATE NOCASE"""
        )
        rows = c.fetchall()
        conn.close()

        return [
            {
                'student_id': row[0],
                'games_played': row[1] or 0,
                'avg_accuracy': round(row[2] or 0.0, 1),
                'best_accuracy': round(row[3] or 0.0, 1),
                'total_points': row[4] or 0,
                'last_played': row[5] or '-',
                'total_gems': row[6] or 0,
            }
            for row in rows
        ]

    def get_student_module_performance(self, student_id):
        """module-by-module stats for one student"""
        sid = str(student_id).strip()
        if not sid:
            return []

        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """SELECT module,
                      COUNT(*) AS plays,
                      AVG(accuracy) AS avg_accuracy,
                      MAX(accuracy) AS best_accuracy,
                      SUM(score) AS total_points
               FROM leaderboard
               WHERE student_id = ?
               GROUP BY module
               ORDER BY avg_accuracy DESC, total_points DESC""",
            (sid,)
        )
        rows = c.fetchall()
        conn.close()

        return [
            {
                'module': row[0],
                'plays': row[1],
                'avg_accuracy': round(row[2] or 0.0, 1),
                'best_accuracy': round(row[3] or 0.0, 1),
                'total_points': row[4] or 0,
            }
            for row in rows
        ]

    def get_student_recent_runs(self, student_id, limit=12):
        """recent leaderboard attempts for one student"""
        sid = str(student_id).strip()
        if not sid:
            return []

        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """SELECT module, score, max_score, accuracy, language, timestamp
               FROM leaderboard
               WHERE student_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (sid, int(limit))
        )
        rows = c.fetchall()
        conn.close()

        return [
            {
                'module': row[0],
                'score': row[1],
                'max_score': row[2],
                'accuracy': row[3],
                'language': row[4],
                'timestamp': row[5],
            }
            for row in rows
        ]

    def get_leaderboard(self, limit=20):
        """top scores for the arcade board"""
        conn = self.get_connection()
        c = conn.cursor()

        c.execute(
            """SELECT student_id, module, score, max_score, accuracy, language, timestamp
               FROM leaderboard
               ORDER BY accuracy DESC, score DESC, timestamp ASC
               LIMIT ?""",
            (int(limit),)
        )
        rows = c.fetchall()
        conn.close()

        return [
            {
                'student_id': r[0],
                'module': r[1],
                'score': r[2],
                'max_score': r[3],
                'accuracy': r[4],
                'language': r[5],
                'timestamp': r[6],
            }
            for r in rows
        ]

    def get_teacher_metrics(self):
        """teacher analytics from real student runs"""
        conn = self.get_connection()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = c.fetchone()[0]

        c.execute("SELECT COUNT(DISTINCT student_id) FROM leaderboard")
        active_students = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM leaderboard")
        total_logged_games = c.fetchone()[0]

        c.execute("SELECT AVG(accuracy) FROM leaderboard")
        avg_accuracy = c.fetchone()[0] or 0.0

        c.execute(
            """SELECT module,
                      COUNT(*) AS plays,
                      COUNT(DISTINCT student_id) AS unique_students,
                      AVG(accuracy) AS avg_accuracy,
                      MAX(accuracy) AS best_accuracy
               FROM leaderboard
               GROUP BY module
               ORDER BY avg_accuracy DESC"""
        )
        module_rows = c.fetchall()

        c.execute(
            """SELECT student_id,
                      COUNT(*) AS games_played,
                      AVG(accuracy) AS avg_accuracy,
                      MAX(accuracy) AS best_accuracy,
                      SUM(score) AS total_points
               FROM leaderboard
               GROUP BY student_id
               ORDER BY avg_accuracy DESC, total_points DESC, games_played DESC"""
        )
        student_rows = c.fetchall()

        conn.close()

        return {
            'total_sessions': total_sessions,
            'active_students': active_students,
            'total_logged_games': total_logged_games,
            'avg_accuracy': round(avg_accuracy, 1),
            'module_breakdown': [
                {
                    'module': r[0],
                    'plays': r[1],
                    'unique_students': r[2],
                    'avg_accuracy': round(r[3] or 0.0, 1),
                    'best_accuracy': round(r[4] or 0.0, 1),
                }
                for r in module_rows
            ],
            'student_breakdown': [
                {
                    'student_id': r[0],
                    'games_played': r[1],
                    'avg_accuracy': round(r[2] or 0.0, 1),
                    'best_accuracy': round(r[3] or 0.0, 1),
                    'total_points': r[4] or 0,
                }
                for r in student_rows
            ]
        }

    # --- teacher difficulty mode controls ---

    def get_difficulty_modes(self):
        """list teacher-defined difficulty labels"""
        conn = self.get_connection()
        c = conn.cursor()
        self._ensure_any_difficulty_mode_cursor(c)
        conn.commit()

        c.execute(
            """SELECT mode_name
               FROM difficulty_modes
               ORDER BY mode_name COLLATE NOCASE"""
        )
        rows = c.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def create_difficulty_mode(self, mode_name):
        """create one new teacher difficulty mode"""
        mode = self._normalize_difficulty_mode(mode_name)

        conn = self.get_connection()
        c = conn.cursor()

        c.execute(
            """SELECT mode_name
               FROM difficulty_modes
               WHERE LOWER(mode_name) = LOWER(?)
               LIMIT 1""",
            (mode,)
        )
        row = c.fetchone()
        if row:
            conn.close()
            raise ValueError('That difficulty mode already exists.')

        created = self._ensure_difficulty_mode_cursor(c, mode)
        conn.commit()
        conn.close()
        return created

    def rename_difficulty_mode(self, old_mode_name, new_mode_name):
        """rename a difficulty mode and move linked question rows"""
        old_mode = self._normalize_difficulty_mode(old_mode_name)
        new_mode = self._normalize_difficulty_mode(new_mode_name)
        if old_mode == new_mode:
            return new_mode

        conn = self.get_connection()
        c = conn.cursor()

        c.execute(
            """SELECT mode_name
               FROM difficulty_modes
               WHERE LOWER(mode_name) = LOWER(?)
               LIMIT 1""",
            (old_mode,)
        )
        source_row = c.fetchone()
        if not source_row:
            conn.close()
            raise ValueError('Difficulty mode not found.')
        source_name = source_row[0]

        c.execute(
            """SELECT mode_name
               FROM difficulty_modes
               WHERE LOWER(mode_name) = LOWER(?)
               LIMIT 1""",
            (new_mode,)
        )
        target_row = c.fetchone()
        if target_row and target_row[0] != source_name:
            conn.close()
            raise ValueError('That difficulty mode already exists.')

        c.execute(
            "UPDATE difficulty_modes SET mode_name = ? WHERE mode_name = ?",
            (new_mode, source_name)
        )
        c.execute(
            "UPDATE custom_questions SET difficulty_mode = ? WHERE difficulty_mode = ?",
            (new_mode, source_name)
        )
        c.execute(
            "UPDATE teacher_difficulty_slots SET difficulty_mode = ? WHERE difficulty_mode = ?",
            (new_mode, source_name)
        )

        conn.commit()
        conn.close()
        return new_mode

    def get_selected_difficulty_mode(self, game_key, language):
        """active difficulty for a game/language pair"""
        gk = str(game_key).strip()
        lang = str(language).strip()

        conn = self.get_connection()
        c = conn.cursor()
        fallback_mode = self._ensure_any_difficulty_mode_cursor(c)

        c.execute(
            """SELECT difficulty_mode
               FROM teacher_difficulty_slots
               WHERE game_key = ? AND language = ?""",
            (gk, lang)
        )
        row = c.fetchone()
        selected = row[0] if row and row[0] else fallback_mode

        c.execute(
            "SELECT 1 FROM difficulty_modes WHERE mode_name = ? LIMIT 1",
            (selected,)
        )
        if not c.fetchone():
            selected = fallback_mode

        now_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute(
            """INSERT INTO teacher_difficulty_slots
               (game_key, language, difficulty_mode, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(game_key, language)
               DO UPDATE SET difficulty_mode = excluded.difficulty_mode,
                             updated_at = excluded.updated_at""",
            (gk, lang, selected, now_stamp)
        )

        conn.commit()
        conn.close()
        return selected

    def set_selected_difficulty_mode(self, game_key, language, mode_name):
        """set active difficulty for one game/language pair"""
        gk = str(game_key).strip()
        lang = str(language).strip()
        mode = self._normalize_difficulty_mode(mode_name)

        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """SELECT mode_name
               FROM difficulty_modes
               WHERE LOWER(mode_name) = LOWER(?)
               LIMIT 1""",
            (mode,)
        )
        row = c.fetchone()
        if row:
            mode = row[0]
        else:
            mode = self._ensure_difficulty_mode_cursor(c, mode)

        now_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute(
            """INSERT INTO teacher_difficulty_slots
               (game_key, language, difficulty_mode, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(game_key, language)
               DO UPDATE SET difficulty_mode = excluded.difficulty_mode,
                             updated_at = excluded.updated_at""",
            (gk, lang, mode, now_stamp)
        )

        conn.commit()
        conn.close()
        return mode

    # --- custom teacher question bank ---

    # question-bank note:
    # each row is generic so one table can feed all mini-games.
    # choices are stored as json for flexibility (2-4 options depending on question).

    def add_custom_question(self, game_key, language, prompt_text, question_text,
                            choices, correct_index, difficulty_mode='General'):
        """add one teacher-made question"""
        clean_choices = [str(c).strip() for c in choices if str(c).strip()]
        if len(clean_choices) < 2:
            raise ValueError('Need at least 2 non-empty choices.')

        correct_index = int(correct_index)
        if correct_index < 0 or correct_index >= len(clean_choices):
            raise ValueError('Correct answer index is out of range.')

        conn = self.get_connection()
        c = conn.cursor()

        mode = self._ensure_difficulty_mode_cursor(c, difficulty_mode)

        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute(
            """INSERT INTO custom_questions
               (game_key, language, difficulty_mode, prompt_text, question_text,
                choices_json, correct_index, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(game_key).strip(),
                str(language).strip(),
                mode,
                str(prompt_text).strip(),
                str(question_text).strip(),
                json.dumps(clean_choices, ensure_ascii=False),
                correct_index,
                created_at,
            )
        )

        conn.commit()
        conn.close()

    def get_custom_questions(self, game_key=None, language=None, difficulty_mode=None):
        """get custom questions filtered by game/language/difficulty"""
        conn = self.get_connection()
        c = conn.cursor()

        query = """SELECT id, game_key, language, difficulty_mode, prompt_text, question_text,
                          choices_json, correct_index, created_at
                   FROM custom_questions"""
        params = []
        clauses = []

        if game_key:
            clauses.append("game_key = ?")
            params.append(game_key)
        if language:
            clauses.append("language = ?")
            params.append(language)
        if difficulty_mode:
            clauses.append("difficulty_mode = ?")
            params.append(difficulty_mode)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY created_at DESC"
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        out = []
        for row in rows:
            try:
                choices = json.loads(row[6])
            except (json.JSONDecodeError, TypeError):
                choices = []

            out.append({
                'id': row[0],
                'game_key': row[1],
                'language': row[2],
                'difficulty_mode': row[3],
                'prompt_text': row[4] or '',
                'question_text': row[5],
                'choices': choices,
                'correct_index': row[7],
                'created_at': row[8],
            })
        return out

    def get_custom_question_counts(self, include_difficulty=False):
        """count custom questions per slot, optionally split by difficulty"""
        conn = self.get_connection()
        c = conn.cursor()
        if include_difficulty:
            c.execute(
                """SELECT game_key, language, difficulty_mode, COUNT(*)
                   FROM custom_questions
                   GROUP BY game_key, language, difficulty_mode
                   ORDER BY game_key, language, difficulty_mode"""
            )
        else:
            c.execute(
                """SELECT game_key, language, COUNT(*)
                   FROM custom_questions
                   GROUP BY game_key, language
                   ORDER BY game_key, language"""
            )
        rows = c.fetchall()
        conn.close()
        return rows

    def delete_custom_question(self, question_id):
        """delete a custom question by id"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM custom_questions WHERE id = ?", (int(question_id),))
        conn.commit()
        conn.close()
    
    def generate_report(self):
        """make the report for the teacher"""
        # report output is intentionally denormalized for dashboard convenience.
        conn = self.get_connection()
        c = conn.cursor()
        
        # get all students
        c.execute("SELECT * FROM student_stats")
        students = c.fetchall()
        
        # count sessions
        c.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = c.fetchone()[0]

        # average time per module
        c.execute("SELECT AVG(time_spent) FROM progress")
        avg_time = c.fetchone()[0] or 0
        
        conn.close()
        
        analytics = self.get_teacher_metrics()
        report = {
            'students': students,
            'total_sessions': total_sessions,
            'avg_time_per_module': avg_time,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analytics': analytics,
            'leaderboard': self.get_leaderboard(limit=20),
            'custom_question_counts': self.get_custom_question_counts(),
        }
        
        return report
