from app.services.sportsdata_client import SportsDataClient
import json

def test_api():
    print("Initializing SportsData Client...")
    try:
        client = SportsDataClient()
    except ValueError as e:
        print(e)
        return

    print("Fetching 2025 Team Stats (Sample)...")
    team_stats = client.get_season_team_stats(2025)
    
    if team_stats:
        print(f"Success! Retrieved stats for {len(team_stats)} teams.")
        print("Sample Team (First entry):")
        # Print a subset of keys to verify we have Runs/RunsAllowed
        first_team = team_stats[0]
        summary = {k: first_team[k] for k in ['Team', 'Wins', 'Losses', 'Runs', 'RunsAgainst'] if k in first_team}
        print(json.dumps(summary, indent=2))
    else:
        print("Failed to fetch team stats.")

    # Note: Not fetching player stats in this quick test as it might be large.

if __name__ == "__main__":
    test_api()
