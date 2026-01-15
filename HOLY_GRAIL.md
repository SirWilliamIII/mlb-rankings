l must price the specific "Current Pitcher vs. Upcoming Pocket of Hitters."
* **Action Item:** Deprecate the `run_daily_cycle` in `scheduler_service.py` for live operations. Implement a `GameLoopService` that initializes a state object `(Inning, Outs, Bases, Count, PitcherID)` and updates it per batter.

[Timing Latency Detection]:

**The "Decision Latency" Edge:**
Since sub-second feed arbitrage is unavailable, we exploit **Managerial & Model Latency**.

* **Inefficiency:** Sportsbook algorithms assume "Rational Coaching" (e.g., the manager will pull a struggling pitcher immediately). In reality, managers hesitate.
* **The Detection Method:**
* Monitor `PitchCount` and `VelocityTrend`.
* If `PitchCount > 95` AND `Velocity < Avg_Velocity - 1.5mph`, the pitch[Live Market Construction]:

**Current Architecture Assessment:**
Your current codebase, specifically `scheduler_service.py`, operates on a "Daily Cycle" triggered at 4:00 AM. This is a **static, macroscopic architecture** designed for season-long futures, not live markets. It treats the market as a snapshot rather than a stream.
**Required Pivot:**
To identify inefficiencies, you must transition from a `BackgroundScheduler` to an **Event-Driven State Engine**.

* **The Construction Logic:** Sportsbooks build live odds using "General State Curves" (e.g., probability of Home Team winning given `Inning=7, ScoreDiff=+1`). They generalize.
* **Your Edge:** You will construct odds based on **Component Specificity**. instead of generic "Home Team," your modeer is "Zombie Walking."
* **The Exploitable Gap:** The sportsbook model often waits for the *result* (a double) to downgrade the pitcher. You downgrade him *before* the pitch.


* **Code Implication:** Your `MlbApi` class fetches static standings. You need to extend this to fetch `live_game_data` (endpoint `/v1.1/game/{gamePk}/feed/live`) to track the active pitcher's current pitch count.

[Core Data Drivers]:

**From Macro-Stats to Micro-States:**
Your `ForecastingModel` relies on `win_percentage` and Pythagorean expectation. These are effectively useless for the bottom of the 8th inning.
**New Inputs Required:**

1. **Bullpen Availability (The "Dead Arm" List):**
* Track reliever usage over the last 3 days. If a High-Leverage Reliever has pitched on Day -1 and Day -2, flag him as **UNAVAILABLE**.
* *Market Error:* If the game is close, the book’s auto-pricing often assumes the Ace Reliever is coming in. When the B-tier reliever warms up instead, the line is mispriced.


2. **Platoon Splits:**
* Your current `get_matchup_probability` looks at Team vs. Team.
* *Correction:* You must calculate `CurrentPitcher (RHP)` vs. `UpcomingBatters (LHH)`. A righty specialist facing 3 lefties is a negative-EV situation for the defense that general stats miss.



[Simulation Strategy]:

**Abandon Monte Carlo for Markov Chains:**
Your `MonteCarloSimulator` runs 2,000 iterations to predict the World Series. This is computationally prohibitive for a 30-second commercial break.
**The "Inning Deconstructor" Strategy:**

* **Method:** Use a **Markov Chain Transition Matrix**.
* **Logic:** You have a matrix of 24 base/out states (0 outs empty, 0 outs 1st, ... 2 outs loaded).
* **Execution:**
1. Get current state (e.g., 1 Out, Runner on 2nd).
2. Apply specific batter/pitcher probabilities (Strikeout %, Walk %, ISO).
3. Calculate expected runs for the *remainder of the inning* instantly.


* **Advantage:** This returns a probability in milliseconds, allowing you to compare your "True Price" against the sportsbook before the commercial break ends.

[Probability vs Price]:

**Dynamic Hold Calculation:**
Your `BettingAnalyzer` currently calculates EV against a static vig approximation (`market_decimal * 0.95`).
**The Real-World Adjustment:**

* **Volatility Expansion:** In high-leverage moments (e.g., bottom 9th, tie game), books widen the spread to protect against volatility. A standard -110/-110 becomes -115/-115.
* **The Signal:** You must calculate the **Implied Vig** of the specific live market.
* If `MarketVig > 6%`, the book is uncertain/scared.
* If your `ModelProbability` differs from `MarketProbability` by > 5% *after* removing this inflated vig, you have a "Sharp Edge."



[In-Game Inefficiency Signals]:

**The "Green Light" Indicators:**
These signals indicate that the sportsbook's generalized model is failing to capture specific game toxicity:

1. **The "Third Time Through" (TTTO) Penalty:**
* **Signal:** Starting pitcher facing the top of the order for the 3rd time (approx. 18-21 batters faced).
* **Inefficiency:** Books depreciate pitcher skill linearly. Reality is often a "cliff." If the pitcher is average, his wOBA allowed spikes by ~.050 here. Bet the **Over** on the inning or the **Batting Team ML**.


2. **The "Blowout" Defense:**
* **Signal:** Run differential > 6 in the 7th+ inning.
* **Inefficiency:** Defensive substitutions (backups) enter. Books model run prevention based on the starter's stats, ignoring the massive defensive downgrade.


3. **Bullpen Mismatch:**
* **Signal:** High-leverage moment (LI > 2.0) + "Tired Bullpen" flag.
* **Inefficiency:** The market assumes "Average Defensive Performance." You know the "Stopper" is unavailable.



[High-Leverage Moment Detection]:

**Sniper Mode Activation:**
Do not bet on every inning. Bet when the **Leverage Index (LI)** dictates that the market is fragile.

* **Formula:** .
* **The "Kill Zone" (LI > 2.0):**
* **Late Innings (7th+):** Score within 2 runs.
* **Base State:** Runners in scoring position.
* **Action:** When LI > 2.0, your system switches priority. It ignores "Season Long Stats" and weights "Current At-Bat Matchups" at 100%.
* *Why:* This is where emotional hedging from the public distorts the line, creating value for the cold, calculated model.



[Professional Insight]:

**Executive Summary for Approval:**
The current application is a high-quality "Season Simulator" suitable for long-term fantasy projections, but it is structurally incapable of beating live betting markets. The proposed pivot does not require faster data feeds (which are expensive); it requires **deeper state analysis**.
By moving from `ForecastingModel` (Macroscopic) to a **State-Transition Engine** (Microscopic), we stop trying to predict the final score and start predicting the next probability shift. The edge lies not in speed, but in recognizing **roster constraints** (fatigue, availability, platoon disadvantages) that sportsbook algorithms generalize away. We are trading *specificity* against their *generality*.
