import numpy as np
from app.services.markov_chain_service import MarkovChainService

def demo():
    service = MarkovChainService()
    
    print("=== MLB Sniper: Markov Engine Demo ===")
    print("Scenario: Tie Game, Bottom 9th, Bases Loaded, 2 Outs.")
    print("This is the ultimate high-leverage state.\n")
    
    inning = 9
    outs = 2
    runners = [1, 1, 1]
    score_diff = 0
    is_top = False # Away Pitcher is on the mound
    
    # 1. Baseline Pitcher (Mod 1.0)
    prob_base = service.get_instant_win_prob(
        inning, outs, runners, score_diff, is_top, pitcher_mod=1.0
    )
    
    # 2. Fatigued Pitcher (Mod 1.15) - 15% worse
    prob_fatigued = service.get_instant_win_prob(
        inning, outs, runners, score_diff, is_top, pitcher_mod=1.15
    )
    
    # 3. Meltdown Pitcher (Mod 1.30) - 30% worse
    prob_meltdown = service.get_instant_win_prob(
        inning, outs, runners, score_diff, is_top, pitcher_mod=1.30
    )
    
    print(f"Fresh Pitcher (1.00): Home Win Prob = {prob_base*100:.2f}%")
    print(f"Tired Pitcher (1.15): Home Win Prob = {prob_fatigued*100:.2f}% (Shift: +{(prob_fatigued-prob_base)*100:.2f}%)")
    print(f"Meltdown Pitcher (1.30): Home Win Prob = {prob_meltdown*100:.2f}% (Shift: +{(prob_meltdown-prob_base)*100:.2f}%)")
    
    print("\n--- Why this matters for the Sniper ---")
    print("A 5% shift in win probability is often the difference between")
    print("a -110 market price and a -150 'True Price'.")
    print("By detecting fatigue before the book adjusts, we capture the edge.")

if __name__ == "__main__":
    demo()
