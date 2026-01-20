import threading
import queue
from datetime import datetime, timezone
import dateutil.parser

class LatencyMonitor:
    """
    Level 300 Non-Blocking Latency Monitor.
    Ensures that database I/O never dictates execution speed.
    """
    
    SAFE_THRESHOLD = 6.0
    MIN_ADVANTAGE_THRESHOLD = 3.0 # We need at least 3s of lag to exploit
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.window_history = []  # In-memory rolling window for O(1) access
        self.max_history = 50
        
        # Non-Blocking Architecture
        self._log_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._db_worker, daemon=True)
        self._worker_thread.start()

    def log_feed_delta(self, game_id, event_ts_str):
        """
        HOT PATH: Executes in microseconds. 
        Calculates delta, updates state, and offloads I/O.
        """
        if not event_ts_str:
            return 0.0
            
        try:
            # 1. Parse & Normalize (UTC)
            event_time = dateutil.parser.parse(event_ts_str)
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            else:
                event_time = event_time.astimezone(timezone.utc)

            receipt_time = datetime.now(timezone.utc)
            
            # 2. Math (Fast)
            delta = (receipt_time - event_time).total_seconds()
            if delta < 0: delta = 0.0
                
            # 3. Update State (Fast)
            self._update_rolling_window(delta)
            
            # 4. Offload I/O (Instant)
            # Drop the payload and return immediately.
            payload = {
                'game_id': game_id,
                'event_ts': event_ts_str,
                'receipt_ts': receipt_time,
                'delta': delta,
                'is_safe': self.is_safe_window()
            }
            self._log_queue.put(payload)
            
            return delta
            
        except Exception as e:
            # Sniper safety: log error but do not block the thread
            print(f"[LatencyMonitor] Critical path error: {e}")
            return 0.0

    def is_safe_window(self):
        """
        Determines if we are within the exploitable latency window.
        Read-only from memory.
        """
        if not self.window_history:
            return False
            
        avg_latency = sum(self.window_history) / len(self.window_history)
        # Must be within 3.0s and 6.0s for a valid "Sniper" opportunity
        return self.MIN_ADVANTAGE_THRESHOLD < avg_latency < self.SAFE_THRESHOLD

    def _update_rolling_window(self, delta):
        self.window_history.append(delta)
        if len(self.window_history) > self.max_history:
            self.window_history.pop(0)

    def _db_worker(self):
        """
        COLD PATH: Drains the queue to the database in a background thread.
        Handles slow network RTT without blocking the sniper engine.
        """
        while not self._stop_event.is_set():
            try:
                payload = self._log_queue.get(timeout=1.0)
                
                self._persist_metric(
                    payload['game_id'], 
                    payload['event_ts'], 
                    payload['receipt_ts'], 
                    payload['delta'], 
                    payload['is_safe']
                )
                self._log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[LatencyMonitor] DB Background Write Failed: {e}")

    def get_current_stats(self):
        if not self.window_history:
            return {"avg": 0.0, "status": "UNKNOWN"}
            
        avg = sum(self.window_history) / len(self.window_history)
        return {
            "avg": round(avg, 3),
            "status": "SAFE" if self.MIN_ADVANTAGE_THRESHOLD < avg < self.SAFE_THRESHOLD else "OUTSIDE_WINDOW"
        }

    def _persist_metric(self, game_id, event_ts, receipt_ts, delta, is_safe):
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO feed_latency_metrics 
                (game_id, event_timestamp, receipt_timestamp, delta_seconds, is_safe_window)
                VALUES (?, ?, ?, ?, ?)
            """
            
            if self.db_manager.is_postgres:
                query = query.replace('?', '%s')
                
            cursor.execute(query, (game_id, event_ts, receipt_ts, delta, 1 if is_safe else 0))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[LatencyMonitor] Database Persistence Error: {e}")

    def stop(self):
        """Graceful shutdown for the worker thread."""
        self._stop_event.set()
        self._worker_thread.join(timeout=2.0)