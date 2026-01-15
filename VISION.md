# Vision: MLB Championship Probability Tracker

## Project Goal
To develop a web application that provides dynamic, data-driven predictions for Major League Baseball team playoff and World Series probabilities throughout the season, complemented by a comparison against bookmaker odds.

## Core Features

### 1. Data Aggregation & Management
*   **MLB Statistics**: Utilizes `MLB-StatsAPI` to fetch real-time and historical data including:
    *   Current team standings (wins, losses, division, league).
    *   Upcoming and completed game schedules.
*   **Betting Odds**: Integrates with `The Odds API` to retrieve:
    *   Futures odds for World Series and League championships.
    *   Moneyline odds for individual upcoming games.
*   **Local Caching**: Implement a caching mechanism (e.g., SQLite, similar to the F1 project) to minimize API calls, store historical data, and improve performance.

### 2. Monte Carlo Simulation Engine
*   **Season Simulation**: Simulates the remainder of the MLB season thousands of times (e.g., 10,000+ iterations).
*   **Win Probability Model**: Employs a configurable model to determine game outcomes:
    *   **Initial Model**: Based on current team win/loss percentages.
    *   **Future Enhancements**: Potential to incorporate run differential, home-field advantage, starting pitchers, recent performance, etc.
*   **Outcome Tracking**: For each simulation, records playoff qualifiers, division winners, league champions, and the World Series winner.
*   **Probability Calculation**: Aggregates simulation results to calculate the probability of each team:
    *   Winning their division.
    *   Securing a playoff spot.
    *   Winning their league pennant.
    *   Winning the World Series.

### 3. Interactive Web Interface
*   **Dashboard**: A clean and intuitive Flask-based web application serving as the primary user interface.
*   **Visualization**: Utilizes Plotly for interactive charts and graphs displaying:
    *   Team-specific playoff and championship probabilities.
    *   Trends over time (if historical data is incorporated).
*   **Bookmaker Comparison**: Displays the application's calculated probabilities alongside implied probabilities derived from betting odds, highlighting discrepancies.
*   **Real-time Updates**: Frontend polls for updated data and simulation results periodically (e.g., every few hours, or after game completions).

## Technology Stack
*   **Backend**: Python 3.13+, Flask
*   **Data Acquisition**: `MLB-StatsAPI`, `requests`
*   **Data Processing & Simulation**: `pandas`, `numpy`, `scipy`
*   **Database/Caching**: SQLite (or similar, for local cache)
*   **Background Tasks**: APScheduler (for periodic data updates and simulation runs)
*   **Frontend**: HTML, CSS, JavaScript, Plotly.js

## High-Level Roadmap

### Phase 1: Data Foundation & Basic Application
*   Project setup and environment configuration.
*   Implement `MLB-StatsAPI` integration for standings and schedule.
*   Implement `The Odds API` integration for initial odds fetching.
*   Develop a basic Flask web server displaying raw data (standings).

### Phase 2: Monte Carlo Simulation Engine Development
*   Design and implement the core simulation logic.
*   Define and integrate the initial game win probability model.
*   Run and validate basic simulation results.

### Phase 3: Visualization, Comparison & Polish
*   Integrate simulation results into the Flask application API.
*   Develop Plotly visualizations for all key probabilities.
*   Implement betting odds conversion to implied probabilities and comparative display.
*   Refine frontend UI/UX, add styling and responsiveness.

## Future Enhancements
*   More advanced statistical models for game outcome prediction (e.g., incorporating individual player stats, sabermetrics).
*   Historical season simulation and backtesting.
*   User-specific configurations or "what-if" scenarios.
*   Integration of news/injury data.
*   Deployment to a cloud platform.
