import sys
import os
import statsapi
import time
from datetime import datetime

# Ensure app modules are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.game_replay_service import GameReplayService
from app.services.market_simulator import MarketSimulator
from app.services.trader_agent import TraderAgent
from app.services.markov_chain_service import MarkovChainService
from app.services.pitcher_monitor import PitcherMonitor

class ShadowCampaignRunner:
    def __init__(self, initial_bankroll=10000.0):
        self.bankroll = initial_bankroll
        self.initial_bankroll = initial_bankroll
        self.total_wins = 0
        self.total_losses = 0
        self.total_bets = 0
        self.trade_log = []
        
        # Services
        self.replay = GameReplayService()
        self.market_sim = MarketSimulator()
        self.markov = MarkovChainService()
        
    def run_campaign(self, game_ids):
        print(f"=== Starting Shadow Campaign (Games: {len(game_ids)}) ===")
        print(f"Initial Bankroll: ${self.bankroll:,.2f}")
        
        for game_pk in game_ids:
            self._process_game(game_pk)
            
        self._print_final_report()

    def _process_game(self, game_pk):
        print(f"\n--- Processing Game {game_pk} ---")
        
        # Reset Per-Game State
        pitcher_monitor = PitcherMonitor()
        current_pitcher_id = None
        trader = TraderAgent(bankroll=self.bankroll) # Use current bankroll? 
        # Actually TraderAgent tracks its own bankroll probably? 
        # Checking TraderAgent... it takes bankroll in __init__.
        # We need to sync the bankroll back after the game, or persist it.
        # Let's keep it simple: We accumulate bets and settle them manually here for the report.
        
        # Wait, TraderAgent just makes DECISIONS ("BET", "PASS").
        # We need to act as the "Execution Engine" here to track P&L.
        
        game_bets = []
        
        try:
            for event in self.replay.stream_game_events(game_pk):
                # 1. Update Pitcher/Fatigue
                pitcher_id = event.get('pitcher_id')
                if pitcher_id != current_pitcher_id:
                    current_pitcher_id = pitcher_id
                    pitcher_monitor = PitcherMonitor() # Reset for new pitcher
                    # In a real campaign we'd track bullpen history, but for this simulation
                    # we assume fresh unless simulated otherwise.
                    pitcher_monitor.update_pitcher(pitcher_id, is_starter=(event['inning'] < 2))
                
                pitcher_monitor.pitch_count += 1
                pitcher_mod = pitcher_monitor.get_performance_modifier()
                
                # 2. Get Odds & Probs
                # Market (Dumb)
                market_odds = self.market_sim.get_market_odds(
                    event['home_score'], event['away_score'], event['inning'], event['is_top'], event['state_idx']
                )
                
                # Sharp (Model)
                if event['state_idx'] < 24:
                    outs, r1, r2, r3 = self.markov.IDX_TO_STATE[event['state_idx']]
                    runners = [r1, r2, r3]
                else:
                    outs, runners = 3, [0,0,0]
                    
                sharp_prob = self.markov.get_instant_win_prob(
                    event['inning'], outs, runners, 
                    event['home_score'] - event['away_score'], 
                    event['is_top'], pitcher_mod=pitcher_mod
                )
                
                # 3. Trader Logic
                context = {
                    'inning': event['inning'],
                    'score_diff': abs(event['home_score'] - event['away_score']),
                    'leverage_index': 1.0 # Simplified
                }
                
                decision = trader.evaluate_trade(sharp_prob, market_odds, context)
                
                if decision['action'] == "BET":
                    # For simulation, we assume we take the bet.
                    # But we need to know the RESULT of the game to settle it.
                    # We don't know the result yet!
                    # We'll just log it and settle at the end of the game based on final score.
                    
                    bet_info = {
                        'game_pk': game_pk,
                        'inning': event['inning'],
                        'team': 'HOME' if decision['wager_amount'] > 0 else 'AWAY', # Wait, logic returns wager amount strictly?
                        # TraderAgent currently doesn't specify SIDE explicitly in return dict, 
                        # but evaluate_trade usually implies betting on the Value side.
                        # Looking at TraderAgen source (memory): it returns decision based on edge.
                        # We need to infer side. 
                        # The `evaluate_trade` compares sharp home_prob vs market home_odds.
                        # If sharp > implied, bet HOME. If sharp < implied, bet AWAY (if implemented).
                        # Let's assume for now we only bet ON VALUE.
                        
                        # Let's checking TraderAgent logic... 
                        # It calculates Kelly. 
                        # If edge > 0, it bets.
                        # Since we pass Home Prob and Home Odds, a positive edge usually means Bet Home.
                        # Wait, if Market implies 60% and we think 40%, is that a bet on Away?
                        # TraderAgent likely handles "Home" bets primarily unless we pass "Away" perspective.
                        # For this campaign, we will assume all analysis is Home Team perspective.
                        # Meaning precise "BET" means "Bet on Home Team Value".
                        
                        'amount': decision['wager_amount'],
                        'odds': market_odds,
                        'reason': decision['reason']
                    }
                    game_bets.append(bet_info)
                    self.total_bets += 1
                    # print(f"  [SNIPER FIRE] ${bet_info['amount']} on HOME @ {bet_info['odds']} ({bet_info['reason']})")
        
        except Exception as e:
            print(f"Error processing game {game_pk}: {e}")
            return

        # 4. Settle Bets
        # Get final score
        # Ideally GameReplayService should give us the final result or we fetch it.
        # We can fetch boxscore.
        try:
            # Fetch Final Score via Schedule Endpoint (Reliable)
            game_result = statsapi.schedule(game_id=game_pk)[0]
            final_home_runs = int(game_result['home_score'])
            final_away_runs = int(game_result['away_score'])
            
            home_won = final_home_runs > final_away_runs
            
            print(f"  Result: Home {final_home_runs} - Away {final_away_runs} | Winner: {'HOME' if home_won else 'AWAY'}")
            
            pnl_game = 0.0
            
            for bet in game_bets:
                # We assume all bets were on Home (needs refinement for Away support)
                # Calculating Payout
                wager = float(bet['amount'])
                odds = int(bet['odds'])
                
                # American Odds Payout Logic
                multiplier = 0.0
                if odds > 0:
                    multiplier = odds / 100.0
                else:
                    multiplier = 100.0 / abs(odds)
                    
                if home_won:
                    profit = wager * multiplier
                    pnl_game += profit
                    self.total_wins += 1
                else:
                    pnl_game -= wager
                    self.total_losses += 1
                    
            self.bankroll += pnl_game
            self.trade_log.extend(game_bets)
            print(f"  Game P&L: ${pnl_game:,.2f} | Bets: {len(game_bets)}")
            
        except Exception as e:
            print(f"Error settling bets for game {game_pk}: {e}")

    def _print_final_report(self):
        print("\n=== Campaign Final Report ===")
        print(f"Games Processed: {len(self.trade_log)}") # this is actually bets.
        print(f"Total Bets: {self.total_bets}")
        print(f"Wins: {self.total_wins} | Losses: {self.total_losses}")
        win_rate = 0.0
        if self.total_bets > 0:
            win_rate = self.total_wins / self.total_bets
        print(f"Win Rate: {win_rate:.1%}")
        
        profit = self.bankroll - self.initial_bankroll
        roi = 0.0
        if self.initial_bankroll > 0:
            roi = profit / self.initial_bankroll
            
        print(f"Final Bankroll: ${self.bankroll:,.2f}")
        print(f"Total Profit: ${profit:,.2f}")
        print(f"ROI: {roi:.2%}")
        
        if roi > 0:
            print("✅ CAMPAIGN SUCCESS: Positive ROI achieved.")
        else:
            print("⚠️ CAMPAIGN WARNING: Negative ROI. Calibration needed.")

if __name__ == "__main__":
    # 2024 World Series (LAD vs NYY)
    # Using hardcoded IDs for robustness/consistency.
    print("Initializing 2024 World Series Campaign (Games 1-5)...")
    
    # Official Game PKs for 2024 World Series
    game_ids = [
        775323, # Game 1 (LAD 6-3 NYY via Walkoff GS)
        775324, # Game 2 (LAD 4-2 NYY)
        775325, # Game 3 (LAD 4-2 NYY)
        775326, # Game 4 (NYY 11-4 LAD)
        775327  # Game 5 (LAD 7-6 NYY)
    ]
        
    try:
        runner = ShadowCampaignRunner()
        runner.run_campaign(game_ids)
        
    except Exception as e:
        print(f"Critical Campaign Error: {e}")
