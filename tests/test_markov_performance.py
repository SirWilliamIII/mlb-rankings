import unittest
import time
import numpy as np
from app.services.markov_chain_service import MarkovChainService

class TestMarkovPerformance(unittest.TestCase):
    def setUp(self):
        self.service = MarkovChainService()

    def test_matrix_generation_speed(self):
        """Benchmark matrix generation and solving."""
        # Warmup
        self.service._get_transition_matrix(1.0, 0)
        
        start = time.perf_counter()
        
        # 1. Generate Matrix
        matrix = self.service._get_transition_matrix(1.15, 2)
        
        # 2. Mock Solver (Invert 24x24)
        # Extract Q (first 24x24)
        Q = matrix[:24, :24]
        I = np.eye(24)
        try:
            N = np.linalg.inv(I - Q)
        except np.linalg.LinAlgError:
            # Singularity possible if probability mass leaks or I-Q is singular (shouldn't be for absorbing chain)
            pass
            
        end = time.perf_counter()
        duration_ms = (end - start) * 1000
        
        print(f"\nMatrix + Inversion Time: {duration_ms:.4f} ms")
        self.assertLess(duration_ms, 1.0, "Markov calculation must be < 1ms")

if __name__ == '__main__':
    unittest.main()

