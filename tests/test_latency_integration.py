import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from app.services.live_game_service import LiveGameService

class TestLatencyIntegration(unittest.TestCase):
    def setUp(self):
        self.mock_db_manager = MagicMock()
        self.mock_db_manager.is_postgres = False
        
        with patch('app.services.live_game_service.MlbApi') as MockApi:
            self.service = LiveGameService(self.mock_db_manager)
            self.mock_api_instance = self.service.mlb_api
            
        self.service.bullpen_service = MagicMock()
        self.service.state_engine = MagicMock()
        self.service.markov_service = MagicMock()
        self.service.market_sim = MagicMock()
        
        self.service.state_engine.get_current_state_index.return_value = 0
        self.service.markov_service.get_instant_win_prob.return_value = 0.60
        self.service.market_sim.get_market_odds.return_value = 100 
        self.service.bullpen_service.get_team_bullpen_fatigue.return_value = 0.0

    @patch('app.services.latency_monitor.datetime')
    def test_high_latency_blocks_trade(self, mock_datetime):
        # Setup: Now is 12:00:10 UTC
        now_utc = datetime(2023, 10, 27, 12, 0, 10, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now_utc
        mock_datetime.timezone.utc = timezone.utc
        
        # Feed Timestamp: 12:00:00 UTC (10s delay) -> OUTSIDE WINDOW (> 6s)
        feed_ts = "2023-10-27T12:00:00Z"
        
        self.mock_api_instance.get_live_game_data.return_value = {
            'metaData': {'timeStamp': feed_ts},
            'gameData': {'teams': {'home': {'id': 1, 'name': 'H'}, 'away': {'id': 2, 'name': 'A'}}},
            'liveData': {'linescore': {'currentInning': 9, 'isTopInning': False, 'outs': 2, 'teams': {'home': {'runs': 0}, 'away': {'runs': 0}}, 'offense': {}, 'defense': {'pitcher': {'id': 99, 'fullName': 'P'}}}}
        }
        
        result = self.service._process_live_game(12345)
        self.assertEqual(result['signal']['action'], 'BLOCK')
        self.assertIn("Latency High", result['signal']['reason'])

    @patch('app.services.latency_monitor.datetime')
    def test_sniper_window_allows_trade(self, mock_datetime):
        # Setup: Now is 12:00:04 UTC
        now_utc = datetime(2023, 10, 27, 12, 0, 4, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now_utc
        mock_datetime.timezone.utc = timezone.utc
        
        # Feed Timestamp: 12:00:00 UTC (4s delay) -> INSIDE WINDOW (3s - 6s)
        feed_ts = "2023-10-27T12:00:00Z"
        
        self.mock_api_instance.get_live_game_data.return_value = {
            'metaData': {'timeStamp': feed_ts},
            'gameData': {'teams': {'home': {'id': 1, 'name': 'H'}, 'away': {'id': 2, 'name': 'A'}}},
            'liveData': {'linescore': {'currentInning': 9, 'isTopInning': False, 'outs': 2, 'teams': {'home': {'runs': 0}, 'away': {'runs': 0}}, 'offense': {}, 'defense': {'pitcher': {'id': 99, 'fullName': 'P'}}}}
        }
        
        result = self.service._process_live_game(12345)
        self.assertEqual(result['signal']['action'], 'BET')
        self.assertNotEqual(result['signal']['wager'], '$0.0')

    @patch('app.services.latency_monitor.datetime')
    def test_too_fast_blocks_trade(self, mock_datetime):
        # Setup: Now is 12:00:01 UTC
        now_utc = datetime(2023, 10, 27, 12, 0, 1, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now_utc
        mock_datetime.timezone.utc = timezone.utc
        
        # Feed Timestamp: 12:00:00 UTC (1s delay) -> TOO FAST (< 3s)
        feed_ts = "2023-10-27T12:00:00Z"
        
        self.mock_api_instance.get_live_game_data.return_value = {
            'metaData': {'timeStamp': feed_ts},
            'gameData': {'teams': {'home': {'id': 1, 'name': 'H'}, 'away': {'id': 2, 'name': 'A'}}},
            'liveData': {'linescore': {'currentInning': 9, 'isTopInning': False, 'outs': 2, 'teams': {'home': {'runs': 0}, 'away': {'runs': 0}}, 'offense': {}, 'defense': {'pitcher': {'id': 99, 'fullName': 'P'}}}}
        }
        
        result = self.service._process_live_game(12345)
        self.assertEqual(result['signal']['action'], 'BLOCK')
        self.assertIn("Latency High", result['signal']['reason'])

if __name__ == '__main__':
    unittest.main()