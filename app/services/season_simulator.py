# app/services/monte_carlo_simulator.py

import copy
import random
from app.services.forecasting_model import ForecastingModel

class SeasonSimulator:
    """
    The 'Monte Carlo Simulation Agent'. It orchestrates the season simulation.
    """

    def __init__(self, teams, schedule, db_manager=None):
        """
        Initializes the simulator with teams and the remaining schedule.

        Args:
            teams (dict): A dictionary of teams indexed by ID.
            schedule (list): A list of game dictionaries for the remaining season.
            db_manager (DatabaseManager): Optional DB connection for advanced stats.
        """
        self.teams = teams
        self.schedule = schedule
        self.forecasting_model = ForecastingModel(db_manager)
        self.simulations_run = 0
        # Results tracking: {team_id: {milestone: count}}
        self.results = {
            team_id: {
                "division_winner": 0,
                "playoff_spot": 0,
                "league_champion": 0,
                "world_series_winner": 0,
            } for team_id in teams
        }

    def run_simulation(self, iterations=1000):
        """
        Runs the full Monte Carlo simulation for the remainder of the season.

        Args:
            iterations (int): The number of times to simulate the season.
        """
        print(f"Running {iterations} simulations...")

        for _ in range(iterations):
            # 1. Initialize standings for this simulation run
            sim_teams = copy.deepcopy(self.teams)
            for team_id in sim_teams:
                # Add current stats if they don't exist
                if 'w' not in sim_teams[team_id]: sim_teams[team_id]['w'] = 0
                if 'l' not in sim_teams[team_id]: sim_teams[team_id]['l'] = 0
                
            # 2. Simulate remaining games
            for game in self.schedule:
                home_id = game['home_id']
                away_id = game['away_id']
                
                if home_id not in sim_teams or away_id not in sim_teams:
                    continue
                    
                home_team = sim_teams[home_id]
                away_team = sim_teams[away_id]
                
                winner_team = self.forecasting_model.predict_winner(home_team, away_team)
                
                if winner_team['id'] == home_id:
                    sim_teams[home_id]['w'] += 1
                    sim_teams[away_id]['l'] += 1
                else:
                    sim_teams[away_id]['w'] += 1
                    sim_teams[home_id]['l'] += 1

            # 3. Determine playoff participants and winners
            self._process_simulation_results(sim_teams)

        self.simulations_run += iterations
        print("Simulations complete.")

    def get_probabilities(self):
        """
        Calculates and returns the probabilities for each team.
        """
        if self.simulations_run == 0:
            return {}

        probabilities = {}
        for team_id, stats in self.results.items():
            probabilities[team_id] = {
                "division_winner": stats["division_winner"] / self.simulations_run,
                "playoff_spot": stats["playoff_spot"] / self.simulations_run,
                "league_champion": stats["league_champion"] / self.simulations_run,
                "world_series_winner": stats["world_series_winner"] / self.simulations_run,
            }
        return probabilities

    def _simulate_series(self, team1, team2, games_needed):
        """
        Simulates a playoff series (e.g., Best of 3, 5, 7).
        Returns the winning team dict.
        """
        wins1 = 0
        wins2 = 0
        while wins1 < games_needed and wins2 < games_needed:
            # Home field: Higher seed (better record) usually hosts.
            # Simplified: Random home field or alternating.
            # Ideally: Pass home field info. For now, assume team1 is higher seed/home.
            winner = self.forecasting_model.predict_winner(team1, team2)
            if winner['id'] == team1['id']:
                wins1 += 1
            else:
                wins2 += 1
        
        return team1 if wins1 == games_needed else team2

    def _process_simulation_results(self, sim_teams):
        """
        Determines playoff qualifiers and simulates the full postseason bracket.
        """
        leagues = {"103": {}, "104": {}} # 103: American, 104: National
        
        # Organize teams by League and Division
        for team_id, team in sim_teams.items():
            l_id = str(team.get('league_id'))
            d_id = str(team.get('division_id'))
            if l_id not in leagues: continue
            if d_id not in leagues[l_id]: leagues[l_id][d_id] = []
            leagues[l_id][d_id].append(team)

        league_champs = {}

        # Process each League (AL/NL) independently
        for l_id, divisions in leagues.items():
            div_winners = []
            all_teams_in_league = []
            
            # Determine Division Winners
            for d_id, teams in divisions.items():
                sorted_teams = sorted(teams, key=lambda x: x['w'], reverse=True)
                div_winner = sorted_teams[0]
                div_winners.append(div_winner)
                self.results[div_winner['id']]["division_winner"] += 1
                all_teams_in_league.extend(teams)

            # Determine Wild Cards (Top 3 non-division winners)
            div_winner_ids = {t['id'] for t in div_winners}
            non_winners = [t for t in all_teams_in_league if t['id'] not in div_winner_ids]
            wild_cards = sorted(non_winners, key=lambda x: x['w'], reverse=True)[:3]
            
            # Record Playoff Spots
            playoff_field = div_winners + wild_cards
            for t in playoff_field:
                self.results[t['id']]["playoff_spot"] += 1
                
            # --- SEEDING (1-6) ---
            # Seeds 1-3: Division winners sorted by record
            sorted_div_winners = sorted(div_winners, key=lambda x: x['w'], reverse=True)
            # Seeds 4-6: Wild Cards sorted by record
            sorted_wild_cards = sorted(wild_cards, key=lambda x: x['w'], reverse=True)
            
            seeds = {}
            if len(sorted_div_winners) >= 3:
                seeds[1] = sorted_div_winners[0]
                seeds[2] = sorted_div_winners[1]
                seeds[3] = sorted_div_winners[2]
            else:
                # Handle unexpected data (fewer than 3 divisions)
                continue 
            
            if len(sorted_wild_cards) >= 3:
                seeds[4] = sorted_wild_cards[0]
                seeds[5] = sorted_wild_cards[1]
                seeds[6] = sorted_wild_cards[2]
            else:
                continue

            # --- WILD CARD ROUND (Best of 3) ---
            # 1 and 2 have Byes
            # 3 vs 6
            winner_3v6 = self._simulate_series(seeds[3], seeds[6], 2)
            # 4 vs 5
            winner_4v5 = self._simulate_series(seeds[4], seeds[5], 2)
            
            # --- DIVISION SERIES (Best of 5) ---
            # 1 vs winner_4v5
            winner_lds_1 = self._simulate_series(seeds[1], winner_4v5, 3)
            # 2 vs winner_3v6
            winner_lds_2 = self._simulate_series(seeds[2], winner_3v6, 3)
            
            # --- LEAGUE CHAMPIONSHIP SERIES (Best of 7) ---
            league_champion = self._simulate_series(winner_lds_1, winner_lds_2, 4)
            self.results[league_champion['id']]["league_champion"] += 1
            league_champs[l_id] = league_champion

        # --- WORLD SERIES (Best of 7) ---
        if "103" in league_champs and "104" in league_champs:
            ws_winner = self._simulate_series(league_champs["103"], league_champs["104"], 4)
            self.results[ws_winner['id']]["world_series_winner"] += 1