import pytest
from app.services.trader_agent import TraderAgent

class TestTraderAgent:
    
    @pytest.fixture
    def agent(self):
        # Bankroll 10000, 1/4 Kelly, Min Edge 2%, Max Bet 5%
        return TraderAgent(bankroll=10000, kelly_fraction=0.25, min_edge=0.02, max_wager_limit=0.05)

    def test_no_edge_pass(self, agent):
        # Model: 50%, Odds: -110 (Implied ~52.4%) -> Negative EV
        # -110 -> 1.909 decimal
        # EV = (0.50 * 1.909) - 1 = -0.045
        result = agent.evaluate_trade(model_prob=0.50, market_odds_american=-110)
        assert result['action'] == "PASS"
        assert "No Edge" in result['reason']
        assert result['wager_amount'] == 0

    def test_strong_edge_bet(self, agent):
        # Model: 60%, Odds: +100 (Implied 50%) -> Positive EV
        # +100 -> 2.0 decimal
        # EV = (0.60 * 2.0) - 1 = 0.20 (20%)
        # Kelly = (1 * 0.6 - 0.4) / 1 = 0.2
        # Quarter Kelly = 0.05 (5%)
        # Bankroll 10000 * 5% = 500
        result = agent.evaluate_trade(model_prob=0.60, market_odds_american=100)
        assert result['action'] == "BET"
        assert result['wager_amount'] == 500.0
        assert result['wager_percent'] == 0.05

    def test_max_limit_cap(self, agent):
        # Model: 90% (Huge lock), Odds: +100
        # Kelly would be huge (~80%), Quarter Kelly ~20%
        # But max limit is 5%
        result = agent.evaluate_trade(model_prob=0.90, market_odds_american=100)
        assert result['action'] == "BET"
        assert result['wager_percent'] == 0.05  # Capped
        assert result['wager_amount'] == 500.0

    def test_garbage_time_safety_valve(self, agent):
        # Context: Inning 8, Score Diff 7 (Blowout)
        context = {'inning': 8, 'score_diff': 7}
        # Even with massive edge
        result = agent.evaluate_trade(model_prob=0.80, market_odds_american=100, game_context=context)
        assert result['action'] == "BLOCK"
        assert "Garbage Time" in result['reason']

    def test_low_leverage_safety_valve(self, agent):
        # Context: LI 0.1
        context = {'leverage_index': 0.1}
        result = agent.evaluate_trade(model_prob=0.60, market_odds_american=100, game_context=context)
        assert result['action'] == "BLOCK"
        assert "Low Leverage" in result['reason']

    def test_american_odds_conversion(self, agent):
        # -200 -> 1.5
        assert agent._american_to_decimal(-200) == 1.5
        # +200 -> 3.0
        assert agent._american_to_decimal(200) == 3.0

    def test_leverage_scaled_staking(self, agent):
        # Model: 60%, Odds: +100. Full Kelly = 0.2. Base Quarter Kelly = 0.05.
        # Case 1: LI = 1.0 (Neutral). Staking should be 0.05.
        context_1 = {'leverage_index': 1.0}
        result_1 = agent.evaluate_trade(model_prob=0.60, market_odds_american=100, game_context=context_1)
        assert result_1['wager_percent'] == 0.05

        # Case 2: LI = 2.0 (High Leverage). Staking should be 0.05 * 2.0 = 0.10.
        # But wait, max_wager_limit is 0.05. So it should be capped.
        context_2 = {'leverage_index': 2.0}
        result_2 = agent.evaluate_trade(model_prob=0.60, market_odds_american=100, game_context=context_2)
        assert result_2['wager_percent'] == 0.05 # Capped at max_wager_limit

        # Let's use an agent with higher limit for testing scaling
        agent_high_limit = TraderAgent(max_wager_limit=0.20)
        result_3 = agent_high_limit.evaluate_trade(model_prob=0.60, market_odds_american=100, game_context=context_2)
        assert result_3['wager_percent'] == 0.10 # 0.05 * 2.0 = 0.10
