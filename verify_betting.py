import sys
import os
sys.path.append(os.getcwd())

from app.services.mlb_api import MlbApi
from app.services.database_manager import DatabaseManager
from app.services.betting_analyzer import BettingAnalyzer

def verify_betting():
    print("Initializing components...")
    db = DatabaseManager()
    mlb = MlbApi(db)
    analyzer = BettingAnalyzer(db)
    
    print("Fetching schedule...")
    teams = mlb.get_teams_for_simulation()
    schedule = mlb.get_remaining_schedule()
    
    # Take next 10 games
    next_games = schedule[:10]
    
    print(f"Analyzing {len(next_games)} games for value...")
    opportunities = analyzer.analyze_schedule(next_games, teams)
    
    print(f"Found {len(opportunities)} value bets.")
    if opportunities:
        print("Top Opportunity:")
        print(opportunities[0])
    else:
        print("No value found (market is efficient!).")

if __name__ == "__main__":
    verify_betting()
