# Project Progress: MLB Championship Probability Tracker

## Current Status
**Feature Complete / Production Ready**. The application now features a robust, autonomous backend with advanced statistical modeling and a "Value Finder" engine.
**NEW:** Successfully pivoted to a "Live Operations" architecture with the **Ghost Replay System**, allowing for real-time simulation and "Sniper Mode" inefficiency detection (TTTO, Fatigue) on historical data.

## Completed Milestones

### Phase 1: Data Foundation (Enhanced)
- [x] **Project Setup**: Initialized with `uv` for dependency management.
- [x] **MLB API Integration**: Implemented `MlbApi` service using `mlb-statsapi`.
- [x] **SportsData.io Integration**: Implemented `SportsDataClient` to fetch granular data.
- [x] **Database Layer**: Implemented `DatabaseManager` using SQLite.

### Phase 2: Monte Carlo Simulation Engine (Upgraded)
- [x] **Full Postseason Logic**: `MonteCarloSimulator` simulates exact MLB bracket structure.
- [x] **Advanced Forecasting Model**: Log5 Model with Pitcher FIP adjustments.

### Phase 3: "Value Finder" & Automation
- [x] **Betting Analyzer**: Compare Model Prob vs. Market Odds for EV.
- [x] **Autonomous Backend**: `SchedulerService` for nightly runs.
- [x] **API Endpoints**: High-performance read endpoints.

### Phase 4: Visualization & UI
- [x] **Interactive Dashboard**: Bootstrap 5 UI.
- [x] **Value Bets Table**: Displays top "Edge" opportunities.
- [x] **Dynamic Charts**: Plotly.js charts.

### Phase 5: Live Operations & Sniper Mode (New)
- [x] **Micro-State Engine**: Implemented `StateEngine` using a simplified RE24/Markov model for real-time win probability.
- [x] **Ghost Replay System**: Created `GameReplayService` to feed historical play-by-play data into the engine, simulating live game conditions.
- [x] **Inefficiency Detection**: Implemented `PitcherMonitor` to detect "Third Time Through Order" (TTTO) penalties and Pitch Count Fatigue (>95 pitches).
- [x] **Verification**: Validated using `verify_live_feed.py` with 2025 World Series game data.

## Technical Architecture
- **Backend**: Flask + APScheduler (Background Tasks)
- **Live Engine**: Event-Driven State Machine (Markov Chain)
- **Database**: SQLite (Local Cache & History)
- **Stats Engine**: Python (NumPy/SciPy), Log5 Model, Pythagorean Expectation.
- **External APIs**: 
    - `mlb-statsapi` (Official MLB Data - Live Feeds)
    - `SportsData.io` (Advanced Stats & Odds)

## Future Considerations
- **Live Odds**: Switch `SportsDataClient` to production mode for real-time odds once the 2026 season begins.
- **Lineup Integration**: Further refine the model by incorporating daily lineups (wOBA) into the game simulation.
- **Trend Visualization**: Use the historical data stored in `simulation_runs` to graph how a team's probability changes over the season.