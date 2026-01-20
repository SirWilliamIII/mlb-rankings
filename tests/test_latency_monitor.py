import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from app.services.latency_monitor import LatencyMonitor

class TestLatencyMonitor(unittest.TestCase):
    def setUp(self):
        self.mock_db_manager = MagicMock()
        self.mock_db_manager.is_postgres = False
        self.monitor = LatencyMonitor(self.mock_db_manager)

    @patch('app.services.latency_monitor.datetime')
    def test_delta_calculation_and_queue(self, mock_datetime):
        # Set "Now" to 12:00:05 UTC
        now_utc = datetime(2023, 10, 27, 12, 0, 5, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now_utc
        mock_datetime.timezone.utc = timezone.utc

        # Event: 12:00:00 UTC (5s delay)
        event_ts = "2023-10-27T12:00:00Z"
        
        delta = self.monitor.log_feed_delta(123, event_ts)
        
        self.assertEqual(delta, 5.0)
        # 5.0 is between 3.0 and 6.0, so it should be safe
        self.assertTrue(self.monitor.is_safe_window())
        
        # Verify item added to queue
        self.assertFalse(self.monitor._log_queue.empty())
        item = self.monitor._log_queue.get()
        self.assertEqual(item['game_id'], 123)
        self.assertEqual(item['delta'], 5.0)

    @patch('app.services.latency_monitor.datetime')
    def test_rolling_average_sniper_window(self, mock_datetime):
        mock_datetime.timezone.utc = timezone.utc
        
        # 1. Very low latency (1s) -> NOT SAFE (No advantage)
        mock_datetime.now.return_value = datetime(2023, 10, 27, 12, 0, 1, tzinfo=timezone.utc)
        for _ in range(10):
            self.monitor.log_feed_delta(123, "2023-10-27T12:00:00Z")
        self.assertFalse(self.monitor.is_safe_window()) 

        # 2. Sniper window latency (4s) -> SAFE
        mock_datetime.now.return_value = datetime(2023, 10, 27, 12, 0, 4, tzinfo=timezone.utc)
        for _ in range(50): # Flush the buffer
            self.monitor.log_feed_delta(123, "2023-10-27T12:00:00Z")
        self.assertTrue(self.monitor.is_safe_window())

        # 3. High latency (10s) -> NOT SAFE (Stale)
        mock_datetime.now.return_value = datetime(2023, 10, 27, 12, 0, 10, tzinfo=timezone.utc)
        for _ in range(50):
            self.monitor.log_feed_delta(123, "2023-10-27T12:00:00Z")
        self.assertFalse(self.monitor.is_safe_window())

    def test_negative_delta_clamped(self):
        event_ts = "2023-10-27T12:00:10Z"
        with patch('app.services.latency_monitor.datetime') as mock_datetime:
             mock_datetime.now.return_value = datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
             mock_datetime.timezone.utc = timezone.utc
             delta = self.monitor.log_feed_delta(123, event_ts)
             self.assertEqual(delta, 0.0)

if __name__ == '__main__':
    unittest.main()