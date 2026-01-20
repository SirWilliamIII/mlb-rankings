from datetime import datetime
import dateutil.parser

class LatencyMonitor:
    """
    Phase 1: Latency & Feed Synchronization.
    Tracks the delay between real-world events (API timestamp) and system receipt.
    """
    
    SAFE_THRESHOLD_SECONDS = 6.0
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.rolling_deltas = [] # Keep last 20 for average
        self.max_history = 20

    def log_feed_delta(self, game_id, event_ts_str):
        """
        Calculates and logs the latency delta.
        
        Args:
            game_id (int): The game PK.
            event_ts_str (str): ISO string from MLB API (e.g., '2023-10-25T19:00:05Z').
        
        Returns:
            float: The calculated delta in seconds.
        """
        if not event_ts_str:
            return 0.0
            
        try:
            # Parse API timestamp (usually UTC)
            event_time = dateutil.parser.parse(event_ts_str)
            
            # Ensure both times are timezone-aware and in UTC for correct comparison
            if event_time.tzinfo is None:
                # If API provides naive timestamp, assume it's UTC
                event_time = event_time.replace(tzinfo=datetime.timezone.utc)
            else:
                # Convert to UTC if it has a different timezone
                event_time = event_time.astimezone(datetime.timezone.utc)

            # Receipt time (Now in UTC)
            receipt_time = datetime.now(datetime.timezone.utc)
            
            delta = (receipt_time - event_time).total_seconds()
            
            # Sanity check for negative delta (clock skew or bad parse) -> clamp to 0
            if delta < 0:
                delta = 0.0
                
            # Update rolling average
            self.rolling_deltas.append(delta)
            if len(self.rolling_deltas) > self.max_history:
                self.rolling_deltas.pop(0)
            
            is_safe = 1 if delta <= self.SAFE_THRESHOLD_SECONDS else 0
            
            # Async log to DB (in production use background task, here direct)
            self._persist_metric(game_id, event_ts_str, receipt_time, delta, is_safe)
            
            return delta
            
        except Exception as e:
            print(f"[LatencyMonitor] Error calculating delta: {e}")
            return 0.0

    def is_safe_window(self):
        """
        Returns True if the average latency is within the safe threshold.
        """
        if not self.rolling_deltas:
            return True # Assume safe if no data
            
        avg_latency = sum(self.rolling_deltas) / len(self.rolling_deltas)
        return avg_latency <= self.SAFE_THRESHOLD_SECONDS

    def get_current_stats(self):
        if not self.rolling_deltas:
            return {"avg": 0.0, "status": "UNKNOWN"}
            
        avg = sum(self.rolling_deltas) / len(self.rolling_deltas)
        return {
            "avg": round(avg, 3),
            "status": "SAFE" if avg <= self.SAFE_THRESHOLD_SECONDS else "LAGGING"
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
            # Handle Postgres syntax if needed (Manager usually handles it but we are bypassing manager's _execute helper here slightly for speed/custom query)
            # Actually, let's use the manager's helper pattern if possible, but manager doesn't expose a generic 'insert' easily without raw SQL.
            # We'll rely on the DB manager's _execute if we had access, but here we have the conn.
            # Let's just use standard SQL and rely on the driver.
            
            if self.db_manager.is_postgres:
                query = query.replace('?', '%s')
                
            cursor.execute(query, (game_id, event_ts, receipt_ts, delta, is_safe))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[LatencyMonitor] DB Write Error: {e}")
