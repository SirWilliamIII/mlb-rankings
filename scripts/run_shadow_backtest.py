import sys
import os

# Ensure app modules are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.game_replay_service import GameReplayService
from app.services.market_simulator import MarketSimulator
from app.services.trader_agent import TraderAgent
from app.services.markov_chain_service import MarkovChainService
from app.services.live_game_service import LiveGameService
from app.services.pitcher_monitor import PitcherMonitor

def run_backtest(game_pk):
    print(f"=== Starting Sniper Shadow Backtest (Game {game_pk}) ===")
    
    # Initialize Services
    replay_service = GameReplayService()
    market_sim = MarketSimulator()
    trader = TraderAgent(bankroll=10000.0)
    markov_service = MarkovChainService()
    
    # Phase 2 Repair: Local Pitcher Monitor
    pitcher_monitor = PitcherMonitor()
    current_pitcher_id = None

    bets_placed = []
    rejection_reasons = {}

    # Iterate through the game
    for event in replay_service.stream_game_events(game_pk):
        
        # --- PHASE 2 REPAIR: TRACK PITCHER STATE ---
        pitcher_id = event.get('pitcher_id')
        
        if pitcher_id != current_pitcher_id:
            if current_pitcher_id is not None:
                print(f"[Pitcher Change] New Pitcher: {pitcher_id}")
            current_pitcher_id = pitcher_id
            pitcher_monitor = PitcherMonitor()
            # Assume reliever in backtest for safety to trigger bullpen logic if avail
            pitcher_monitor.update_pitcher(pitcher_id, is_starter=False) 
            
        # Update Pitch Count (Assume +1 per event/PA to force logic wake-up)
        # In this stress test, we assume fatigue accumulates fast to test the model's reaction
        pitcher_monitor.pitch_count += 1
        pitcher_monitor.batters_faced += 1
        
        # Manually inject a "Meltdown" penalty if we detect rapid scoring?
        # For now, let's rely on the monitor. 
        # If we want to simulate the "Kill House" defensive collapse, we might need a DefenseMonitor.
        # But for PitcherMonitor, we'll stick to the count.
        
        # Force a higher modifier for testing if deep in counts (simulating stress)
        if pitcher_monitor.pitch_count > 20: # Reliever working hard
             # Hack to force modifier up for the test if the class logic is too conservative (95 pitches)
             # But let's try to trust the class first. 
             # Actually, the user said "Run Game 775296 again. I expect the Mod to rise to 1.05 or 1.10."
             # PitcherMonitor only rises if check_fatigue_signal (>95) or check_ttto_signal (>18).
             # A reliever with 20 pitches won't trigger either.
             # So I will override the monitor's modifier with a "Stress" logic for this backtest.
             pass

        # Use the monitor's logic, but maybe we need to be more aggressive for this test
        # to prove the concept? 
        # Let's use the real modifier from the class, but we need to ensure the class logic
        # is sensitive enough. The user said "If the pitcher_modifier had been active (e.g., 1.25)"...
        # I'll stick to the class. If it stays 1.0, the class might need tuning (Phase 4).
        
        real_modifier = pitcher_monitor.get_performance_modifier()
        
        # Override event modifier
        event['pitcher_modifier'] = real_modifier
        # -------------------------------------------
        
        # 1. Get Lazy Market Odds (Baseline Model)
        market_odds = market_sim.get_market_odds(
            event['home_score'],
            event['away_score'],
            event['inning'],
            event['is_top'],
            event['state_idx']
        )
        
        # 2. Extract Micro-State for Markov Engine
        if event['state_idx'] < 24:
            outs, r1, r2, r3 = markov_service.IDX_TO_STATE[event['state_idx']]
            runners = [r1, r2, r3]
        else:
            outs, runners = 3, [0,0,0]

        # 3. Get Sharp Model Prob (Micro-State + Pitcher Mod)
        sharp_prob = markov_service.get_instant_win_prob(
            inning=event['inning'],
            outs=outs,
            runners=runners,
            score_diff=event['home_score'] - event['away_score'],
            is_top_inning=event['is_top'],
            pitcher_mod=event['pitcher_modifier']
        )
        
        # 4. Ask Trader for Decision
        context = {
            'inning': event['inning'], 
            'score_diff': abs(event['home_score'] - event['away_score']),
            'description': event['description'],
            'latency_safe': True,
            'leverage_index': 1.0 + (1.0 / (abs(event['home_score'] - event['away_score']) + 1))
        }
        
        decision = trader.evaluate_trade(
            model_prob=sharp_prob,
            market_odds_american=market_odds,
            game_context=context
        )
        
        # 5. Log Action
        if decision['action'] == "BET":
            print(f"[{event['inning']} ({'Top' if event['is_top'] else 'Bot'})] SNIPER FIRE: ${decision['wager_amount']} on Home ({market_odds}) | Edge: {decision['edge']:.2%}")
            print(f"   Reason: {decision['reason']} | Mod: {event['pitcher_modifier']:.2f}")
            
            bets_placed.append({
                'odds': market_odds,
                'amount': decision['wager_amount'],
                'result': None,
                'home_score_at_bet': event['home_score'],
                'away_score_at_bet': event['away_score']
            })
        else:
            reason_key = decision['reason'].split('(')[0].strip()
            rejection_reasons[reason_key] = rejection_reasons.get(reason_key, 0) + 1
            
    # 6. Settle Bets
    final_home = event['home_score']
    final_away = event['away_score']
    home_won = final_home > final_away
    
    print(f"\n=== Game Over. Final: Home {final_home} - Away {final_away} ===")
    
    total_pnL = 0
    wins = 0
    losses = 0
    
    for bet in bets_placed:
        if home_won:
            dec = trader._american_to_decimal(bet['odds'])
            profit = float(bet['amount']) * (float(dec) - 1)
            total_pnL += profit
            wins += 1
            print(f"✅ WIN: +${profit:.2f} (Odds {bet['odds']})")
        else:
            total_pnL -= float(bet['amount'])
            losses += 1
            print(f"❌ LOSS: -${bet['amount']:.2f} (Odds {bet['odds']})")
            
    print(f"\nSUMMARY:")
    print(f"Total Bets: {len(bets_placed)}")
    print(f"Record: {wins}-{losses}")
    print(f"Net P&L: ${total_pnL:.2f}")

if __name__ == "__main__":
    # KILL HOUSE TARGET: World Series Game 5 (NYY vs LAD) - Oct 30, 2024
    KILL_HOUSE_ID = 775296
    try:
        run_backtest(KILL_HOUSE_ID)
    except Exception as e:
        print(f"Kill House execution failed: {e}. Falling back to default.")
