import statsapi
import json

def inspect_box():
    game_pk = 775323
    print(f"Fetching boxscore for {game_pk}...")
    box = statsapi.boxscore_data(game_pk)
    
    # Print keys
    print(f"Top Keys: {list(box.keys())}")
    
    # Inspect linescore
    linescore = box.get('linescore')
    print(f"Linescore Type: {type(linescore)}")
    if isinstance(linescore, dict):
        print(f"Linescore Keys: {list(linescore.keys())}")
        if 'teams' in linescore:
            print(f"Teams: {linescore['teams']}")
        else:
            print("No 'teams' key in linescore.")
    else:
        print(f"Linescore Content: {linescore}")
        
    # Inspect teamInfo
    if 'teamInfo' in box:
        print(f"TeamInfo: {box['teamInfo']}")

if __name__ == "__main__":
    inspect_box()
