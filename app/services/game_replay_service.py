import time
from app.services.mlb_api import MlbApi
from app.services.state_engine import StateEngine
from app.services.pitcher_monitor import PitcherMonitor

class GameReplayService:
    """
    Simulates a live game by replaying historical play-by-play data.
    Feeds events into the StateEngine to calculate real-time probabilities.
    """

    def __init__(self, db_manager=None):
        self.mlb_api = MlbApi(db_manager)
        self.state_engine = StateEngine()
        self.home_pitcher_monitor = PitcherMonitor()
        self.away_pitcher_monitor = PitcherMonitor()

    def replay_game(self, game_pk, delay=1.0):
        """
        Replays the game event-by-event.
        delay: Time in seconds to wait between events (simulating live pace).
        """
        print(f"--- Starting Replay for Game {game_pk} ---")
        
        # 1. Fetch Full Game Data
        live_data = self.mlb_api.get_live_game_data(game_pk)
        if not live_data:
            print("Failed to fetch game data.")
            return

        game_data = live_data.get('gameData', {})
        live_feed = live_data.get('liveData', {})
        
        home_team = game_data.get('teams', {}).get('home', {}).get('name')
        away_team = game_data.get('teams', {}).get('away', {}).get('name')
        print(f"Matchup: {away_team} @ {home_team}")
        
        # 2. Extract Plays
        all_plays = live_feed.get('plays', {}).get('allPlays', [])
        print(f"Total Events: {len(all_plays)}")
        
        # Track initial starters to determine bullpen usage
        home_starter_id = None
        away_starter_id = None

        # 3. Iterate and Simulate
        current_score = {"home": 0, "away": 0}
        
        for i, play in enumerate(all_plays):
            result = play.get('result', {})
            about = play.get('about', {})
            count = play.get('count', {})
            matchup = play.get('matchup', {})
            
            # Update Score
            current_score['home'] = result.get('homeScore', current_score['home'])
            current_score['away'] = result.get('awayScore', current_score['away'])
            
            # --- Pitcher Monitoring ---
            pitcher_data = matchup.get('pitcher', {})
            pitcher_id = pitcher_data.get('id')
            pitcher_name = pitcher_data.get('fullName')
            
            inning = about.get('inning')
            is_top = about.get('isTopInning')
            
            # Select Active Monitor (Defense)
            # Top Inning: Away Batting, Home Pitching
            # Bot Inning: Home Batting, Away Pitching
            if is_top:
                active_monitor = self.home_pitcher_monitor
                if home_starter_id is None: home_starter_id = pitcher_id
                is_starter = (pitcher_id == home_starter_id)
            else:
                active_monitor = self.away_pitcher_monitor
                if away_starter_id is None: away_starter_id = pitcher_id
                is_starter = (pitcher_id == away_starter_id)
            
            if pitcher_id:
                active_monitor.update_pitcher(pitcher_id, is_starter)
                active_monitor.log_at_bat()
                
                # Estimate pitches per PA (avg 3.8) since granular pitch-by-pitch is deeper in JSON
                # For more accuracy, we could count 'playEvents' where 'isPitch' is true.
                pitch_events = [e for e in play.get('playEvents', []) if e.get('isPitch')]
                active_monitor.log_pitch(len(pitch_events) if pitch_events else 1)

            # --- State Engine ---
            outs = count.get('outs', 0)
            
            runner_1 = 1 if match_key_exists(play, 'matchup.postOnFirst') else 0
            runner_2 = 1 if match_key_exists(play, 'matchup.postOnSecond') else 0
            runner_3 = 1 if match_key_exists(play, 'matchup.postOnThird') else 0
            
            state_idx = self.state_engine.get_current_state_index(outs, runner_1, runner_2, runner_3)
            
            re24 = self.state_engine.calculate_expected_runs(state_idx)
            win_prob = self.state_engine.get_win_probability(
                current_score['home'], 
                current_score['away'], 
                inning, 
                0 if is_top else 1, 
                state_idx
            )
            
            # Output Event
            desc = result.get('description', 'No description')
            print(f"\n{('Top' if is_top else 'Bot')} {inning} | Outs: {outs} | Score: {current_score['away']}-{current_score['home']}")
            print(f"Event: {desc}")
            print(f"State: {self.state_engine.IDX_TO_STATE[state_idx]}")
            
            # Alerts
            if active_monitor.check_ttto_signal():
                print(f"  [ALERT] TTTO Danger: {pitcher_name} facing batter #{active_monitor.batters_faced}")
                # Adjust win prob in favor of batting team?
            
            if active_monitor.check_fatigue_signal():
                print(f"  [ALERT] Fatigue Watch: {pitcher_name} over 95 pitches ({active_monitor.pitch_count})")

            print(f"RE24: {re24:.2f} runs | Win Prob (Home): {win_prob:.1%}")
            
            # time.sleep(delay) 

def match_key_exists(data, key_path):
    """
    Helper to check nested keys.
    key_path: 'matchup.postOnFirst'
    """
    keys = key_path.split('.')
    curr = data
    for k in keys:
        if isinstance(curr, dict) and k in curr:
            curr = curr[k]
        else:
            return False
    return True
