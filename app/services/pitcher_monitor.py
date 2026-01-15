class PitcherMonitor:
    """
    Tracks pitcher state to detect 'Dead Arm' and 'Third Time Through Order' (TTTO) penalties.
    """

    def __init__(self, bullpen_fatigue=None):
        """
        Args:
            bullpen_fatigue: Dict of {pitcher_id: {'modifier': float, 'status': str, ...}}
                             from BullpenHistoryService. Used for reliever fatigue tracking.
        """
        self.current_pitcher_id = None
        self.batters_faced = 0
        self.pitch_count = 0
        self.is_bullpen = False  # Flag if current pitcher is a reliever
        self.bullpen_fatigue = bullpen_fatigue or {}

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

    def get_performance_modifier(self):
        """
        Returns a float multiplier representing pitcher effectiveness.

        Used by StateEngine to adjust RE24 (Run Expectancy).
        - 1.0 = average/neutral performance
        - >1.0 = compromised pitcher (expect more runs)
        - <1.0 = dominant pitcher (expect fewer runs)

        Compounds multiple factors:
        - TTTO (starter only): 1.15x
        - In-game fatigue (>95 pitches): 1.10x
        - Bullpen fatigue (reliever only): 1.15-1.25x based on recent usage

        Returns:
            Float coefficient capped at 1.50 to avoid extreme values.
        """
        modifier = 1.0

        # TTTO penalty: +15% expected runs (starters only)
        if self.check_ttto_signal():
            modifier *= 1.15

        # In-game fatigue penalty: +10% expected runs
        if self.check_fatigue_signal():
            modifier *= 1.10

        # Bullpen fatigue: Apply historical usage penalty for relievers
        if self.is_bullpen and self.current_pitcher_id:
            pitcher_data = self.bullpen_fatigue.get(self.current_pitcher_id, {})
            bullpen_mod = pitcher_data.get('modifier', 1.0)
            modifier *= bullpen_mod

        # Cap to avoid unrealistic extremes (increased for compound effects)
        return min(modifier, 1.50)
