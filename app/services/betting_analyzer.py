from app.services.forecasting_model import ForecastingModel
from app.services.trader_agent import TraderAgent
import random
from decimal import Decimal

class BettingAnalyzer:
    """
    Analyzes games to find betting value (Edge) using the TraderAgent.
    Level 300 Update: Implements Vig Removal and Fair Price Discovery.
    """

    def __init__(self, db_manager):
        self.forecasting_model = ForecastingModel(db_manager)
        self.trader_agent = TraderAgent()

    def generate_mock_odds(self, home_prob):
        """Generates realistic market odds with vig."""
        fair_decimal = 1 / home_prob
        market_decimal = fair_decimal * 0.95 # Add vig
        if market_decimal >= 2.0:
            odds = (market_decimal - 1) * 100
        else:
            odds = -100 / (market_decimal - 1)
        return int(odds)

    def remove_vig(self, home_odds, away_odds):
        """
        Strips the sportsbook overround (vig) using the Multiplicative Method.
        Returns: (fair_home_prob, fair_away_prob)
        """
        dec_home = self.trader_agent._american_to_decimal(home_odds)
        dec_away = self.trader_agent._american_to_decimal(away_odds)
        
        # 1/dec is implied prob
        implied_home = Decimal("1.0") / dec_home
        implied_away = Decimal("1.0") / dec_away
        
        overround = implied_home + implied_away
        
        return implied_home / overround, implied_away / overround

    def analyze_schedule(self, schedule, teams):
        """
        Analyzes a list of games and returns value opportunities.
        """
        insights = []
        
        for game in schedule:
            home_id = game['home_id']
            away_id = game['away_id']
            
            if home_id not in teams or away_id not in teams:
                continue
                
            home_team = teams[home_id]
            away_team = teams[away_id]
            
            # 1. Get Model Probability
            home_prob = self.forecasting_model.get_matchup_probability(home_team, away_team)
            
            # 2. Get Market Odds (Mocked for now)
            variance = random.uniform(-0.10, 0.10) 
            market_home_prob = min(max(home_prob + variance, 0.20), 0.80)
            home_odds = self.generate_mock_odds(market_home_prob)
            
            # --- CRITICAL FIX: Generate Away Odds for Vig Removal ---
            market_away_prob = 1.0 - market_home_prob
            away_odds = self.generate_mock_odds(market_away_prob)
            
            # 3. Evaluate Trade (Using Trader Agent)
            trade_decision = self.trader_agent.evaluate_trade(
                model_prob=home_prob,
                market_odds_american=home_odds,
                game_context={'inning': 1, 'score_diff': 0, 'leverage_index': 1.0} 
            )
            
            # 4. Filter for Actionable Bets
            if trade_decision['action'] == "BET":
                # Calculate Fair Prob for reporting
                fair_home, _ = self.remove_vig(home_odds, away_odds)
                
                insights.append({
                    "game": f"{away_team['name']} @ {home_team['name']}",
                    "bet_on": home_team['name'],
                    "model_prob": round(home_prob * 100, 1),
                    "market_odds": home_odds,
                    "implied_prob": round(trade_decision['implied_prob'] * 100, 1),
                    "fair_prob": round(float(fair_home) * 100, 1), # New Metric
                    "ev_percent": round(trade_decision['edge'] * 100, 1), 
                    "wager_amount": trade_decision['wager_amount'],
                    "wager_percent": round(trade_decision['wager_percent'] * 100, 2),
                    "reason": trade_decision['reason']
                })
        
        return sorted(insights, key=lambda x: x['ev_percent'], reverse=True)