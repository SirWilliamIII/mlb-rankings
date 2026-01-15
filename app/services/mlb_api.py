# app/services/mlb_api.py
import statsapi # This is the mlb-statsapi library
from app.services.database_manager import DatabaseManager
from datetime import datetime

class MlbApi:
    """
    A wrapper for the MLB-StatsAPI to fetch MLB data.
    """

    def __init__(self, db_manager=None):
        self.db = db_manager if db_manager else DatabaseManager()

    def get_standings(self):
        """
        Fetches the current league standings.
        """
        # 1. Check Cache
        cached_standings = self.db.get_cached_data("standings")
        if cached_standings:
            print("Returning cached standings.")
            return cached_standings

        # 2. Fetch from API
        try:
            # Fetch standings data as a dictionary
            # During offseason (like Jan 2026), default to the last completed season (2025)
            # if the current season returns no data.
            standings = statsapi.standings_data(leagueId="103,104", season=None)
            if not standings:
                current_year = datetime.now().year
                standings = statsapi.standings_data(leagueId="103,104", season=current_year - 1)
            
            # 3. Save to Cache
            if standings:
                self.db.set_cached_data("standings", standings)
                
            return standings
        except Exception as e:
            print(f"Error fetching standings: {e}")
            return None

    def get_teams_for_simulation(self, season=2025):
        """
        Fetches teams and their current stats for simulation.
        """
        try:
            data = self.get_standings() # This now handles the season logic
            if not data:
                return {}
                
            teams = {}
            for div_id, div in data.items():
                for team in div['teams']:
                    team_id = team['team_id']
                    teams[team_id] = {
                        'id': team_id,
                        'name': team['name'],
                        'w': team['w'],
                        'l': team['l'],
                        'win_percentage': team['w'] / (team['w'] + team['l']) if (team['w'] + team['l']) > 0 else 0.5,
                        'league_id': "103" if "American" in div['div_name'] else "104",
                        'division_id': div_id
                    }
            return teams
        except Exception as e:
            print(f"Error fetching teams for simulation: {e}")
            return {}

    def get_remaining_schedule(self, season=2026):
        """
        Fetches the remaining schedule for the given season.
        """
        cache_key = f"schedule_{season}"
        
        # 1. Check Cache
        cached_schedule = self.db.get_cached_data(cache_key)
        if cached_schedule:
            print("Returning cached schedule.")
            return cached_schedule

        # 2. Fetch from API
        start_date = datetime.now().strftime('%Y-%m-%d')
        # End of regular season is usually early October
        end_date = f"{season}-10-05"
        
        try:
            schedule = statsapi.schedule(start_date=start_date, end_date=end_date)
            # Filter for regular season games and format for simulator
            formatted_schedule = []
            for game in schedule:
                if game.get('game_type') == 'R': # Regular Season
                    formatted_schedule.append({
                        'home_id': game['home_id'],
                        'away_id': game['away_id']
                    })
            
            # 3. Save to Cache
            if formatted_schedule:
                self.db.set_cached_data(cache_key, formatted_schedule)
                
            return formatted_schedule
        except Exception as e:
            print(f"Error fetching schedule for simulation: {e}")
            return []

    def get_live_game_data(self, game_pk):
        """
        Fetches real-time granular data for a specific game (play-by-play, linescore, boxscore).
        This data comes from the /v1.1/game/{gamePk}/feed/live endpoint.
        """
        try:
            # Use statsapi.get() to hit the specific endpoint if a direct wrapper isn't preferred
            # or statsapi.game_scoring_play_data etc. 
            # The most comprehensive is getting the full game feed.
            # 'game' endpoint usually corresponds to the full feed.
            return statsapi.get('game', {'gamePk': game_pk})
        except Exception as e:
            print(f"Error fetching live data for game {game_pk}: {e}")
            return None