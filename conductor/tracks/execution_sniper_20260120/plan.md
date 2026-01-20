# Implementation Plan: Phase 3 - Execution & Sniper

## Phase 1: Market & Staking Intelligence
- [x] Task: Implement Multiplicative Vig Removal
    - [x] TDD: Write tests for `BettingAnalyzer.remove_vig` with varying market spreads.
    - [x] Implement the normalization logic in `app/services/betting_analyzer.py`.
- [x] Task: Leverage-Scaled Staking Logic
    - [x] Update `TraderAgent` to accept `leverage_index` in the decision context.
    - [x] Implement scaling formula: `wager = Base_Kelly * min(LI, 2.0)`.
- [x] Task: Enforce Hard Latency Gate
    - [x] Refactor `TraderAgent` to strictly check the `latency_safe` flag.
    - [x] Verify that `BLOCK` is returned immediately if the window is closed.

## Phase 2: Shadow Infrastructure & Persistence
- [ ] Task: Shadow Bets Database
    - [ ] Update `DatabaseManager` to create the `shadow_bets` table.
    - [ ] Include fields for `latency_ms`, `predicted_prob`, and `fair_market_prob`.
- [ ] Task: Tier 2 Operator Alerts
    - [ ] Implement a `NotificationService` for Slack/Discord webhooks.
    - [ ] Trigger async alerts from `LiveGameService` upon signal execution.
- [ ] Task: Logging & Performance Audit
    - [ ] Integrate `shadow_bets` persistence into the `TraderAgent` (Non-blocking).
    - [ ] TDD: Verify the signal-to-persistence latency is < 50ms.

## Phase 3: Calibration & Validation
- [ ] Task: Post-Game Settlement
    - [ ] Create `scripts/settle_shadow_bets.py` to update results from completed games.
- [ ] Task: The Calibration Loop
    - [ ] Implement `scripts/calibrate_sniper.py`.
    - [ ] Calculate Brier Score and Expected vs. Observed win rates.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
