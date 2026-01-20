# Implementation Plan: Phase 2 - Micro-State Markov Engine

## Phase 1: Core Markov Logic
- [ ] Task: Service Scaffolding
    - [ ] Create `app/services/markov_chain_service.py` with the base class structure.
    - [ ] Implement the `TRANSITION_MATRICES` lookup architecture (O(1)).
- [ ] Task: Implement Pitcher Degradation Formula
    - [ ] TDD: Write tests for `p_out` scaling and `p_bb` inflation logic.
    - [ ] Implement the mathematical models for Fatigue and TTTO adjustments.
- [ ] Task: Performance Benchmarking
    - [ ] TDD: Write a benchmark test ensuring < 1ms response time.
    - [ ] Optimize matrix calculations to meet the latency budget.

## Phase 2: Orchestration & Integration
- [ ] Task: Refactor StateEngine
    - [ ] Update `app/services/state_engine.py` to import `MarkovChainService`.
    - [ ] Replace `_get_re24_baseline` calls with `markov_service.get_instant_win_prob`.
- [ ] Task: Live Data Flow
    - [ ] Verify `LiveGameService` correctly passes `PitcherMonitor` modifiers to the new engine.
    - [ ] TDD: Integration test simulating a live game transition with a fatigued pitcher.

## Phase 3: Validation & Calibration
- [ ] Task: Sensitivity Analysis
    - [ ] Verify that the model's win probability reacts correctly to "BIP Variance" (e.g., more HRs in high-fatigue states).
    - [ ] TDD: Unit tests for specific high-leverage states (e.g., Bases Loaded, 2 Outs).
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
