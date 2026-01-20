PROJECT SNIPER: Live-Betting Market Deconstruction & Execution Protocol

1. Mission Doctrine

Objective: Outperform institutional sportsbook pricing algorithms by exploiting latency, model rigidity, and time-decay inefficiencies in MLB live betting markets.
Role: Market Deconstructor & Edge Hunter.
Philosophy: Sportsbook lines are not "true probabilities"; they are risk-management instruments subject to latency and human bias. We do not predict the game; we price the probability faster than the feed updates.

2. System Architecture (The Kill Chain)

A. The Feed (Ingestion)

Component: LiveGameService & SportsDataClient

Function: Ingests real-time play-by-play data.

Edge: We treat the feed as a "delayed echo" of reality.

Status: ACTIVE. Polling at high frequency to minimize our own internal latency.

B. The Chronometer (Latency Detection)

Component: LatencyMonitor

Function: Measures the delta between EventTimestamp (Pitch) and SystemTimestamp (Ingestion).

Sniper Protocol:

Green Zone (<2s): Standard operation.

Yellow Zone (2s-5s): Caution. Verify odds against previous state.

Red Zone (>5s): ATTACK VECTOR. The book is blind. If a material event occurs (Hit/Walk/Out) during a Red Zone window, the odds on screen are "stale" and mathematically incorrect.

C. The Engine (Simulation & Probability)

Component: MarkovChainService & StateEngine

Function:

State Space: Maps the game into 24 distinct states (3 Outs x 8 Base Configurations).

Transition Matrix: Uses historical transition probabilities to project the "Rest of Game" (ROG) run expectancy.

Absorbing States: Calculates the exact probability of reaching a "Win" state from the current node.

Advantage: While books use generalized linear models (GLMs), our Markov Chain solves for the exact ergodic distribution of the game state instantly.

D. The Trigger (Execution)

Component: TraderAgent & BettingAnalyzer

Function:

Fair Price Calculation: Converts Markov Win% into American Odds (removing vig).

Kelly Criterion: Dynamically sizes positions based on the magnitude of the edge.

Signal Detection: Identifies specific inefficiency patterns (e.g., "Overreaction to Solo HR", "Pitcher Fatigue Lag").

3. Operational Phases

Phase 1: Foundation (COMPLETED)

[x] Data Pipeline: Real-time ingestion of MLB game states (Inning, Outs, Count, Score).

[x] State Engine: Robust tracking of game context.

[x] Latency Monitoring: Sub-second tracking of feed delays.

Phase 2: Intelligence (ACTIVE)

[x] Markov Implementation: 24-State transition matrix for run expectancy.

[x] Odds Polling: Shadow logging of sportsbook lines.

[x] Inefficiency Detection: Logic to compare Model_Prob vs Implied_Odds.

[ ] Bullpen Dynamic Adjustment: Adjusting transition matrices based on specific reliever stats (In Progress).

Phase 3: Execution (NEXT)

[ ] Automated Shadow Betting: Paper trading in app.log to verify ROI.

[ ] Sniper UI: Real-time dashboard showing "Stale Line" alerts.

[ ] API Integration: Direct connection to betting API for programmatic execution.

4. Inefficiency Signals (The Playbook)

Signal ID

Name

Description

Trigger

SIG-01

The Lagging Strike

Book fails to adjust odds after a 0-2 count.

Latency > 3s AND Count == 0-2

SIG-02

Bullpen Panic

Market over-adjusts after a pitching change.

PitcherChange AND OddsShift > 15%

SIG-03

The Leadoff Overreaction

Lead-off double swings Win% too heavily.

RunnerFirst=True AND Inning > 7

SIG-04

Zombie Line

Line remains static during a scoring play.

ScoreChange != 0 AND OddsChange == 0

5. Technical Directives

Precision: All probabilities must be calculated to 4 decimal places before rounding for display.

Speed: Total processing time (Ingest -> Sim -> Signal) must be < 200ms.

Safety: TraderAgent must disengage if LatencyMonitor indicates data staleness > 8 seconds (risk of "ghosting").

Authorized by: Commander Sir William III
Role: Lead Market Deconstructor