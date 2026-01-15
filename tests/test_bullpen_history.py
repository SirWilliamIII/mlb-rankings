# tests/test_bullpen_history.py

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.services.bullpen_history_service import BullpenHistoryService


@pytest.fixture
def service():
    return BullpenHistoryService()


@pytest.fixture
def mock_dates():
    """Returns consistent date strings for testing."""
    today = datetime.now()
    return {
        'today': today.strftime('%Y-%m-%d'),
        'yesterday': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
        'day_before': (today - timedelta(days=2)).strftime('%Y-%m-%d'),
        'three_days_ago': (today - timedelta(days=3)).strftime('%Y-%m-%d'),
    }


class TestFatigueCalculations:
    """Tests for the _calculate_fatigue_metrics method."""

    def test_dead_arm_consecutive_days(self, service, mock_dates):
        """Pitcher who pitched yesterday AND day before should be 'Dead'."""
        pitcher_logs = {
            12345: {
                'name': 'Test Pitcher',
                'appearances': [
                    {'date': mock_dates['yesterday'], 'pitches': 20},
                    {'date': mock_dates['day_before'], 'pitches': 15},
                ]
            }
        }

        result = service._calculate_fatigue_metrics(pitcher_logs)

        assert result[12345]['status'] == 'Dead'
        assert result[12345]['modifier'] == 1.25
        assert result[12345]['consecutive_days'] == 2

    def test_tired_high_pitch_yesterday(self, service, mock_dates):
        """Pitcher with >25 pitches yesterday (but not consecutive) should be 'Tired'."""
        pitcher_logs = {
            12345: {
                'name': 'Test Pitcher',
                'appearances': [
                    {'date': mock_dates['yesterday'], 'pitches': 30},
                ]
            }
        }

        result = service._calculate_fatigue_metrics(pitcher_logs)

        assert result[12345]['status'] == 'Tired'
        assert result[12345]['modifier'] == 1.15
        assert result[12345]['consecutive_days'] == 1

    def test_fresh_no_recent_pitches(self, service, mock_dates):
        """Pitcher with no pitches in last 2 days should be 'Fresh'."""
        pitcher_logs = {
            12345: {
                'name': 'Test Pitcher',
                'appearances': [
                    {'date': mock_dates['three_days_ago'], 'pitches': 40},
                ]
            }
        }

        result = service._calculate_fatigue_metrics(pitcher_logs)

        assert result[12345]['status'] == 'Fresh'
        assert result[12345]['modifier'] == 1.0
        assert result[12345]['consecutive_days'] == 0

    def test_fresh_low_pitch_yesterday(self, service, mock_dates):
        """Pitcher with <=25 pitches yesterday (not consecutive) should be 'Fresh'."""
        pitcher_logs = {
            12345: {
                'name': 'Test Pitcher',
                'appearances': [
                    {'date': mock_dates['yesterday'], 'pitches': 20},
                ]
            }
        }

        result = service._calculate_fatigue_metrics(pitcher_logs)

        assert result[12345]['status'] == 'Fresh'
        assert result[12345]['modifier'] == 1.0
        assert result[12345]['consecutive_days'] == 1

    def test_dead_trumps_tired(self, service, mock_dates):
        """Dead status should apply even if yesterday's pitches were low."""
        pitcher_logs = {
            12345: {
                'name': 'Test Pitcher',
                'appearances': [
                    {'date': mock_dates['yesterday'], 'pitches': 10},
                    {'date': mock_dates['day_before'], 'pitches': 10},
                ]
            }
        }

        result = service._calculate_fatigue_metrics(pitcher_logs)

        # Dead because of consecutive days, not pitch count
        assert result[12345]['status'] == 'Dead'
        assert result[12345]['modifier'] == 1.25

    def test_multiple_appearances_same_day(self, service, mock_dates):
        """Doubleheader: pitches should be summed for the same day."""
        pitcher_logs = {
            12345: {
                'name': 'Test Pitcher',
                'appearances': [
                    {'date': mock_dates['yesterday'], 'pitches': 15},
                    {'date': mock_dates['yesterday'], 'pitches': 15},  # Doubleheader
                ]
            }
        }

        result = service._calculate_fatigue_metrics(pitcher_logs)

        # 30 total pitches yesterday -> Tired
        assert result[12345]['status'] == 'Tired'
        assert result[12345]['modifier'] == 1.15
        assert result[12345]['yesterday_pitches'] == 30

    def test_total_pitches_3d(self, service, mock_dates):
        """Total pitches should sum all appearances in the window."""
        pitcher_logs = {
            12345: {
                'name': 'Test Pitcher',
                'appearances': [
                    {'date': mock_dates['yesterday'], 'pitches': 20},
                    {'date': mock_dates['day_before'], 'pitches': 25},
                    {'date': mock_dates['three_days_ago'], 'pitches': 15},
                ]
            }
        }

        result = service._calculate_fatigue_metrics(pitcher_logs)

        assert result[12345]['pitches_3d'] == 60


class TestPitcherModifierMethod:
    """Tests for the get_pitcher_modifier convenience method."""

    @patch.object(BullpenHistoryService, 'get_team_bullpen_fatigue')
    def test_returns_modifier_for_known_pitcher(self, mock_fatigue, service):
        """Should return correct modifier for a pitcher in the fatigue report."""
        mock_fatigue.return_value = {
            12345: {'modifier': 1.25, 'status': 'Dead'}
        }

        modifier = service.get_pitcher_modifier(12345, team_id=110)

        assert modifier == 1.25

    @patch.object(BullpenHistoryService, 'get_team_bullpen_fatigue')
    def test_returns_fresh_for_unknown_pitcher(self, mock_fatigue, service):
        """Should return 1.0 (Fresh) for a pitcher not in the fatigue report."""
        mock_fatigue.return_value = {
            12345: {'modifier': 1.25, 'status': 'Dead'}
        }

        modifier = service.get_pitcher_modifier(99999, team_id=110)

        assert modifier == 1.0


class TestAPIIntegration:
    """Tests for the get_team_bullpen_fatigue method with mocked API."""

    @patch('app.services.bullpen_history_service.statsapi')
    def test_empty_schedule_returns_empty(self, mock_statsapi, service):
        """No games in window should return empty dict."""
        mock_statsapi.schedule.return_value = []

        result = service.get_team_bullpen_fatigue(team_id=110)

        assert result == {}

    @patch('app.services.bullpen_history_service.statsapi')
    def test_parses_boxscore_correctly(self, mock_statsapi, service, mock_dates):
        """Should correctly parse pitcher data from boxscore."""
        # Mock schedule
        mock_statsapi.schedule.return_value = [
            {
                'game_id': 123456,
                'game_date': mock_dates['yesterday'],
                'home_id': 110,
            }
        ]

        # Mock boxscore
        mock_statsapi.boxscore_data.return_value = {
            'home': {
                'pitchers': [12345, 67890],
                'players': {
                    'ID12345': {
                        'person': {'fullName': 'Test Reliever'},
                        'stats': {'pitching': {'numberOfPitches': 30}}
                    },
                    'ID67890': {
                        'person': {'fullName': 'Another Pitcher'},
                        'stats': {'pitching': {'numberOfPitches': 0}}  # Didn't pitch
                    }
                }
            }
        }

        result = service.get_team_bullpen_fatigue(team_id=110)

        # Should only include pitcher who actually pitched
        assert 12345 in result
        assert 67890 not in result
        assert result[12345]['name'] == 'Test Reliever'
        assert result[12345]['status'] == 'Tired'  # 30 pitches yesterday

    @patch('app.services.bullpen_history_service.statsapi')
    def test_handles_api_error_gracefully(self, mock_statsapi, service):
        """Should return empty dict on API errors."""
        mock_statsapi.schedule.side_effect = Exception("API Error")

        result = service.get_team_bullpen_fatigue(team_id=110)

        assert result == {}

    @patch('app.services.bullpen_history_service.statsapi')
    def test_handles_boxscore_error_gracefully(self, mock_statsapi, service, mock_dates):
        """Should continue processing other games if one boxscore fails."""
        mock_statsapi.schedule.return_value = [
            {'game_id': 111, 'game_date': mock_dates['yesterday'], 'home_id': 110},
            {'game_id': 222, 'game_date': mock_dates['day_before'], 'home_id': 110},
        ]

        # First boxscore fails, second succeeds
        mock_statsapi.boxscore_data.side_effect = [
            Exception("Boxscore Error"),
            {
                'home': {
                    'pitchers': [12345],
                    'players': {
                        'ID12345': {
                            'person': {'fullName': 'Test Pitcher'},
                            'stats': {'pitching': {'numberOfPitches': 20}}
                        }
                    }
                }
            }
        ]

        result = service.get_team_bullpen_fatigue(team_id=110)

        # Should still have data from second game
        assert 12345 in result


class TestEdgeCases:
    """Edge case tests."""

    def test_boundary_pitch_threshold(self, service, mock_dates):
        """Exactly 25 pitches should be Fresh, not Tired."""
        pitcher_logs = {
            12345: {
                'name': 'Test Pitcher',
                'appearances': [
                    {'date': mock_dates['yesterday'], 'pitches': 25},
                ]
            }
        }

        result = service._calculate_fatigue_metrics(pitcher_logs)

        assert result[12345]['status'] == 'Fresh'

    def test_boundary_pitch_threshold_plus_one(self, service, mock_dates):
        """26 pitches should be Tired."""
        pitcher_logs = {
            12345: {
                'name': 'Test Pitcher',
                'appearances': [
                    {'date': mock_dates['yesterday'], 'pitches': 26},
                ]
            }
        }

        result = service._calculate_fatigue_metrics(pitcher_logs)

        assert result[12345]['status'] == 'Tired'

    def test_empty_pitcher_logs(self, service):
        """Empty pitcher logs should return empty dict."""
        result = service._calculate_fatigue_metrics({})
        assert result == {}
