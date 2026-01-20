# Implementation Plan: Sniper Engine Risk Mitigation

## Approach
To address the identified risks (Financial Precision, Thread Safety, and Defensive Modeling gaps), we will execute a targeted hardening phase.
- **Financial Precision:** We will migrate all monetary and probability calculations from `float` to `decimal.Decimal` and update database schemas to `NUMERIC`. This prevents floating-point drift.
- **Thread Safety:** We will implement a centralized `ShutdownHandler` that catches system signals (SIGTERM/SIGINT) and gracefully stops all background services (`LatencyMonitor`, `TraderAgent`, `NotificationService`), ensuring queues are drained before exit.
- **Defensive Modeling:** We will scaffold a `DefenseMonitor` and update the `MarkovChainService` to accept a `defense_modifier`, fixing the "blind spot" revealed by the WS Game 5 backtest.

## Steps

### 1. Financial Hardening (25 min)
- **Database:** Update `app/services/database_manager.py` to use `NUMERIC` types for `stake`, `odds`, `profit_loss`, `edge`.
- **Code:** Refactor `TraderAgent`, `BettingAnalyzer`, and `MarketSimulator` to use Python's `decimal.Decimal`.
- **Verification:** Update `tests/test_trader_agent.py` to assert exact Decimal values.

### 2. Thread Safety & Graceful Shutdown (20 min)
- **Utility:** Create `app/utils/shutdown_handler.py` to manage service lifecycle.
- **Refactor:** Ensure `LatencyMonitor`, `TraderAgent`, and `NotificationService` expose a `stop()` method that joins threads and drains queues.
- **Integration:** Update `app/app.py` and `main.py` to register these services with the `ShutdownHandler`.

### 3. Defensive Modeling Scaffolding (15 min)
- **Scaffold:** Create `app/services/defense_monitor.py` (Stub).
- **Update Markov:** Modify `MarkovChainService.get_instant_win_prob` to accept a `defense_mod` (default 1.0).
- **Logic:** Add a basic scalar to `_get_transition_matrix` (e.g., `defense_mod > 1.0` increases `p_error` or effectively `p_hit`).

## Timeline
| Phase | Duration |
|-------|----------|
| Financial Hardening | 25 min |
| Thread Safety | 20 min |
| Defensive Modeling | 15 min |
| **Total** | **1 hour** |

## Rollback Plan
- **Database:** If migration fails, revert `shadow_bets` table schema to `REAL`.
- **Code:** Use git revert to restore `float` based logic if performance degrades significantly (>50ms).

## Security Checklist
- [x] Input validation (Checked in Phase 2)
- [ ] Precision checks (Decimal implementation)
- [ ] Concurrency checks (Thread join timeouts)
