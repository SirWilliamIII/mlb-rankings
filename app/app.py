# app/app.py
from flask import Flask, jsonify, request, render_template
from app.services.mlb_api import MlbApi
from app.services.season_simulator import SeasonSimulator
from app.services.database_manager import DatabaseManager
from app.services.betting_analyzer import BettingAnalyzer
from app.services.scheduler_service import SchedulerService
from app.services.live_game_service import LiveGameService
from app.utils.shutdown_handler import ShutdownHandler

app = Flask(__name__)
db_manager = DatabaseManager()
mlb_api = MlbApi(db_manager)
betting_analyzer = BettingAnalyzer(db_manager)
live_service = LiveGameService(db_manager)

# Initialize Shutdown Handler
shutdown_handler = ShutdownHandler()
shutdown_handler.register(live_service.latency_monitor)
shutdown_handler.register(live_service.notifier)
# Register other threaded services if any

# Initialize and Start Scheduler
scheduler = SchedulerService()
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/live-dashboard')
def live_dashboard():
    """
    Returns real-time data for the Sniper Dashboard.
    """
    try:
        data = live_service.get_live_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sniper-logs')
def sniper_logs():
    """
    Returns the history of generated signals.
    """
    return jsonify(live_service.get_signal_history())

@app.route('/standings')
def standings():
    standings_data = mlb_api.get_standings()
    if standings_data:
        return jsonify(standings_data)
    else:
        return jsonify({"error": "Could not fetch standings."}), 500

@app.route('/api/latest-simulation')
def latest_simulation():
    """
    Returns the results of the most recent background simulation.
    """
    result = db_manager.get_latest_simulation_results()
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No simulation results found."}), 404

@app.route('/betting-value')
def betting_value():
    # Get upcoming games (just next 15 for demo)
    teams = mlb_api.get_teams_for_simulation()
    schedule = mlb_api.get_remaining_schedule()

    if not teams or not schedule:
        return jsonify({"error": "Missing data."}), 500

    next_games = schedule[:15]
    opportunities = betting_analyzer.analyze_schedule(next_games, teams)

    return jsonify({
        "count": len(opportunities),
        "opportunities": opportunities
    })

@app.route('/simulate')
def simulate():
    iterations = request.args.get('iterations', default=100, type=int)

    # 1. Get current data
    teams = mlb_api.get_teams_for_simulation()
    schedule = mlb_api.get_remaining_schedule()

    if not teams or not schedule:
        return jsonify({"error": "Missing data for simulation."}), 500

    # 2. Run simulation
    simulator = SeasonSimulator(teams, schedule, db_manager)
    simulator.run_simulation(iterations=iterations)

    # 3. Get results
    probabilities = simulator.get_probabilities()

    # 4. Enhance results with team names
    enhanced_probabilities = {}
    for team_id, probs in probabilities.items():
        enhanced_probabilities[team_id] = probs
        enhanced_probabilities[team_id]['name'] = teams[team_id]['name']

    # 5. Save results to database
    run_id = db_manager.save_simulation_results(iterations, enhanced_probabilities)

    return jsonify({
        "run_id": run_id,
        "iterations": iterations,
        "probabilities": enhanced_probabilities
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5555)
