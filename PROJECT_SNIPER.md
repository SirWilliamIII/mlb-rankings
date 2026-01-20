rget:** `update_live_game_state()`
    -   **Action:** Extract the `Updated` or `Time` field from the SportsDataIO payload.
    -   **Integration:** Call `LatencyMonitor.log_feed_delta` immediately upon payload receipt.
    -   **Constraint:** If `feed_delta` > `THRESHOLD` (e.g., 6s), trigger a `HighUrgency` flag for the `BettingAnalyzer`.

#### **Phase 2: Micro-State Markov Engine (The "Speed")**

*Objective: Replace slow Monte Carlo simulations with instant lookup tables for pitch-by-pitch probability.*

-   **[ ] Create `app/services/markov_chain_service.py`**
    -   **Data Structure:** `TRANSITION_MATRICES` (Dict). Keys = `(Inning, Outs, Runners_Bitmask, Score_Diff)`. Values = `Win_Probability_Home`.
    -   **Method:** `get_instant_win_prob(game_state)### **Project: "Sniper Calibration" - Implementation Plan**

#### **Phase 1: Latency & Feed Synchronization (The "Scope")**

*Objective: Quantify and exploit the time delta between on-field events and sportsbook API updates.*

-   **[ ] Create `app/services/latency_monitor.py`**
    -   **Class:** `LatencyMonitor`
    -   **Method:** `log_feed_delta(event_timestamp: datetime, receipt_timestamp: datetime)`
    -   **Logic:** Calculate the difference in seconds. Maintain a rolling average (last 50 events) to determine the current "Opportunity Window" (e.g., "We are 4.5s ahead of the book").
    -   **Storage:** Log these deltas to a new table `feed_latency_metrics` in `data/mlb_data.db`.
-   **[ ] Update `app/services/live_game_service.py`**
    -   **Ta`
    -   **Logic:** Instead of running 1000 sims, look up the base state. Adjust slightly for current pitcher/batter xFIP matchup.
    -   **Speed Goal:** < 5ms return time.
-   **[ ] Refactor `app/services/state_engine.py`**
    -   **Action:** Integrate `MarkovChainService` as the primary driver for *in-inning* updates.
    -   **Fallback:** Keep `MonteCarloSimulator` (`app/services/monte_carlo_simulator.py`) only for *between-inning* deep dives or pre-game modeling.

#### **Phase 3: True Price Discovery (The "Edge")**

*Objective: Strip sportsbook vigorish (vig) to reveal their true model inputs.*

-   **[ ] Update `app/services/betting_analyzer.py`**
    -   **Method:** `remove_vig(home_odds, away_odds)`
    -   **Algorithm:** Implement the **Multiplicative Method** (standard for 2-way markets) to normalize implied probabilities to 100%.
    -   **New Property:** `fair_implied_prob`.
    -   **Comparison Logic:**
        -   IF `our_markov_prob` > `fair_implied_prob` + `EDGE_THRESHOLD` (e.g., 2.5%):
        -   AND `LatencyMonitor.is_safe_window()` is True:
        -   THEN `signal = "BET_IMMEDIATE"`

#### **Phase 4: High-Leverage Context (The "Filter")**

*Objective: Only trade when volatility is high enough to hide our edge.*

-   **[ ] Update `app/services/state_engine.py`**
    -   **Method:** `calculate_leverage_index(inning, score_diff, runners, outs)`
    -   **Logic:** Implement standard LI formula.
        -   `LI < 0.8`: Mark state as `Low_Variance` (Do not trade, market is efficient).
        -   `LI > 2.0`: Mark state as `High_Variance` (Aggressive trading allowed).
-   **[ ] Update `app/services/bullpen_history_service.py`**
    -   **Method:** `get_bullpen_fatigue_score(team_id)`
    -   **Inputs:** Sum of pitches thrown in last 3 days by top 3 available relievers.
    -   **Output:** `fatigue_factor` (0.0 to 1.0).
    -   **Integration:** Pass `fatigue_factor` to `MarkovChainService` to penalize late-game defensive win probability.

#### **Phase 5: Shadow Execution (The "Test")**

*Objective: Dry-run the sniper logic without risking capital.*

-   **[ ] Update `app/services/trader_agent.py`**
    -   **Config:** Add `TRADING_MODE` environment variable (`LIVE`, `SHADOW`, `BACKTEST`).
    -   **Action:**
        -   If `SHADOW`: Do not send API order. Instead, insert record into `shadow_bets` table with `timestamp`, `odds`, `stake`, `predicted_edge`, `latency_at_execution`.
    -   **Reporting:** Create `scripts/shadow_report.py` to print P&L from the `shadow_bets` table.

------

### **Execution Priority Sequence**

1.  **Step 1**: Implement **Phase 1 (Latency)**. We cannot fight time if we don't measure it.
2.  **Step 2**: Implement **Phase 3 (True Price)**. We need to know the target's real size.
3.  **Step 3**: Implement **Phase 2 (Markov)**. Speed up the calculations to fit inside the latency window.
4.  **Step 4**: Activate **Shadow Mode** on a live game.

**Awaiting your command to execute Step 1.**
