import statsapi
import json

def inspect_mlb_data():
    print("Fetching standings data...")
    standings = statsapi.standings_data(leagueId="103,104", season=2025)
    
    # Just look at the first team found to see structure
    for div in standings.values():
        for team in div['teams']:
            print(f"Team: {team['name']}")
            print(f"Keys: {list(team.keys())}")
            # We hope to see 'abbreviation' or similar
            print(f"ID: {team['team_id']}")
            # statsapi usually doesn't give abbreviation in standings_data directly, 
            # might need statsapi.lookup_team(team_id)
            
            # Let's try looking up this specific team to see what full metadata we get
            full_data = statsapi.lookup_team(team['team_id'])
            if full_data:
                print("Lookup Data Keys:", full_data[0].keys())
                print("Abbreviation:", full_data[0].get('fileCode')) # 'fileCode' is often the abbr
                print("TeamName:", full_data[0].get('teamName'))
                print("Abbreviation (alt):", full_data[0].get('abbreviation'))
            
            return # Just one is enough

if __name__ == "__main__":
    inspect_mlb_data()
