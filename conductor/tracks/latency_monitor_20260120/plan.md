# Implementation Plan: Phase 1 - Latency Monitor

## Phase 1: Database & Core Service
- [ ] Task: Database Schema Update
    - [ ] Create migration/schema change for `feed_latency_metrics` table.
    - [ ] Verify table creation in SQLite/Postgres.
- [ ] Task: Implement LatencyMonitor Class
    - [ ] TDD: Write tests for timestamp parsing and delta calculation (UTC handling).
    - [ ] Implement `log_feed_delta` method with rolling average logic.
    - [ ] Implement `is_safe_window` guardrail logic.
    - [ ] Verify asynchronous/efficient DB logging.

## Phase 2: Integration & Signal Protocol
- [ ] Task: Integrate with LiveGameService
    - [ ] Extract timestamps from MLB API payloads in `live_game_service.py`.
    - [ ] Call `LatencyMonitor.log_feed_delta` on every poll.
    - [ ] Inject `is_safe_window` check into the trading logic loop.
- [ ] Task: Implement Tier 1 Signal Formatting
    - [ ] Create `SignalGenerator` or update `TraderAgent` to output minified JSON.
    - [ ] Validate JSON output against the strict schema `{"t":..., "g":...}`.
    - [ ] Benchmark signal generation speed (< 50ms).

## Phase 3: Verification
- [ ] Task: End-to-End Latency Test
    - [ ] Simulate feed data with varying timestamps.
    - [ ] Verify "High Latency" blocks execution.
    - [ ] Verify "Low Latency" allows execution.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

