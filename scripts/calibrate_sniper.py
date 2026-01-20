import os
import sys
import numpy as np

# Ensure app modules are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.database_manager import DatabaseManager

def calibrate():
    print("=== Sniper Calibration: Performance Audit ===")
    db = DatabaseManager()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. Fetch settled bets
    db._execute(cursor, "SELECT predicted_prob, outcome FROM shadow_bets WHERE outcome IN ('WON', 'LOST')")
    bets = cursor.fetchall()
    
    if not bets:
        print("No settled bets found for calibration.")
        return

    print(f"Analyzing {len(bets)} signals.")
    
    probs = np.array([b['predicted_prob'] for b in bets])
    outcomes = np.array([1.0 if b['outcome'] == 'WON' else 0.0 for b in bets])
    
    # 2. Brier Score (Mean Squared Error)
    # Lower is better. 0.0 is perfect prediction.
    brier_score = np.mean((probs - outcomes)**2)
    
    # 3. Expected vs Observed Win Rate
    expected_win_rate = np.mean(probs)
    observed_win_rate = np.mean(outcomes)
    
    print(f"\n--- Metrics ---")
    print(f"Brier Score: {brier_score:.4f}")
    print(f"Expected Win Rate: {expected_win_rate:.2%}")
    print(f"Observed Win Rate: {observed_win_rate:.2%}")
    print(f"Calibration Bias: {observed_win_rate - expected_win_rate:+.2%}")
    
    # 4. Decile Binning (Simple)
    print("\n--- Calibration by Confidence ---")
    bins = np.linspace(0, 1, 11)
    for i in range(len(bins)-1):
        mask = (probs >= bins[i]) & (probs < bins[i+1])
        count = np.sum(mask)
        if count > 0:
            bin_expected = np.mean(probs[mask])
            bin_observed = np.mean(outcomes[mask])
            print(f"Bin {bins[i]:.1f}-{bins[i+1]:.1f}: Count {count:3d} | Exp {bin_expected:5.1%} | Obs {bin_observed:5.1%}")

    conn.close()

if __name__ == "__main__":
    calibrate()
