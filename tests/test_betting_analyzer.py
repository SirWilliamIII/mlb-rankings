import unittest
from app.services.betting_analyzer import BettingAnalyzer
from unittest.mock import MagicMock

class TestBettingAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.analyzer = BettingAnalyzer(self.mock_db)

    def test_remove_vig_multiplicative(self):
        """
        Verify that vig is correctly removed using the multiplicative method.
        Example: -110 / -110 market.
        -110 American -> 52.38% implied.
        Total = 104.76%.
        Fair = 52.38 / 104.76 = 50.0%
        """
        # Test Case 1: Even market
        home_odds = -110
        away_odds = -110
        
        fair_home, fair_away = self.analyzer.remove_vig(home_odds, away_odds)
        
        self.assertAlmostEqual(fair_home, 0.50, places=4)
        self.assertAlmostEqual(fair_away, 0.50, places=4)
        self.assertEqual(fair_home + fair_away, 1.0)

        # Test Case 2: Uneven market
        # Home -150 (60%), Away +130 (43.48%)
        # Total = 103.48%
        # Fair Home = 60 / 103.48 = 57.98%
        # Fair Away = 43.48 / 103.48 = 42.02%
        home_odds_2 = -150
        away_odds_2 = 130
        
        fair_home_2, fair_away_2 = self.analyzer.remove_vig(home_odds_2, away_odds_2)
        
        self.assertAlmostEqual(fair_home_2 + fair_away_2, 1.0, places=4)
        self.assertAlmostEqual(fair_home_2, 0.5798, places=4)

if __name__ == '__main__':
    unittest.main()
