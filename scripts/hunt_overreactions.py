import sys
import os

# Ensure app modules are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.market_simulator import MarketSimulator
from app.services.trader_agent import TraderAgent
from app.services.markov_chain_service import MarkovChainService

def hunt_overreactions():
    print("=== Signal Validation: Hunting 'Bullpen Panic' (SIG-02) ===")
    
    market_sim = MarketSimulator()
    trader = TraderAgent(bankroll=10000.0)
    markov = MarkovChainService()
    
    # Scenario: Top 8th, Home Leading 4-3.
    # Event: Home Pitcher walks the leadoff batter.
    # State: 0 Outs, Runner on 1st.
    print("Scenario: Top 8th, Home Leads 4-3. 0 Outs, Runner on 1st.")
    print("Event: Leadoff Walk. Market PANICS (Factor 0.15).")
    
    home_score = 4
    away_score = 3
    inning = 8
    is_top = True
    # State: 0 Outs, R1=1, R2=0, R3=0 (Index 1) -> Wait, Index map check?
    # 0 Outs: 0-7. R1=1 is offset 1 (1 = 001 binary? No, usually 1=R1).
    # Let's use Markov service to be safe.
    state_idx = 1 # 0 Outs, R1
    
    # 1. Get True Probability (Sharp)
    sharp_prob = markov.get_instant_win_prob(
        inning, 0, [1, 0, 0], home_score - away_score, is_top, pitcher_mod=1.0
    )
    print(f"Sharp Win Prob (Home): {sharp_prob:.2%}")
    
    # 2. Get Market Odds (Panic)
    # We inject a 15% panic drop in Home Win Prob
    panic_odds = market_sim.get_market_odds(
        home_score, away_score, inning, is_top, state_idx, panic_factor=0.15
    )
    
    # 3. Evaluate Trade
    context = {
        'inning': inning,
        'score_diff': abs(home_score - away_score),
        'leverage_index': 2.0, # High Leverage
        'signal_id': 'SIG-02'
    }
    
    decision = trader.evaluate_trade(sharp_prob, panic_odds, context)
    
    print(f"Market Odds (Panic): {panic_odds}")
    print(f"Decision: {decision['action']}")
    print(f"Edge: {decision['edge']:.2%}")
    print(f"Reason: {decision['reason']}")
    
    if decision['action'] == "BET" and decision['edge'] > 0.05:
        print("✅ SUCCESS: System detected the Panic Overreaction!")
    else:
        print("❌ FAILURE: System failed to detect value.")

if __name__ == "__main__":
    hunt_overreactions()
