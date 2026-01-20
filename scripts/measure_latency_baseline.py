import sys
import os
import random
import numpy as np
from datetime import datetime, timezone, timedelta

# Ensure app modules are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.game_replay_service import GameReplayService
from app.services.latency_monitor import LatencyMonitor

def measure_baseline(game_pk):
    print(f"=== Starting Latency Baseline Measurement (Game {game_pk}) ===")
    
    replay_service = GameReplayService()
    # Mock DB Manager not needed for in-memory checks if we mock the method or use SQLite
    # For now, LatencyMonitor needs a db_manager to init, but we can pass None if we suppress the worker error
    # or give it a dummy. Let's pass None and accept the thread error print or fix logic.
    latency_monitor = LatencyMonitor(db_manager=None)
    
    # Storage for stats
    metrics = {
        'Ball/Strike': [],
        'Hit/Out': [],
        'Scoring': []
    }
    
    for event in replay_service.stream_game_events(game_pk):
        desc = event['description'].lower()
        score_change = abs(event['home_score'] - event.get('home_score_prev', event['home_score'])) + \
                       abs(event['away_score'] - event.get('away_score_prev', event['away_score']))
        
        # Categorize
        if 'homer' in desc or 'run' in desc or score_change > 0:
            category = 'Scoring'
            mean, sigma = 8.0, 1.0
        elif 'strike' in desc or 'ball' in desc or 'foul' in desc:
            category = 'Ball/Strike'
            mean, sigma = 2.5, 0.2
        else:
            category = 'Hit/Out'
            mean, sigma = 4.5, 0.5
            
        # Inject Synthetic Latency
        synthetic_delta = max(0.0, np.random.normal(mean, sigma))
        
        # Feed Monitor
        # We need to spoof the time. event['timestamp'] is the "Event Time".
        # "Receipt Time" would be Event Time + Delta.
        # LatencyMonitor.log_feed_delta calculates Receipt - Event.
        # So we just pass the delta directly to update_rolling_window relative to now?
        # No, the logic calls `dateutil.parser.parse(event_ts_str)`.
        # To test the logic end-to-end, we should construct a fake current time.
        # But LatencyMonitor uses datetime.now(timezone.utc). We can't easily mock that without patching.
        # FOR BASELINING: We can bypass log_feed_delta and call _update_rolling_window directly
        # since we want to test the CLASSIFICATION logic (is_safe_window).
        
        latency_monitor._update_rolling_window(synthetic_delta)
        is_safe = latency_monitor.is_safe_window()
        
        metrics[category].append({
            'delta': synthetic_delta,
            'is_safe': is_safe
        })
        
        print(f"[{category}] Delta: {synthetic_delta:.2f}s | Safe? {is_safe} | WinAvg: {sum(latency_monitor.window_history)/len(latency_monitor.window_history):.2f}")

    print("\n=== LATENCY PROFILE REPORT ===")
    for cat, data in metrics.items():
        if not data: continue
        deltas = [d['delta'] for d in data]
        safe_count = sum(1 for d in data if d['is_safe'])
        
        print(f"\nCategory: {cat}")
        print(f"  Count: {len(data)}")
        print(f"  Mean Latency: {np.mean(deltas):.3f}s")
        print(f"  Std Dev: {np.std(deltas):.3f}s")
        print(f"  Safe Window %: {safe_count/len(data):.1%}")
        
        # Validation Logic
        if cat == 'Scoring':
            if np.mean(deltas) < 6.0:
                print("  [FAIL] Scoring latency too low (Unrealistic)")
        elif cat == 'Ball/Strike':
            if np.mean(deltas) > 4.0:
                print("  [FAIL] Ball/Strike latency too high")

if __name__ == "__main__":
    KILL_HOUSE_ID = 775296
    measure_baseline(KILL_HOUSE_ID)
