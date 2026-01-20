# app/services/forecasting_model.py

import random

class ForecastingModel:
    """
    The 'Forecasting Agent'. Its responsibility is to predict the outcome of a single game.
    """
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        self.stats_cache = {}

    def predict_winner(self, home_team, away_team):
        """
        Predicts the winner of a single game using a stochastic model.
        """
        home_prob = self.get_matchup_probability(home_team, away_team)

        if random.random() < home_prob:
            return home_team
        else:
            return away_team

    def get_matchup_probability(self, home_team, away_team):
        """
        Returns the probability (0.0 to 1.0) of the home team winning.
        """
        # 1. Base Probability (Pythagorean or Standard)
        home_prob = self._get_base_probability(home_team, away_team)
        
        # 2. Home Field Advantage (+3% is standard/conservative)
        home_prob += 0.03
        
        # 3. Clamp probability between 1% and 99%
        return min(max(home_prob, 0.01), 0.99)

    def _get_base_probability(self, home_team, away_team):
        """
        Calculates the base win probability for the home team using Log5
        with either Pythagorean Win % (preferred) or actual Win %.
        """
        h_id = str(home_team['id'])
        a_id = str(away_team['id'])
        
        h_pct = self.stats_cache.get(h_id)
        a_pct = self.stats_cache.get(a_id)
        
        # 1. Try to get Pythagorean Win % from DB and cache it
        if self.db:
            if h_pct is None:
                h_pyth = self.db.get_advanced_team_stats(h_id)
                h_pct = h_pyth if h_pyth is not None else home_team.get('win_percentage', 0.5)
                self.stats_cache[h_id] = h_pct
                
            if a_pct is None:
                a_pyth = self.db.get_advanced_team_stats(a_id)
                a_pct = a_pyth if a_pyth is not None else away_team.get('win_percentage', 0.5)
                self.stats_cache[a_id] = a_pct

        # 2. Fallback to standard Win % (Standings) if DB missing
        if h_pct is None:
            h_pct = home_team.get('win_percentage', 0.5)
        if a_pct is None:
            a_pct = away_team.get('win_percentage', 0.5)
            
        # 3. Log5 Formula: (A - A*B) / (A + B - 2*A*B)
        # This handles the relative strength better than simple ratio
        # A = h_pct, B = a_pct
        
        num = h_pct - (h_pct * a_pct)
        den = h_pct + a_pct - (2 * h_pct * a_pct)
        
        if den == 0:
            return 0.5
            
        return num / den
