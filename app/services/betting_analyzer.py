from app.services.forecasting_model import ForecastingModel
import random

class BettingAnalyzer:
    """
    Analyzes games to find betting value (Edge).
    """

    def __init__(self, db_manager):
        self.forecasting_model = ForecastingModel(db_manager)

    def american_to_decimal(self, american_odds):
        """Converts American odds (e.g., -110, +150) to Decimal odds (e.g., 1.91, 2.50)."""
        if american_odds > 0:
            return 1 + (american_odds / 100)
        else:
            return 1 + (100 / abs(american_odds))

    def calculate_ev(self, win_prob, american_odds):
        """
        Calculates Expected Value (EV).
        EV = (Probability * DecimalOdds) - 1
        Returns percentage (e.g., 0.05 for 5% edge).
        """
        decimal_odds = self.american_to_decimal(american_odds)
        return (win_prob * decimal_odds) - 1

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
            # In real app: odds = sportsdata_client.get_odds(game_id)
            # We mock odds slightly different from our model to create "Edge" cases
            variance = random.uniform(-0.10, 0.10) # Market disagrees by up to 10%
            market_home_prob = min(max(home_prob + variance, 0.20), 0.80)
            
            home_odds = self.generate_mock_odds(market_home_prob)
            away_odds = self.generate_mock_odds(1 - market_home_prob)
            
            # 3. Calculate EV
            home_ev = self.calculate_ev(home_prob, home_odds)
            
            # 4. Filter for Value (Positive EV)
            if home_ev > 0:
                insights.append({
                    "game": f"{away_team['name']} @ {home_team['name']}",
                    "bet_on": home_team['name'],
                    "model_prob": round(home_prob * 100, 1),
                    "market_odds": home_odds,
                    "implied_prob": round((1/self.american_to_decimal(home_odds))*100, 1),
                    "ev_percent": round(home_ev * 100, 1)
                })
        
        # Sort by best EV
        return sorted(insights, key=lambda x: x['ev_percent'], reverse=True)
