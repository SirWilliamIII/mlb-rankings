# Specification: Phase 3 - Execution & Sniper

## 1. Overview
Transform the intelligence pipeline into a high-frequency execution engine. Implement real-time market price discovery (Vig Removal), volatility-aware staking (Leverage-Scaled Kelly), and a robust audit loop for Shadow Mode operations.

## 2. Functional Requirements
### 2.1 True Price Discovery (`BettingAnalyzer`)
- **Multiplicative Vig Removal:** Normalize sportsbook implied probabilities to a 100% fair market price.
- **Fair Value Calculation:** Derive the "Naked Line" to compare against Markov win probabilities.

### 2.2 Volatility-Aware Staking (`TraderAgent`)
- **Leverage-Scaled Kelly:** Adjust the Kelly fraction (staking size) based on the game's Leverage Index (LI).
- **Hard Latency Gate:** Strictly enforce `LatencyMonitor.is_safe_window()`. If False, return `BLOCK` status immediately.

### 2.3 Shadow Audit & Calibration
- **Black Box Logging:** Implement the `shadow_bets` database table to track wagers, odds, edge, and execution latency.
- **Real-Time Spotter:** Integrate Slack/Discord webhooks for Tier 2 operator alerts.
- **Calibration Loop:** Create `scripts/calibrate_sniper.py` to calculate the Brier Score and calibration curve of the Markov Engine.

## 3. Non-Functional Requirements
- **Execution Budget:** Decision + Logging must complete in < 50ms (Tier 1 Protocol).
- **Persistence:** Ensure `shadow_bets` are logged before any external API calls to prevent data loss on network failure.

## 4. Acceptance Criteria
- [ ] `BettingAnalyzer` correctly strips vig (e.g., -110/-110 becomes 50%/50% exactly).
- [ ] `TraderAgent` blocks bets during high-latency windows or low-leverage "Garbage Time".
- [ ] `shadow_bets` table correctly records every signal with millisecond-precision timestamps.
- [ ] `calibrate_sniper.py` generates a summary report of predicted vs. actual win rates.
