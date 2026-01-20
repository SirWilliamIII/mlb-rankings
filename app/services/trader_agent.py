from typing import Dict, Optional, Tuple
import json
import time
import uuid
import threading
import queue
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

class TraderAgent:
    """
    Automated Trading Agent for MLB Live Betting.
    Responsible for executing the 'Active Trading' logic:
    1. Kelly Criterion Sizing
    2. Divergence/Edge Detection
    3. Safety Valve Checks (Garbage Time, etc.)
    4. Non-blocking persistence of shadow bets.
    """

    def __init__(self, db_manager=None, bankroll: float = 10000.0, kelly_fraction: float = 0.25, 
                 min_edge: float = 0.02, max_wager_limit: float = 0.05):
        """
        Args:
            db_manager: Database connection manager.
            bankroll: Total capital available.
            kelly_fraction: Fraction of Full Kelly to wager (e.g., 0.25 = Quarter Kelly).
            min_edge: Minimum positive EV required to trigger a bet (e.g., 0.02 = 2%).
            max_wager_limit: Hard cap on wager size as % of bankroll (e.g., 0.05 = 5%).
        """
        self.db_manager = db_manager
        self.bankroll = Decimal(str(bankroll))
        self.kelly_fraction = Decimal(str(kelly_fraction))
        self.min_edge = Decimal(str(min_edge))
        self.max_wager_limit = Decimal(str(max_wager_limit))
        
        # Async Bet Logger Setup
        self._bet_queue = queue.Queue()
        self._stop_event = threading.Event()
        if self.db_manager:
            self._worker_thread = threading.Thread(target=self._bet_logger_worker, daemon=True)
            self._worker_thread.start()

    def generate_tier1_signal(self, data: Dict) -> str:
        """
        Generates a Tier 1 Execution Signal (Minified JSON).
        Latency Budget: < 50ms.
        """
        signal = {
            "t": str(time.time()),
            "g": data.get("game_id"),
            "m": data.get("market"),
            "o": data.get("odds"),
            "p": float(data.get("prob", 0.0)),
            "s": float(data.get("stake", 0.0)),
            "id": str(uuid.uuid4())
        }
        return json.dumps(signal, separators=(',', ':'))

    def evaluate_trade(self, model_prob: float, market_odds_american: int, 
                       game_context: Optional[Dict] = None) -> Dict:
        """
        Evaluates a potential trade and returns a decision.
        """
        # Convert inputs to Decimal
        d_model_prob = Decimal(str(model_prob))
        
        # 1. Convert Market Odds to Implied Probability & Decimal
        d_decimal_odds = self._american_to_decimal(market_odds_american)
        d_implied_prob = Decimal("1.0") / d_decimal_odds

        # 2. Calculate Edge (EV)
        d_ev = (d_model_prob * d_decimal_odds) - Decimal("1.0")
        d_edge = d_model_prob - d_implied_prob

        # 3. Check Safety Valves
        is_safe, safety_reason = self._check_safety_valves(game_context)
        if not is_safe:
            return self._build_response("BLOCK", safety_reason, Decimal("0.0"), d_implied_prob, d_edge)

        # 4. Check Value Threshold
        if d_ev < self.min_edge:
            reason = f"No Edge (EV: {d_ev:.2%}, Min: {self.min_edge:.2%})"
            return self._build_response("PASS", reason, Decimal("0.0"), d_implied_prob, d_edge)

        # 5. Calculate Position Size (Kelly Criterion)
        li = game_context.get('leverage_index', 1.0) if game_context else 1.0
        d_li = Decimal(str(li))
        
        d_wager_pct = self._calculate_kelly_fraction(d_model_prob, d_decimal_odds, d_li)
        
        # Apply limits
        d_wager_pct = min(d_wager_pct, self.max_wager_limit)
        d_wager_amount = self.bankroll * d_wager_pct

        if d_wager_amount <= Decimal("0.0"):
             return self._build_response("PASS", "Kelly suggested <= 0", Decimal("0.0"), d_implied_prob, d_edge)

        response = self._build_response("BET", f"Value detected (EV: {d_ev:.2%}, LI: {d_li:.2f})", 
                                    d_wager_amount, d_implied_prob, d_edge, d_wager_pct)
        
        # Async Persistence
        if self.db_manager:
            payload = {
                'game_id': game_context.get('game_id', 0) if game_context else 0,
                'market': game_context.get('market', 'ML') if game_context else 'ML',
                'odds': market_odds_american,
                'stake': float(response['wager_amount']),
                'predicted_prob': float(d_model_prob),
                'fair_market_prob': float(d_implied_prob),
                'edge': float(d_edge),
                'leverage_index': float(d_li),
                'latency_ms': game_context.get('latency_ms', 0.0) if game_context else 0.0,
                'timestamp': datetime.now(timezone.utc)
            }
            self._bet_queue.put(payload)

        return response

    def _calculate_kelly_fraction(self, win_prob: Decimal, decimal_odds: Decimal, leverage_index: Decimal = Decimal("1.0")) -> Decimal:
        """
        Calculates the optimal bet fraction using the Kelly Criterion,
        scaled by the game's Leverage Index.
        Formula: min(max(0.5, li * 0.5 + 0.5), 1.5)
        """
        b = decimal_odds - Decimal("1.0")
        p = win_prob
        q = Decimal("1.0") - p

        if b <= Decimal("0.0"):
            return Decimal("0.0")

        full_kelly = (b * p - q) / b
        
        # Apply Leverage Scaling
        # li * 0.5 + 0.5
        scaled_li = (leverage_index * Decimal("0.5")) + Decimal("0.5")
        # max(0.5, ...)
        floored_li = max(Decimal("0.5"), scaled_li)
        # min(..., 1.5)
        li_multiplier = min(floored_li, Decimal("1.5"))
        
        return max(Decimal("0.0"), full_kelly) * self.kelly_fraction * li_multiplier

    def _american_to_decimal(self, odds: int) -> Decimal:
        if odds > 0:
            return Decimal("1.0") + (Decimal(str(odds)) / Decimal("100.0"))
        else:
            return Decimal("1.0") + (Decimal("100.0") / Decimal(str(abs(odds))))

    def _check_safety_valves(self, context: Optional[Dict]) -> Tuple[bool, str]:
        if not context:
            return True, "Safe"

        score_diff = abs(context.get('score_diff', 0))
        inning = context.get('inning', 1)
        
        if inning >= 7 and score_diff >= 6:
            return False, f"Garbage Time (Inning {inning}, Diff {score_diff})"
            
        li = context.get('leverage_index')
        if li is not None and float(li) < 0.2: 
             return False, f"Low Leverage ({li})"

        if context.get('latency_safe') is False:
            return False, "Latency High (System lagging behind feed)"

        return True, "Safe"

    def _build_response(self, action: str, reason: str, amount: Decimal, 
                        implied_prob: Decimal, edge: Decimal, pct: Decimal = Decimal("0.0")) -> Dict:
        return {
            "action": action,
            "reason": reason,
            "wager_amount": float(round(amount, 2)),
            "wager_percent": float(round(pct, 4)),
            "implied_prob": float(round(implied_prob, 4)),
            "edge": float(round(edge, 4))
        }

    def _bet_logger_worker(self):
        """Background thread to drain the bet queue."""
        while not self._stop_event.is_set():
            try:
                payload = self._bet_queue.get(timeout=1.0)
                self._persist_shadow_bet(payload)
                self._bet_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[TraderAgent] Bet Logger Worker Error: {e}")

    def _persist_shadow_bet(self, payload):
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO shadow_bets 
                (game_id, market, odds, stake, predicted_prob, fair_market_prob, edge, leverage_index, latency_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            if self.db_manager.is_postgres:
                query = query.replace('?', '%s')
                
            cursor.execute(query, (
                payload['game_id'], payload['market'], payload['odds'], payload['stake'],
                payload['predicted_prob'], payload['fair_market_prob'], payload['edge'],
                payload['leverage_index'], payload['latency_ms'], payload['timestamp']
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[TraderAgent] Bet Persistence Error: {e}")

    def stop(self):
        """Graceful shutdown for the worker thread."""
        self._stop_event.set()
        if hasattr(self, '_worker_thread') and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
