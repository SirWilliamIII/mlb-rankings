import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class SportsDataClient:
    """
    Client for interacting with the SportsData.io MLB API.
    """
    BASE_URL = "https://api.sportsdata.io/v3/mlb"

    def __init__(self):
        self.api_key = os.getenv("SPORTSDATA_API_KEY")
        if not self.api_key:
            raise ValueError("SPORTSDATA_API_KEY not found in environment variables.")
        self.headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }

    def _get(self, endpoint):
        """Helper to make GET requests."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_season_team_stats(self, season=2025):
        """
        Fetches aggregate team statistics (Runs Scored, Runs Allowed, etc.).
        Endpoint: /scores/json/TeamSeasonStats/{season}
        """
        return self._get(f"scores/json/TeamSeasonStats/{season}")

    def get_games_by_date(self, date_str):
        """
        Fetches games for a specific date, including probable pitchers.
        Endpoint: /scores/json/GamesByDate/{date}
        """
        return self._get(f"scores/json/GamesByDate/{date_str}")

    def get_player_season_stats(self, season=2025):
        """
        Fetches aggregate player statistics (needed for Pitcher ERA/FIP).
        Endpoint: /stats/json/PlayerSeasonStats/{season}
        WARNING: This response can be large.
        """
        return self._get(f"stats/json/PlayerSeasonStats/{season}")

    def get_daily_odds(self, date_str):
        """
        Fetches betting odds for a specific date.
        Endpoint: /odds/json/GameOddsByDate/{date}
        Format: YYYY-MM-DD
        """
        return self._get(f"odds/json/GameOddsByDate/{date_str}")
