import numpy as np
import math

class StateEngine:
    """
    Micro-State Engine for MLB games using Markov Chain Transition Matrices.
    Calculates expected runs and state transition probabilities.
    """

    # 24 Base/Out States
    # Format: (outs, runner_on_1st, runner_on_2nd, runner_on_3rd)
    STATES = [
        (o, r1, r2, r3)
        for o in range(3)
        for r1 in [0, 1]
        for r2 in [0, 1]
        for r3 in [0, 1]
    ]
    STATE_TO_IDX = {state: i for i, state in enumerate(STATES)}
    IDX_TO_STATE = {i: state for i, state in enumerate(STATES)}
    END_STATE_IDX = 24 # 3 Outs

    # First-principles constants (derived from MLB scoring data)
    VOLATILITY_SCALE = 1.17   # Derived: 3.5 runs std dev / 3 = 1.17
    HOME_FIELD_Z = 0.10       # ~53-54% win prob at tie (historical HFA)
    BASELINE_RE24 = 0.51      # Expected runs for "null state" (bases empty, 0 outs)

    def __init__(self):
        # Add End State label
        self.IDX_TO_STATE[self.END_STATE_IDX] = "End of Inning"
        
        # League Average Transition Probabilities (Placeholder - will be refined)
        # In a production environment, these would be derived from historical play-by-play data.
        self.base_transition_matrix = self._initialize_base_matrix()

    def _initialize_base_matrix(self):
        """
        Initializes a 25x25 transition matrix with baseline probabilities.
        """
        # Initialize with zeros
        matrix = np.zeros((25, 25))
        
        # Simplified MLB Transition Probabilities (Approximate League Averages)
        # Event Probabilities:
        # Out: 0.68, 1B: 0.15, 2B: 0.05, 3B: 0.005, HR: 0.03, BB/HBP: 0.085
        
        # These basic event probabilities map to state transitions depending on the current state.
        # This is a simplified "Bucket" model where runners advance standard amounts.
        
        p_out = 0.68
        p_1b = 0.15
        p_2b = 0.05
        p_3b = 0.005
        p_hr = 0.03
        p_bb = 0.085
        
        # We iterate through all 24 base/out states to define their transitions
        for idx in range(24):
            outs, r1, r2, r3 = self.IDX_TO_STATE[idx]
            
            # 1. OUTS
            if outs < 2:
                next_state_out = self.get_current_state_index(outs + 1, r1, r2, r3)
                matrix[idx, next_state_out] += p_out
            else:
                matrix[idx, self.END_STATE_IDX] += p_out

            # 2. WALKS (Force plays only)
            # If 1st is empty, runner goes to 1st.
            # If 1st occupied, r1->2. If 2nd occupied, r2->3. If 3rd occupied, run scores (state unchanged w.r.t runners except force)
            new_r1, new_r2, new_r3 = 1, r1, r2 # Default walk logic (force)
            if r1 == 0: new_r2, new_r3 = r2, r3 # No force at 2nd/3rd
            elif r2 == 0: new_r3 = r3 # No force at 3rd
            
            next_state_bb = self.get_current_state_index(outs, new_r1, new_r2, new_r3)
            matrix[idx, next_state_bb] += p_bb

            # 3. SINGLES (Assume runner on 2nd scores, runner on 1st goes to 2nd)
            # Standard: R1->2, R2->Score, R3->Score
            next_state_1b = self.get_current_state_index(outs, 1, (1 if r1 else 0), 0)
            matrix[idx, next_state_1b] += p_1b

            # 4. DOUBLES (Assume R1->3, R2->Score, R3->Score)
            next_state_2b = self.get_current_state_index(outs, 0, 1, (1 if r1 else 0))
            matrix[idx, next_state_2b] += p_2b

            # 5. TRIPLES (Clear bases, runner on 3rd)
            next_state_3b = self.get_current_state_index(outs, 0, 0, 1)
            matrix[idx, next_state_3b] += p_3b

            # 6. HOMERS (Clear bases)
            next_state_hr = self.get_current_state_index(outs, 0, 0, 0)
            matrix[idx, next_state_hr] += p_hr
            
            # Normalize row (handle rounding errors)
            row_sum = np.sum(matrix[idx])
            if row_sum > 0:
                matrix[idx] /= row_sum
                
        # End state stays in end state
        matrix[self.END_STATE_IDX, self.END_STATE_IDX] = 1.0

        return matrix

    def get_current_state_index(self, outs, runner_on_1st, runner_on_2nd, runner_on_3rd):
        """
        Returns the index of the current state.
        """
        if outs >= 3:
            return self.END_STATE_IDX
            
        state = (outs, int(runner_on_1st), int(runner_on_2nd), int(runner_on_3rd))
        return self.STATE_TO_IDX.get(state, self.END_STATE_IDX)

    def calculate_expected_runs(self, state_idx, pitcher_modifier=1.0):
        """
        Calculates the expected runs for the remainder of the inning from state_idx.

        Args:
            state_idx: The current base/out state index (0-23, or 24 for end of inning)
            pitcher_modifier: Float coefficient for pitcher quality/fatigue.
                              1.0 = average pitcher
                              >1.0 = compromised pitcher (expect more runs)
                              <1.0 = dominant pitcher (expect fewer runs)
        """
        if state_idx >= self.END_STATE_IDX:
            return 0.0

        base_re24 = self._get_re24_baseline(state_idx)
        return base_re24 * pitcher_modifier

    def _get_re24_baseline(self, state_idx):
        """
        Standard RE24 table (Run Expectancy based on 24 states).
        Source: Average MLB run expectancy (approximate).
        """
        # Outs: 0
        # 000: 0.51, 100: 0.91, 010: 1.14, 001: 1.40, 110: 1.48, 101: 1.73, 011: 2.01, 111: 2.36
        # Outs: 1
        # 000: 0.27, 100: 0.53, 010: 0.69, 001: 0.95, 110: 0.94, 101: 1.18, 011: 1.44, 111: 1.63
        # Outs: 2
        # 000: 0.10, 100: 0.22, 010: 0.32, 001: 0.38, 110: 0.44, 101: 0.53, 011: 0.60, 111: 0.77
        
        re24_values = [
            0.51, 0.91, 1.14, 1.40, 1.48, 1.73, 2.01, 2.36, # 0 Outs
            0.27, 0.53, 0.69, 0.95, 0.94, 1.18, 1.44, 1.63, # 1 Out
            0.10, 0.22, 0.32, 0.38, 0.44, 0.53, 0.60, 0.77  # 2 Outs
        ]
        
        if state_idx < len(re24_values):
            return re24_values[state_idx]
        return 0.0

    def get_win_probability(self, home_score, away_score, inning, half_inning,
                            state_idx, pitcher_modifier=1.0):
        """
        Calculates the probability of the home team winning using logistic regression
        with 'Leverage Delta' approach.

        The key insight: we only care about runs ABOVE the baseline expectation.
        Bases empty at start of inning = leverage of 0 (neutral).
        Bases loaded = leverage of +1.85 runs (high swing potential).

        Args:
            home_score: Current home team runs
            away_score: Current away team runs
            inning: Current inning (1-9+)
            half_inning: 0 for Top (away batting), 1 for Bottom (home batting)
            state_idx: Current base/out state index
            pitcher_modifier: Float coefficient for pitcher fatigue/TTTO
        """
        # Handle walk-off not needed (home already ahead in bottom 9+)
        if inning >= 9 and half_inning == 1 and home_score > away_score:
            return 1.0

        # 1. Raw score differential
        score_diff = home_score - away_score

        # 2. Calculate Leverage Delta (marginal value above baseline)
        # This is the key fix: we don't use raw RE24, only the DELTA from null state
        current_re24 = self.calculate_expected_runs(state_idx, pitcher_modifier)
        leverage = current_re24 - self.BASELINE_RE24

        # 3. Apply leverage based on who's batting
        if half_inning == 1:  # Bottom - home batting, leverage helps home
            effective_diff = score_diff + leverage
        else:  # Top - away batting, leverage hurts home
            effective_diff = score_diff - leverage

        # 4. Innings remaining (precision calculation)
        # Top of inning: full half-inning + remaining full innings
        # Bottom of inning: partial half-inning + remaining full innings
        if inning >= 9:
            innings_remaining = 0.5 + (1.0 if half_inning == 0 else 0.0)
        else:
            innings_remaining = (9 - inning) + (1.0 if half_inning == 0 else 0.5)
        innings_remaining = max(innings_remaining, 0.5)

        # 5. Volatility (std dev of remaining score differential)
        # Derived: sqrt(innings_remaining / 9) * 3.5 = 1.17 * sqrt(innings_remaining)
        std_dev = self.VOLATILITY_SCALE * math.sqrt(innings_remaining)

        # 6. Z-score with home field advantage
        z = (effective_diff / std_dev) + self.HOME_FIELD_Z

        # 7. Sigmoid function
        win_prob = 1.0 / (1.0 + math.exp(-z))

        # 8. Clamp (widened - blowouts do happen)
        return min(0.999, max(0.001, win_prob))
