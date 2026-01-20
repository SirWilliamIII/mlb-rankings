from app.services.mlb_api import MlbApi
from app.services.state_engine import StateEngine
from app.services.bullpen_history_service import BullpenHistoryService
from app.services.pitcher_monitor import PitcherMonitor
from app.services.trader_agent import TraderAgent
from app.services.market_simulator import MarketSimulator
from app.services.latency_monitor import LatencyMonitor
from app.services.markov_chain_service import MarkovChainService
from app.services.notification_service import NotificationService
import datetime

class LiveGameService:
    """
    Orchestrates Live Operations (Phase 3).
    Polls active games, calculates real-time probabilities, and generates Sniper Signals.
    """

    def __init__(self, db_manager=None):
        self.mlb_api = MlbApi(db_manager)
        self.state_engine = StateEngine()
        self.markov_service = MarkovChainService()
        self.bullpen_service = BullpenHistoryService()
        self.trader_agent = TraderAgent()
        self.market_sim = MarketSimulator() # Placeholder for real odds API
        self.latency_monitor = LatencyMonitor(db_manager)
        self.notifier = NotificationService()
        
        # Cache for PitcherMonitors (keyed by game_pk)
        self.monitors = {}
        
        # Signal History (In-Memory for now)
        self.signal_history = []

    def get_signal_history(self):
        """Returns the list of recent generated signals."""
        return sorted(self.signal_history, key=lambda x: x['timestamp'], reverse=True)

    def get_live_dashboard_data(self):
        """
        Main entry point for the frontend.
        Returns a list of active games with their current 'Sniper' status.
        """
        # 1. Get Today's Games
        # For Dev/Demo: If no games live, we might want to mock one or use replay data?
        # We will assume "today" logic.
        
        # In 'Production', we use datetime.now().
        # For this 'Phase 3' setup, we'll try to fetch real live games.
        # If none are live, we might return an empty list or a 'demo' mode flag.
        
        schedule = self.mlb_api.get_schedule(date=None) # Defaults to today
        
        live_games = []
        
        # --- MOCK DATA INJECTION (Offseason/Demo) ---
        if not schedule or not any(g.get('status') == 'I' for g in schedule):
            return self._get_mock_games()
        # --------------------------------------------

        for game in schedule:
            # Check status
            status = game.get('status', 'Unknown')
            if status == 'I': 
                game_data = self._process_live_game(game['game_id'])
                if game_data:
                    live_games.append(game_data)
        
        return live_games

    def _get_mock_games(self):
        """
        Returns simulated live games for demonstration.
        Also populates history for demo purposes.
        """
        # Populate mock history if empty
        if not self.signal_history:
            self.signal_history = [
                {
                    "key": "mock_1", 
                    "timestamp": datetime.datetime.now().strftime('%H:%M:%S'),
                    "game": "NYY @ BOS",
                    "inning": "Bot 8",
                    "wager": 415.00,
                    "odds": -110,
                    "reason": "Fatigue Mismatch (Mod 1.15)"
                }
            ]

        # Mock 1: High Leverage, Fatigue Alert -> Bet Signal
        mock_1 = {
            "game_id": 999001,
            "matchup": "NYY @ BOS",
            "status": "In Progress",
            "inning_state": "Bot 8",
            "score": "3-3",
            "outs": 1,
            "runners": [0, 1, 0], # Runner on 2nd
            "pitcher": {
                "name": "Clay Holmes",
                "modifier": 1.15,
                "alert": "FATIGUE"
            },
            "model_prob": 62.5,
            "market_odds": -110,
            "signal": {
                "action": "BET",
                "edge": "4.15%",
                "wager": "$415.00",
                "reason": "Fatigue Mismatch (Mod 1.15)"
            }
        }

        # Mock 2: Blowout -> Block Signal
        mock_2 = {
            "game_id": 999002,
            "matchup": "LAD @ SF",
            "status": "In Progress",
            "inning_state": "Top 7",
            "score": "8-1",
            "outs": 2,
            "runners": [0, 0, 0],
            "pitcher": {
                "name": "Logan Webb",
                "modifier": 1.0,
                "alert": "OK"
            },
            "model_prob": 98.2,
            "market_odds": -5000,
            "signal": {
                "action": "BLOCK",
                "edge": "0.00%",
                "wager": "$0.00",
                "reason": "Garbage Time (Diff 7)"
            }
        }
        
        return [mock_1, mock_2]

    def _process_live_game(self, game_pk):
        """
        Analyzes a single live game.
        """
        # 1. Fetch Granular Data
        live_data = self.mlb_api.get_live_game_data(game_pk)
        if not live_data:
            return None
            
        game_data = live_data.get('gameData', {})
        live_feed = live_data.get('liveData', {})
        linescore = live_feed.get('linescore', {})
        
        # --- PHASE 1: LATENCY CHECK ---
        # Extract Timestamp (statsapi usually puts it in metaData)
        meta_data = live_data.get('metaData', {})
        event_ts = meta_data.get('timeStamp') # e.g. "2023-10-25T21:03:01.123Z"
        
        self.latency_monitor.log_feed_delta(game_pk, event_ts)
        is_latency_safe = self.latency_monitor.is_safe_window()
        # ------------------------------
        
        # 2. Extract Key State
        home_id = game_data.get('teams', {}).get('home', {}).get('id')
        away_id = game_data.get('teams', {}).get('away', {}).get('id')
        home_name = game_data.get('teams', {}).get('home', {}).get('name')
        away_name = game_data.get('teams', {}).get('away', {}).get('name')
        
        current_inning = linescore.get('currentInning', 1)
        is_top = linescore.get('isTopInning', True)
        outs = linescore.get('outs', 0)
        home_score = linescore.get('teams', {}).get('home', {}).get('runs', 0)
        away_score = linescore.get('teams', {}).get('away', {}).get('runs', 0)
        
        # Runners
        offense = linescore.get('offense', {})
        r1 = 1 if 'first' in offense else 0
        r2 = 1 if 'second' in offense else 0
        r3 = 1 if 'third' in offense else 0
        
        state_idx = self.state_engine.get_current_state_index(outs, r1, r2, r3)

        # 3. Manage Monitors (Fatigue/TTTO)
        if game_pk not in self.monitors:
            # Initialize if new
            h_fatigue = self.bullpen_service.get_team_bullpen_fatigue(home_id)
            a_fatigue = self.bullpen_service.get_team_bullpen_fatigue(away_id)
            self.monitors[game_pk] = {
                'home': PitcherMonitor(bullpen_fatigue=h_fatigue),
                'away': PitcherMonitor(bullpen_fatigue=a_fatigue)
            }
            
        monitors = self.monitors[game_pk]
        
        # Identify Current Pitcher
        # In linescore 'defense' usually has 'pitcher'
        defense = linescore.get('defense', {})
        pitcher_id = defense.get('pitcher', {}).get('id')
        pitcher_name = defense.get('pitcher', {}).get('fullName', 'Unknown')
        
        if is_top:
            active_monitor = monitors['home'] # Home pitching
        else:
            active_monitor = monitors['away'] # Away pitching
            
        # Update Monitor (Simplified for poll-based: just update ID)
        active_monitor.update_pitcher(pitcher_id, is_starter=True) 
        
        # 4. Calculate Probabilities
        pitcher_modifier = active_monitor.get_performance_modifier()
        
        # Phase 2: Use Markov Service for Instant Lookup
        sharp_prob = self.markov_service.get_instant_win_prob(
            inning=current_inning,
            outs=outs,
            runners=[r1, r2, r3],
            score_diff=home_score - away_score,
            is_top_inning=is_top,
            pitcher_mod=pitcher_modifier,
            defense_mod=1.0 # Placeholder for Phase 3 Hardening
        )
        
        # 5. Market Odds (Simulated for Phase 3 until API upgrade)
        market_odds = self.market_sim.get_market_odds(
            home_score, away_score, current_inning, is_top, state_idx
        )
        
        # 6. Trader Analysis
        context = {
            'inning': current_inning,
            'score_diff': abs(home_score - away_score),
            'leverage_index': 1.0, # Placeholder
            'latency_safe': is_latency_safe # Pass latency flag
        }
        
        decision = self.trader_agent.evaluate_trade(sharp_prob, market_odds, context)
        
        # --- LOGGING SIGNALS ---
        if decision['action'] == 'BET':
            # Create a unique key for this moment to prevent duplicate logs during polling
            signal_key = f"{game_pk}_{current_inning}_{outs}_{home_score}-{away_score}"
            
            # Check if we already logged this exact moment recently
            # (Simple linear scan for demo - optimize for production)
            if not any(s['key'] == signal_key for s in self.signal_history):
                self.signal_history.append({
                    "key": signal_key,
                    "timestamp": datetime.datetime.now().strftime('%H:%M:%S'),
                    "game": f"{away_name} @ {home_name}",
                    "inning": f"{'Top' if is_top else 'Bot'} {current_inning}",
                    "wager": decision['wager_amount'],
                    "odds": market_odds,
                    "reason": decision['reason']
                })
                
                # Trigger Tier 2 Operator Alert
                self.notifier.send_alert(
                    title="SNIPER SIGNAL: BET",
                    message=f"Game: {away_name} @ {home_name}\nInning: {'Top' if is_top else 'Bot'} {current_inning}\nWager: ${decision['wager_amount']} @ {market_odds}\nReason: {decision['reason']}",
                    level="SUCCESS"
                )
        # -----------------------
        
        return {
            "game_id": game_pk,
            "matchup": f"{away_name} @ {home_name}",
            "status": "In Progress",
            "inning_state": f"{'Top' if is_top else 'Bot'} {current_inning}",
            "score": f"{away_score}-{home_score}",
            "outs": outs,
            "runners": [r1, r2, r3],
            "pitcher": {
                "name": pitcher_name,
                "modifier": round(pitcher_modifier, 2),
                "alert": "FATIGUE" if pitcher_modifier > 1.1 else ("TTTO" if pitcher_modifier > 1.05 else "OK")
            },
            "model_prob": round(sharp_prob * 100, 1),
            "market_odds": market_odds,
            "signal": {
                "action": decision['action'],
                "edge": f"{decision['edge']:.2%}",
                "wager": f"${decision['wager_amount']}",
                "reason": decision['reason']
            }
        }
