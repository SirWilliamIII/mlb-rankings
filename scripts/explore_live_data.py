import statsapi
import json

def explore_game_data(game_id):
    # Get boxscore data
    print(f"Fetching data for game {game_id}...")
    
    # 1. Game Linescore (Inning by inning, current state)
    linescore = statsapi.linescore(game_id)
    print("\n[Linescore Preview]")
    print(linescore[:200] + "...") # Print first 200 chars
    
    # 2. Game Play-by-Play (Live events)
    pbp = statsapi.get('game_playByPlay', {'gamePk': game_id})
    print("\n[Play-by-Play Keys]")
    print(pbp.keys())
    
    # Check for win probability data if available in pbp
    if 'allPlays' in pbp and len(pbp['allPlays']) > 0:
        # Check the last 5 plays for any probability data
        for play in pbp['allPlays'][-5:]:
            print("\n[Play Result]")
            print(json.dumps(play.get('result'), indent=2))
            if 'winProbability' in play:
                print(f"Found WinProb: {play['winProbability']}")
            elif 'playEvents' in play:
                 # sometimes it's nested
                 pass


    # 3. Game Context Metrics (Win Probability)
    # This endpoint is often where win probability lives: /api/v1/game/{gamePk}/contextMetrics
    try:
        metrics = statsapi.get('game_contextMetrics', {'gamePk': game_id})
        print("\n[Context Metrics]")
        print(json.dumps(metrics, indent=2)[:500] + "...")
    except Exception as e:
        print(f"\nCould not fetch context metrics: {e}")

if __name__ == "__main__":
    # Example Game: 2024 World Series Game 1 (Dodgers vs Yankees)
    # Date: 2024-10-25. 
    # I need to find the gamePk first.
    
    sched = statsapi.schedule(start_date='2024-10-25', end_date='2024-10-25')
    if sched:
        game_id = sched[0]['game_id']
        explore_game_data(game_id)
    else:
        print("No game found for that date.")
