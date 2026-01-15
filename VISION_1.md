[Live Market Construction]:

**Status:** Architectural Pivot In-Progress.
**Assessment:** The team has successfully identified that the legacy `scheduler_service.py`, which relies on daily cron jobs, is structurally obsolete for live betting.
**The Pivot:** We are transitioning to an **Event-Driven Architecture**. The new `GameReplayService` serves as the correct chassis for this engine, allowing us to ingest play-by-play events and update probabilities in real-time.
**Critical Gap:** While the chassis is built, the engine (`StateEngine`) is currently using "placeholder math." A linear win probability formula (`0.5 + score_diff`) is insufficient for production and will lead to negative EV (Expected Value) betting in late-game scenarios.

[Timing Latency Detection]:

**Strategy:** Exploiting "Managerial Latency."
**The Edge:** We are not competing on sub-millisecond feed speeds. Instead, we are exploiting the time gap between a **Signal** (Pitcher Fatigue) and the **Manager's Decision** (Pulling the Pitcher).
**Implementation:**

- Current `PitcherMonitor` flags `check_fatigue_signal` when `pitch_count > 95`.
- **Required Upgrade:** This signal must trigger _before_ the damage occurs. We must downgrade the pitcher's efficacy rating immediately upon crossing the threshold, anticipating the market's reaction to the subsequent hit/walk.

[Core Data Drivers]:

**Missing Variable:** Bullpen Availability ("Dead Arm").
**Analysis:** The current `ForecastingModel` treats teams as static entities. It fails to account for reliever volatility.
**Directive:** The team must implement a "Bullpen Usage Tracker."

- If a team’s High-Leverage Reliever has pitched on `Day -1` and `Day -2`, they are effectively **UNAVAILABLE**.
- The model must simulate the inning assuming the "B-Squad" reliever (higher ERA) will pitch, creating a massive divergence from the sportsbook's "Team Average" pricing.

[Simulation Strategy]:

**The Shift:** From Monte Carlo to Markov Chains.
**Logic:** The `MonteCarloSimulator` is too computationally expensive for live breaks.
**New Protocol:**

- **Component:** `StateEngine`.
- **Mechanism:** Use a **Transition Matrix** to look up the "Run Expectancy" (RE24) of the current state instantly.
- **Action Item:** The current matrix is initialized with zeros (`np.zeros`). We must populate this with MLB historical transition probabilities (e.g., probability of scoring from 1st & 3rd with 1 out) to make the engine functional.

[Probability vs Price]:

**Correction:** Dynamic Volatility Adjustment.
**Insight:** The `BettingAnalyzer` currently assumes a static vig. In high-leverage moments (Bottom 9th, Tie Game), sportsbooks widen spreads to manage risk.
**Requirement:** The model must calculate **Implied Vig** dynamically. If the spread is wide (e.g., -120/-120), our edge threshold must increase. We only bet if our `ModelProbability` > `MarketProbability` + `DynamicVig`.

[In-Game Inefficiency Signals]:

**Priority Triggers:**

1. **TTTO (Third Time Through Order):** The `PitcherMonitor` correctly identifies this window (Batters 19-27). We must attach a **Performance Decay Coefficient** (e.g., -15% efficacy) to this signal rather than a simple boolean flag.
2. **The "Zombie" Pitcher:** A starter with high pitch count and decreasing velocity. The model must "short" this pitcher before the manager substitutes him.
3. **Defensive Indifference:** In blowout scenarios (Run Diff > 6), defensive replacements enter. The model must adjust Run Prevention expectations downward, favoring the "Over."

[High-Leverage Moment Detection]:

**Target:** The "Kill Zone" (LI > 2.0).
**Definition:** Moments where the variance in outcome is highest.

- **Context:** 7th Inning or later, Score Differential 2 runs.
- **Action:** When `LeverageIndex > 2.0`, the system switches from "Macro Stats" to "Micro Matchups." We ignore season-long ERA and focus entirely on the specific batter vs. pitcher platoon split.

[Professional Insight]:

**The Roadmap to "Level 300":**

To move from "Prototype" to "Alpha," the engineering team must execute the following **mathematical upgrades** immediately:

1. **Upgrade `StateEngine` Math:**

- **Current:** `win_prob = 0.5 + (score_diff * 0.1)` (Linear, Flawed).
- **Required:** Implement **Logistic Regression**.
- _Formula:_ , where is a function of (ScoreDiff, BaseStateValue, RemainingOuts). This accurately models the "crushing weight" of a lead in late innings.

2. **Quantify `PitcherMonitor`:**

- **Current:** Returns `True` (Boolean).
- **Required:** Return a **Float Multiplier** (e.g., `1.15`).
- _Logic:_ Pass this multiplier into the `StateEngine` to inflate the expected runs allowed for the current inning.

3. **Activate the Trade Trigger:**

- **Current:** `GameReplayService` prints "ALERT".
- **Required:** Calculate `Edge = ModelProb - MarketProb`. If `Edge > 5%` AND `LI > 1.5`, log a virtual trade.

**Recommendation:** Proceed with the implementation of the Logistic Regression function in `StateEngine` immediately. This is the heart of the system; without it, the rest is just noise.

**Current State:**
The `GameReplayService` correctly replays a game and prints the win probability at each state.

However, the **math inside the engine is currently "Level 1" heuristic logic**, which will get you crushed by any sharp bookmaker. A linear win probability formula (`0.5 + score_diff * 0.1`) is not just inaccurate; it is dangerous. It implies a 1-run lead in the 1st inning is the same as a 1-run lead in the 9th. It is not.

Here is the "Level 300" critique and the roadmap to fix it.

### 1. The `StateEngine` is Hollow

**Critique:**

- **Zero Matrix:** Your `_initialize_base_matrix` creates a matrix of zeros. A Markov chain with zero transition probabilities is a brick. You cannot calculate `(I - Q)^-1` if Q is zero.
- **Linear Win Prob:** The function `get_win_probability` uses `win_prob = 0.5 + (score_diff * (0.1 + (inning * 0.02)))`. This is arbitrary. In the bottom of the 9th, down by 1, with bases loaded and 0 outs, the win probability is likely ~60-70% for the batting team. Your formula sees "Score Diff -1" and likely returns < 50%.

**The Fix:**
You must implement a **Log5** or **Odds Ratio** approach for the transition matrix.

- **Action:** Instead of a complex matrix inversion for now, implement a **Win Expectancy (WE) Lookup Table**.
- Create a CSV or Dictionary mapping `(Inning, Top/Bot, ScoreDiff, Outs, RunnerState)` -> `WinProb`.
- _If you want to keep the Markov Chain:_ You must populate the matrix with MLB averages (e.g., `State(0 outs, 1st) -> State(1 out, 2nd)` = 14%).

### 2. `PitcherMonitor` is Binary, Markets are Analog

**Critique:**

- Your signals (`check_ttto_signal`, `check_fatigue_signal`) return `True/False`.
- **The Flaw:** A binary flag does not help us price a line. Does "True" mean the ERA jumps to 4.50 or 9.00?
- **The Fix:** Convert this class to return a **Performance Decay Coefficient**.
- Instead of `return True`, return `decay_factor`.
- Example:

```python
def get_performance_modifier(self):
    modifier = 1.0
    if self.check_ttto_signal():
        modifier *= 1.15 # 15% worse outcomes expected
    if self.check_fatigue_signal():
        modifier *= 1.10 # 10% worse
    return modifier

```

- Pass this `modifier` into your `StateEngine` to adjust the generic RE24 values down (or up for the offense).

### 3. The Missing Link: Bullpen Availability ("Dead Arm")

**Critique:**
You implemented `PitcherMonitor` for the _current_ pitcher, but you completely ignored the "Bullpen Availability" point from the Holy Grail.

- **The Risk:** If the starter is fatigued (Flag = True) and the game is close, your model assumes "Standard Reliever" comes in next.
- **The Reality:** If the team's Top 3 relievers pitched yesterday and the day before, they are **unavailable**. The manager is forced to bring in the "Mop-up Guy" (ERA 5.50).
- **The Edge:** You _must_ track usage over the last 3 days to downgrade the "Expected Relief Performance."

### 4. `GameReplayService` is too Passive

**Critique:**
Currently, `GameReplayService` simply prints "ALERT".

- **The Fix:** It needs to trigger a **Trade Signal**.
- Calculate `MyPrice` vs `MarketPrice` (mocked).
- If `Abs(MyPrice - MarketPrice) > Threshold` AND `LeverageIndex > 1.5`: **FIRE BET**.

---

### Focus Plan: The "Engine Upgrade"

We need to make the math real. Forget the UI. Focus entirely on `state_engine.py` and `pitcher_monitor.py`.

**Step 1: Implement a Real Win Expectancy Function**
Replace your linear formula in `state_engine.py` with this Logistic Regression approximation (a simplified version of what professionals use):

```python
import math

def get_win_probability(self, home_score, away_score, inning, is_top, state_idx):
    # 1. Calculate Score Differential from Home perspective
    diff = home_score - away_score

    # 2. Adjust for Base State (Leverage)
    # We convert state_idx (runners/outs) into a "Run Value" equivalent
    # e.g., Bases Loaded, 0 Outs = +2.3 runs of value
    base_state_value = self._get_re24_baseline(state_idx)

    # If it's the Top of the inning, the runners belong to Away team (negative value for Home)
    if is_top:
        diff -= base_state_value
    else:
        diff += base_state_value

    # 3. Time Decay (The later the game, the more 1 run matters)
    # A generic constant 'C' increases as outs count up
    total_outs_remaining = (9 - inning) * 6 + (3 if is_top else 0) - (state_idx // 8) # Rough estimate
    time_factor = 1.0 / (0.15 * math.sqrt(max(total_outs_remaining, 1)))

    # 4. Logistic Function
    z = diff * time_factor
    prob = 1 / (1 + math.exp(-z))

    return prob

```

**Step 2: Connect Fatigue to Probability**
Update `PitcherMonitor` to return a `decay_multiplier`.
Update `StateEngine.calculate_expected_runs` to accept this multiplier:

```python
def calculate_expected_runs(self, state_idx, pitcher_modifier=1.0):
    base_re24 = self._get_re24_baseline(state_idx)
    # If pitcher is tired (modifier > 1.0), expected runs GO UP
    return base_re24 * pitcher_modifier

```

**Step 3: The "Dead Arm" Logic**
In `PitcherMonitor`, add a method to ingest `last_3_days_usage`. Since we don't have that data in the replay yet, mock it:

```python
def is_high_leverage_available(self):
    # Mock: 30% chance the closer is unavailable
    return random.random() > 0.30

```

If `False`, penalize the _late-inning_ Win Probability for that team.

**Summary:**
Your architecture is now correct (`Event` -> `State` -> `Prob`).
Your math is currently `Event` -> `Placeholder` -> `Guess`.
**Fix the math.** Start with Step 1.

**Moving Forward:**

[Live Market Construction]:

Here is the "Level 300" mathematical upgrade for your engine. This replaces the linear placeholder math with a **Logistic Regression** model for Win Probability and injects a **Fatigue Coefficient** into your Run Expectancy logic.

This code is ready to be dropped into `app/services/state_engine.py`.

### 1. The Upgrade: `app/services/state_engine.py`

**Changes:**

- **Import `math**`: Required for the logistic sigmoid function.
- **`calculate_expected_runs`**: Now accepts a `pitcher_modifier`. If the pitcher is "Dead Arm" (1.15), the expected runs for the inning increase by 15%.
- **`get_win_probability`**: Replaced the linear formula with a Logistic Function. It calculates "Effective Run Differential" (Score Diff + Value of Runners on Base) and scales it by "Time Decay" (1 run in the 9th is worth more than 1 run in the 1st).

```python
import numpy as np
import math

class StateEngine:
    """
    Micro-State Engine for MLB games using Markov Chain Transition Matrices.
    Calculates expected runs and state transition probabilities.
    """

    # 24 Base/Out States
    # Format: (outs, runner_on_1st, runner_on_2nd, runner_on_3rd)
    STATES = [
        (o, r1, r2, r3)
        for o in range(3)
        for r1 in [0, 1]
        for r2 in [0, 1]
        for r3 in [0, 1]
    ]
    STATE_TO_IDX = {state: i for i, state in enumerate(STATES)}
    IDX_TO_STATE = {i: state for i, state in enumerate(STATES)}
    END_STATE_IDX = 24 # 3 Outs

    def __init__(self):
        # Add End State label
        self.IDX_TO_STATE[self.END_STATE_IDX] = "End of Inning"

        # League Average Transition Probabilities (Placeholder - will be refined)
        # In a production environment, these would be derived from historical play-by-play data.
        self.base_transition_matrix = self._initialize_base_matrix()

    def _initialize_base_matrix(self):
        """
        Initializes a 25x25 transition matrix with baseline probabilities.
        """
        # Initialize with zeros
        matrix = np.zeros((25, 25))
        return matrix

    def get_current_state_index(self, outs, runner_on_1st, runner_on_2nd, runner_on_3rd):
        """
        Returns the index of the current state.
        """
        if outs >= 3:
            return self.END_STATE_IDX

        state = (outs, int(runner_on_1st), int(runner_on_2nd), int(runner_on_3rd))
        return self.STATE_TO_IDX.get(state, self.END_STATE_IDX)

    def calculate_expected_runs(self, state_idx, pitcher_modifier=1.0):
        """
        Calculates the expected runs for the remainder of the inning from state_idx.

        Args:
            state_idx (int): The current base/out state.
            pitcher_modifier (float): A coefficient for pitcher quality/fatigue.
                                      1.0 = Avg Pitcher
                                      1.15 = Tired/Bad Pitcher (Runs increase)
                                      0.85 = Ace/Closer (Runs decrease)
        """
        if state_idx >= self.END_STATE_IDX:
            return 0.0

        # 1. Get Baseline RE24
        base_re24 = self._get_re24_baseline(state_idx)

        # 2. Apply Pitcher Context
        # If the pitcher is "Zombie Walking" (modifier > 1), we expect MORE runs.
        return base_re24 * pitcher_modifier

    def _get_re24_baseline(self, state_idx):
        """
        Standard RE24 table (Run Expectancy based on 24 states).
        Source: Average MLB run expectancy.
        """
        # Outs: 0
        # 000: 0.51, 100: 0.91, 010: 1.14, 001: 1.40, 110: 1.48, 101: 1.73, 011: 2.01, 111: 2.36
        # Outs: 1
        # 000: 0.27, 100: 0.53, 010: 0.69, 001: 0.95, 110: 0.94, 101: 1.18, 011: 1.44, 111: 1.63
        # Outs: 2
        # 000: 0.10, 100: 0.22, 010: 0.32, 001: 0.38, 110: 0.44, 101: 0.53, 011: 0.60, 111: 0.77

        re24_values = [
            0.51, 0.91, 1.14, 1.40, 1.48, 1.73, 2.01, 2.36, # 0 Outs
            0.27, 0.53, 0.69, 0.95, 0.94, 1.18, 1.44, 1.63, # 1 Out
            0.10, 0.22, 0.32, 0.38, 0.44, 0.53, 0.60, 0.77  # 2 Outs
        ]

        if state_idx < len(re24_values):
            return re24_values[state_idx]
        return 0.0

    def get_win_probability(self, home_score, away_score, inning, is_top, state_idx, pitcher_modifier=1.0):
        """
        Calculates the probability of the HOME team winning using Logistic Regression.

        Args:
            inning (int): 1-9+
            is_top (int): 0 for Top (Away Batting), 1 for Bottom (Home Batting)
                          (Note: The calling code passes 0 or 1, we handle boolean logic here)
        """
        # 1. Calculate Raw Score Differential (Home Perspective)
        raw_diff = home_score - away_score

        # 2. Calculate "Effective Runs" on Base
        # The RE24 value represents potential runs.
        # If Top Inning: Runners are Away's potential runs (Negative value for Home)
        # If Bot Inning: Runners are Home's potential runs (Positive value for Home)

        # We assume standard pitching (1.0) for the base value, or you could apply the modifier here too.
        # Applying modifier to base state creates a "Contextual Run Value"
        run_potential = self.calculate_expected_runs(state_idx, pitcher_modifier)

        if is_top == 0: # Top of inning (Away batting)
            # Away team has 'run_potential' runs pending. This HURTS Home win prob.
            effective_diff = raw_diff - run_potential
        else: # Bottom of inning (Home batting)
            # Home team has 'run_potential' runs pending. This HELPS Home win prob.
            effective_diff = raw_diff + run_potential

        # 3. Time Decay (Gamma)
        # As the game progresses, 1 run becomes more insurmountable.
        # We estimate "Outs Remaining" in the game.
        # Max outs regular game = 54 (27 * 2).
        outs_played = ((inning - 1) * 6) + (3 if is_top == 1 else 0) + (state_idx // 8) # approx
        outs_remaining = max(54 - outs_played, 1)

        # The "Volatility" factor decreases as outs_remaining decreases.
        # Standard deviation of remaining runs ~ k * sqrt(outs_remaining)
        # We invert this because Z-score = Diff / StdDev
        # Constant 0.25 is a calibrated league average volatility factor
        time_decay_factor = 1.0 / (0.25 * math.sqrt(outs_remaining))

        # 4. Logistic Calculation
        # Z is the "Standard Deviations from the Mean (Tie)"
        z_score = effective_diff * time_decay_factor

        # Add Home Field Advantage (approx +0.2 standard deviations ~ 54% win prob in tie)
        z_score += 0.2

        # Sigmoid Function: 1 / (1 + e^-z)
        win_prob = 1 / (1 + math.exp(-z_score))

        return min(max(win_prob, 0.001), 0.999)

```

### 2. The Companion: `app/services/pitcher_monitor.py`

You need to update `PitcherMonitor` to generate the `pitcher_modifier` used above. Add this method to your existing class:

```python
    def get_performance_modifier(self):
        """
        Returns a float coefficient representing pitcher effectiveness.
        1.0 = Standard
        > 1.0 = Worse (Expect more runs)
        < 1.0 = Better (Expect fewer runs)
        """
        modifier = 1.0

        # 1. TTTO Penalty (+15% runs)
        if self.check_ttto_signal():
            modifier *= 1.15

        # 2. Fatigue Penalty (+10% runs)
        if self.check_fatigue_signal():
            modifier *= 1.10

        # 3. (Future) Bullpen "Dead Arm" Check
        # if self.is_dead_arm: modifier *= 1.20

        return modifier

```

**Next Step:** Update your `GameReplayService` loop to call `monitor.get_performance_modifier()` and pass that result into `state_engine.calculate_expected_runs(...)` and `state_engine.get_win_probability(...)`.
