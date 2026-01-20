import sys
import os
import time

# Ensure app modules are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.monte_carlo_simulator import MonteCarloSimulator

def verify_deep_layer():
    print("=== Deep Layer Verification: Roster-Aware Fatigue Model ===")
    
    sim = MonteCarloSimulator()
    
    # Scenario: Tie game, Bottom 8th. Home Betting.
    # Current State: 0 Outs, Empty Bases
    # Score: 3-3
    print("Scenario: Bottom 8th, Tie Game (3-3). Home Batting.")
    print("Testing impact of AWAY Bullpen Fatigue on Home Win Probability.\n")
    
    # Run Baseline (Fresh Bullpen)
    start_time = time.time()
    prob_fresh = sim.simulate_game_vectorized(
        initial_state_idx=0,
        home_score=3,
        away_score=3,
        inning=8,
        is_top=False, # Bot 8th
        home_bullpen_mod=1.0,
        away_bullpen_mod=1.0, # Fresh
        iterations=20000
    )
    print(f"Test A (Fresh Bullpen): Win Prob {prob_fresh:.2%} (Time: {time.time()-start_time:.3f}s)")
    
    # Run Fatigued (Dead Bullpen)
    start_time = time.time()
    prob_dead = sim.simulate_game_vectorized(
        initial_state_idx=0,
        home_score=3,
        away_score=3,
        inning=8,
        is_top=False, # Bot 8th
        home_bullpen_mod=1.0,
        away_bullpen_mod=1.25, # Dead (25% degradation)
        iterations=20000
    )
    print(f"Test B (Dead Bullpen):  Win Prob {prob_dead:.2%} (Time: {time.time()-start_time:.3f}s)")
    
    delta = prob_dead - prob_fresh
    print(f"\nDelta: {delta:+.2%}")
    
    if delta > 0.03: # Expect Home WinProb to RISE if Away Pitching is bad
        print("✅ SUCCESS: Win Probability increased significantly against a fatigued bullpen.")
    else:
        print("❌ FAILURE: Win Probability did not change significantly.")

if __name__ == "__main__":
    verify_deep_layer()
