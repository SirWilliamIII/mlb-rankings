# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MLB Championship Probability Tracker - a Flask web application that predicts MLB team playoff and World Series probabilities using Monte Carlo simulation, comparing results against betting market odds.

## Commands

```bash
# Install dependencies
uv sync

# Run development server (Flask on port 5000)
./start-dev.sh
# or directly:
uv run python -m app.app

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_app.py::test_standings

# Docker (includes PostgreSQL)
docker compose up
```

## Architecture

### Core Services (`app/services/`)

The application uses a service-based architecture with distinct responsibilities:

- **MonteCarloSimulator** (`monte_carlo_simulator.py`): Orchestrates season simulation (default 1000 iterations). Simulates remaining regular season games, determines playoff qualifiers, and runs full postseason bracket including Wild Card, Division Series, LCS, and World Series.

- **ForecastingModel** (`forecasting_model.py`): Predicts individual game outcomes using the Log5 formula with Pythagorean win % (preferred) or actual win %. Applies +3% home field advantage. Called by both simulator and betting analyzer.

- **DatabaseManager** (`database_manager.py`): Dual-database abstraction supporting both SQLite (local dev) and PostgreSQL (production via `DATABASE_URL` env var). Handles API response caching, simulation results storage, and advanced team/pitcher stats. Uses `?` placeholders that auto-convert to `%s` for PostgreSQL.

- **MlbApi** (`mlb_api.py`): Wrapper around `mlb-statsapi` library for standings and schedule data with built-in caching.

- **SportsDataClient** (`sportsdata_client.py`): Client for SportsData.io API (team stats, player stats, odds). Requires `SPORTSDATA_API_KEY` in `.env`.

- **BettingAnalyzer** (`betting_analyzer.py`): Calculates Expected Value by comparing model probabilities to market odds. Currently uses mock odds for demonstration.

- **SchedulerService** (`scheduler_service.py`): APScheduler-based background task runner. Executes daily cycle at 4 AM: refresh data → run simulation → save results.

- **DataProcessor** (`data_processor.py`): Orchestrates data refresh from multiple APIs. Maps SportsData team keys to MLB IDs.

### Data Flow

1. `SchedulerService` triggers daily at 4 AM (or on-demand via `/simulate` endpoint)
2. `DataProcessor` refreshes standings, schedules, and advanced stats
3. `MonteCarloSimulator` runs N iterations using `ForecastingModel` for each game
4. Results saved via `DatabaseManager` and served via `/api/latest-simulation`

### API Endpoints

- `GET /` - Dashboard (HTML)
- `GET /standings` - Current MLB standings (JSON)
- `GET /simulate?iterations=N` - Run simulation on-demand
- `GET /api/latest-simulation` - Most recent simulation results
- `GET /betting-value` - Analyze upcoming games for betting value

## Environment Variables

Required in `.env`:
- `SPORTSDATA_API_KEY` - For advanced stats and odds
- `DATABASE_URL` - PostgreSQL connection string (optional, falls back to SQLite)
