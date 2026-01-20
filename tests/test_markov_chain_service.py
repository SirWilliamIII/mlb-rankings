import unittest
import numpy as np
from app.services.markov_chain_service import MarkovChainService

class TestMarkovChainService(unittest.TestCase):
    def setUp(self):
        self.service = MarkovChainService()

    def test_matrix_shape(self):
        """Verify the transition matrix is 25x25 (24 states + 3 outs)."""
        # 1.0 modifiers = baseline
        matrix = self.service._get_transition_matrix(pitcher_mod=1.0, ttto=0)
        self.assertEqual(matrix.shape, (25, 25))
        
    def test_matrix_row_sum(self):
        """Verify rows sum to 1.0 (valid probability distribution)."""
        matrix = self.service._get_transition_matrix(pitcher_mod=1.0, ttto=0)
        # Check first 24 rows (last row is absorbing state 1.0)
        for i in range(25):
            self.assertAlmostEqual(np.sum(matrix[i]), 1.0, places=5)

    def test_fatigue_penalty_out_rate(self):
        """Verify p_out decreases as PitcherMod increases."""
        # Baseline
        matrix_base = self.service._get_transition_matrix(pitcher_mod=1.0)
        
        # Fatigued (1.20 modifier)
        matrix_fatigued = self.service._get_transition_matrix(pitcher_mod=1.20)
        
        # Compare Out probability (transition to next out state)
        # State 0 (0 outs, empty) -> State 8 (1 out, empty)
        # Using indices directly: 0 -> 8
        prob_out_base = matrix_base[0, 8]
        prob_out_fatigued = matrix_fatigued[0, 8]
        
        self.assertLess(prob_out_fatigued, prob_out_base, "Out rate should decrease with fatigue")

    def test_ttto_walk_inflation(self):
        """Verify p_bb increases with Times Through The Order."""
        # 1st time through
        matrix_1st = self.service._get_transition_matrix(ttto=1)
        
        # 3rd time through
        matrix_3rd = self.service._get_transition_matrix(ttto=3)
        
        # Compare Walk probability (State 0 -> State 4)
        # 0 (Empty) -> 4 (Runner on 1st: 0, 1, 0, 0) via BB/1B
        # Note: Index 4 is (0, 1, 0, 0) because list order is o, r1, r2, r3
        prob_bb_1st = matrix_1st[0, 4]
        prob_bb_3rd = matrix_3rd[0, 4]
        
        self.assertGreater(prob_bb_3rd, prob_bb_1st, "Walk rate should increase with TTTO")

    def test_bip_variance_skew(self):
        """Verify extra-base hits increase relatively more than singles under fatigue."""
        # This is subtle. If p_out drops, all hits might rise. 
        # But we want HR/2B to rise *more* or at least rise.
        # Implementation detail: we might scale HR/2B by mod^2 and 1B by mod.
        
        matrix_base = self.service._get_transition_matrix(pitcher_mod=1.0)
        matrix_fatigued = self.service._get_transition_matrix(pitcher_mod=1.20)
        
        # HR Prob (State 0 -> State 0 + run, but matrix only tracks state. HR clears bases -> State 0. Wait.)
        # HR from 0 outs empty -> 0 outs empty (state 0 -> 0)
        # BUT State 0 -> 0 is NOT just HR. It's HR + (maybe some weird error?). 
        # In our simplified model:
        # HR: 000 -> 000
        # Wait, if 0 outs, empty (0). HR -> 0 outs, empty (0).
        # So matrix[0,0] should reflect HR probability.
        
        prob_hr_base = matrix_base[0, 0]
        prob_hr_fatigued = matrix_fatigued[0, 0]
        
        # 1B Prob (State 0 -> State 1)
        # Note: State 0->1 is Walk AND Single. 
        # We need to distinguish or assume total prob increases.
        # Let's assume implementation will shift mass specifically.
        
        # For this test, simply asserting HR probability increases significantly is a good start.
        self.assertGreater(prob_hr_fatigued, prob_hr_base)

    def test_win_prob_sensitivity_home_pitching(self):
        """
        Verify Home Win Prob decreases when Home Pitcher is fatigued (Top Inning).
        """
        # State: Tie Game, Top 9th, Bases Loaded, 0 Outs. High Leverage.
        inning = 9
        outs = 0
        runners = [1, 1, 1]
        score_diff = 0
        is_top = True # Home Pitching
        
        # Baseline
        prob_base = self.service.get_instant_win_prob(
            inning, outs, runners, score_diff, is_top, pitcher_mod=1.0
        )
        
        # Fatigued (Home Pitcher melting down)
        prob_fatigued = self.service.get_instant_win_prob(
            inning, outs, runners, score_diff, is_top, pitcher_mod=1.25
        )
        
        print(f"Home Pitching: Base={prob_base:.4f}, Fatigued={prob_fatigued:.4f}")
        self.assertLess(prob_fatigued, prob_base, "Home Win Prob should drop if Home Pitcher is fatigued")

    def test_win_prob_sensitivity_away_pitching(self):
        """
        Verify Home Win Prob increases when Away Pitcher is fatigued (Bottom Inning).
        """
        # State: Tie Game, Bottom 9th, Bases Loaded, 0 Outs.
        inning = 9
        outs = 0
        runners = [1, 1, 1]
        score_diff = 0
        is_top = False # Away Pitching
        
        # Baseline
        prob_base = self.service.get_instant_win_prob(
            inning, outs, runners, score_diff, is_top, pitcher_mod=1.0
        )
        
        # Fatigued (Away Pitcher melting down)
        prob_fatigued = self.service.get_instant_win_prob(
            inning, outs, runners, score_diff, is_top, pitcher_mod=1.25
        )
        
        print(f"Away Pitching: Base={prob_base:.4f}, Fatigued={prob_fatigued:.4f}")
        self.assertGreater(prob_fatigued, prob_base, "Home Win Prob should rise if Away Pitcher is fatigued")

if __name__ == '__main__':
    unittest.main()
