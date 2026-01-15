import sys
import os
# Ensure app modules are found
sys.path.append(os.getcwd())

import statsapi
from app.services.database_manager import DatabaseManager
from app.services.sportsdata_client import SportsDataClient
from app.services.mlb_api import MlbApi

def populate_data():
    print("--- Starting Data Population ---")
    
    db = DatabaseManager()
    sd_client = SportsDataClient()
    mlb_api = MlbApi(db)

    # 1. Build Mapping (SportsData Key -> MLB ID)
    print("Building ID Map...")
    standings = mlb_api.get_standings()
    id_map = {} # {'ARI': 109, ...}
    
    # Iterate through all teams in standings
    total_teams = 0
    for div in standings.values():
        for team in div['teams']:
            mlb_id = team['team_id']
            # Lookup full details to get abbreviation
            # Warning: making 30 calls here. It's a script, so it's fine.
            meta = statsapi.lookup_team(mlb_id)
            if meta:
                # fileCode is usually 'ari', 'tor' etc.
                abbr = meta[0].get('fileCode', '').upper()
                if abbr:
                    # Special cases for discrepancies if any (e.g. WAS vs WSH)
                    # SportsData uses: WAS, CWS, CHW?, NYY, NYM, LAD, LAA, SF, SD...
                    # Let's handle known discrepancies if we encounter them.
                    # statsapi 'fileCode' is usually robust.
                    id_map[abbr] = mlb_id
                    
                    # Also map 'teamCode' just in case
                    code = meta[0].get('teamCode', '').upper()
                    if code and code != abbr:
                        id_map[code] = mlb_id
                        
            total_teams += 1
            print(f"Mapped {team['name']} ({mlb_id}) -> {abbr}", end="\r")
            
    print(f"\nID Map built for {len(id_map)} keys.")

    # 2. Fetch and Save Advanced Team Stats
    print("\nFetching Team Stats from SportsData...")
    # Fetch for 2025 (completed season) for base strength
    team_stats = sd_client.get_season_team_stats(2025)
    
    if team_stats:
        print(f"Saving {len(team_stats)} team records...")
        db.save_advanced_team_stats(team_stats, 2025, id_mapper=id_map)
        print("Team Stats Saved.")
    else:
        print("Error fetching team stats.")

    # 3. Fetch and Save Pitcher Stats
    print("\nFetching Player Stats from SportsData (this may take a moment)...")
    player_stats = sd_client.get_player_season_stats(2025)
    
    if player_stats:
        print(f"Received {len(player_stats)} player records. Saving pitchers...")
        db.save_pitcher_stats(player_stats, 2025)
        print("Pitcher Stats Saved.")
    else:
        print("Error fetching player stats.")

    print("\n--- Data Population Complete ---")

if __name__ == "__main__":
    populate_data()
