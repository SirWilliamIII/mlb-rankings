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
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name='feed_latency_metrics';")
        table = cursor.fetchone()
        if table:
            print("Table 'feed_latency_metrics' exists in Postgres.")
            cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'feed_latency_metrics';")
            columns = cursor.fetchall()
            for col in columns:
                print(col)
        else:
            print("Table 'feed_latency_metrics' does not exist in Postgres.")
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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feed_latency_metrics';")
        table = cursor.fetchone()
        if table:
            print("Table 'feed_latency_metrics' exists.")
            cursor.execute("PRAGMA table_info(feed_latency_metrics);")
            columns = cursor.fetchall()
            for col in columns:
                print(col)
        else:
            print("Table 'feed_latency_metrics' does not exist.")
        conn.close()