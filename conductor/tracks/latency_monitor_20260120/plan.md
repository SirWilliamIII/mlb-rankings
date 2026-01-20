# Implementation Plan: Phase 1 - Latency Monitor

## Phase 1: Database & Core Service
- [x] Task: Database Schema Update
    - [x] Create migration/schema change for `feed_latency_metrics` table.
    - [x] Verify table creation in SQLite/Postgres.
- [x] Task: Implement LatencyMonitor Class
    - [x] TDD: Write tests for timestamp parsing and delta calculation (UTC handling).
    - [x] Implement `log_feed_delta` method with rolling average logic.
    - [x] Implement `is_safe_window` guardrail logic.
    - [x] Verify asynchronous/efficient DB logging.

## Phase 2: Integration & Signal Protocol
- [x] Task: Integrate with LiveGameService
    - [x] Extract timestamps from MLB API payloads in `live_game_service.py`.
    - [x] Call `LatencyMonitor.log_feed_delta` on every poll.
    - [x] Inject `is_safe_window` check into the trading logic loop.
- [x] Task: Implement Tier 1 Signal Formatting
    - [x] Create `SignalGenerator` or update `TraderAgent` to output minified JSON.
    - [x] Validate JSON output against the strict schema `{"t":..., "g":...}`.
    - [x] Benchmark signal generation speed (< 50ms).

## Phase 3: Verification
- [x] Task: End-to-End Latency Test
    - [x] Simulate feed data with varying timestamps.
    - [x] Verify "High Latency" blocks execution.
    - [x] Verify "Low Latency" allows execution.
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

