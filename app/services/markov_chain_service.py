from app.services.state_engine import StateEngine

class MarkovChainService:
    """
    Phase 2: Micro-State Markov Engine.
    Provides O(1) lookups for Win Probability based on Game State.
    Replaces slow Monte Carlo simulations with pre-calculated Transition Matrices.
    """

    def __init__(self):
        self.state_engine = StateEngine()
        
        # TRANSITION_MATRICES (The "Lookup Table")
        # Key: (Inning, Outs, RunnerBitmask, ScoreDiff)
        # Value: Win_Probability_Home (float)
        # RunnerBitmask: 1=1st, 2=2nd, 4=3rd. e.g. 1st+3rd = 5.
        # ScoreDiff: Home - Away.
        self.transition_cache = {}
        
        # Populate with some common late-game states if we had data
        # self._load_matrices()

    def get_instant_win_prob(self, inning, outs, runners, score_diff, is_top_inning, pitcher_mod=1.0):
        """
        Returns the Win Probability for the Home Team.
        
        Args:
            inning (int): 1-9+
            outs (int): 0-2
            runners (list): [0/1, 0/1, 0/1] corresponding to 1st, 2nd, 3rd.
            score_diff (int): Home Score - Away Score.
            is_top_inning (bool): True if Away is batting.
            pitcher_mod (float): Multiplier for current pitcher.
            
        Returns:
            float: 0.0 to 1.0
        """
        # 1. Construct Lookup Key
        runner_mask = 0
        if runners[0]: runner_mask += 1
        if runners[1]: runner_mask += 2
        if runners[2]: runner_mask += 4
        
        # Normalize deep extra innings to "Extra Innings" bucket if needed, 
        # or just use inning number.
        # Normalize score diff if it's huge (e.g. > +10 or < -10) to cap?
        # For cache key, let's keep it exact.
        
        key = (inning, outs, runner_mask, score_diff, is_top_inning)
        
        # 2. Try Cache Lookup
        if key in self.transition_cache:
            return self.transition_cache[key]
            
        # 3. Fallback: Analytical Approximation (StateEngine Logic)
        # Since we don't have the 1GB lookup table loaded, we use the 
        # StateEngine's robust RE24->Sigmoid formula.
        # This is still O(1) relative to Monte Carlo.
        
        # Need to reconstruct inputs for StateEngine
        # StateEngine expects: home_score, away_score. We have diff.
        # Let's assume 0-0 baseline + diff for the formula, 
        # as the formula relies on diff anyway.
        home_score_dummy = score_diff if score_diff > 0 else 0
        away_score_dummy = abs(score_diff) if score_diff < 0 else 0
        
        # Get State Index
        state_idx = self.state_engine.get_current_state_index(outs, runners[0], runners[1], runners[2])
        
        prob = self.state_engine.get_win_probability(
            home_score_dummy, away_score_dummy, 
            inning, 
            0 if is_top_inning else 1, 
            state_idx, 
            pitcher_mod
        )
        
        # Optional: Cache this result? 
        # Logic says yes, but only if inputs are discrete. 
        # Pitcher Mod is continuous, so we CANNOT cache key strictly on game state 
        # if the result depends on float Pitcher Mod.
        # So we only cache if pitcher_mod ~= 1.0 (Standard) OR we include it in key.
        # For now, we return calculated.
        
        return prob
