import sys
import os
sys.path.append(os.getcwd())

from app.services.mlb_api import MlbApi
from app.services.season_simulator import SeasonSimulator
from app.services.database_manager import DatabaseManager

def verify_season_sim():
    print("Initializing components...")
    db = DatabaseManager()
    mlb = MlbApi(db)
    
    print("Fetching teams...")
    teams = mlb.get_teams_for_simulation()
    print("Fetching schedule...")
    schedule = mlb.get_remaining_schedule()
    
    if not teams or not schedule:
        print("Error: Could not fetch teams or schedule.")
        return

    # Take a tiny slice of the schedule for speed
    test_schedule = schedule[:50]
    
    print(f"Running Season Simulation with {len(teams)} teams and {len(test_schedule)} games...")
    simulator = SeasonSimulator(teams, test_schedule, db)
    simulator.run_simulation(iterations=5)
    
    probs = simulator.get_probabilities()
    
    if probs:
        print("SUCCESS: Simulation produced probabilities.")
        sample_id = list(probs.keys())[0]
        print(f"Sample Team ({sample_id}) Playoff Prob: {probs[sample_id]['playoff_spot']}")
        
        # Test saving to DB
        print("Testing DB Save...")
        enhanced_probs = {}
        for team_id, p in probs.items():
            enhanced_probs[team_id] = p
            enhanced_probs[team_id]['name'] = teams[team_id]['name']
            
        run_id = db.save_simulation_results(5, enhanced_probs)
        print(f"Saved results with Run ID: {run_id}")
        
    else:
        print("FAILURE: Simulation returned no results.")

if __name__ == "__main__":
    verify_season_sim()
