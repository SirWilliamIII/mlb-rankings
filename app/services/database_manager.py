import sqlite3
import json
import os
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_path="data/mlb_data.db"):
        self.db_url = os.getenv("DATABASE_URL")
        self.db_path = db_path
        
        if not self.db_url:
            self._ensure_data_dir()
            
        self.init_db()

    def _ensure_data_dir(self):
        directory = os.path.dirname(self.db_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    @property
    def is_postgres(self):
        return bool(self.db_url)

    def get_connection(self):
        if self.is_postgres:
            conn = psycopg.connect(self.db_url, row_factory=dict_row)
            return conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    def _execute(self, cursor, query, params=None):
        """
        Executes a query, handling placeholder differences.
        SQLite uses ?, Postgres uses %s.
        """
        if self.is_postgres:
            query = query.replace('?', '%s')
        
        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)
            
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # DDL Differences
        if self.is_postgres:
            pk_type = "SERIAL PRIMARY KEY"
            text_type = "TEXT"
            datetime_type = "TIMESTAMP"
            # Postgres doesn't strictly need this for SERIAL but good to be explicit if using identity
        else:
            pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
            text_type = "TEXT"
            datetime_type = "DATETIME"

        # Table for caching API responses (JSON blobs)
        self._execute(cursor, f'''
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key {text_type} PRIMARY KEY,
                response_json {text_type} NOT NULL,
                timestamp {datetime_type} DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table for tracking simulation runs
        self._execute(cursor, f'''
            CREATE TABLE IF NOT EXISTS simulation_runs (
                id {pk_type},
                timestamp {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                iterations INTEGER
            )
        ''')

        # Table for storing team probabilities for a specific run
        self._execute(cursor, f'''
            CREATE TABLE IF NOT EXISTS team_probabilities (
                id {pk_type},
                run_id INTEGER,
                team_id INTEGER,
                team_name {text_type},
                division_winner REAL,
                playoff_spot REAL,
                league_champion REAL,
                world_series_winner REAL,
                FOREIGN KEY (run_id) REFERENCES simulation_runs (id)
            )
        ''')
        
        # NEW: Table for Advanced Team Stats (Pythagorean inputs)
        self._execute(cursor, f'''
            CREATE TABLE IF NOT EXISTS team_stats_advanced (
                team_id {text_type} PRIMARY KEY,
                season INTEGER,
                runs_scored REAL,
                runs_allowed REAL,
                pythagorean_win_pct REAL,
                updated_at {datetime_type} DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # NEW: Table for Pitcher Stats (FIP, etc)
        self._execute(cursor, f'''
            CREATE TABLE IF NOT EXISTS pitcher_stats (
                player_id INTEGER PRIMARY KEY,
                name {text_type},
                team {text_type},
                season INTEGER,
                era REAL,
                fip REAL,
                ip REAL,
                updated_at {datetime_type} DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    # --- Caching Methods ---

    def get_cached_data(self, key, max_age_seconds=3600):
        """
        Retrieves cached data if it exists and is younger than max_age_seconds.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        self._execute(cursor, "SELECT response_json, timestamp FROM api_cache WHERE cache_key = ?", (key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            # Handle timestamp type differences
            ts = row['timestamp']
            if isinstance(ts, str):
                cached_time = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            else:
                cached_time = ts # Postgres returns datetime object

            if datetime.now() - cached_time < timedelta(seconds=max_age_seconds):
                return json.loads(row['response_json'])
        
        return None

    def set_cached_data(self, key, data):
        """
        Saves data to the cache, updating the timestamp if it already exists.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Ensure 'now' is compatible with both (string for sqlite, datetime for PG usually works or cast)
        # For simplicity, we pass string to sqlite, but psycopg adapts datetime objects.
        # Let's use the adapter logic or just pass string which PG casts to TIMESTAMP if configured, 
        # but better to pass object if PG.
        
        val_timestamp = now if self.is_postgres else now_str

        query = '''
            INSERT INTO api_cache (cache_key, response_json, timestamp) 
            VALUES (?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                response_json=excluded.response_json,
                timestamp=excluded.timestamp
        '''
        self._execute(cursor, query, (key, json.dumps(data), val_timestamp))
        
        conn.commit()
        conn.close()

    # --- Simulation Results Methods ---

    def save_simulation_results(self, iterations, probabilities):
        """
        Saves the results of a simulation run.
        probabilities: dict {team_id: {'name': str, 'division_winner': float, ...}}
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Create Run Record
        if self.is_postgres:
             cursor.execute("INSERT INTO simulation_runs (iterations) VALUES (%s) RETURNING id", (iterations,))
             run_id = cursor.fetchone()['id']
        else:
             cursor.execute("INSERT INTO simulation_runs (iterations) VALUES (?)", (iterations,))
             run_id = cursor.lastrowid
        
        # 2. Insert Team Probabilities
        for team_id, stats in probabilities.items():
            query = '''
                INSERT INTO team_probabilities 
                (run_id, team_id, team_name, division_winner, playoff_spot, league_champion, world_series_winner)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                run_id,
                team_id,
                stats.get('name', f"Team {team_id}"),
                stats.get('division_winner', 0.0),
                stats.get('playoff_spot', 0.0),
                stats.get('league_champion', 0.0),
                stats.get('world_series_winner', 0.0)
            )
            self._execute(cursor, query, params)
            
        conn.commit()
        conn.close()
        return run_id

    def get_latest_simulation_results(self):
        """
        Retrieves the most recent simulation run and its results.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get latest run
        self._execute(cursor, "SELECT id, iterations, timestamp FROM simulation_runs ORDER BY timestamp DESC LIMIT 1")
        run = cursor.fetchone()
        
        if not run:
            conn.close()
            return None
            
        run_id = run['id']
        result_data = {
            "run_id": run_id,
            "timestamp": run['timestamp'],
            "iterations": run['iterations'],
            "probabilities": {}
        }
        
        # Get probabilities for that run
        self._execute(cursor, "SELECT * FROM team_probabilities WHERE run_id = ?", (run_id,))
        rows = cursor.fetchall()
        
        for row in rows:
            result_data["probabilities"][row['team_id']] = {
                "name": row['team_name'],
                "division_winner": row['division_winner'],
                "playoff_spot": row['playoff_spot'],
                "league_champion": row['league_champion'],
                "world_series_winner": row['world_series_winner']
            }
            
        conn.close()
        return result_data
    
    # --- Advanced Stats Methods ---
    
    def save_advanced_team_stats(self, stats_list, season, id_mapper=None):
        """
        Saves run scored/allowed data.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        val_timestamp = now if self.is_postgres else now.strftime("%Y-%m-%d %H:%M:%S")

        for stat in stats_list:
            sd_key = stat.get('Team')
            if not sd_key: continue
            
            if id_mapper and sd_key in id_mapper:
                storage_id = id_mapper[sd_key]
            else:
                storage_id = sd_key
            
            runs = stat.get('Runs', 0) or 0
            runs_allowed = stat.get('RunsAgainst', 0) or 0
            
            if runs + runs_allowed == 0:
                pyth_pct = 0.5
            else:
                r_exp = runs ** 1.83
                ra_exp = runs_allowed ** 1.83
                pyth_pct = r_exp / (r_exp + ra_exp)
            
            query = '''
                INSERT INTO team_stats_advanced 
                (team_id, season, runs_scored, runs_allowed, pythagorean_win_pct, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(team_id) DO UPDATE SET
                    runs_scored=excluded.runs_scored,
                    runs_allowed=excluded.runs_allowed,
                    pythagorean_win_pct=excluded.pythagorean_win_pct,
                    updated_at=excluded.updated_at
            '''
            params = (storage_id, season, runs, runs_allowed, pyth_pct, val_timestamp)
            self._execute(cursor, query, params)
            
        conn.commit()
        conn.close()

    def save_pitcher_stats(self, players_list, season):
        """
        Saves pitcher stats (FIP, etc).
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        val_timestamp = now if self.is_postgres else now.strftime("%Y-%m-%d %H:%M:%S")

        for p in players_list:
            if p.get('PositionCategory') != 'Pitcher' or (p.get('InningsPitched') or 0) < 5:
                continue

            ip = p.get('InningsPitched')
            hr = p.get('HomeRunsAllowed') or 0
            bb = p.get('Walks') or 0
            hbp = p.get('HitByPitch') or 0
            k = p.get('Strikeouts') or 0
            
            fip = 4.00
            if ip and ip > 0:
                fip = ((13*hr + 3*(bb+hbp) - 2*k) / ip) + 3.10
            
            query = '''
                INSERT INTO pitcher_stats
                (player_id, name, team, season, era, fip, ip, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    era=excluded.era,
                    fip=excluded.fip,
                    ip=excluded.ip,
                    updated_at=excluded.updated_at
            '''
            params = (
                p.get('PlayerID'),
                p.get('Name'),
                p.get('Team'),
                season,
                p.get('EarnedRunAverage') or 4.00,
                fip,
                ip,
                val_timestamp
            )
            self._execute(cursor, query, params)
            
        conn.commit()
        conn.close()
        
    def get_advanced_team_stats(self, team_key):
        """Returns {pythagorean_win_pct: float}"""
        conn = self.get_connection()
        cursor = conn.cursor()
        self._execute(cursor, "SELECT pythagorean_win_pct FROM team_stats_advanced WHERE team_id = ?", (team_key,))
        row = cursor.fetchone()
        conn.close()
        return row['pythagorean_win_pct'] if row else None
