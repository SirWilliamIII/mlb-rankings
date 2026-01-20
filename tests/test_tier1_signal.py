import pytest
import time
import json
from app.services.trader_agent import TraderAgent

class TestTier1Signal:
    
    @pytest.fixture
    def agent(self):
        return TraderAgent()

    def test_signal_generation_format(self, agent):
        # Setup inputs
        signal_data = {
            "game_id": "NYY-BOS",
            "market": "H_ML",
            "odds": -115,
            "prob": 0.58,
            "stake": 450.00
        }
        
        # Generate
        start = time.perf_counter()
        json_output = agent.generate_tier1_signal(signal_data)
        end = time.perf_counter()
        
        # 1. Performance Check (< 50ms)
        duration_ms = (end - start) * 1000
        assert duration_ms < 50, f"Signal generation too slow: {duration_ms}ms"
        
        # 2. Format Check (No whitespace)
        assert " " not in json_output
        assert "\n" not in json_output
        
        # 3. Structure Check
        data = json.loads(json_output)
        assert "t" in data
        assert "g" in data
        assert "m" in data
        assert "o" in data
        assert "p" in data
        assert "s" in data
        assert "id" in data
        
        # 4. Value Verification
        assert data["g"] == "NYY-BOS"
        assert data["o"] == -115
        assert data["s"] == 450.00
