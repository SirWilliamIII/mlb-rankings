import signal
import sys
import logging

class ShutdownHandler:
    """
    Centralized handler for graceful shutdown.
    Catches SIGINT/SIGTERM and stops registered services.
    """
    def __init__(self):
        self.services = []
        self.logger = logging.getLogger("ShutdownHandler")
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def register(self, service):
        """Register a service that has a .stop() method."""
        if hasattr(service, 'stop'):
            self.services.append(service)
        else:
            self.logger.warning(f"Service {service} does not have a stop() method.")

    def _handle_signal(self, signum, frame):
        self.logger.info(f"Received signal {signum}. Shutting down...")
        for service in self.services:
            try:
                self.logger.info(f"Stopping {service.__class__.__name__}...")
                service.stop()
            except Exception as e:
                self.logger.error(f"Error stopping {service.__class__.__name__}: {e}")
        
        self.logger.info("Shutdown complete. Exiting.")
        sys.exit(0)
