# Specification: Phase 2 - Micro-State Markov Engine

## 1. Overview
Replace the legacy, static RE24 run-expectancy tables with a dynamic, context-aware Markov Chain transition engine. This service will enable pitch-by-pitch probability updates that account for real-time pitcher degradation (Fatigue and TTTO).

## 2. Functional Requirements
### 2.1 Markov Chain Service (`markov_chain_service.py`)
- **Matrix Architecture:** Implement a memory-resident transition matrix for the 24 base/out states.
- **Dynamic Probabilities:** The engine must adjust transition probabilities (p_out, p_hit, p_bb) based on input modifiers.
- **Pitcher Penalty Logic:**
    - **Out Rate:** Scale `p_out` downward as `PitcherModifier` increases.
    - **BIP Variance:** Skew hit distribution toward extra-base hits (2B/HR) under high fatigue.
    - **Walk Inflation:** Increase `p_bb` based on "Times Through The Order" (TTTO) count.
- **Lookup Performance:** Achieve < 1ms response time for a single state win-probability calculation.

### 2.2 Integration with StateEngine
- **Orchestration:** `StateEngine` will delegate in-inning probability lookups to `MarkovChainService`.
- **Matchup Data:** Ensure `PitcherMonitor` data is correctly passed into the Markov engine for every state update.

## 3. Non-Functional Requirements
- **O(1) Efficiency:** Use pre-computed matrices or high-speed lookup tables where possible.
- **Thread Safety:** The service must handle concurrent requests from multiple live games.

## 4. Acceptance Criteria
- [ ] `MarkovChainService` returns a probability in < 1ms.
- [ ] Probability shifts significantly (e.g., > 3%) when a `PitcherModifier` moves from 1.0 to 1.15.
- [ ] Tests verify that Walk Rate increases and Out Rate decreases as TTTO rises.
- [ ] `StateEngine` no longer references the static `_get_re24_baseline` table for live updates.
