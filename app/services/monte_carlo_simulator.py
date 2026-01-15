import numpy as np
from app.services.state_engine import StateEngine

class MonteCarloSimulator:
    """
    High-performance Vectorized Monte Carlo Simulator for MLB Live Games.
    Simulates 'Rest of Game' outcomes using Markov Chain transitions.
    """

    def __init__(self, state_engine=None):
        self.state_engine = state_engine if state_engine else StateEngine()
        
        # Pre-compute matrices for vectorized operations
        # Dimensions: 25 States (0-23 + End)
        self.transition_matrix = np.zeros((25, 25))
        self.run_matrix = np.zeros((25, 25))
        
        self._build_matrices()
        
        # Pre-compute Cumulative Distribution Function (CDF) for fast sampling
        # We process the transition matrix into a CDF for each state row
        self.cdf_matrix = np.cumsum(self.transition_matrix, axis=1)

    def _build_matrices(self):
        """
        Reconstructs the StateEngine's transition logic into 
        Numpy-compatible Probability (P) and Run (R) matrices.
        """
        # Event Probabilities (Must match StateEngine)
        p_out = 0.68
        p_1b = 0.15
        p_2b = 0.05
        p_3b = 0.005
        p_hr = 0.03
        p_bb = 0.085
        
        # Re-iterate logic to capture Runs Scored, which StateEngine doesn't explicitly store in the matrix
        for idx in range(24):
            outs, r1, r2, r3 = self.state_engine.IDX_TO_STATE[idx]
            
            # 1. OUTS
            if outs < 2:
                next_state_out = self.state_engine.get_current_state_index(outs + 1, r1, r2, r3)
                self.transition_matrix[idx, next_state_out] += p_out
                self.run_matrix[idx, next_state_out] = 0 # 0 runs on generic out (ignoring sac flies for now)
            else:
                self.transition_matrix[idx, self.state_engine.END_STATE_IDX] += p_out
                self.run_matrix[idx, self.state_engine.END_STATE_IDX] = 0

            # 2. WALKS
            new_r1, new_r2, new_r3 = 1, r1, r2
            runs_bb = 0
            if r1 == 1:
                if r2 == 1:
                    if r3 == 1:
                        runs_bb = 1 # Bases loaded walk
                    else:
                        new_r3 = 1
                else:
                    new_r2 = 1
            else:
                new_r2, new_r3 = r2, r3
            
            next_state_bb = self.state_engine.get_current_state_index(outs, new_r1, new_r2, new_r3)
            self.transition_matrix[idx, next_state_bb] += p_bb
            self.run_matrix[idx, next_state_bb] = runs_bb

            # 3. SINGLES (R2 scores, R3 scores)
            # Assumption: R1 goes to 2nd, R2 scores, R3 scores
            runs_1b = r3 + r2
            next_state_1b = self.state_engine.get_current_state_index(outs, 1, 1 if r1 else 0, 0)
            self.transition_matrix[idx, next_state_1b] += p_1b
            self.run_matrix[idx, next_state_1b] = runs_1b

            # 4. DOUBLES (R1->3, R2 scores, R3 scores)
            runs_2b = r3 + r2
            next_state_2b = self.state_engine.get_current_state_index(outs, 0, 1, 1 if r1 else 0)
            self.transition_matrix[idx, next_state_2b] += p_2b
            self.run_matrix[idx, next_state_2b] = runs_2b

            # 5. TRIPLES (All score)
            runs_3b = r1 + r2 + r3
            next_state_3b = self.state_engine.get_current_state_index(outs, 0, 0, 1)
            self.transition_matrix[idx, next_state_3b] += p_3b
            self.run_matrix[idx, next_state_3b] = runs_3b

            # 6. HOMERS (All + Batter score)
            runs_hr = r1 + r2 + r3 + 1
            next_state_hr = self.state_engine.get_current_state_index(outs, 0, 0, 0)
            self.transition_matrix[idx, next_state_hr] += p_hr
            self.run_matrix[idx, next_state_hr] = runs_hr
            
            # Normalize probabilities (essential for random sampling)
            row_sum = np.sum(self.transition_matrix[idx])
            if row_sum > 0:
                self.transition_matrix[idx] /= row_sum
                
        # End State Identity
        self.transition_matrix[self.state_engine.END_STATE_IDX, self.state_engine.END_STATE_IDX] = 1.0

    def simulate_game_vectorized(self, initial_state_idx, home_score, away_score, inning, is_top, iterations=10000):
        """
        Simulates the remainder of the game N times using vectorized operations.
        Returns win probability for the Home team.
        """
        n_sims = iterations
        
        # 1. Initialize State Vectors
        # Current Base/Out State for each sim
        current_states = np.full(n_sims, initial_state_idx, dtype=int)
        
        # Runs Scored in the remainder of the game (Home/Away)
        # We track "runs added" separately.
        runs_home = np.zeros(n_sims, dtype=int)
        runs_away = np.zeros(n_sims, dtype=int)
        
        # Game Progress Tracking
        current_innings = np.full(n_sims, inning, dtype=int)
        is_top_inning = np.full(n_sims, is_top, dtype=bool) # True=Top(Away), False=Bot(Home)
        game_over = np.zeros(n_sims, dtype=bool)

        # Simulation Loop (Step-by-step for all N sims)
        # In baseball, max batters in an inning is theoretically infinite, but practically bounded.
        # We loop until all games are over.
        max_steps = 200 # Safety break
        
        for _ in range(max_steps):
            if np.all(game_over):
                break
                
            # Filter active games
            active_mask = ~game_over
            if not np.any(active_mask):
                break
                
            active_indices = np.where(active_mask)[0]
            active_states = current_states[active_mask]
            
            # --- Vectorized Transition ---
            # Generate random numbers for transition
            rand_vals = np.random.rand(len(active_indices))
            
            # Fast lookup of next state using CDF
            # We select the column index where CDF > rand_val
            # This is tricky to vectorize fully for different states (rows).
            # Solution: Fancy Indexing with searchsorted is too slow for 2D.
            # Faster approach for Matrix Sampling:
            # Since N=25 states is small, we can iterate states? No, N_Sims is large (10k).
            # We can use np.random.choice but it's slow in a loop.
            # Best Vectorized Approach: 
            #   current_cdf = self.cdf_matrix[active_states] # Shape (N_active, 25)
            #   next_state_indices = (current_cdf < rand_vals[:, None]).sum(axis=1)
            #   (Because CDF is cumulative, sum of "less thans" gives the index)
            
            current_cdf = self.cdf_matrix[active_states]
            # Next state is the first index where random < cdf
            # argmax on boolean array gives first True.
            # condition: cdf >= random
            next_states = (current_cdf >= rand_vals[:, None]).argmax(axis=1)
            
            # Get Runs Scored on this transition
            # self.run_matrix is 25x25. We need values at [old, new]
            transition_runs = self.run_matrix[active_states, next_states]
            
            # Update Runs
            # If is_top (Away Batting), add to Away. Else Home.
            # We need to apply this only to active sims
            runs_away[active_indices] += (transition_runs * is_top_inning[active_mask]).astype(int)
            runs_home[active_indices] += (transition_runs * (~is_top_inning[active_mask])).astype(int)
            
            # Update States
            current_states[active_indices] = next_states
            
            # --- Handle Inning Changes ---
            # If state reached END_STATE (3 Outs)
            inning_end_mask = (current_states[active_indices] == self.state_engine.END_STATE_IDX)
            
            if np.any(inning_end_mask):
                # Indices within the active set
                ended_indices_local = np.where(inning_end_mask)[0]
                ended_indices_global = active_indices[ended_indices_local]
                
                # Reset State to 0 (0 Outs, Empty)
                current_states[ended_indices_global] = 0
                
                # Flip Inning Side / Increment Inning
                # If Top -> Bot (Same Inning)
                # If Bot -> Top (Next Inning)
                
                # We need to update is_top and inning vectors
                # Logic: if is_top: is_top=False. else: is_top=True, inning+=1
                
                # Vectorized Update:
                # 1. Identify Top endings
                top_end_mask = is_top_inning[ended_indices_global]
                
                # 2. Identify Bot endings
                bot_end_mask = ~top_end_mask
                
                # Global indices for Top/Bot endings
                top_end_global = ended_indices_global[top_end_mask]
                bot_end_global = ended_indices_global[bot_end_mask]
                
                # Apply updates
                is_top_inning[top_end_global] = False # Top -> Bot
                
                is_top_inning[bot_end_global] = True # Bot -> Top
                current_innings[bot_end_global] += 1 # Increment Inning
                
            # --- Check Game Over Conditions ---
            # Recalculate Totals
            total_home = home_score + runs_home
            total_away = away_score + runs_away
            
            # Condition 1: Middle of 9th (or later) and Home leads
            # (Inning >= 9 AND is_top=False AND Home > Away)
            # wait, middle of 9th is when Top 9 ends.
            # So if Inning >= 9 AND just finished Top (now is_top is False) AND Home > Away.
            
            # Condition 2: End of 9th (or later) and Away leads
            # (Inning >= 10 AND is_top=True AND Away > Home) -- wait, if 9th ends, inning becomes 10, is_top becomes True.
            
            # Let's simplify:
            # Game Over if:
            # 1. Inning >= 9
            # 2. AND (
            #      (is_top=False AND total_home > total_away)  # Home winning in bottom (Walkoff or Mid-Inning)
            #      OR 
            #      (is_top=True AND Inning >= 10 AND total_away != total_home) # End of full inning (after Bot 9/10/etc) and not tied
            #    )
            # Wait, "End of full inning" means we are ABOUT to start Top of Next Inning.
            # So if current_state is 0 (start of inning) and inning >= 10.
            
            # Actually, check strictly at transition points or state changes is safer.
            
            # Simplified Logic check for vector:
            cond_9plus = (current_innings >= 9)
            cond_home_leads = (total_home > total_away)
            cond_away_leads = (total_away > total_home)
            cond_bot = (~is_top_inning)
            cond_top = (is_top_inning)
            
            # Walkoff / Home Leads in Bottom 9+
            win_home_mask = cond_9plus & cond_bot & cond_home_leads
            
            # Away Wins: End of Bottom 9+ (so start of Top 10+) and Away Leads
            # Note: "End of Bottom 9" transitions to "Start of Top 10"
            # So if we are at Start of Top 10 (State 0) and Away Leads...
            win_away_mask = cond_9plus & cond_top & cond_away_leads & (current_states == 0) & (current_innings > 9)
            
            # Wait, standard regulation end:
            # End of 9th inning. Inning becomes 10, is_top becomes True.
            # If Away > Home, Away wins.
            # If Home > Away, Home won already (caught by win_home_mask).
            # If Tie, continue.
            
            over_mask = win_home_mask | win_away_mask
            game_over[over_mask] = True
            
        # 3. Calculate Win %
        final_home = home_score + runs_home
        final_away = away_score + runs_away
        home_wins = np.sum(final_home > final_away)
        
        return home_wins / n_sims

# Alias for backward compatibility
GameSimulator = MonteCarloSimulator