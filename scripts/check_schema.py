import sqlite3
import os
import psycopg
from psycopg.rows import dict_row

db_url = os.getenv("DATABASE_URL")
if db_url:
    print("Checking Postgres schema...")
    try:
        conn = psycopg.connect(db_url)
        cursor = conn.cursor()
        for table_name in ['feed_latency_metrics', 'shadow_bets']:
            cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_name='{table_name}';")
            table = cursor.fetchone()
            if table:
                print(f"Table '{table_name}' exists in Postgres.")
                cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}';")
                columns = cursor.fetchall()
                for col in columns:
                    print(col)
            else:
                print(f"Table '{table_name}' does not exist in Postgres.")
        conn.close()
    except Exception as e:
        print(f"Error connecting to Postgres: {e}")

else:
    print("Checking SQLite schema...")
    db_path = "data/mlb_data.db"
    print(f"Check schema using DB path: {os.path.abspath(db_path)}")
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist.")
    else:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for table_name in ['feed_latency_metrics', 'shadow_bets']:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            table = cursor.fetchone()
            if table:
                print(f"Table '{table_name}' exists.")
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                for col in columns:
                    print(col)
            else:
                print(f"Table '{table_name}' does not exist.")
        conn.close()