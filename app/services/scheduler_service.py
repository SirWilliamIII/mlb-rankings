from apscheduler.schedulers.background import BackgroundScheduler
from app.services.data_processor import DataProcessor
from app.services.monte_carlo_simulator import MonteCarloSimulator
from app.services.mlb_api import MlbApi
from app.services.database_manager import DatabaseManager
import logging
import atexit

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.db_manager = DatabaseManager()
        self.data_processor = DataProcessor(self.db_manager)
        
    def start(self):
        # Schedule the daily refresh at 4:00 AM
        self.scheduler.add_job(
            func=self.run_daily_cycle, 
            trigger="cron", 
            hour=4, 
            minute=0,
            id="daily_cycle",
            replace_existing=True
        )
        
        self.scheduler.start()
        logging.info("Scheduler started.")
        
        # Shut down scheduler when exiting the app
        atexit.register(lambda: self.scheduler.shutdown())

    def run_daily_cycle(self):
        """
        The core workflow: Refresh Data -> Run Simulation -> Save Results
        """
        logging.info("Starting Daily Cycle...")
        
        # 1. Update Data
        self.data_processor.refresh_all_data(season=2025)
        
        # 2. Run Simulation
        mlb_api = MlbApi(self.db_manager)
        teams = mlb_api.get_teams_for_simulation()
        schedule = mlb_api.get_remaining_schedule() # Defaults to 2026/current
        
        if teams and schedule:
            logging.info("Running Daily Simulation...")
            # We run a high number of iterations for the daily cached result
            simulator = MonteCarloSimulator(teams, schedule, self.db_manager)
            simulator.run_simulation(iterations=2000)
            
            # Save results
            probs = simulator.get_probabilities()
            
            # Enhance with team names for DB storage
            enhanced_probs = {}
            for team_id, p in probs.items():
                enhanced_probs[team_id] = p
                if team_id in teams:
                    enhanced_probs[team_id]['name'] = teams[team_id]['name']
            
            run_id = self.db_manager.save_simulation_results(2000, enhanced_probs)
            logging.info(f"Daily Simulation Complete. Run ID: {run_id}")
        else:
            logging.error("Skipping simulation due to missing data.")
