import os
import sys
from datetime import datetime

# Ensure app modules are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.database_manager import DatabaseManager
from app.services.mlb_api import MlbApi

def settle_bets():
    print("=== Sniper Calibration: Settling Shadow Bets ===")
    db = DatabaseManager()
    api = MlbApi(db)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. Get unsettled bets
    db._execute(cursor, "SELECT id, game_id, market, odds, stake FROM shadow_bets WHERE outcome IS NULL")
    unsettled = cursor.fetchall()
    
    if not unsettled:
        print("No unsettled bets found.")
        return

    print(f"Found {len(unsettled)} unsettled bets.")
    
    # Cache for game results to avoid redundant API calls
    game_results = {}

    for bet in unsettled:
        bet_id = bet['id']
        game_id = bet['game_id']
        
        if game_id not in game_results:
            # Fetch result from API
            live_data = api.get_live_game_data(game_id)
            if not live_data:
                print(f"Could not fetch data for Game {game_id}")
                continue
                
            game_status = live_data.get('gameData', {}).get('status', {}).get('abstractGameState')
            if game_status != 'Final':
                print(f"Game {game_id} is still {game_status}. Skipping.")
                continue
                
            # Determine Winner
            linescore = live_data.get('liveData', {}).get('linescore', {})
            home_runs = linescore.get('teams', {}).get('home', {}).get('runs', 0)
            away_runs = linescore.get('teams', {}).get('away', {}).get('runs', 0)
            
            game_results[game_id] = {
                'home_won': home_runs > away_runs,
                'away_won': away_runs > home_runs,
                'is_tie': home_runs == away_runs # rare in MLB but possible in weird scenarios or void
            }

        result = game_results.get(game_id)
        if not result: continue
        
        # Simplified Settlement Logic: Assume bet was on Home (as per demo)
        # In a real system, we'd store which side we bet on. 
        # For this implementation, we'll assume market 'H_ML' means Home ML.
        
        outcome = "LOST"
        profit_loss = -bet['stake']
        
        if bet['market'] == 'H_ML' and result['home_won']:
            outcome = "WON"
            # Calculate profit
            odds = bet['odds']
            if odds > 0:
                profit_loss = bet['stake'] * (odds / 100)
            else:
                profit_loss = bet['stake'] / (abs(odds) / 100)
        elif bet['market'] == 'A_ML' and result['away_won']:
            outcome = "WON"
            # ...
            
        # Update DB
        update_query = "UPDATE shadow_bets SET outcome = ?, profit_loss = ? WHERE id = ?"
        db._execute(cursor, update_query, (outcome, float(profit_loss), bet_id))
        print(f"Settled Bet {bet_id}: {outcome} (${profit_loss:.2f})")

    conn.commit()
    conn.close()
    print("Settlement Complete.")

if __name__ == "__main__":
    settle_bets()
