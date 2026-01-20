import unittest
from unittest.mock import MagicMock, patch
from app.services.live_game_service import LiveGameService

class TestMarkovIntegration(unittest.TestCase):
    def setUp(self):
        self.mock_db_manager = MagicMock()
        self.mock_db_manager.is_postgres = False
        
        with patch('app.services.live_game_service.MlbApi') as MockApi:
            self.service = LiveGameService(self.mock_db_manager)
            self.mock_api = self.service.mlb_api
            
        # We want real MarkovService to verify end-to-end logic, or mock it to verify inputs?
        # Mocking ensures we verify what is passed.
        self.service.markov_service = MagicMock()
        self.service.markov_service.get_instant_win_prob.return_value = 0.55
        
        self.service.market_sim = MagicMock()
        self.service.market_sim.get_market_odds.return_value = 100
        
        self.service.trader_agent = MagicMock()
        self.service.trader_agent.evaluate_trade.return_value = {'action': 'PASS', 'edge': 0.0, 'wager_amount': 0.0, 'reason': 'Test'}

    @patch('app.services.latency_monitor.datetime')
    def test_live_game_flow_passes_modifiers(self, mock_datetime):
        # Setup: Fatigued Pitcher scenario
        # We need PitcherMonitor to return a specific modifier.
        # LiveGameService creates PitcherMonitors internally.
        # We can inject a mock into self.service.monitors cache.
        
        game_id = 123
        mock_monitor = MagicMock()
        mock_monitor.get_performance_modifier.return_value = 1.25 # Highly fatigued
        
        self.service.monitors[game_id] = {
            'home': mock_monitor,
            'away': MagicMock()
        }
        
        # Mock Live Data (Top of 9th, Away batting -> Home Pitching (mock_monitor))
        self.mock_api.get_live_game_data.return_value = {
            'metaData': {'timeStamp': "2023-10-27T12:00:00Z"},
            'gameData': {'teams': {'home': {'id': 1, 'name': 'H'}, 'away': {'id': 2, 'name': 'A'}}},
            'liveData': {'linescore': {
                'currentInning': 9, 
                'isTopInning': True, 
                'outs': 0, 
                'teams': {'home': {'runs': 0}, 'away': {'runs': 0}}, 
                'offense': {}, 
                'defense': {'pitcher': {'id': 99, 'fullName': 'FatiguedGuy'}}
            }}
        }
        
        self.service._process_live_game(game_id)
        
        # Assertions
        # 1. Verify PitcherMonitor updated
        mock_monitor.update_pitcher.assert_called_with(99, is_starter=True)
        
        # 2. Verify Markov Service called with Modifier
        self.service.markov_service.get_instant_win_prob.assert_called_once()
        args, kwargs = self.service.markov_service.get_instant_win_prob.call_args
        
        # Check arguments (kwargs or args depending on call style)
        # Call signature: inning, outs, runners, score_diff, is_top_inning, pitcher_mod
        # self.markov_service.get_instant_win_prob(
        #    inning=current_inning,
        #    outs=outs,
        #    runners=[r1, r2, r3],
        #    score_diff=home_score - away_score,
        #    is_top_inning=is_top,
        #    pitcher_mod=pitcher_modifier
        #)
        
        self.assertEqual(kwargs['pitcher_mod'], 1.25)
        self.assertEqual(kwargs['inning'], 9)

if __name__ == '__main__':
    unittest.main()
