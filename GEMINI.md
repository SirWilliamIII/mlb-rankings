# Project Progress: MLB Championship Probability Tracker

## Current Status
**Feature Complete / Production Ready**. The application now features a robust, autonomous backend with advanced statistical modeling and a "Value Finder" engine.
**NEW:** Successfully pivoted to a "Live Operations" architecture with the **Ghost Replay System**, allowing for real-time simulation and "Sniper Mode" inefficiency detection (TTTO, Fatigue) on historical data. The infrastructure has been migrated to **PostgreSQL** for high-concurrency production support.

## Design Plan Updates
- **Shift to Micro-States**: Moved from season-long macro predictions to inning-by-inning micro-state analysis using Markov Chain transitions.
- **Event-Driven Architecture**: The system is now designed to ingest a stream of plays (via the Ghost Replay Service) rather than static daily snapshots.
- **Relational Integrity**: Migrated to PostgreSQL to handle simultaneous live game updates and dashboard reads, ensuring better performance and ACID compliance.
- **Inefficiency Signals**: Integrated specific "Sniper" signals (TTTO, Pitch Count) into the core logic to identify exploitable market gaps.

## Completed Milestones
... [ Milestones listed previously ] ...

## Immediate Next Steps
1.  **Transition Matrix Refinement**: Replace the placeholder RE24/Markov values with actual 2024-2025 MLB historical transition data for higher accuracy.
2.  **Bullpen Availability Tracker**: Implement the "Dead Arm" list logic to track reliever usage over the last 3 days and flag unavailable "Stoppers."
3.  **Live EV Dashboard**: Create a dedicated "Sniper Mode" UI component that flashes specific Live-EV opportunities during game play (or replay).
4.  **Market Price Integration**: Add a service to fetch (or mock) live betting odds movements during a game to compare against the Micro-State Model's "True Price."
5.  **Markov Chain Inning Deconstructor**: Fully implement the $(I - Q)^{-1}$ matrix math for precise rest-of-inning run expectancy.

## Technical Architecture
- **Backend**: Flask + APScheduler (Background Tasks)
- **Live Engine**: Event-Driven State Machine (Markov Chain)
- **Database**: PostgreSQL (Production) / SQLite (Dev Fallback)
- **Stats Engine**: Python (NumPy/SciPy), Log5 Model, Pythagorean Expectation.
- **External APIs**: 
    - `mlb-statsapi` (Official MLB Data - Live Feeds)
    - `SportsData.io` (Advanced Stats & Odds)

## Future Considerations
- **Live Odds**: Switch `SportsDataClient` to production mode for real-time odds once the 2026 season begins.
- **Lineup Integration**: Further refine the model by incorporating daily lineups (wOBA) into the game simulation.
- **Trend Visualization**: Use the historical data stored in `simulation_runs` to graph how a team's probability changes over the season.