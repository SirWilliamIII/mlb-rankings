class PitcherMonitor:
    """
    Tracks pitcher state to detect 'Dead Arm' and 'Third Time Through Order' (TTTO) penalties.
    """
    
    def __init__(self):
        self.current_pitcher_id = None
        self.batters_faced = 0
        self.pitch_count = 0
        self.is_bullpen = False # Flag if current pitcher is a reliever

    def update_pitcher(self, pitcher_id, is_starter=True):
        """
        Called when a new pitcher enters the game.
        """
        if self.current_pitcher_id != pitcher_id:
            print(f"  [Pitcher Change] New Pitcher: {pitcher_id}")
            self.current_pitcher_id = pitcher_id
            self.batters_faced = 0
            self.pitch_count = 0
            self.is_bullpen = not is_starter

    def log_at_bat(self):
        """
        Increment batters faced.
        """
        self.batters_faced += 1

    def log_pitch(self, count=1):
        """
        Increment pitch count.
        """
        self.pitch_count += count

    def check_ttto_signal(self):
        """
        Checks if the 'Third Time Through Order' penalty is active.
        Rule of Thumb: Batters 19-27 are dangerous for a starter.
        """
        if self.is_bullpen:
            return False
            
        if 18 < self.batters_faced <= 27:
            return True
            
        return False

    def check_fatigue_signal(self):
        """
        Checks for high pitch count fatigue.
        """
        if self.pitch_count > 95:
            return True
        return False
