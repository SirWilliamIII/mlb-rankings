from app.services.forecasting_model import ForecastingModel
from app.services.trader_agent import TraderAgent
import random

class BettingAnalyzer:
    """
    Analyzes games to find betting value (Edge) using the TraderAgent.
    """

    def __init__(self, db_manager):
        self.forecasting_model = ForecastingModel(db_manager)
        self.trader_agent = TraderAgent()

    def generate_mock_odds(self, home_prob):
        """
        Generates realistic market odds based on a 'true' probability but with vig.
        Used for demonstration when real odds aren't available.
        """
        # Market usually adds ~4-5% vig total.
        # If true prob is 0.60, fair line is -150. Market might be -165.
        
        fair_decimal = 1 / home_prob
        market_decimal = fair_decimal * 0.95 # Add vig (worse odds)
        
        # Convert back to American for display
        if market_decimal >= 2.0:
            odds = (market_decimal - 1) * 100
        else:
            odds = -100 / (market_decimal - 1)
            
        return int(odds)

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
            variance = random.uniform(-0.10, 0.10) # Market disagrees by up to 10%
            market_home_prob = min(max(home_prob + variance, 0.20), 0.80)
            
            home_odds = self.generate_mock_odds(market_home_prob)
            
            # 3. Evaluate Trade (Using Trader Agent)
            trade_decision = self.trader_agent.evaluate_trade(
                model_prob=home_prob,
                market_odds_american=home_odds,
                game_context={'inning': 1, 'score_diff': 0} # Default pre-game context
            )
            
            # 4. Filter for Actionable Bets
            if trade_decision['action'] == "BET":
                insights.append({
                    "game": f"{away_team['name']} @ {home_team['name']}",
                    "bet_on": home_team['name'],
                    "model_prob": round(home_prob * 100, 1),
                    "market_odds": home_odds,
                    "implied_prob": round(trade_decision['implied_prob'] * 100, 1),
                    "ev_percent": round(trade_decision['edge'] * 100, 1), # Mapping edge to ev_percent
                    "wager_amount": trade_decision['wager_amount'],
                    "wager_percent": round(trade_decision['wager_percent'] * 100, 2),
                    "reason": trade_decision['reason']
                })
        
        # Sort by best EV/Edge
        return sorted(insights, key=lambda x: x['ev_percent'], reverse=True)
