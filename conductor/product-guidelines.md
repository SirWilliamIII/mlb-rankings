hook.
* **Content:** Human-readable status with visual urgency codes.
    * **RED:** High Leverage + Latency Open (Sniper Window).
    * **YELLOW:** Discrepancy Found but Latency Unknown (Warning).
    * **GREEN:** Trade Executed (Kill Confirmed).

## 2. Latency Guardrails & Kill Switches
The code must strictly enforce these thresholds. If violated, the signal is **VOID**.

| Metric | Max Threshold | Action |
| :--- | :--- | :--- |
| **Feed Age** | 6.0 seconds | ABORT TRADE (Data stale) |
| **Calculation Time** | 100 ms | ABORT TRADE (System lag) |
| **Odds Drift** | > 5% variance | RETRY/RE-QUOTE |
| **LI (Leverage)** | < 0.5 | FILTER (Low value) |

## 3. Logging Standards (Audit Trail)
Do not clutter the console.
* **`execution.log`:** Only successful trad# Operational Guidelines: MLB Sniper Engine

## 1. Signal Communication Protocol
The system operates on a **Tiered Latency Model**. Signals are prioritized by speed of execution.

### Tier 1: Execution Signals (The Bot)
* **Latency Budget:** < 50ms
* **Format:** Minified JSON (No formatting, no whitespace).
* **Destination:** `TraderAgent` -> Sportsbook API / `shadow_bets` DB.
* **Content:** Pure execution vector.
    ```json
    {"t":"1620010203.45","g":"NYY-BOS","m":"H_ML","o":-115,"p":0.58,"s":450,"id":"uuid"}
    ```
    *(Key: t=timestamp, g=game, m=market, o=odds, p=prob, s=stake)*

### Tier 2: Operator Alerts (The Dashboard)
* **Latency Budget:** < 500ms (Asynchronous)
* **Format:** WebSocket Broadcast.
* **Destination:** Frontend UI / Slack Webe signals and API responses.
* **`latency.log`:** CSV format of `PlayTime` vs `SystemTime` deltas (for post-game calibration).
* **`debug.log`:** Full verbose dump of Markov matrices and logic chains (Enabled only in `DEV` mode).

## 4. UI/UX "Dark Mode" Standards
The dashboard is not for entertainment; it is for risk management.
* **No clutter:** Remove team logos, player faces, and news feeds.
* **Data First:** Display `WinProb`, `ImpliedOdds`, and `KellyEV` in large, high-contrast fonts.
* **Live Latency Ticker:** A dedicated corner showing current `Feed_Delta` (e.g., "4.2s AHEAD").

## 5. Developer "Do Not Cross" Lines
1.  **Never** fetch odds without immediately checking the timestamp.
2.  **Never** run a Monte Carlo sim (1000+ iterations) inside the hot loop. Use the Markov Lookup.
3.  **Never** allow the UI rendering thread to block the Execution thread.
