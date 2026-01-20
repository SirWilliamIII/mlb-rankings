import time
from datetime import datetime, timezone
from app.services.mlb_api import MlbApi
from app.services.state_engine import StateEngine
from app.services.pitcher_monitor import PitcherMonitor
from app.services.bullpen_history_service import BullpenHistoryService

class GameReplayService:
    """
    Simulates a live game by replaying historical play-by-play data.
    Feeds events into the StateEngine to calculate real-time probabilities.
    """

    def __init__(self, db_manager=None):
        self.mlb_api = MlbApi(db_manager)
        self.state_engine = StateEngine()
        self.bullpen_service = BullpenHistoryService()
        # PitcherMonitors are initialized per-game with bullpen fatigue data
        self.home_pitcher_monitor = None
        self.away_pitcher_monitor = None

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

        home_team_data = game_data.get('teams', {}).get('home', {})
        away_team_data = game_data.get('teams', {}).get('away', {})
        home_team = home_team_data.get('name')
        away_team = away_team_data.get('name')
        home_team_id = home_team_data.get('id')
        away_team_id = away_team_data.get('id')
        print(f"Matchup: {away_team} @ {home_team}")

        # Fetch bullpen fatigue for both teams
        print("Fetching bullpen fatigue data...")
        home_fatigue = self.bullpen_service.get_team_bullpen_fatigue(home_team_id) if home_team_id else {}
        away_fatigue = self.bullpen_service.get_team_bullpen_fatigue(away_team_id) if away_team_id else {}

        # Initialize pitcher monitors with bullpen fatigue data
        self.home_pitcher_monitor = PitcherMonitor(bullpen_fatigue=home_fatigue)
        self.away_pitcher_monitor = PitcherMonitor(bullpen_fatigue=away_fatigue)

        if home_fatigue:
            dead_count = sum(1 for p in home_fatigue.values() if p.get('status') == 'Dead')
            tired_count = sum(1 for p in home_fatigue.values() if p.get('status') == 'Tired')
            print(f"  {home_team} bullpen: {dead_count} Dead, {tired_count} Tired, {len(home_fatigue) - dead_count - tired_count} Fresh")
        if away_fatigue:
            dead_count = sum(1 for p in away_fatigue.values() if p.get('status') == 'Dead')
            tired_count = sum(1 for p in away_fatigue.values() if p.get('status') == 'Tired')
            print(f"  {away_team} bullpen: {dead_count} Dead, {tired_count} Tired, {len(away_fatigue) - dead_count - tired_count} Fresh")

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

            # Get pitcher fatigue/TTTO modifier
            pitcher_modifier = active_monitor.get_performance_modifier()

            re24 = self.state_engine.calculate_expected_runs(state_idx, pitcher_modifier)
            win_prob = self.state_engine.get_win_probability(
                current_score['home'],
                current_score['away'],
                inning,
                0 if is_top else 1,
                state_idx,
                pitcher_modifier=pitcher_modifier
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

            modifier_note = f" [Pitcher Mod: {pitcher_modifier:.2f}]" if pitcher_modifier > 1.0 else ""
            print(f"RE24: {re24:.2f} runs | Win Prob (Home): {win_prob:.1%}{modifier_note}")
            
            # time.sleep(delay) 

    def stream_game_events(self, game_pk):
        """
        Generator that yields game state dictionaries for backtesting.
        Allows the TraderAgent to 'pause' the game at every event and make a decision.
        """
        # 1. Fetch Full Game Data
        live_data = self.mlb_api.get_live_game_data(game_pk)
        if not live_data:
            return

        game_data = live_data.get('gameData', {})
        live_feed = live_data.get('liveData', {})
        
        home_team_id = game_data.get('teams', {}).get('home', {}).get('id')
        away_team_id = game_data.get('teams', {}).get('away', {}).get('id')

        # Initialize Pitcher Monitors
        home_fatigue = self.bullpen_service.get_team_bullpen_fatigue(home_team_id) if home_team_id else {}
        away_fatigue = self.bullpen_service.get_team_bullpen_fatigue(away_team_id) if away_team_id else {}
        
        self.home_pitcher_monitor = PitcherMonitor(bullpen_fatigue=home_fatigue)
        self.away_pitcher_monitor = PitcherMonitor(bullpen_fatigue=away_fatigue)

        # Track starters
        home_starter_id = None
        away_starter_id = None
        
        current_score = {"home": 0, "away": 0}
        all_plays = live_feed.get('plays', {}).get('allPlays', [])

        for play in all_plays:
            result = play.get('result', {})
            about = play.get('about', {})
            count = play.get('count', {})
            matchup = play.get('matchup', {})
            
            # Update Score
            current_score['home'] = result.get('homeScore', current_score['home'])
            current_score['away'] = result.get('awayScore', current_score['away'])

            # --- Pitcher Logic ---
            pitcher_data = matchup.get('pitcher', {})
            pitcher_id = pitcher_data.get('id')
            pitcher_name = pitcher_data.get('fullName')
            inning = about.get('inning')
            is_top = about.get('isTopInning')

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
                pitch_events = [e for e in play.get('playEvents', []) if e.get('isPitch')]
                active_monitor.log_pitch(len(pitch_events) if pitch_events else 1)

            # --- State Engine Logic ---
            outs = count.get('outs', 0)
            runner_1 = 1 if match_key_exists(play, 'matchup.postOnFirst') else 0
            runner_2 = 1 if match_key_exists(play, 'matchup.postOnSecond') else 0
            runner_3 = 1 if match_key_exists(play, 'matchup.postOnThird') else 0

            state_idx = self.state_engine.get_current_state_index(outs, runner_1, runner_2, runner_3)
            pitcher_modifier = active_monitor.get_performance_modifier()

            # Yield the Context Bundle
            yield {
                "game_pk": game_pk,
                "inning": inning,
                "is_top": is_top,
                "home_score": current_score['home'],
                "away_score": current_score['away'],
                "outs": outs,
                "state_idx": state_idx,
                "pitcher_id": pitcher_id,
                "pitcher_name": pitcher_name,
                "pitcher_modifier": pitcher_modifier,
                "description": result.get('description', ''),
                "event_type": result.get('eventType', 'unknown'),
                "timestamp": about.get('startTime', datetime.now(timezone.utc).isoformat()), # Capture play time
                "is_complete": result.get('type') == 'atBat' 
            }

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
