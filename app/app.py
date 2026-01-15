# app/app.py
from flask import Flask, jsonify, request, render_template
from app.services.mlb_api import MlbApi
from app.services.monte_carlo_simulator import MonteCarloSimulator
from app.services.database_manager import DatabaseManager
from app.services.betting_analyzer import BettingAnalyzer
from app.services.scheduler_service import SchedulerService

app = Flask(__name__)
db_manager = DatabaseManager()
mlb_api = MlbApi(db_manager)
betting_analyzer = BettingAnalyzer(db_manager)

# Initialize and Start Scheduler
scheduler = SchedulerService()
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

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
    simulator = MonteCarloSimulator(teams, schedule, db_manager)
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
    app.run(debug=True)
