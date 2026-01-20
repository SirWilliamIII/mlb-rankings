import sys
import os
sys.path.append(os.getcwd())

from app.services.database_manager import DatabaseManager
import time

def debug_db():
    print("Connecting to DB...")
    db = DatabaseManager()
    print(f"Is Postgres: {db.is_postgres}")
    print(f"DB URL: {db.db_url[:20]}..." if db.db_url else "DB URL: None")
    
    print("Testing READ...")
    start = time.time()
    # Read one advanced stat
    val = db.get_advanced_team_stats(110) # 110 is usually a valid ID (BAL?) - actually we use IDs from map. 
    # Let's just query raw sql to be safe if ID is wrong, but get_advanced_team_stats handles logic.
    # The error before was on team_id=109/etc.
    # Let's try a raw fetch.
    conn = db.get_connection()
    cursor = conn.cursor()
    db._execute(cursor, "SELECT count(*) as c FROM team_stats_advanced")
    row = cursor.fetchone()
    print(f"READ Success. Count: {row['c']}. Time: {time.time()-start:.2f}s")
    
    # List tables
    db._execute(cursor, "SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cursor.fetchall()
    print("Tables:", [t['table_name'] for t in tables])

    conn.close()
    
    print("Testing WRITE...")
    start = time.time()
    # Write a dummy run
    run_id = db.save_simulation_results(1, {})
    print(f"WRITE Success. Run ID: {run_id}. Time: {time.time()-start:.2f}s")

if __name__ == "__main__":
    debug_db()
