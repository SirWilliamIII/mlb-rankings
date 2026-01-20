# Specification: Risk Mitigation & Hardening

## 1. Overview
Address critical risks identified during the "Kill House" stress test and code review. This includes migrating financial calculations to fixed-point precision, ensuring thread safety for background workers, and scaffolding defensive modeling to capture fielding errors.

## 2. Functional Requirements
### 2.1 Financial Hardening
- **Precision:** Use `decimal.Decimal` for all monetary (stake, profit) and probability calculations.
- **Storage:** Use `NUMERIC` types in PostgreSQL for financial columns in `shadow_bets`.

### 2.2 Thread Safety
- **Graceful Shutdown:** Implement a `ShutdownHandler` that intercepts SIGTERM/SIGINT.
- **Resource Cleanup:** Ensure all background threads (`LatencyMonitor`, `TraderAgent`, `NotificationService`) are joined and queues drained upon exit.

### 2.3 Defensive Modeling
- **Defense Monitor:** Create a service to track defensive efficiency (e.g., DRS, UZR) - scaffolding only.
- **Markov Integration:** Update `MarkovChainService` to accept a `defense_mod` parameter.

## 3. Non-Functional Requirements
- **No Performance Regression:** Hardening must not push the Tier 1 latency above 50ms.
- **Backward Compatibility:** Database schema changes should preserve existing data if possible (or recreate if dev/shadow).

## 4. Acceptance Criteria
- [ ] `shadow_bets` table uses `NUMERIC` columns.
- [ ] `tests/test_trader_agent.py` passes with `Decimal` assertions.
- [ ] Application exits cleanly without "Thread still running" warnings.
- [ ] `MarkovChainService` signature accepts `defense_mod`.
