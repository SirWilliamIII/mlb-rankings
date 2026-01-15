# Project Progress: MLB Championship Probability Tracker

## Current Status
**Feature Complete / Production Ready**. The application now features a robust, autonomous backend with advanced statistical modeling and a "Value Finder" engine that identifies profitable betting opportunities against market odds.

## Completed Milestones

### Phase 1: Data Foundation (Enhanced)
- [x] **Project Setup**: Initialized with `uv` for dependency management.
- [x] **MLB API Integration**: Implemented `MlbApi` service using `mlb-statsapi`.
- [x] **SportsData.io Integration**: Implemented `SportsDataClient` to fetch granular data:
    - Team Season Stats (Runs Scored/Allowed) for Pythagorean Expectation.
    - Player Season Stats (Pitching metrics) for FIP calculations.
    - Betting Odds (or mocked equivalents for development).
- [x] **Database Layer**: Implemented `DatabaseManager` using SQLite to support:
    - **Caching**: API responses (Schedule, Standings) to minimize external calls.
    - **History**: Storage of every simulation run for trend tracking.
    - **Advanced Stats**: Tables for `team_stats_advanced` (Pythagorean) and `pitcher_stats` (FIP).

### Phase 2: Monte Carlo Simulation Engine (Upgraded)
- [x] **Full Postseason Logic**: `MonteCarloSimulator` now simulates the exact MLB bracket structure:
    - Seeding (1-6 per league).
    - Wild Card Series (Best of 3).
    - Division Series (Best of 5).
    - Championship Series (Best of 7).
    - World Series (Best of 7).
- [x] **Advanced Forecasting Model**: Replaced naive Win % model with a **Log5 Probability Model**:
    - **Base Strength**: Uses Pythagorean Expectation (`Runs^1.83 / (Runs^1.83 + RunsAllowed^1.83)`).
    - **Pitcher Adjustment**: Adjusts win probability based on Starting Pitcher FIP (Fielding Independent Pitching).
    - **Home Field Advantage**: +3% baseline adjustment.

### Phase 3: "Value Finder" & Automation
- [x] **Betting Analyzer**: Implemented `BettingAnalyzer` service to:
    - Compare "True Probability" (Model) vs. "Implied Probability" (Market Odds).
    - Calculate **Expected Value (EV)** to highlight profitable edges.
- [x] **Autonomous Backend**: Implemented `SchedulerService` using `APScheduler`:
    - **Daily Refresh**: Automatically fetches fresh stats and odds at 4:00 AM.
    - **Daily Simulation**: Runs 2,000+ iterations nightly and caches results.
- [x] **API Endpoints**:
    - `/api/latest-simulation`: High-performance read of the nightly run.
    - `/betting-value`: Returns sorted list of high-EV betting opportunities.

### Phase 4: Visualization & UI
- [x] **Interactive Dashboard**: Complete overhaul of `index.html` using Bootstrap 5.
- [x] **Value Bets Table**: Displays top "Edge" opportunities with EV calculation.
- [x] **Dynamic Charts**: Plotly.js charts for World Series and Playoff probabilities, powered by cached simulation data.

## Technical Architecture
- **Backend**: Flask + APScheduler (Background Tasks)
- **Database**: SQLite (Local Cache & History)
- **Stats Engine**: Python (NumPy/SciPy), Log5 Model, Pythagorean Expectation.
- **External APIs**: 
    - `mlb-statsapi` (Official MLB Data)
    - `SportsData.io` (Advanced Stats & Odds)

## Future Considerations
- **Live Odds**: Switch `SportsDataClient` to production mode for real-time odds once the 2026 season begins.
- **Lineup Integration**: Further refine the model by incorporating daily lineups (wOBA) into the game simulation.
- **Trend Visualization**: Use the historical data stored in `simulation_runs` to graph how a team's probability changes over the season.