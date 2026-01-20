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
            # Fetch official abbreviation directly from team endpoint
            try:
                team_data = statsapi.get('team', {'teamId': mlb_id})
                if team_data and 'teams' in team_data:
                    abbr = team_data['teams'][0].get('abbreviation', '').upper()
                    if abbr:
                        id_map[abbr] = mlb_id
                        # Comprehensive SportsData Discrepancy Map
                        discrepancies = {
                            'LAN': 'LAD', 'LAD': 'LAD',
                            'CHN': 'CHC', 'CHC': 'CHC',
                            'CHA': 'CHW', 'CWS': 'CHW',
                            'AZ':  'ARI', 'ARI': 'ARI',
                            'NYA': 'NYY', 'NYY': 'NYY',
                            'NYN': 'NYM', 'NYM': 'NYM',
                            'SDN': 'SD',  'SD':  'SD',  'SDP': 'SD',
                            'SFN': 'SF',  'SF':  'SF',  'SFG': 'SF',
                            'ANA': 'LAA', 'LAA': 'LAA',
                            'TBA': 'TB',  'TB':  'TB',  'TBR': 'TB',
                            'KCA': 'KC',  'KC':  'KC',  'KCR': 'KC',
                            'WAS': 'WSH', 'WSH': 'WSH',
                            'OAK': 'ATH' # SportsData uses ATH for Athletics
                        }
                        # Map the discrepancy key to the MLB ID
                        for m_abbr, s_abbr in discrepancies.items():
                            if abbr == m_abbr:
                                id_map[s_abbr] = mlb_id
            except:
                pass
                        
            total_teams += 1
            print(f"Mapped {team['name']} ({mlb_id}) -> {abbr if 'abbr' in locals() else '???'}", end="\r")
            
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
