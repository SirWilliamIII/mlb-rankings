import numpy as np
from app.services.state_engine import StateEngine

class MonteCarloSimulator:
    """
    High-performance Vectorized Monte Carlo Simulator for MLB Live Games.
    Simulates 'Rest of Game' outcomes using Markov Chain transitions.
    Level 300 Upgrade: Roster-Aware Fatigue Modeling.
    """

    def __init__(self, state_engine=None):
        self.state_engine = state_engine if state_engine else StateEngine()
        
        # Dimensions: 25 States (0-23 + End)
        self.transition_matrix_normal = np.zeros((25, 25))
        self.transition_matrix_fatigued = np.zeros((25, 25))
        self.run_matrix = np.zeros((25, 25))
        
        # Build both Normal and Fatigued environment matrices
        self._build_matrices(modifier=1.0, target_matrix=self.transition_matrix_normal)
        self._build_matrices(modifier=1.25, target_matrix=self.transition_matrix_fatigued) # 25% degradation
        
        # Pre-compute CDFs for fast sampling
        self.cdf_normal = np.cumsum(self.transition_matrix_normal, axis=1)
        self.cdf_fatigued = np.cumsum(self.transition_matrix_fatigued, axis=1)

    def _build_matrices(self, modifier, target_matrix):
        """
        Builds a transition matrix with a specific offensive modifier.
        modifier > 1.0 means MORE offense (Pitcher Fatigue).
        """
        # Base Probabilities (League Average)
        # We scale offensive events by the modifier, and reduce Out prob to normalize.
        p_1b = 0.15 * modifier
        p_2b = 0.05 * modifier
        p_3b = 0.005 * modifier
        p_hr = 0.03 * modifier
        p_bb = 0.085 * modifier
        
        total_offense = p_1b + p_2b + p_3b + p_hr + p_bb
        if total_offense > 0.99: # Safety cap
            total_offense = 0.99
            
        p_out = 1.0 - total_offense
        
        for idx in range(24):
            outs, r1, r2, r3 = self.state_engine.IDX_TO_STATE[idx]
            
            # 1. OUTS
            if outs < 2:
                next_state_out = self.state_engine.get_current_state_index(outs + 1, r1, r2, r3)
                target_matrix[idx, next_state_out] += p_out
                # Run matrix is shared/static (runs don't change, just likelihood)
                if modifier == 1.0: self.run_matrix[idx, next_state_out] = 0 
            else:
                target_matrix[idx, self.state_engine.END_STATE_IDX] += p_out
                if modifier == 1.0: self.run_matrix[idx, self.state_engine.END_STATE_IDX] = 0

            # 2. WALKS
            new_r1, new_r2, new_r3 = 1, r1, r2
            runs_bb = 0
            if r1 == 1:
                if r2 == 1:
                    if r3 == 1: runs_bb = 1
                    else: new_r3 = 1
                else: new_r2 = 1
            else: new_r2, new_r3 = r2, r3
            
            next_state_bb = self.state_engine.get_current_state_index(outs, new_r1, new_r2, new_r3)
            target_matrix[idx, next_state_bb] += p_bb
            if modifier == 1.0: self.run_matrix[idx, next_state_bb] = runs_bb

            # 3. SINGLES
            runs_1b = r3 + r2
            next_state_1b = self.state_engine.get_current_state_index(outs, 1, 1 if r1 else 0, 0)
            target_matrix[idx, next_state_1b] += p_1b
            if modifier == 1.0: self.run_matrix[idx, next_state_1b] = runs_1b

            # 4. DOUBLES
            runs_2b = r3 + r2
            next_state_2b = self.state_engine.get_current_state_index(outs, 0, 1, 1 if r1 else 0)
            target_matrix[idx, next_state_2b] += p_2b
            if modifier == 1.0: self.run_matrix[idx, next_state_2b] = runs_2b

            # 5. TRIPLES
            runs_3b = r1 + r2 + r3
            next_state_3b = self.state_engine.get_current_state_index(outs, 0, 0, 1)
            target_matrix[idx, next_state_3b] += p_3b
            if modifier == 1.0: self.run_matrix[idx, next_state_3b] = runs_3b

            # 6. HOMERS
            runs_hr = r1 + r2 + r3 + 1
            next_state_hr = self.state_engine.get_current_state_index(outs, 0, 0, 0)
            target_matrix[idx, next_state_hr] += p_hr
            if modifier == 1.0: self.run_matrix[idx, next_state_hr] = runs_hr
            
            # Normalize
            row_sum = np.sum(target_matrix[idx])
            if row_sum > 0:
                target_matrix[idx] /= row_sum
                
        # End State Identity
        target_matrix[self.state_engine.END_STATE_IDX, self.state_engine.END_STATE_IDX] = 1.0

    def simulate_game_vectorized(self, initial_state_idx, home_score, away_score, inning, is_top, 
                                 home_bullpen_mod=1.0, away_bullpen_mod=1.0, iterations=10000):
        """
        Simulates the remainder of the game N times using vectorized operations.
        Accepts bullpen modifiers to degrade pitching performance in late innings (7+).
        """
        n_sims = iterations
        
        # 1. Initialize State Vectors
        current_states = np.full(n_sims, initial_state_idx, dtype=int)
        runs_home = np.zeros(n_sims, dtype=int)
        runs_away = np.zeros(n_sims, dtype=int)
        current_innings = np.full(n_sims, inning, dtype=int)
        is_top_inning = np.full(n_sims, is_top, dtype=bool) 
        game_over = np.zeros(n_sims, dtype=bool)

        # Simulation Loop
        max_steps = 200 
        
        for _ in range(max_steps):
            if np.all(game_over): break
                
            active_mask = ~game_over
            if not np.any(active_mask): break
                
            active_indices = np.where(active_mask)[0]
            active_states = current_states[active_mask]
            active_innings = current_innings[active_mask]
            active_is_top = is_top_inning[active_mask]
            
            # --- Determine Fatigue Application ---
            # Rule: If Inning >= 7, apply bullpen modifiers.
            # If Top Inning (Home Pitching), use home_bullpen_mod
            # If Bot Inning (Away Pitching), use away_bullpen_mod
            
            # We construct a boolean mask for "Is Fatigued?"
            # We assume "Fatigued" means mod > 1.10. 
            # If mod is low (1.0), we stick to Normal matrix.
            
            is_late_game = (active_innings >= 7)
            
            # Home Pitching (Top) & Fatigued
            home_pitching_mask = active_is_top & is_late_game & (home_bullpen_mod > 1.10)
            
            # Away Pitching (Bot) & Fatigued
            away_pitching_mask = (~active_is_top) & is_late_game & (away_bullpen_mod > 1.10)
            
            fatigue_mask = home_pitching_mask | away_pitching_mask
            
            # --- Vectorized Transition ---
            rand_vals = np.random.rand(len(active_indices))
            
            # Conditional Matrix Lookup
            # If fatigue_mask is True, look up from cdf_fatigued. Else cdf_normal.
            
            # We need to map the global 'state' indices to the correct CDF
            # np.where allows us to select values, but we need to select ROWS from 2D matrices.
            # efficient way:
            # cdf_normal[active_states] -> shape (N, 25)
            # cdf_fatigued[active_states] -> shape (N, 25)
            # np.where(fatigue_mask[:, None], A, B)
            
            current_cdf = np.where(
                fatigue_mask[:, None], 
                self.cdf_fatigued[active_states], 
                self.cdf_normal[active_states]
            )
            
            # Next state selection
            next_states = (current_cdf >= rand_vals[:, None]).argmax(axis=1)
            
            transition_runs = self.run_matrix[active_states, next_states]
            
            runs_away[active_indices] += (transition_runs * active_is_top).astype(int)
            runs_home[active_indices] += (transition_runs * (~active_is_top)).astype(int)
            
            current_states[active_indices] = next_states
            
            # --- Handle Inning Changes ---
            inning_end_mask = (current_states[active_indices] == self.state_engine.END_STATE_IDX)
            
            if np.any(inning_end_mask):
                ended_indices_local = np.where(inning_end_mask)[0]
                ended_indices_global = active_indices[ended_indices_local]
                
                current_states[ended_indices_global] = 0
                
                # Flip Sides
                top_end_mask = is_top_inning[ended_indices_global]
                bot_end_mask = ~top_end_mask
                
                top_end_global = ended_indices_global[top_end_mask]
                bot_end_global = ended_indices_global[bot_end_mask]
                
                is_top_inning[top_end_global] = False 
                is_top_inning[bot_end_global] = True 
                current_innings[bot_end_global] += 1 
                
            # --- Check Game Over Conditions ---
            total_home = home_score + runs_home
            total_away = away_score + runs_away
            
            cond_9plus = (current_innings >= 9)
            cond_home_leads = (total_home > total_away)
            cond_away_leads = (total_away > total_home)
            cond_bot = (~is_top_inning)
            cond_top = (is_top_inning)
            
            win_home_mask = cond_9plus & cond_bot & cond_home_leads
            win_away_mask = cond_9plus & cond_top & cond_away_leads & (current_states == 0) & (current_innings > 9)
            
            over_mask = win_home_mask | win_away_mask
            game_over[over_mask] = True
            
        final_home = home_score + runs_home
        final_away = away_score + runs_away
        home_wins = np.sum(final_home > final_away)
        
        return home_wins / n_sims

# Alias for backward compatibility
GameSimulator = MonteCarloSimulator