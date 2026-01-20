# Specification: Phase 1 - Latency Monitor & Tier 1 Protocol

## 1. Overview
Implement the core `LatencyMonitor` service to quantify the time delta between live data feeds and system receipt. Establish the "Tier 1" execution signal protocol to ensure high-frequency trading capabilities.

## 2. Functional Requirements
### 2.1 Latency Monitoring
- **Ingestion:** Parse timestamp fields from incoming data payloads.
- **Calculation:** Compute `Delta = ReceiptTime - EventTime`.
- **Rolling Average:** Maintain a sliding window (N=50) of deltas.
- **Guardrails:**
    - `is_safe_window()` returns `True` only if `3.0s < AverageDelta < 6.0s` (The Sniper Window).
    - Log all deltas to `feed_latency_metrics` table asynchronously.

### 2.2 Tier 1 Signal Generation
- **Format:** Strict Minified JSON (No whitespace).
- **Structure:** `{"t": "...", "g": "...", "m": "...", "o": ..., "p": ..., "s": ..., "id": "..."}`
- **Constraint:** Signal generation must take < 50ms.

## 3. Non-Functional Requirements
- **Precision:** Time calculations must handle millisecond precision.
- **Timezone:** All timestamps must be normalized to UTC before comparison.
- **Performance:** Logging must be asynchronous or non-blocking to the main execution thread.

## 4. Acceptance Criteria
- [ ] `LatencyMonitor` correctly identifies "stale" feeds (> 6s delay).
- [ ] `LiveGameService` blocks trades when `is_safe_window()` is False.
- [ ] Generated betting signals match the Tier 1 JSON schema exactly.
- [ ] Latency metrics are persisted to the database.

