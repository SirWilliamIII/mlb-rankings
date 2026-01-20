class DefenseMonitor:
    """
    Tracks real-time defensive efficiency (DRS, UZR, Errors) to penalize
    teams during "Meltdown" events (e.g., WS Game 5 2024).
    """
    
    def __init__(self, team_id):
        self.team_id = team_id
        self.error_count = 0
        self.defensive_runs_saved = 0.0 # Placeholder
        
    def log_error(self):
        self.error_count += 1
        
    def get_defense_modifier(self):
        """
        Returns a modifier for the Markov Engine.
        1.0 = Average Defense.
        > 1.0 = Poor Defense (Inflates p_hit / p_error).
        """
        # Simple penalty for in-game errors
        if self.error_count > 0:
            # 1 error -> 1.05, 2 errors -> 1.15
            return 1.0 + (self.error_count * 0.05)
        return 1.0
