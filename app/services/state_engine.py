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

    # Tunable calibration constants
    HOME_FIELD_Z = 0.12       # ~3-4% win prob boost (calibrate with historical data)
    VOLATILITY_SCALE = 0.25   # Tune with Brier score on historical outcomes

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
        
        # This is a complex matrix to fill manually with accuracy.
        # For now, we will use a simplified transition logic:
        # Every state has a probability to move to another state or end the inning.
        # We'll refine this with real matchup data.
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
        Calculates the probability of the home team winning using logistic regression.

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

        score_diff = home_score - away_score
        re24 = self._get_re24_baseline(state_idx) * pitcher_modifier

        # Effective run differential: who benefits from baserunners?
        if half_inning == 1:  # Bottom - home batting, RE24 helps home
            effective_diff = score_diff + re24
        else:  # Top - away batting, RE24 hurts home
            effective_diff = score_diff - re24

        # Innings remaining (handle extras, avoid division by zero)
        if inning >= 9:
            innings_remaining = 0.5 + (1.0 if half_inning == 0 else 0.0)
        else:
            innings_remaining = (9 - inning) + (0.5 if half_inning == 0 else 0.0)

        # Z-score: run differential normalized by remaining volatility + home advantage
        volatility = self.VOLATILITY_SCALE * math.sqrt(max(0.5, innings_remaining))
        z = (effective_diff / volatility) + self.HOME_FIELD_Z

        # Sigmoid function, clamped for live betting realism (books never show 99%)
        win_prob = 1.0 / (1.0 + math.exp(-z))
        return min(0.95, max(0.05, win_prob))
