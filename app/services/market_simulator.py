from app.services.state_engine import StateEngine

class MarketSimulator:
    """
    The 'Lazy Bookmaker'.
    Generates betting odds based on standard/baseline models (RE24) 
    WITHOUT the advanced 'Sharp' modifiers (Fatigue, TTTO, Dead Arm).
    
    This acts as the opponent for our TraderAgent in backtesting.
    """

    def __init__(self):
        self.state_engine = StateEngine()

    def get_market_odds(self, home_score, away_score, inning, is_top, state_idx):
        """
        Returns the 'Market' American Odds for the Home Team.
        
        Logic:
        1. Calculate Win Probability using BASELINE math (pitcher_modifier=1.0).
        2. Apply a 'Vig' (Bookmaker Fee).
        3. Convert to American Odds.
        """
        # 1. Baseline Probability (No Fatigue/Matchup modifiers)
        # Note: We pass pitcher_modifier=1.0 explicitly
        raw_prob = self.state_engine.get_win_probability(
            home_score, 
            away_score, 
            inning, 
            0 if is_top else 1, 
            state_idx, 
            pitcher_modifier=1.0
        )

        # 2. Apply Vig (The 'Overround')
        # Standard market is ~4% vig (2% per side).
        # We inflate the probability of the favorite and the underdog to ensure sum > 100%
        # Simple approach: standard -110 lines imply 52.38% breakeven.
        
        # Let's say we split the vig.
    def calculate_dynamic_vig(self, inning, score_diff):
        """
        Calculates the 'Vig' (Overround) based on market volatility.
        
        Logic:
        - Baseline Vig: 2.5% (Early game)
        - High Leverage Vig: Up to 6.0% (Late game, close score)
        - Blowout Vig: 3.5% (Late game, blowout - often wide spreads but less liquidity)
        
        Returns:
            float: Vig multiplier (e.g., 1.025 for 2.5%)
        """
        base_vig = 1.025
        
        # Late Innings (7+)
        if inning >= 7:
            if score_diff <= 2:
                # High Leverage/Uncertainty -> Higher Vig
                return 1.055 # 5.5%
            elif score_diff >= 5:
                # Blowout -> Moderate Vig
                return 1.035
            else:
                return 1.040 # Standard Late Game
                
        return base_vig

    def get_market_odds(self, home_score, away_score, inning, is_top, state_idx):
        """
        Returns the 'Market' American Odds for the Home Team.
        """
        # 1. Baseline Probability
        raw_prob = self.state_engine.get_win_probability(
            home_score, 
            away_score, 
            inning, 
            0 if is_top else 1, 
            state_idx, 
            pitcher_modifier=1.0
        )

        # 2. Apply Dynamic Vig
        score_diff = abs(home_score - away_score)
        vig_factor = self.calculate_dynamic_vig(inning, score_diff)
        
        market_prob_home = raw_prob
        # Inflate probability to represent cost
        priced_prob_home = min(0.99, market_prob_home * vig_factor)
        
        # 3. Convert to American Odds
        return self._prob_to_american(priced_prob_home)

    def _prob_to_american(self, prob):
        """
        Converts probability (0.0-1.0) to American Odds Integer.
        """
        if prob <= 0.5:
            # Positive Odds (e.g., 0.40 -> +150)
            # Odds = (1/p - 1) * 100
            decimal = 1/prob
            return int((decimal - 1) * 100)
        else:
            # Negative Odds (e.g., 0.60 -> -150)
            # Odds = -100 / (1/p - 1)
            decimal = 1/prob
            return int(-100 / (decimal - 1))
