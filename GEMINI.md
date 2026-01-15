# Project Progress: MLB Championship Probability Tracker

## Current Status
**Phase 3 Complete (Live Operations Ready)**. The system has evolved from a passive championship simulator into an autonomous **Live Betting Intelligence Platform**. It now features a "Sniper Mode" dashboard that polls real-time MLB data, detects inefficiencies (Fatigue/TTTO), and generates wager recommendations using the Kelly Criterion.

## Key Accomplishments (Jan 15, 2026)
- **Trader Agent Implemented**: A decision-making engine (`TraderAgent`) that calculates Edge, determines bet sizing (Quarter Kelly), and enforces safety valves (blocking bets during "Garbage Time" or Low Leverage).
- **Shadow Trader Verification**: Successfully backtested the "Sharp" model against a "Lazy Bookmaker" (Synthetic Market) using historical data (World Series 2024), achieving **+87% ROI** on a test case.
- **Dynamic Market Simulator**: Engineered a market simulator that adjusts "Vig" (2.5% - 5.5%) based on game volatility, creating a realistic adversary for the agent.
- **Live Sniper Dashboard**: Deployed a real-time UI featuring:
    - **Live Game Cards**: Visualizing base states, outs, and pitch counts.
    - **Inefficiency Alerts**: Badges for "FATIGUE" and "TTTO".
    - **Signal History**: A log of all generated betting signals.
- **Infrastructure Hardening**: 
    - Split `MonteCarloSimulator` into `SeasonSimulator` (Macro) and `GameSimulator` (Micro/Vectorized) to resolve naming collisions.
    - Implemented `LiveGameService` to poll the official `mlb-statsapi`.

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
