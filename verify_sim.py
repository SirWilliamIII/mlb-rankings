import sys
import os
sys.path.append(os.getcwd())

from app.services.mlb_api import MlbApi
from app.services.monte_carlo_simulator import MonteCarloSimulator
from app.services.database_manager import DatabaseManager
import json

def verify_sim():
    print("Initializing components...")
    db = DatabaseManager()
    mlb = MlbApi(db)
    
    print("Fetching teams...")
    teams = mlb.get_teams_for_simulation()
    print("Fetching schedule...")
    schedule = mlb.get_remaining_schedule()
    
    # Take a tiny slice of the schedule for speed
    test_schedule = schedule[:50]
    
    print(f"Running simulation with {len(teams)} teams and {len(test_schedule)} games...")
    simulator = MonteCarloSimulator(teams, test_schedule, db)
    simulator.run_simulation(iterations=10)
    
    probs = simulator.get_probabilities()
    
    # Check if we got results
    if probs:
        print("SUCCESS: Simulation produced probabilities.")
        # Print a sample team's playoff probability
        sample_id = list(probs.keys())[0]
        print(f"Sample Team ({sample_id}) Playoff Prob: {probs[sample_id]['playoff_spot']}")
    else:
        print("FAILURE: Simulation returned no results.")

if __name__ == "__main__":
    verify_sim()
