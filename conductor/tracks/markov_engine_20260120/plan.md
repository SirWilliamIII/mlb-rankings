# Implementation Plan: Phase 2 - Micro-State Markov Engine

## Phase 1: Core Markov Logic
- [x] Task: Service Scaffolding
    - [x] Create `app/services/markov_chain_service.py` with the base class structure.
    - [x] Implement the `TRANSITION_MATRICES` lookup architecture (O(1)).
- [x] Task: Implement Pitcher Degradation Formula
    - [x] TDD: Write tests for `p_out` scaling and `p_bb` inflation logic.
    - [x] Implement the mathematical models for Fatigue and TTTO adjustments.
- [x] Task: Performance Benchmarking
    - [x] TDD: Write a benchmark test ensuring < 1ms response time.
    - [x] Optimize matrix calculations to meet the latency budget.

## Phase 2: Orchestration & Integration
- [x] Task: Refactor StateEngine
    - [x] Update `app/services/state_engine.py` to import `MarkovChainService`.
    - [x] Replace `_get_re24_baseline` calls with `markov_service.get_instant_win_prob`.
- [x] Task: Live Data Flow
    - [x] Verify `LiveGameService` correctly passes `PitcherMonitor` modifiers to the new engine.
    - [x] TDD: Integration test simulating a live game transition with a fatigued pitcher.

## Phase 3: Validation & Calibration
- [x] Task: Sensitivity Analysis
    - [x] Verify that the model's win probability reacts correctly to "BIP Variance" (e.g., more HRs in high-fatigue states).
    - [x] TDD: Unit tests for specific high-leverage states (e.g., Bases Loaded, 2 Outs).
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
