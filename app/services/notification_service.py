import os
import json
import requests
import threading
import queue

class NotificationService:
    """
    Tier 2 Operator Alerts (Phase 3).
    Asynchronously sends signals to Slack/Discord for manual oversight.
    """

    def __init__(self):
        self.webhook_url = os.getenv("NOTIFIER_WEBHOOK_URL")
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        
        if self.webhook_url:
            self.worker = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker.start()

    def send_alert(self, title, message, level="INFO"):
        """
        Enqueues an alert to be sent asynchronously.
        level: INFO, WARNING, SUCCESS (RED/YELLOW/GREEN in guidelines)
        """
        if not self.webhook_url:
            # print(f"[NotificationService] Mock Alert [{level}]: {title} - {message}")
            return

        payload = {
            "title": title,
            "message": message,
            "level": level
        }
        self.queue.put(payload)

    def _worker_loop(self):
        while not self.stop_event.is_set():
            try:
                # Block for 1s
                payload = self.queue.get(timeout=1.0)
                self._dispatch_webhook(payload)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[NotificationService] Worker Error: {e}")

    def _dispatch_webhook(self, payload):
        """Actually sends the HTTP request."""
        try:
            # Simplified generic webhook format
            # Can be tailored for Slack blocks or Discord embeds
            color = 0x3498db # blue
            if payload['level'] == 'SUCCESS': color = 0x2ecc71 # green
            elif payload['level'] == 'WARNING': color = 0xf1c40f # yellow
            elif payload['level'] == 'ERROR': color = 0xe74c3c # red

            data = {
                "content": f"**[{payload['level']}] {payload['title']}**\n{payload['message']}"
            }
            
            response = requests.post(self.webhook_url, json=data, timeout=5)
            response.raise_for_status()
        except Exception as e:
            print(f"[NotificationService] Webhook Dispatch Failed: {e}")

    def stop(self):
        self.stop_event.set()
