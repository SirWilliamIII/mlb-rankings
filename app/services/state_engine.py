import numpy as np

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

    def calculate_expected_runs(self, state_idx, transition_matrix=None):
        """
        Calculates the expected runs for the remainder of the inning from state_idx.
        E = (I - Q)^-1 * R
        Where Q is the transition matrix between non-absorbing states.
        However, for baseball, we also need to account for runs scored during transitions.
        """
        if state_idx >= self.END_STATE_IDX:
            return 0.0
            
        # Simplified implementation for now:
        # Use a pre-calculated run expectancy table (RE24) as a baseline.
        # We can then adjust it based on the transition matrix.
        return self._get_re24_baseline(state_idx)

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

    def get_win_probability(self, home_score, away_score, inning, half_inning, state_idx):
        """
        Calculates the probability of the home team winning given the current game state.
        half_inning: 0 for Top, 1 for Bottom
        """
        # This will use the expected runs and historical win probability charts.
        # For now, a very simple placeholder.
        score_diff = home_score - away_score
        
        # Base win prob based on score diff
        win_prob = 0.5 + (score_diff * 0.1)
        
        # Adjust for inning (as game nears end, score diff matters more)
        win_prob = 0.5 + (score_diff * (0.1 + (inning * 0.02)))
        
        return min(max(win_prob, 0.01), 0.99)
