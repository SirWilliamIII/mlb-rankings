# Implementation Plan: Risk Mitigation & Hardening

## Phase 1: Financial Hardening
- [x] Task: Database Schema Update
    - [x] Update `DatabaseManager` to use `NUMERIC` for `shadow_bets`.
    - [x] Migrate/Recreate `shadow_bets` table.
- [x] Task: Decimal Migration
    - [x] Refactor `TraderAgent` to use `decimal.Decimal`.
    - [x] Refactor `BettingAnalyzer` to use `decimal.Decimal`.
    - [x] Update tests to verify precision.

## Phase 2: Thread Safety
- [x] Task: Shutdown Logic
    - [x] Create `app/utils/shutdown_handler.py`.
    - [x] Implement `stop()` methods in all background services.
- [x] Task: Integration
    - [x] Register services with `ShutdownHandler` in `app.py`.

## Phase 3: Defensive Modeling Scaffolding
- [ ] Task: Defense Monitor
    - [ ] Create `app/services/defense_monitor.py` (stub).
- [ ] Task: Markov Integration
    - [ ] Update `MarkovChainService.get_instant_win_prob` signature.
    - [ ] Update `LiveGameService` to pass default defense mod (1.0).
- [ ] Task: Conductor - User Manual Verification 'Phase 3'
