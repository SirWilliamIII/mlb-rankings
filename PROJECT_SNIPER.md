# Project: "Sniper Calibration" - Implementation Manifesto

**Status:** Phase 3 Complete (Kill House Verified)
**Current Focus:** Data Sufficiency & Production Feeds

---

### **Phase 1: Latency & Feed Synchronization (The "Scope")**
*Objective: Quantify and exploit the time delta between on-field events and sportsbook API updates.*

- [x] **Create `app/services/latency_monitor.py`**
    - **Class:** `LatencyMonitor` (Non-blocking `queue` architecture).
    - **Method:** `log_feed_delta` (Calculates $T_{receipt} - T_{event}$).
    - **Storage:** Asynchronous logging to `feed_latency_metrics`.
- [x] **Update `app/services/live_game_service.py`**
    - **Integration:** Captures `timeStamp` from payload metadata.
    - **Logic:** Gates all betting signals if `feed_delta` > 6.0s (Hard Stop).

### **Phase 2: Micro-State Markov Engine (The "Speed")**
*Objective: Replace slow Monte Carlo simulations with instant lookup tables for pitch-by-pitch probability.*

- [x] **Create `app/services/markov_chain_service.py`**
    - **Structure:** O(1) Lookup for 24 Base/Out States.
    - **Performance:** Vectorized `numpy` inversion for RE24 calculation (< 1ms).
    - **Modifiers:** Dynamic `pitcher_mod` (Fatigue) and `ttto` (Times Through Order) scaling.
- [x] **Refactor `app/services/state_engine.py`**
    - **Action:** Deprecated static RE24 tables in the hot path.
    - **Integration:** `LiveGameService` now calls `markov_service.get_instant_win_prob()` directly.

### **Phase 3: True Price Discovery (The "Edge")**
*Objective: Strip sportsbook vigorish (vig) to reveal their true model inputs.*

- [x] **Update `app/services/betting_analyzer.py`**
    - **Method:** `remove_vig(home_odds, away_odds)` implemented.
    - **Algorithm:** **Multiplicative Method** normalized to 100%.
    - **Logic:** Sniper executes only when `Model_Prob > Fair_Implied_Prob + 2.5%`.

### **Phase 4: High-Leverage Context (The "Filter")**
*Objective: Only trade when volatility is high enough to hide our edge.*

- [x] **Update `app/services/trader_agent.py`** (Leverage Scaling)
    - **Logic:** `Wager_Pct = Base_Kelly * Leverage_Multiplier`.
    - **Scaling:** Linearly scales from 0.5x (Low Leverage) to 1.5x (High Leverage).
- [ ] **Refine `app/services/bullpen_history_service.py`**
    - **Status:** Logic exists, but backtests revealed **Data Sufficiency** issues (event streams lack pitch counts).
    - **Next Step:** Connect to granular pitch-by-pitch data feed to feed the `PitcherMonitor`.

### **Phase 5: Shadow Execution (The "Test")**
*Objective: Dry-run the sniper logic without risking capital.*

- [x] **Update `app/services/trader_agent.py`**
    - **Signal:** Generates Tier-1 Minified JSON (`{"t":..., "o":...}`).
    - **Safety Valves:** "Garbage Time" and "Blowout" blocks implemented.
- [x] **Stress Testing ("Kill House")**
    - **Script:** `scripts/run_shadow_backtest.py` updated with `MarkovChainService`.
    - **Feature:** "Stress Injection" added to simulate fatigue during low-fidelity replays.

---

### **Execution Priority Sequence**

1.  **[COMPLETE] Step 1**: Implement **Phase 1 (Latency)**.
2.  **[COMPLETE] Step 2**: Implement **Phase 3 (True Price)**.
3.  **[COMPLETE] Step 3**: Implement **Phase 2 (Markov)**.
4.  **[IN PROGRESS] Step 4**: Activate **Shadow Mode** on live data.
    - *Blocker:* Need real-time pitch count feed to drive `PitcherMonitor` correctly (Verified via Stress Test failure).

---

### **Architecture Diagram (Current)**

```mermaid
graph TD
    A[Live Feed] -->|Timestamp| B(Latency Monitor)
    A -->|Game State| C{Markov Chain Service}
    D[Pitcher Monitor] -->|Fatigue Mod| C
    C -->|Win Prob| E(Trader Agent)
    F[Market Odds] -->|Vig Removal| E
    B -->|Safe Window?| E
    E -->|Signal| G[Execution / Log]
