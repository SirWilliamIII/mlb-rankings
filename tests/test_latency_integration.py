import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from app.services.live_game_service import LiveGameService

class TestLatencyIntegration(unittest.TestCase):
    def setUp(self):
        self.mock_db_manager = MagicMock()
        self.mock_db_manager.is_postgres = False
        
        # We need to mock MlbApi so we don't hit the network
        with patch('app.services.live_game_service.MlbApi') as MockApi:
            self.service = LiveGameService(self.mock_db_manager)
            self.mock_api_instance = self.service.mlb_api
            
        # Mock other services to focus on latency
        self.service.bullpen_service = MagicMock()
        self.service.state_engine = MagicMock()
        self.service.markov_service = MagicMock()
        self.service.market_sim = MagicMock()
        
        # Setup default mock returns
        self.service.state_engine.get_current_state_index.return_value = 0
        self.service.markov_service.get_instant_win_prob.return_value = 0.60
        self.service.market_sim.get_market_odds.return_value = 100 # +100 odds
        self.service.bullpen_service.get_team_bullpen_fatigue.return_value = 0.0

    @patch('app.services.latency_monitor.datetime')
    def test_high_latency_blocks_trade(self, mock_datetime):
        # Setup: Now is 12:00:10 UTC
        now_utc = datetime(2023, 10, 27, 12, 0, 10, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now_utc
        mock_datetime.timezone.utc = timezone.utc
        
        # Feed Timestamp: 12:00:00 UTC (10s delay)
        # Threshold is 6s
        feed_ts = "2023-10-27T12:00:00Z"
        
        # Mock API response
        self.mock_api_instance.get_live_game_data.return_value = {
            'metaData': {'timeStamp': feed_ts},
            'gameData': {
                'teams': {
                    'home': {'id': 1, 'name': 'Home'},
                    'away': {'id': 2, 'name': 'Away'}
                }
            },
            'liveData': {
                'linescore': {
                    'currentInning': 9,
                    'isTopInning': False,
                    'outs': 2,
                    'teams': {'home': {'runs': 0}, 'away': {'runs': 0}},
                    'offense': {},
                    'defense': {'pitcher': {'id': 99, 'fullName': 'Closer'}}
                }
            }
        }
        
        # Run process
        # We need to ensure TraderAgent sees a bet opportunity first, then gets blocked.
        # Model: 0.60, Odds: +100 -> Edge 10%
        
        result = self.service._process_live_game(12345)
        
        # Assertions
        # Action should be BLOCK (or PASS if agent handled it as block)
        # TraderAgent returns BLOCK if safety valve fails
        self.assertEqual(result['signal']['action'], 'BLOCK')
        self.assertIn("Latency High", result['signal']['reason'])
        self.assertEqual(result['signal']['wager'], '$0.0')

    @patch('app.services.latency_monitor.datetime')
    def test_low_latency_allows_trade(self, mock_datetime):
        # Setup: Now is 12:00:02 UTC
        now_utc = datetime(2023, 10, 27, 12, 0, 2, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now_utc
        mock_datetime.timezone.utc = timezone.utc
        
        # Feed Timestamp: 12:00:00 UTC (2s delay)
        feed_ts = "2023-10-27T12:00:00Z"
        
        self.mock_api_instance.get_live_game_data.return_value = {
            'metaData': {'timeStamp': feed_ts},
            'gameData': {
                'teams': {
                    'home': {'id': 1, 'name': 'Home'},
                    'away': {'id': 2, 'name': 'Away'}
                }
            },
            'liveData': {
                'linescore': {
                    'currentInning': 9,
                    'isTopInning': False,
                    'outs': 2,
                    'teams': {'home': {'runs': 0}, 'away': {'runs': 0}},
                    'offense': {},
                    'defense': {'pitcher': {'id': 99, 'fullName': 'Closer'}}
                }
            }
        }
        
        # Run process
        result = self.service._process_live_game(12345)
        
        # Assertions
        self.assertEqual(result['signal']['action'], 'BET')
        self.assertNotIn("Latency High", result['signal']['reason'])
        self.assertNotEqual(result['signal']['wager'], '$0.0')

if __name__ == '__main__':
    unittest.main()
