import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from app.services.latency_monitor import LatencyMonitor

class TestLatencyMonitor(unittest.TestCase):
    def setUp(self):
        self.mock_db_manager = MagicMock()
        self.mock_db_manager.is_postgres = False
        self.monitor = LatencyMonitor(self.mock_db_manager)

    def test_log_feed_delta_utc_calculation(self):
        # Event time: 12:00:00 UTC
        event_ts_str = "2023-10-27T12:00:00Z"
        
        # Receipt time: 12:00:04 UTC (4 seconds later)
        receipt_time = datetime(2023, 10, 27, 12, 0, 4, tzinfo=timezone.utc)
        
        with patch('app.services.latency_monitor.datetime') as mock_datetime:
            mock_datetime.now.return_value = receipt_time
            mock_datetime.timezone = timezone
            # Need to patch dateutil.parser if we want to control parsing, 
            # but usually it's fine.
            
            # Since LatencyMonitor imports datetime class, we need to be careful mocking it.
            # Easier to mock datetime.now only if possible, but it's a built-in.
            # Let's try mocking the module.
            pass
            
    @patch('app.services.latency_monitor.datetime')
    def test_delta_calculation(self, mock_datetime):
        # Set "Now" to 12:00:05 UTC
        now_utc = datetime(2023, 10, 27, 12, 0, 5, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now_utc
        mock_datetime.timezone.utc = timezone.utc

        # Event: 12:00:00 UTC
        event_ts = "2023-10-27T12:00:00Z"
        
        delta = self.monitor.log_feed_delta(123, event_ts)
        
        self.assertEqual(delta, 5.0)
        self.assertTrue(self.monitor.is_safe_window())
        
        # Verify item added to queue
        self.assertFalse(self.monitor.log_queue.empty())
        item = self.monitor.log_queue.get()
        self.assertEqual(item[0], 123) # game_id
        self.assertEqual(item[3], 5.0) # delta

    @patch('app.services.latency_monitor.datetime')
    def test_rolling_average_and_safe_window(self, mock_datetime):
        mock_datetime.timezone.utc = timezone.utc
        
        # 1. Add 10 fast updates (2s latency)
        mock_datetime.now.return_value = datetime(2023, 10, 27, 12, 0, 2, tzinfo=timezone.utc)
        for _ in range(10):
            self.monitor.log_feed_delta(123, "2023-10-27T12:00:00Z")
            
        self.assertTrue(self.monitor.is_safe_window()) # Avg 2.0 < 6.0
        
        # 2. Add 40 slow updates (10s latency)
        # N=50 is the spec, implementation currently N=20. We will test behavior and fix N later.
        # Assuming current implementation N=20:
        # We fill it with 10s latency
        
        mock_datetime.now.return_value = datetime(2023, 10, 27, 12, 0, 10, tzinfo=timezone.utc)
        for _ in range(60): # Overflow the buffer (N=50)
            self.monitor.log_feed_delta(123, "2023-10-27T12:00:00Z")
            
        # Now avg should be 10.0
        self.assertFalse(self.monitor.is_safe_window())
        self.assertEqual(self.monitor.get_current_stats()['avg'], 10.0)

    def test_negative_delta_clamped(self):
        # Event in future (clock skew)
        event_ts = "2023-10-27T12:00:10Z"
        
        with patch('app.services.latency_monitor.datetime') as mock_datetime:
             mock_datetime.now.return_value = datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
             mock_datetime.timezone.utc = timezone.utc
             
             delta = self.monitor.log_feed_delta(123, event_ts)
             self.assertEqual(delta, 0.0)

if __name__ == '__main__':
    unittest.main()
