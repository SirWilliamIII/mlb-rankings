from app.services.sportsdata_client import SportsDataClient
import json

def check_odds():
    client = SportsDataClient()
    # Try a date likely to have games/odds? 
    # Opening day 2026 might be around March 26
    date_str = "2026-03-26" 
    print(f"Checking odds for {date_str}...")
    odds = client.get_daily_odds(date_str)
    
    if odds:
        print(f"Found {len(odds)} games with odds.")
        print(json.dumps(odds[0], indent=2))
    else:
        print("No odds found (expected, as it's too early).")

if __name__ == "__main__":
    check_odds()
