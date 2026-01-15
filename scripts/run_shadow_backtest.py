import sys
import os

# Ensure app modules are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.game_replay_service import GameReplayService
from app.services.market_simulator import MarketSimulator
from app.services.trader_agent import TraderAgent
from app.services.state_engine import StateEngine

def run_backtest(game_pk):
    print(f"=== Starting Shadow Trader Backtest (Game {game_pk}) ===")
    
    # Initialize Services
    replay_service = GameReplayService()
    market_sim = MarketSimulator()
    trader = TraderAgent(bankroll=10000.0)
    state_engine = StateEngine()

    bets_placed = []
    rejection_reasons = {}

    # Iterate through the game
    for event in replay_service.stream_game_events(game_pk):
        
        # 1. Get Lazy Market Odds (Baseline Model, Modifier=1.0)
        market_odds = market_sim.get_market_odds(
            event['home_score'],
            event['away_score'],
            event['inning'],
            event['is_top'],
            event['state_idx']
        )
        
        # 2. Get Sharp Model Prob (With Fatigue/TTTO Modifier)
        sharp_prob = state_engine.get_win_probability(
            event['home_score'],
            event['away_score'],
            event['inning'],
            0 if event['is_top'] else 1,
            event['state_idx'],
            pitcher_modifier=event['pitcher_modifier']
        )
        
        # 3. Ask Trader for Decision
        context = {
            'inning': event['inning'], 
            'score_diff': abs(event['home_score'] - event['away_score']),
            'description': event['description']
        }
        
        decision = trader.evaluate_trade(
            model_prob=sharp_prob,
            market_odds_american=market_odds,
            game_context=context
        )
        
        # 4. Log Action
        if decision['action'] == "BET":
            # For this demo, we assume we bet on the Home Team if odds are generated for Home
            # (In a full version, we'd check both sides)
            print(f"[{event['inning']} ({'Top' if event['is_top'] else 'Bot'})] BET PLACED: ${decision['wager_amount']} on Home ({market_odds}) | Edge: {decision['edge']:.2%}")
            print(f"   Reason: {decision['reason']} | Mod: {event['pitcher_modifier']:.2f}")
            
            bets_placed.append({
                'odds': market_odds,
                'amount': decision['wager_amount'],
                'result': None, # Pending
                'home_score_at_bet': event['home_score'],
                'away_score_at_bet': event['away_score']
            })
            
        else:
            reason_key = decision['reason'].split('(')[0].strip() # Group by main reason
            rejection_reasons[reason_key] = rejection_reasons.get(reason_key, 0) + 1
            
    # 5. Settle Bets (Simple: Who actually won?)
    # We need the final score. 
    # The last event in the stream contains the final running score.
    final_home = event['home_score']
    final_away = event['away_score']
    
    home_won = final_home > final_away
    print(f"\n=== Game Over. Final: Home {final_home} - Away {final_away} ===")
    
    total_pnL = 0
    wins = 0
    losses = 0
    
    for bet in bets_placed:
        # Simple settlement: We only bet Home in this demo logic
        if home_won:
            # Profit calculation
            decimal_odds = market_sim._prob_to_american(0.5) # Wait, need inverse of american_to_decimal
            # Let's use trader helper
            dec = trader._american_to_decimal(bet['odds'])
            profit = bet['amount'] * (dec - 1)
            total_pnL += profit
            wins += 1
            print(f"✅ WIN: +${profit:.2f} (Odds {bet['odds']})")
        else:
            total_pnL -= bet['amount']
            losses += 1
            print(f"❌ LOSS: -${bet['amount']:.2f} (Odds {bet['odds']})")
            
    print(f"\nSUMMARY:")
    print(f"Total Bets: {len(bets_placed)}")
    print(f"Record: {wins}-{losses}")
    print(f"Net P&L: ${total_pnL:.2f}")
    print("\nDecision Breakdown:")
    for reason, count in rejection_reasons.items():
        print(f"  {reason}: {count}")
    
if __name__ == "__main__":
    # Use a known game PK from 2024/2025 (or find one via script)
    # 748534 is World Series Game 5 (Dodgers/Yankees 2024) - Example ID
    # If that fails, the script will just print nothing.
    # Let's try to find a valid one or user can provide.
    
    # We'll use a hardcoded one for now or fetch one via MlbApi if needed.
    # Let's try a generic ID, or fetch recent.
    
    from app.services.mlb_api import MlbApi
    api = MlbApi()
    # Get a game from last season?
    # For now, let's just pick one we used in testing or rely on user to provide.
    # I'll use 748550 (random valid looking ID) or let's inspect.
    
    # Better: Fetch the first game from a specific date to ensure validity.
    import statsapi
    try:
        schedule = statsapi.schedule(date="2024-10-25") # WS Game 1
        if schedule and len(schedule) > 0:
            game_pk = schedule[0]['game_id']
            print(f"Found Game PK: {game_pk} ({schedule[0]['away_name']} @ {schedule[0]['home_name']})")
            run_backtest(game_pk)
        else:
            print("Could not find a valid game for backtesting. Using fallback.")
            run_backtest(748534) # Fallback
    except Exception as e:
        print(f"Error fetching schedule: {e}. Using fallback.")
        run_backtest(748534) # Fallback
