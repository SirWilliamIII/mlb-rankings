# Project Progress: MLB Championship Probability Tracker

## Current Status
Initial application structure, data integration, and simulation engine are operational.

## Completed Milestones

### Phase 1: Data Foundation
- [x] **Project Setup**: Initialized with `uv` for dependency management.
- [x] **MLB API Integration**: Implemented `MlbApi` service using `mlb-statsapi`.
    - Handles standings and schedule fetching.
    - Includes offseason fallback logic (defaults to 2025 data when 2026 isn't yet active).
- [x] **Basic Web Server**: Flask application serving as the backbone.

### Phase 2: Monte Carlo Simulation Engine
- [x] **Simulation Orchestrator**: `MonteCarloSimulator` simulates remaining regular season games and basic playoff outcomes.
- [x] **Forecasting Model**: Stochastic prediction based on win percentages with home-field advantage adjustment.
- [x] **Result Aggregation**: Calculates probabilities for Division Wins, Playoff Berths, League Pennants, and World Series titles.

### Phase 3: Visualization & Polish (Partial)
- [x] **Interactive Dashboard**: Flask-based UI serving a Plotly-powered frontend.
- [x] **Probability Charts**: Dynamic bar charts for World Series and Playoff probabilities.

## Remaining Work

### Data & Performance
- [ ] **SQLite Caching**: Implement local storage to reduce API calls and store historical simulation results.
- [ ] **Background Tasks**: Integrate `APScheduler` to automate data refreshes and simulation runs.

### Features
- [ ] **Betting Odds Integration**: Fetch data from `The Odds API` to calculate implied probabilities.
- [ ] **Comparison Logic**: Compare model probabilities vs. market odds to identify "value" bets.
- [ ] **Trend Tracking**: Store historical probabilities to visualize changes over the course of the season.

### Refinement
- [ ] Enhanced statistical models (e.g., Elo ratings, pitcher-specific data).
- [ ] Improved playoff tie-breaking logic.
- [ ] Mobile-responsive UI polish.
