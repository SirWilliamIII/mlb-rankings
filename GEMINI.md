# Project Progress: MLB Championship Probability Tracker

## Current Status
**Phase 4 Complete (Shadow Campaign Verified)**. The system has evolved from a passive championship simulator into an autonomous **Live Betting Intelligence Platform**. It now features a "Sniper Mode" dashboard that polls real-time MLB data, detects inefficiencies (Fatigue/TTTO), and generates wager recommendations using the Kelly Criterion.

## Key Accomplishments (Jan 20, 2026)
- **Phase 4 (Shadow Operations) Complete**:
    - **Campaign Runner**: Deployed `scripts/run_shadow_campaign.py` to automate multi-game paper trading.
    - **Bet Settlement**: Implemented automated P&L tracking matched against final game scores.
    - **Outcome**: Executed 37 trades across 5 games (54.1% Win Rate).
- **Phase 3 (Signal Validation) Complete**:
    - **Inefficiency Hunting**: Verified detection of "Bullpen Panic" (SIG-02) with 8.58% Edge.
- **Phase 2 (Intelligence) Complete**: Replaced static RE24 tables with a **Vectorized O(1) Markov Engine** (`MarkovChainService`). Verified dynamic probability shifts (+13.8% win prob) under "Meltdown" pitcher conditions.
- **Phase 1 (Latency) Complete**: Implemented `LatencyMonitor` with non-blocking queue architecture to track `Feed_Delta`. Added strict 3.0s - 6.0s "Sniper Window" guardrails.

## Concerns & Risks (Jan 20, 2026)
- **Financial Calibration**: The Negative ROI (-11.82%) despite a positive Win Rate (54%) indicates that the **Kelly Criterion sizing is too aggressive**.
- **Data Integrity**: Observed minor discrepancies in `statsapi` boxscore data.
- **Execution Speed**: Python `statsapi` polling is the bottleneck. Future shift to AsyncIO or direct WebSocket feed is recommended.

## Design Plan Updates (Completed)
- **Active Trading Logic**: Shifted from pure probability display to "Actionable Signals" (BET/PASS/BLOCK).
- **Synthetic Markets**: Added `MarketSimulator` to allow rigorous backtesting without purchasing expensive historical odds data.
- **Live Polling**: Implemented a polling architecture (5s interval) for the frontend dashboard.

## Completed Milestones
- [x] **Transition Matrix Refinement**: `StateEngine` now fully operational with fatigue modifiers.
- [x] **Bullpen Availability Tracker**: `BullpenHistoryService` tracks "Dead Arm" status.
- [x] **Live EV Dashboard**: "Sniper Mode" UI deployed and verified with Mock Data.
- [x] **Market Price Integration**: `MarketSimulator` provides dynamic odds for comparison.
- [x] **Automated Trader**: `TraderAgent` handles the logic for sizing and execution.
- [x] **Shadow Campaign**: Validated on 2024 World Series (Games 1-5).

## Immediate Next Steps
1.  **Strategy Calibration**: Reduce Kelly Fraction (e.g., `0.25 * Kelly`) to stabilize ROI.
2.  **Live Activation**: Connect `LiveGameService` to real-time `mlb-statsapi` polls for 2026 Season Opener.
3.  **Persistent Logging**: Move `signal_history` from in-memory list to the PostgreSQL database for long-term tracking.

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
