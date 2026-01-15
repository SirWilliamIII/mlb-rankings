import pytest
from app.services.state_engine import StateEngine


@pytest.fixture
def engine():
    return StateEngine()


class TestRE24Baseline:
    """Tests for Run Expectancy (RE24) values."""

    def test_bases_empty_0_outs(self, engine):
        """Bases empty, 0 outs should be ~0.51 runs."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        re24 = engine.calculate_expected_runs(state_idx)
        assert 0.50 <= re24 <= 0.52

    def test_bases_loaded_0_outs(self, engine):
        """Bases loaded, 0 outs should be ~2.36 runs (highest leverage)."""
        state_idx = engine.get_current_state_index(0, 1, 1, 1)
        re24 = engine.calculate_expected_runs(state_idx)
        assert 2.30 <= re24 <= 2.40

    def test_bases_empty_2_outs(self, engine):
        """Bases empty, 2 outs should be ~0.10 runs (lowest leverage)."""
        state_idx = engine.get_current_state_index(2, 0, 0, 0)
        re24 = engine.calculate_expected_runs(state_idx)
        assert 0.08 <= re24 <= 0.12

    def test_end_of_inning(self, engine):
        """3 outs (end of inning) should return 0 runs."""
        state_idx = engine.get_current_state_index(3, 0, 0, 0)
        re24 = engine.calculate_expected_runs(state_idx)
        assert re24 == 0.0


class TestPitcherModifier:
    """Tests for pitcher fatigue/TTTO modifier impact."""

    def test_modifier_neutral(self, engine):
        """Modifier of 1.0 should not change RE24."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        base_re24 = engine._get_re24_baseline(state_idx)
        modified_re24 = engine.calculate_expected_runs(state_idx, pitcher_modifier=1.0)
        assert base_re24 == modified_re24

    def test_modifier_increases_expected_runs(self, engine):
        """Modifier > 1.0 should increase expected runs."""
        state_idx = engine.get_current_state_index(0, 1, 0, 0)  # Runner on 1st
        base_re24 = engine._get_re24_baseline(state_idx)
        modified_re24 = engine.calculate_expected_runs(state_idx, pitcher_modifier=1.15)
        assert modified_re24 == pytest.approx(base_re24 * 1.15, rel=0.01)

    def test_modifier_compound(self, engine):
        """TTTO + Fatigue compound: 1.15 * 1.10 = 1.265."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        base_re24 = engine._get_re24_baseline(state_idx)
        modified_re24 = engine.calculate_expected_runs(state_idx, pitcher_modifier=1.265)
        assert modified_re24 == pytest.approx(base_re24 * 1.265, rel=0.01)


class TestWinProbability:
    """Tests for logistic win probability model.

    Note: Exact probability ranges require calibration with historical data.
    These tests verify directional correctness and reasonable bounds.
    """

    def test_tie_game_start_not_extreme(self, engine):
        """Tie game at start should be in reasonable range (not near 0 or 1)."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        win_prob = engine.get_win_probability(0, 0, 1, 0, state_idx)
        # Should be in the middle range, not extreme
        assert 0.20 <= win_prob <= 0.80

    def test_home_lead_better_than_tie(self, engine):
        """Home +1 should be better than tie."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        tie_prob = engine.get_win_probability(0, 0, 1, 0, state_idx)
        lead_prob = engine.get_win_probability(1, 0, 1, 0, state_idx)
        assert lead_prob > tie_prob

    def test_home_lead_late(self, engine):
        """Home +3 in 9th inning should be very high probability."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        win_prob = engine.get_win_probability(5, 2, 9, 0, state_idx)
        # Late lead should be > 85%
        assert win_prob >= 0.85

    def test_bases_loaded_helps_batting_team(self, engine):
        """Bases loaded should help the batting team's probability."""
        empty_idx = engine.get_current_state_index(0, 0, 0, 0)
        loaded_idx = engine.get_current_state_index(0, 1, 1, 1)

        # Use early inning to avoid clamping
        empty_prob = engine.get_win_probability(3, 3, 3, 1, empty_idx)
        loaded_prob = engine.get_win_probability(3, 3, 3, 1, loaded_idx)
        assert loaded_prob > empty_prob

    def test_bases_loaded_hurts_fielding_team(self, engine):
        """Bases loaded for opponent should hurt the fielding team."""
        empty_idx = engine.get_current_state_index(0, 0, 0, 0)
        loaded_idx = engine.get_current_state_index(0, 1, 1, 1)

        # Top of 9th: away batting with bases loaded should hurt home
        empty_prob = engine.get_win_probability(3, 3, 9, 0, empty_idx)
        loaded_prob = engine.get_win_probability(3, 3, 9, 0, loaded_idx)
        assert loaded_prob < empty_prob

    def test_walkoff_not_needed(self, engine):
        """Home ahead in bottom 9+ should return 1.0 (game over)."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        win_prob = engine.get_win_probability(5, 3, 9, 1, state_idx)
        assert win_prob == 1.0

    def test_extra_innings_no_crash(self, engine):
        """Extra innings should not crash (division by zero protection)."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        # Should not raise, should return reasonable value
        win_prob = engine.get_win_probability(3, 3, 12, 0, state_idx)
        assert 0.05 <= win_prob <= 0.95

    def test_clamped_values(self, engine):
        """Probabilities should be clamped to 0.001-0.999 range."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        # Huge home lead
        win_prob = engine.get_win_probability(15, 0, 9, 0, state_idx)
        assert win_prob <= 0.999
        # Huge away lead
        win_prob = engine.get_win_probability(0, 15, 9, 0, state_idx)
        assert win_prob >= 0.001


class TestFirstPrinciplesCalibration:
    """Tests verifying the first-principles model produces sensible values."""

    def test_tie_game_start_is_hfa_only(self, engine):
        """Tie game, top 1st, bases empty should be ~52-53% (just HFA)."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        win_prob = engine.get_win_probability(0, 0, 1, 0, state_idx)
        # Should be close to 50% + small HFA boost
        assert 0.51 <= win_prob <= 0.55

    def test_one_run_lead_early_modest_advantage(self, engine):
        """Home +1 in 1st should be ~55-62% (modest, lots of game left)."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        win_prob = engine.get_win_probability(1, 0, 1, 0, state_idx)
        assert 0.55 <= win_prob <= 0.65

    def test_bases_loaded_walkoff_threat(self, engine):
        """Tie, bot 9th, bases loaded = very high home probability."""
        loaded_idx = engine.get_current_state_index(0, 1, 1, 1)
        win_prob = engine.get_win_probability(0, 0, 9, 1, loaded_idx)
        # Home only needs 1 run with 2.36 RE24 situation
        assert win_prob >= 0.85

    def test_bases_loaded_away_threat(self, engine):
        """Tie, top 9th, bases loaded = low home probability."""
        loaded_idx = engine.get_current_state_index(0, 1, 1, 1)
        win_prob = engine.get_win_probability(0, 0, 9, 0, loaded_idx)
        # Away threatening with 2.36 RE24 situation
        assert win_prob <= 0.35

    def test_three_run_lead_ninth_commanding(self, engine):
        """Home +3 in 9th should be ~85-95%."""
        state_idx = engine.get_current_state_index(0, 0, 0, 0)
        win_prob = engine.get_win_probability(5, 2, 9, 0, state_idx)
        assert 0.85 <= win_prob <= 0.95


class TestPitcherModifierOnWinProb:
    """Tests for pitcher modifier impact on win probability."""

    def test_tired_pitcher_hurts_defense(self, engine):
        """Tired pitcher should lower home win prob when home is pitching."""
        state_idx = engine.get_current_state_index(0, 1, 0, 0)  # Runner on 1st
        # Top of inning = away batting, home pitching
        # Use earlier inning to avoid clamping at extremes
        base_prob = engine.get_win_probability(3, 3, 5, 0, state_idx, pitcher_modifier=1.0)
        tired_prob = engine.get_win_probability(3, 3, 5, 0, state_idx, pitcher_modifier=1.25)
        # Tired home pitcher should lower home's win probability
        assert tired_prob < base_prob

    def test_tired_pitcher_helps_offense(self, engine):
        """Tired away pitcher should help home when home is batting."""
        state_idx = engine.get_current_state_index(0, 1, 0, 0)
        # Bottom of inning = home batting, away pitching
        # Use very early inning to avoid clamping at extremes
        base_prob = engine.get_win_probability(3, 3, 2, 1, state_idx, pitcher_modifier=1.0)
        tired_prob = engine.get_win_probability(3, 3, 2, 1, state_idx, pitcher_modifier=1.25)
        # Tired away pitcher should help home's win probability
        assert tired_prob > base_prob
