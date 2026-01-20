import numpy as np
from app.services.state_engine import StateEngine

class MarkovChainService:
    """
    Phase 2: Micro-State Markov Engine.
    Provides O(1) lookups for Win Probability based on Game State.
    Replaces slow Monte Carlo simulations with pre-calculated Transition Matrices.
    """

    # 24 Base/Out States (Same as StateEngine)
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

    def __init__(self):
        self.state_engine = StateEngine()
        self.transition_cache = {}
        self._init_masks()
        self._init_run_masks()

    def _init_masks(self):
        """Pre-compute transition masks for O(1) matrix generation."""
        self.mask_out = np.zeros((25, 25))
        self.mask_bb = np.zeros((25, 25))
        self.mask_1b = np.zeros((25, 25))
        self.mask_2b = np.zeros((25, 25))
        self.mask_3b = np.zeros((25, 25))
        self.mask_hr = np.zeros((25, 25))
        
        for idx in range(24):
            outs, r1, r2, r3 = self.IDX_TO_STATE[idx]
            
            # Outs
            if outs < 2:
                next_out = self._get_state_index(outs + 1, r1, r2, r3)
                self.mask_out[idx, next_out] = 1.0
            else:
                self.mask_out[idx, self.END_STATE_IDX] = 1.0
                
            # BB
            new_r1, new_r2, new_r3 = 1, r1, r2
            if r1 == 0: new_r2, new_r3 = r2, r3
            elif r2 == 0: new_r3 = r3
            self.mask_bb[idx, self._get_state_index(outs, new_r1, new_r2, new_r3)] = 1.0
            
            # 1B
            self.mask_1b[idx, self._get_state_index(outs, 1, 1 if r1 else 0, 0)] = 1.0
            # 2B
            self.mask_2b[idx, self._get_state_index(outs, 0, 1, 1 if r1 else 0)] = 1.0
            # 3B
            self.mask_3b[idx, self._get_state_index(outs, 0, 0, 1)] = 1.0
            # HR
            self.mask_hr[idx, self._get_state_index(outs, 0, 0, 0)] = 1.0
            
        # End State
        self.mask_out[self.END_STATE_IDX, self.END_STATE_IDX] = 1.0

    def _init_run_masks(self):
        """Pre-compute runs scored for each event from each state."""
        self.runs_hr = np.zeros(24)
        self.runs_3b = np.zeros(24)
        self.runs_2b = np.zeros(24)
        self.runs_1b = np.zeros(24)
        self.runs_bb = np.zeros(24)
        
        for idx in range(24):
            # outs, r1, r2, r3 = self.IDX_TO_STATE[idx]
            # Easier to decode from list directly
            _, r1, r2, r3 = self.STATES[idx]
            
            # HR: 1 + all runners
            self.runs_hr[idx] = 1 + r1 + r2 + r3
            
            # 3B: all runners
            self.runs_3b[idx] = r1 + r2 + r3
            
            # 2B: all runners (StateEngine: "Assume R1->3, R2->Score, R3->Score")
            # So R2 and R3 score. R1 goes to 3rd (does not score).
            self.runs_2b[idx] = r2 + r3
            
            # 1B: "Assume runner on 2nd scores, runner on 1st goes to 2nd"
            # So R2 scores, R3 scores. R1 -> 2nd (no score).
            self.runs_1b[idx] = r2 + r3
            
            # BB: Forced.
            # Score if Loaded (111).
            if r1 and r2 and r3:
                self.runs_bb[idx] = 1
            else:
                self.runs_bb[idx] = 0

    def get_instant_win_prob(self, inning, outs, runners, score_diff, is_top_inning, pitcher_mod=1.0, defense_mod=1.0):
        """
        Returns the Win Probability for the Home Team.
        """
        # 1. Construct Lookup Key
        runner_mask = 0
        if runners[0]: runner_mask += 1
        if runners[1]: runner_mask += 2
        if runners[2]: runner_mask += 4
        
        # TTTO approximation (placeholder, should be passed in)
        ttto = 1 
        
        # 2. Get Matrix
        matrix = self._get_transition_matrix(pitcher_mod, ttto, defense_mod)
        
        # 3. Calculate RE24 Vector (Expected Runs) from Matrix
        re24_vector = self._calculate_re24_vector(matrix)
        
        # 4. Get Current State Index
        state_idx = self.state_engine.get_current_state_index(outs, runners[0], runners[1], runners[2])
        
        # 5. Extract Expected Runs for current state
        if state_idx < 24:
            current_re24 = re24_vector[state_idx]
        else:
            current_re24 = 0.0
            
        # 6. Apply Sigmoid Logic (Leverage Delta)
        # Constants from StateEngine
        BASELINE_RE24 = 0.51
        VOLATILITY_SCALE = 1.17
        HOME_FIELD_Z = 0.10
        
        leverage = current_re24 - BASELINE_RE24
        
        if is_top_inning: # Away batting
            effective_diff = score_diff - leverage
        else: # Home batting
            effective_diff = score_diff + leverage
            
        # Innings remaining logic
        if inning >= 9:
            innings_remaining = 0.5 + (1.0 if not is_top_inning else 0.0)
        else:
            innings_remaining = (9 - inning) + (1.0 if not is_top_inning else 0.5)
        innings_remaining = max(innings_remaining, 0.5)
        
        std_dev = VOLATILITY_SCALE * np.sqrt(innings_remaining)
        z = (effective_diff / std_dev) + HOME_FIELD_Z
        win_prob = 1.0 / (1.0 + np.exp(-z))
        
        return min(0.999, max(0.001, win_prob))

    def _get_transition_matrix(self, pitcher_mod=1.0, ttto=0, defense_mod=1.0):
        """
        Generates a 25x25 transition matrix adjusted for pitcher fatigue.
        Optimized: Uses pre-computed masks for vector addition.
        """
        # Base Probabilities
        p_out = 0.68
        p_1b = 0.15
        p_2b = 0.05
        p_3b = 0.005
        p_hr = 0.03
        p_bb = 0.085
        
        # Adjustments
        if ttto > 1:
            p_bb *= (1.0 + (0.10 * (ttto - 1)))

        p_1b *= pitcher_mod
        p_bb *= pitcher_mod
        
        power_scaler = pitcher_mod
        if pitcher_mod > 1.0:
            power_scaler *= 1.1
            
        p_2b *= power_scaler
        p_3b *= power_scaler
        p_hr *= power_scaler
        
        # Defense Adjustment (Phase 3 Hardening)
        if defense_mod > 1.0:
            p_1b *= defense_mod
            p_bb *= defense_mod # Errors extend innings like walks
        
        # Vectorized Combination
        matrix = (
            self.mask_out * p_out +
            self.mask_bb * p_bb +
            self.mask_1b * p_1b +
            self.mask_2b * p_2b +
            self.mask_3b * p_3b +
            self.mask_hr * p_hr
        )
        
        # Row Normalization (Fast)
        row_sums = matrix.sum(axis=1)[:, np.newaxis]
        matrix /= row_sums
        
        # R_imm Construction (Immediate Runs Vector)
        # We only care about the first 24 states for R_imm
        inv_row_sums_24 = 1.0 / row_sums[:24].flatten()
        
        r_imm = (
            (self.runs_hr * p_hr) +
            (self.runs_3b * p_3b) +
            (self.runs_2b * p_2b) +
            (self.runs_1b * p_1b) +
            (self.runs_bb * p_bb)
        )
        
        # Normalize R_imm by the same row_sums
        r_imm *= inv_row_sums_24
        
        # Store for solver
        self._last_r_imm = r_imm
        
        return matrix

    def _calculate_re24_vector(self, matrix):
        """
        Solves (I - Q)^-1 * R_imm to get Expected Runs for all states.
        """
        # Extract Q (Transient 24x24)
        Q = matrix[:24, :24]
        I = np.eye(24)
        
        try:
            N = np.linalg.inv(I - Q)
        except np.linalg.LinAlgError:
            return np.zeros(24)
            
        if hasattr(self, '_last_r_imm'):
            R_imm = self._last_r_imm
        else:
            R_imm = np.zeros(24)
        
        # Total Expected Runs = N * R_imm
        E = N @ R_imm
        return E

    def _get_state_index(self, outs, r1, r2, r3):
        if outs >= 3: return self.END_STATE_IDX
        state = (outs, int(r1), int(r2), int(r3))
        return self.STATE_TO_IDX.get(state, self.END_STATE_IDX)