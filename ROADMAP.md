# FUTURE_ROADMAP.md

## 1. Executive Summary: The "Level 300" Pivot

The project has evolved beyond a "Season Simulator" (Level 1) into a **Live Betting Inefficiency Engine** (Level 300). The core mission is no longer predicting who _will_ win the World Series, but identifying **mispriced micro-moments** in real-time games where sportsbook algorithms fail to account for specific constraints (Fatigue, "Dead Arm", Platoon Splits).

**North Star:** Build an autonomous agent capable of detecting "Decision Latency"—the gap between a pitcher's performance degradation and the manager's decision to remove them—and executing virtual trades before the market corrects.

---

## 2. Phase 1: Mathematical Hardening (The Engine Room)

### Current Status: In Progress

The chassis (Event-Driven Architecture) is built. The focus is now on replacing placeholder constants with sharp, historical math.

### A. Transition Matrix Refinement

- **Objective:** Replace the generic `RE24` placeholders with a precise **Markov Chain Transition Matrix**.
- **Action:**
- Ingest 2024-2025 MLB play-by-play data to populate the 24-state matrix.
- Implement the matrix inversion to calculate "True" Run Expectancy instantly for any state.
- **Goal:** Move from "Average Runs" to "Exact Expectancy" based on the current run environment.

### B. The "Dead Arm" Logic (Bullpen History Service)

- **Objective:** Quantify the "Unavailable" reliever edge.
- **Action:**
- Implement the `BullpenHistoryService` to track trailing 3-day pitch counts for all active relievers.
- **Logic:**
- **Dead:** Pitched consecutive days Modifier `1.25x` (25% degradation).
- **Tired:** >25 pitches yesterday Modifier `1.15x`.
- **Overworked:** Pitching Game 2 of a doubleheader Modifier `1.50x`.

### C. Logistic Regression Tuning

- **Objective:** Calibrate the new `StateEngine` win probability formula.
- **Action:**
- Validate the `VOLATILITY_SCALE` (currently derived as ~1.17) against historical blowout data.
- Refine the "Time Decay" factor to ensure the model doesn't become overconfident (99%+) too early in non-blowout games.

---

## 3. Phase 2: Automation & Execution (The Trader)

### Current Status: Design Phase

Moving from "Passive Analysis" (printing probabilities) to "Active Trading" (generating signals).

### A. The `TraderAgent` Service

- **Objective:** Automate the decision-making process.
- **Components:**
- **Kelly Criterion Sizing:** Dynamic bet sizing based on Edge % and Bankroll.
- **Divergence Logic:** Trigger trade ONLY if `Abs(Model_Price - Market_Price) > Threshold`.
- **Safety Valves:** Hard blocks on betting during "Garbage Time" (Low Leverage Index) or extreme blowouts.

### B. "Shadow Trader" Backtesting

- **Objective:** Prove the edge without risking capital.
- **Action:**
- Use `GameReplayService` to simulate the "Lazy Bookmaker" (Standard RE24 without Fatigue modifiers).
- Pit the "Sharp Model" (With Fatigue modifiers) against the "Lazy Model."
- **KPI:** Verify that the Sharp Model generates positive ROI specifically in the moments the Lazy Model ignores (e.g., "Zombie" Pitcher scenarios).

### C. Dynamic Vig Calculation

- **Objective:** Account for live market volatility.
- **Action:**
- Stop using static vig (e.g., -110).
- Calculate **Implied Vig** dynamically based on spread width.
- **Rule:** If Market Vig > 6% (High Uncertainty), increase the required Edge threshold before betting.

---

## 4. Phase 3: Live Operations (The Sniper)

### Current Status: Planned

Deploying the engine to handle real-time MLB feeds during the season.

### A. Live "Sniper Mode" Dashboard

- **Objective:** Visual interface for the "Kill Zone."
- **Features:**
- **Flash Alerts:** Visual indicators when `Leverage Index (LI) > 2.0`.
- **Fatigue Watch:** Sidebar tracking the current pitcher's pitch count and velocity decay trend.
- **Inefficiency Signals:** Real-time flags for TTTO (Third Time Through Order) penalties.

### B. Production Data Feeds

- **Objective:** Replace dev/mock data with live inputs.
- **Action:**
- Upgrade `SportsDataClient` to production tier for real-time Odds API access.
- Connect `mlb-statsapi` to the live game stream endpoint (`/v1.1/game/{gamePk}/feed/live`).
- Ensure PostgreSQL can handle concurrent writes (Live Feed) and reads (Dashboard) without locking.

---

## 5. Phase 4: Advanced Alpha (Long Term)

### Current Status: Conceptual

### A. Micro-Matchup Integration (Platoon Splits)

- **Current State:** Uses team-level averages.
- **Future State:** Calculate Win Probability based on the _specific_ batter vs. pitcher matchup (e.g., "Righty Specialist vs. Pocket of 3 Lefties").
- **Impact:** Exploits the "Lineup Churn" delay where books fail to price in a pinch-hitter immediately.

### B. Trend Visualization

- **Objective:** Visualizing the "Story of the Game."
- **Action:**
- Graph `WinProbability` over time using Plotly.
- Overlay "Trade Entry Points" on the graph to visualize where the model found value vs. the market line.

---

## Technical Debt & Infrastructure

- **Database:** Maintain PostgreSQL for production ACID compliance; deprecate SQLite for everything but local unit tests.
- **Latency:** Optimize `GameLoopService` to process a play event and update probabilities in < 200ms.
- **Testing:** Expand unit tests to cover 100% of "Edge Case" scenarios (e.g., Ghost Runner in extra innings, rained-out games, doubleheaders).
