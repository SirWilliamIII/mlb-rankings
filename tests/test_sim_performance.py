import time
import numpy as np
from app.services.monte_carlo_simulator import GameSimulator

def verify_performance():
    sim = GameSimulator()
    
    # Test Scenario: Top 8th, Tie Game, Runner on 2nd, 1 Out
    # Home: 4, Away: 4
    # Inning: 8, Top (is_top=True)
    # State: 1 Out, Runner on 2nd (State Index lookup needed)
    
    # State lookup: 1 Out, 0 on 1st, 1 on 2nd, 0 on 3rd
    # Outs=1, R1=0, R2=1, R3=0
    state_idx = sim.state_engine.get_current_state_index(1, 0, 1, 0)
    print(f"Test State Index: {state_idx} ({sim.state_engine.IDX_TO_STATE[state_idx]})")
    
    iterations = 10000
    
    print(f"Running {iterations} vectorized simulations...")
    start_time = time.time()
    
    win_prob = sim.simulate_game_vectorized(
        initial_state_idx=state_idx,
        home_score=4,
        away_score=4,
        inning=8,
        is_top=True,
        iterations=iterations
    )
    
    end_time = time.time()
    duration = (end_time - start_time) * 1000
    
    print(f"Win Probability (Home): {win_prob:.4f}")
    print(f"Execution Time: {duration:.2f} ms")
    
    if duration < 200:
        print("SUCCESS: Performance target met (<200ms)")
    else:
        print("WARNING: Performance target NOT met (>200ms)")

if __name__ == "__main__":
    verify_performance()
