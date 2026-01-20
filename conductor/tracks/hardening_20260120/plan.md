# Implementation Plan: Risk Mitigation & Hardening

## Phase 1: Financial Hardening
- [ ] Task: Database Schema Update
    - [ ] Update `DatabaseManager` to use `NUMERIC` for `shadow_bets`.
    - [ ] Migrate/Recreate `shadow_bets` table.
- [ ] Task: Decimal Migration
    - [ ] Refactor `TraderAgent` to use `decimal.Decimal`.
    - [ ] Refactor `BettingAnalyzer` to use `decimal.Decimal`.
    - [ ] Update tests to verify precision.

## Phase 2: Thread Safety
- [ ] Task: Shutdown Logic
    - [ ] Create `app/utils/shutdown_handler.py`.
    - [ ] Implement `stop()` methods in all background services.
- [ ] Task: Integration
    - [ ] Register services with `ShutdownHandler` in `app.py`.

## Phase 3: Defensive Modeling Scaffolding
- [ ] Task: Defense Monitor
    - [ ] Create `app/services/defense_monitor.py` (stub).
- [ ] Task: Markov Integration
    - [ ] Update `MarkovChainService.get_instant_win_prob` signature.
    - [ ] Update `LiveGameService` to pass default defense mod (1.0).
- [ ] Task: Conductor - User Manual Verification 'Phase 3'
