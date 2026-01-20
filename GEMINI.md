# Project Progress: MLB Championship Probability Tracker

## Current Status
**Phase 3 Complete (Live Operations Ready)**. The system has evolved from a passive championship simulator into an autonomous **Live Betting Intelligence Platform**. It now features a "Sniper Mode" dashboard that polls real-time MLB data, detects inefficiencies (Fatigue/TTTO), and generates wager recommendations using the Kelly Criterion.

## Key Accomplishments (Jan 20, 2026)
- **Phase 1 (Latency) Complete**: Implemented `LatencyMonitor` with non-blocking queue architecture to track `Feed_Delta`. Added strict 3.0s - 6.0s "Sniper Window" guardrails.
- **Phase 2 (Intelligence) Complete**: Replaced static RE24 tables with a **Vectorized O(1) Markov Engine** (`MarkovChainService`). Verified dynamic probability shifts (+4.05% win prob) under "Meltdown" pitcher conditions.
- **Phase 3 (Execution) Complete**:
    - **Vig Removal**: Implemented Multiplicative method in `BettingAnalyzer` to find "Fair Value".
    - **Leverage-Scaled Staking**: Updated `TraderAgent` to boost bet sizes (up to 2x Kelly) during high-leverage moments (LI > 2.0).
    - **Shadow Infrastructure**: Deployed `shadow_bets` table and `scripts/settle_shadow_bets.py` for closed-loop calibration.
    - **Kill House Verified**: Ran stress test on WS Game 5 (LAD @ NYY). Identified need for defensive error modeling.

## Concerns & Risks (Jan 20, 2026)
- **Financial Precision**: Current implementation uses `FLOAT/REAL` for financial calculations. Must migrate to `DECIMAL` before handling real money to avoid rounding errors.
- **Thread Safety**: Background workers (`LatencyMonitor`, `TraderAgent`) use daemon threads without graceful shutdown hooks. Risk of data loss (dropped logs/bets) on application restart.
- **Defensive Modeling**: The "Kill House" test revealed the Markov Engine is blind to fielding errors, leading to losses during defensive collapses. Future "Phase 4" should incorporate fielding metrics.

## Design Plan Updates
- **Active Trading Logic**: Shifted from pure probability display to "Actionable Signals" (BET/PASS/BLOCK).
- **Synthetic Markets**: Added `MarketSimulator` to allow rigorous backtesting without purchasing expensive historical odds data.
- **Live Polling**: Implemented a polling architecture (5s interval) for the frontend dashboard.

## Completed Milestones
- [x] **Transition Matrix Refinement**: `StateEngine` now fully operational with fatigue modifiers.
- [x] **Bullpen Availability Tracker**: `BullpenHistoryService` tracks "Dead Arm" status.
- [x] **Live EV Dashboard**: "Sniper Mode" UI deployed and verified with Mock Data.
- [x] **Market Price Integration**: `MarketSimulator` provides dynamic odds for comparison.
- [x] **Automated Trader**: `TraderAgent` handles the logic for sizing and execution.

## Immediate Next Steps
1.  **Production Data Feeds**: Monitor the system during the first real MLB games of the 2026 season to validate the `mlb-statsapi` live feed format.
2.  **Persistent Logging**: Move `signal_history` from in-memory list to the PostgreSQL database for long-term tracking.
3.  **Lineup Integration**: Incorporate daily lineup data (Batter vs. Pitcher splits) into the `StateEngine` transition probabilities.
4.  **Trend Visualization**: Add a graph to the frontend showing how `WinProbability` evolved over the course of a specific game.

## Technical Architecture
- **Backend**: Flask + APScheduler (Background Tasks)
- **Live Engine**: `LiveGameService` (Orchestrator) + `StateEngine` (Math) + `TraderAgent` (Logic)
- **Database**: PostgreSQL (Production) / SQLite (Dev Fallback)
- **Simulation**: 
    - **Macro**: `SeasonSimulator` (1000s of iterations for Championship odds).
    - **Micro**: `MonteCarloSimulator` (Vectorized, In-Game probabilities).
- **External APIs**: `mlb-statsapi` (Official Live Feeds).

## Future Considerations
- **Advanced Alpha**: Move from Team-Level averages to Player-Level granularity (e.g., specific Batter wOBA vs. Pitcher Type).
- **Latency Arbitrage**: Implement a specialized service to detect "Frozen Lines" where the bookmaker feed lags behind the TV feed by >10 seconds.
