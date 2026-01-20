import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.game_replay_service import GameReplayService
from app.services.market_simulator import MarketSimulator
from app.services.trader_agent import TraderAgent
# NEW IMPORT
from app.services.markov_chain_service import MarkovChainService
from app.services.pitcher_monitor import PitcherMonitor

def run_backtest(game_pk):
    print(f"=== Starting Sniper Shadow Backtest (Game {game_pk}) ===")
    
    replay_service = GameReplayService()
    market_sim = MarketSimulator()
    trader = TraderAgent(bankroll=10000.0)
    # FERRARI ENGINE
    markov_service = MarkovChainService()
    
    # FATIGUE MONITOR
    pitcher_monitor = PitcherMonitor()
    current_pitcher_id = None

    bets_placed = []
    
    for event in replay_service.stream_game_events(game_pk):
        # --- STRESS INJECTION (LEVEL 300) ---
        pitcher_id = event.get('pitcher_id')
        if pitcher_id != current_pitcher_id:
            print(f"[Pitcher Change] New Pitcher: {pitcher_id}")
            current_pitcher_id = pitcher_id
            pitcher_monitor = PitcherMonitor() 
            pitcher_monitor.update_pitcher(pitcher_id, is_starter=False)

        # Mock Stress: 5 pitches/PA normally, 15 pitches/PA if late-game close score
        simulated_pitches = 5
        if event['inning'] >= 8 and abs(event['home_score'] - event['away_score']) <= 2:
             simulated_pitches = 15 
        pitcher_monitor.pitch_count += simulated_pitches
        
        real_modifier = pitcher_monitor.get_performance_modifier()
        event['pitcher_modifier'] = real_modifier
        # ------------------------------------
        
        market_odds = market_sim.get_market_odds(
            event['home_score'], event['away_score'], event['inning'], event['is_top'], event['state_idx']
        )
        
        # EXTRACT MICRO-STATE
        if event['state_idx'] < 24:
            outs, r1, r2, r3 = markov_service.IDX_TO_STATE[event['state_idx']]
            runners = [r1, r2, r3]
        else:
            outs, runners = 3, [0,0,0]

        # INSTANT MARKOV LOOKUP
        sharp_prob = markov_service.get_instant_win_prob(
            inning=event['inning'],
            outs=outs,
            runners=runners,
            score_diff=event['home_score'] - event['away_score'],
            is_top_inning=event['is_top'],
            pitcher_mod=event['pitcher_modifier']
        )
        
        # CALCULATE LEVERAGE (Mocked for demo)
        li = 1.0 + (1.0 / (abs(event['home_score'] - event['away_score']) + 1))
        
        context = {
            'inning': event['inning'], 
            'score_diff': abs(event['home_score'] - event['away_score']),
            'leverage_index': li
        }
        
        decision = trader.evaluate_trade(sharp_prob, market_odds, context)
        
        if decision['action'] == "BET":
            print(f"[{event['inning']}] SNIPER FIRE: ${decision['wager_amount']} on Home ({market_odds}) | Edge: {decision['edge']:.2%} | LI: {li:.2f} | Mod: {real_modifier:.2f}")
            bets_placed.append(decision) # Simplified log

    print(f"\nFinal Bets Placed: {len(bets_placed)}")

if __name__ == "__main__":
    # KILL HOUSE TARGET: World Series Game 5 (NYY vs LAD) - Oct 30, 2024
    KILL_HOUSE_ID = 775296
    run_backtest(KILL_HOUSE_ID)
