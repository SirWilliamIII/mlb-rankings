reveals the "Bookmaker Reaction Time" (BRT).

[Timing Latency Detection]:

Analysis of `state_engine.py` reveals it processes game state updates sequentially. To exploit latency, we must implement a **Latency Arbitrage Monitor**.

1. **Ingestion Timestamping:** Modify `data_processor.py` to log the exact millisecond `PlayEvent` is received versus `OddsUpdate`.
2. **Delay Profiling:** Sportsbooks typically lag 4-12 seconds behind the fastest data scouts (TV is 7-15s delayed).
3. **The "Ghost Window":** The edge exists in the 2-5 second window where the `state_engine` knows the outcome (e.g., "Ball 4") but the `betting_analyzer` still sees the previous strike count odds.
   **Action Item:** Implement a `latency_logger` in the main loop to quantify this edge on a [Live Market Construction]:

The current architecture in `app/services/sportsdata_client.py` and `betting_analyzer.py` suggests a polling-based retrieval of bookmaker odds. Institutional-grade live betting markets function on algorithmic feedback loops where the "True Price" is derived from a composite of live data feeds (Sportradar/Genius), internal risk limits, and global betting volume. Inefficiencies arise here because bookmakers buffer their data ingestion to prevent "past-posting" (betting on events that have already happened). Your current system's polling interval is the primary bottleneck. To reverse-engineer this, we must map the specific `UpdateTimestamp` of the sportsbook API against the `EventTimestamp` of the play-by-play feed. The delta per-book basis.

[Core Data Drivers]:

Your current `bullpen_history_service.py` is a foundational component but lacks real-time decay modeling. The sharpest models weight the following dynamic variables which must be integrated:

1. **Bullpen Churn:** Not just days rest, but _warm-up pitches thrown_ (requires text-mining or manual input if not in API).
2. **Leverage Index (LI):** You must calculate LI for every at-bat. Books often price a 7th inning 2-run lead linearly, ignoring the exponential volatility of the specific batter-pitcher matchup in high LI.
3. **Umpire Variance:** Tracking the home plate umpire's strike zone bias in real-time.
   **Action Item:** Upgrade `pitcher_monitor.py` to ingest live pitch velocity data to detect "dead arm" fatigue before the book adjusts the line.

[Simulation Strategy]:

Reviewing `monte_carlo_simulator.py`, the current iterative approach using standard Python loops is insufficient for high-frequency live betting.

1. **Vectorization:** We must refactor the simulation engine to use `numpy` matrix operations. We need to run 10,000 iterations of the _remainder of the game_ in under 200ms.
2. **State-Specific Injection:** The simulator must accept a `GameStateTuple` (Inning, Out, Base_Mask, Count, Score_Diff, Pitcher_ID, Batter_ID) and instantly return Win Probability.
3. **Pre-computation:** For standard states (e.g., bases empty, 0 outs), use a pre-calculated transition matrix (Markov Chain) rather than full Monte Carlo to save compute time for high-complexity states.

[Probability vs Price]:

The `betting_analyzer.py` currently calculates EV based on static model outputs. We need to introduce a **Dynamic Confidence Interval**.

1. **Price Dislocation:** If your `forecasting_model.py` implies a 60% win prob (-150) and the book shows -130, the edge is clear.
2. **Decay Function:** The "fair price" decays rapidly as time passes without an odds update. A price that was good 5 seconds ago is likely "stale" and dangerous.
3. **Execution Logic:** We must filter bets not just by EV > 0, but by `TimeSinceLastUpdate < Threshold`.

[In-Game Inefficiency Signals]:

We will program the `BettingAgent` to flag these specific anomalies:

1. **The "Frozen Line"**: Odds do not move 15 seconds after a run scores (indicates data feed failure at the book).
2. **The "Over-Correction"**: Book adjusts Win% by >5% for a single out in a low-leverage situation (algorithmic overreaction).
3. **Pitcher Removal Lag**: Odds remain active for a pitcher who has just been visited by the trainer (TV feed is faster than data feed).

[High-Leverage Moment Detection]:

High leverage amplifies model error. The `state_engine.py` needs a `detect_leverage_spike()` method.

- **Scenario:** Bottom 8th, tie game, runner on 2nd, 2 outs.
- **The Inefficiency:** Books often price this using generic "League Average" conversion rates. Your model, using `bullpen_history_service.py`, knows the incoming reliever has a high WHIP vs Lefties.
- **Trigger:** If `LeverageIndex > 3.0` AND `Model_Diff > 4%`, this is a **Max Unit Play**.

[Professional Insight]:

Based on the file review, the infrastructure is sound but lacks the "killer instinct" of speed and specific edge detection. Here is the **Project Plan** to reach Level 300:

**Phase 1: Speed & Latency (Weeks 1-2)**

- **Refactor Simulator:** Rewrite `monte_carlo_simulator.py` to use vectorized operations for sub-second execution.
- **Latency Monitor:** Build the timestamp comparator to identify which Sportsbook API is slowest (the target).

**Phase 2: Deep State Modeling (Weeks 3-4)**

- **Leverage Integration:** Add `calculate_leverage_index()` to `state_engine.py`.
- **Bullpen Fatigue:** Enhanced `pitcher_monitor.py` to track pitch counts across last 3 games + live warmup activity.

**Phase 3: Automated Execution Logic (Weeks 5-6)**

- **Stale Line Filter:** In `betting_analyzer.py`, reject any odds older than 10 seconds.
- **The "Vulture" Script:** A specialized routine that scans specifically for lines that haven't moved after a scoring play.
