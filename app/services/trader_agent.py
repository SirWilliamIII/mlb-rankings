from typing import Dict, Optional, Tuple
import json
import time
import uuid

class TraderAgent:
    """
    Automated Trading Agent for MLB Live Betting.
    Responsible for executing the 'Active Trading' logic:
    1. Kelly Criterion Sizing
    2. Divergence/Edge Detection
    3. Safety Valve Checks (Garbage Time, etc.)
    """

    def __init__(self, bankroll: float = 10000.0, kelly_fraction: float = 0.25, 
                 min_edge: float = 0.02, max_wager_limit: float = 0.05):
        """
        Args:
            bankroll: Total capital available.
            kelly_fraction: Fraction of Full Kelly to wager (e.g., 0.25 = Quarter Kelly).
            min_edge: Minimum positive EV required to trigger a bet (e.g., 0.02 = 2%).
            max_wager_limit: Hard cap on wager size as % of bankroll (e.g., 0.05 = 5%).
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.min_edge = min_edge
        self.max_wager_limit = max_wager_limit

    def generate_tier1_signal(self, data: Dict) -> str:
        """
        Generates a Tier 1 Execution Signal (Minified JSON).
        Latency Budget: < 50ms.
        
        Args:
            data (Dict): Contains 'game_id', 'market', 'odds', 'prob', 'stake'.
            
        Returns:
            str: Minified JSON string.
        """
        signal = {
            "t": str(time.time()),
            "g": data.get("game_id"),
            "m": data.get("market"),
            "o": data.get("odds"),
            "p": data.get("prob"),
            "s": data.get("stake"),
            "id": str(uuid.uuid4())
        }
        # dumps with separators=(',', ':') removes whitespace
        return json.dumps(signal, separators=(',', ':'))

    def evaluate_trade(self, model_prob: float, market_odds_american: int, 
                       game_context: Optional[Dict] = None) -> Dict:
        """
        Evaluates a potential trade and returns a decision.

        Args:
            model_prob: The 'True' Win Probability from our StateEngine (0.0 - 1.0).
            market_odds_american: American odds from the sportsbook (e.g., -110, 150).
            game_context: Optional dict containing 'inning', 'score_diff', 'leverage_index'.

        Returns:
            Dict: {
                "action": "BET" | "PASS" | "BLOCK",
                "reason": str,
                "wager_amount": float,
                "wager_percent": float,
                "implied_prob": float,
                "edge": float
            }
        """
        # 1. Convert Market Odds to Implied Probability & Decimal
        decimal_odds = self._american_to_decimal(market_odds_american)
        implied_prob = 1.0 / decimal_odds

        # 2. Calculate Edge (EV)
        # Edge = Model_Prob - Implied_Prob (Simplified) or pure EV calculation
        # EV = (Model_Prob * Decimal_Odds) - 1
        ev = (model_prob * decimal_odds) - 1.0
        edge = model_prob - implied_prob

        # 3. Check Safety Valves (Block bad contexts)
        is_safe, safety_reason = self._check_safety_valves(game_context)
        if not is_safe:
            return self._build_response("BLOCK", safety_reason, 0.0, implied_prob, edge)

        # 4. Check Value Threshold
        if ev < self.min_edge:
            reason = f"No Edge (EV: {ev:.2%}, Min: {self.min_edge:.2%})"
            return self._build_response("PASS", reason, 0.0, implied_prob, edge)

        # 5. Calculate Position Size (Kelly Criterion)
        wager_pct = self._calculate_kelly_fraction(model_prob, decimal_odds)
        
        # Apply limits
        wager_pct = min(wager_pct, self.max_wager_limit)
        wager_amount = self.bankroll * wager_pct

        if wager_amount <= 0:
             return self._build_response("PASS", "Kelly suggested <= 0", 0.0, implied_prob, edge)

        return self._build_response("BET", f"Value detected (EV: {ev:.2%})", 
                                    wager_amount, implied_prob, edge, wager_pct)

    def _calculate_kelly_fraction(self, win_prob: float, decimal_odds: float) -> float:
        """
        Calculates the optimal bet fraction using the Kelly Criterion.
        f* = (bp - q) / b
        where:
            b = net odds received on the wager (decimal_odds - 1)
            p = probability of winning
            q = probability of losing (1 - p)
        """
        b = decimal_odds - 1.0
        p = win_prob
        q = 1.0 - p

        if b <= 0:
            return 0.0

        full_kelly = (b * p - q) / b
        return max(0.0, full_kelly) * self.kelly_fraction

    def _check_safety_valves(self, context: Optional[Dict]) -> Tuple[bool, str]:
        """
        Checks for conditions where we should NOT bet regardless of edge.
        e.g., Low Leverage (Garbage Time), Extreme Blowouts.
        """
        if not context:
            return True, "Safe"

        # Check Blowout (Score Diff > 6 in late innings)
        score_diff = abs(context.get('score_diff', 0))
        inning = context.get('inning', 1)
        
        if inning >= 7 and score_diff >= 6:
            return False, f"Garbage Time (Inning {inning}, Diff {score_diff})"
            
        # Check Leverage Index (if available) - Don't bet on 0.0 leverage (dead game)
        # Assuming LI scale: 1.0 is avg. < 0.5 is very low.
        li = context.get('leverage_index')
        if li is not None and li < 0.2:
             return False, f"Low Leverage ({li})"

        # NEW: Latency Safety Check (Phase 1)
        if context.get('latency_safe') is False:
            return False, "Latency High (System lagging behind feed)"

        return True, "Safe"

    def _american_to_decimal(self, odds: int) -> float:
        if odds > 0:
            return 1.0 + (odds / 100.0)
        else:
            return 1.0 + (100.0 / abs(odds))

    def _build_response(self, action: str, reason: str, amount: float, 
                        implied_prob: float, edge: float, pct: float = 0.0) -> Dict:
        return {
            "action": action,
            "reason": reason,
            "wager_amount": round(amount, 2),
            "wager_percent": round(pct, 4),
            "implied_prob": round(implied_prob, 4),
            "edge": round(edge, 4)
        }
