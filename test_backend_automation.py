import sys
import os
import logging
sys.path.append(os.getcwd())

from app.services.scheduler_service import SchedulerService

# Configure logging to see output in console
logging.basicConfig(level=logging.INFO)

def test_automation():
    print("Initializing Scheduler Service...")
    service = SchedulerService()
    
    print("Forcing Daily Cycle (Data Refresh + Simulation)...")
    try:
        service.run_daily_cycle()
        print("\nSUCCESS: Daily cycle completed without error.")
    except Exception as e:
        print(f"\nFAILURE: Daily cycle failed: {e}")

if __name__ == "__main__":
    test_automation()

