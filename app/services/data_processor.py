import statsapi
import logging
from app.services.database_manager import DatabaseManager
from app.services.sportsdata_client import SportsDataClient
from app.services.mlb_api import MlbApi

# Configure Logging
logging.basicConfig(
    filename='app.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DataProcessor:
    """
    Handles the orchestration of fetching fresh data from APIs 
    and persisting it to the database.
    """
    def __init__(self, db_manager=None):
        self.db = db_manager if db_manager else DatabaseManager()
        self.sd_client = SportsDataClient()
        self.mlb_api = MlbApi(self.db)

    def refresh_all_data(self, season=2025):
        """
        Main entry point to refresh all data sources.
        """
        logging.info("Starting Daily Data Refresh...")
        
        try:
            # 1. Refresh Basic MLB Data (Schedule/Standings)
            # calling these methods on MlbApi triggers the cache check/update logic
            self.mlb_api.get_standings() 
            self.mlb_api.get_remaining_schedule(season + 1) # Next season schedule
            logging.info("Basic MLB Data Refreshed.")

            # 2. Build/Refresh ID Map
            id_map = self._build_id_map()
            
            # 3. Refresh Advanced Team Stats (Pythagorean)
            team_stats = self.sd_client.get_season_team_stats(season)
            if team_stats:
                self.db.save_advanced_team_stats(team_stats, season, id_mapper=id_map)
                logging.info(f"Advanced Team Stats updated for {len(team_stats)} teams.")
            
            # 4. Refresh Pitcher Stats (FIP)
            player_stats = self.sd_client.get_player_season_stats(season)
            if player_stats:
                self.db.save_pitcher_stats(player_stats, season)
                logging.info(f"Pitcher Stats updated for {len(player_stats)} records.")

        except Exception as e:
            logging.error(f"Error during data refresh: {e}")
            raise e
            
        logging.info("Daily Data Refresh Complete.")

    def _build_id_map(self):
        """
        Helper to map SportsData keys to MLB IDs.
        """
        standings = self.mlb_api.get_standings()
        id_map = {}
        if not standings:
            return id_map

        for div in standings.values():
            for team in div['teams']:
                mlb_id = team['team_id']
                try:
                    # We accept the overhead of lookup for accuracy
                    meta = statsapi.lookup_team(mlb_id)
                    if meta:
                        abbr = meta[0].get('fileCode', '').upper()
                        if abbr:
                            id_map[abbr] = mlb_id
                            # Also map teamCode
                            code = meta[0].get('teamCode', '').upper()
                            if code and code != abbr:
                                id_map[code] = mlb_id
                except Exception as e:
                    logging.warning(f"Failed to lookup map for team {mlb_id}: {e}")
        
        return id_map
