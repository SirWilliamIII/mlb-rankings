# app/services/bullpen_history_service.py

from datetime import datetime, timedelta
import statsapi


class BullpenHistoryService:
    """
    Tracks reliever usage over the last 3 days to determine availability.

    Fatigue Definitions:
    - Dead: Pitched last 2 consecutive days (modifier: 1.25)
    - Tired: Pitched yesterday with >25 pitches (modifier: 1.15)
    - Fresh: 0 pitches in last 2 days (modifier: 1.0)
    """

    # Fatigue thresholds
    HIGH_PITCH_THRESHOLD = 25  # Pitches that count as "high stress"
    DEAD_MODIFIER = 1.25       # 25% worse outcomes expected
    TIRED_MODIFIER = 1.15      # 15% worse outcomes expected
    FRESH_MODIFIER = 1.0       # Neutral

    def get_team_bullpen_fatigue(self, team_id, lookback_days=3):
        """
        Fetches recent games and calculates fatigue for all pitchers on a team.

        Args:
            team_id: MLB team ID
            lookback_days: Number of days to look back (default 3)

        Returns:
            dict: {pitcher_id: {
                'name': str,
                'status': 'Dead' | 'Tired' | 'Fresh',
                'modifier': float,
                'pitches_3d': int,
                'days_pitched': list[str],
                'consecutive_days': int
            }}
        """
        try:
            # 1. Get date range (yesterday back to lookback_days ago)
            today = datetime.now()
            end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (today - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

            # 2. Fetch schedule for this team
            schedule = statsapi.schedule(
                start_date=start_date,
                end_date=end_date,
                team=team_id
            )

            if not schedule:
                return {}

            # 3. Build pitcher usage logs
            # Structure: {pitcher_id: {'name': str, 'appearances': [{'date': str, 'pitches': int}]}}
            pitcher_logs = {}

            for game in schedule:
                game_pk = game['game_id']
                game_date = game['game_date']

                try:
                    # Get boxscore data for this game
                    box = statsapi.boxscore_data(game_pk)

                    # Determine if team is home or away
                    is_home = (game.get('home_id') == team_id)
                    team_key = 'home' if is_home else 'away'

                    # Get pitcher IDs from boxscore
                    team_data = box.get(team_key, {})
                    pitcher_ids = team_data.get('pitchers', [])
                    players = team_data.get('players', {})

                    for p_id in pitcher_ids:
                        player_key = f'ID{p_id}'
                        player_data = players.get(player_key, {})
                        player_name = player_data.get('person', {}).get('fullName', f'Pitcher {p_id}')

                        # Get pitching stats
                        stats = player_data.get('stats', {}).get('pitching', {})
                        pitches = int(stats.get('numberOfPitches', 0))

                        # Skip if no pitches (didn't actually pitch)
                        if pitches == 0:
                            continue

                        if p_id not in pitcher_logs:
                            pitcher_logs[p_id] = {
                                'name': player_name,
                                'appearances': []
                            }

                        pitcher_logs[p_id]['appearances'].append({
                            'date': game_date,
                            'pitches': pitches
                        })

                except Exception as e:
                    # Log error but continue processing other games
                    print(f"Error fetching boxscore for game {game_pk}: {e}")
                    continue

            # 4. Calculate fatigue metrics for each pitcher
            return self._calculate_fatigue_metrics(pitcher_logs)

        except Exception as e:
            print(f"Error fetching bullpen fatigue for team {team_id}: {e}")
            return {}

    def _calculate_fatigue_metrics(self, pitcher_logs):
        """
        Analyzes pitcher appearance logs and determines fatigue status.

        Args:
            pitcher_logs: {pitcher_id: {'name': str, 'appearances': [{'date': str, 'pitches': int}]}}

        Returns:
            dict: Fatigue report for each pitcher
        """
        today = datetime.now().date()
        yesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        day_before = (today - timedelta(days=2)).strftime('%Y-%m-%d')

        fatigue_report = {}

        for p_id, data in pitcher_logs.items():
            appearances = data['appearances']
            name = data['name']

            # Get unique dates pitched
            dates_pitched = sorted(set(a['date'] for a in appearances), reverse=True)

            # Total pitches in window
            total_pitches = sum(a['pitches'] for a in appearances)

            # Check for consecutive days (yesterday AND day before)
            pitched_yesterday = yesterday in dates_pitched
            pitched_day_before = day_before in dates_pitched
            consecutive_days = 2 if (pitched_yesterday and pitched_day_before) else (1 if pitched_yesterday else 0)

            # Yesterday's pitch count (for "Tired" check)
            yesterday_pitches = sum(
                a['pitches'] for a in appearances
                if a['date'] == yesterday
            )

            # Determine status and modifier
            if consecutive_days >= 2:
                status = 'Dead'
                modifier = self.DEAD_MODIFIER
            elif pitched_yesterday and yesterday_pitches > self.HIGH_PITCH_THRESHOLD:
                status = 'Tired'
                modifier = self.TIRED_MODIFIER
            else:
                status = 'Fresh'
                modifier = self.FRESH_MODIFIER

            fatigue_report[p_id] = {
                'name': name,
                'status': status,
                'modifier': modifier,
                'pitches_3d': total_pitches,
                'days_pitched': dates_pitched,
                'consecutive_days': consecutive_days,
                'yesterday_pitches': yesterday_pitches
            }

        return fatigue_report

    def get_pitcher_modifier(self, pitcher_id, team_id):
        """
        Convenience method to get the fatigue modifier for a specific pitcher.

        Args:
            pitcher_id: MLB player ID
            team_id: MLB team ID

        Returns:
            float: The fatigue modifier (1.0 if unknown/fresh)
        """
        fatigue = self.get_team_bullpen_fatigue(team_id)
        pitcher_data = fatigue.get(pitcher_id, {})
        return pitcher_data.get('modifier', self.FRESH_MODIFIER)

    def print_fatigue_report(self, team_id, team_name=None):
        """
        Prints a formatted fatigue report for a team's bullpen.
        Useful for debugging and verification.
        """
        fatigue = self.get_team_bullpen_fatigue(team_id)

        header = f"Bullpen Fatigue Report: {team_name or f'Team {team_id}'}"
        print(f"\n{'=' * len(header)}")
        print(header)
        print('=' * len(header))

        if not fatigue:
            print("No recent pitching data found.")
            return

        # Sort by status (Dead first, then Tired, then Fresh)
        status_order = {'Dead': 0, 'Tired': 1, 'Fresh': 2}
        sorted_pitchers = sorted(
            fatigue.items(),
            key=lambda x: (status_order.get(x[1]['status'], 3), -x[1]['pitches_3d'])
        )

        for p_id, data in sorted_pitchers:
            status_emoji = {'Dead': '🔴', 'Tired': '🟡', 'Fresh': '🟢'}.get(data['status'], '⚪')
            print(f"{status_emoji} {data['name']:25} | {data['status']:6} | "
                  f"Mod: {data['modifier']:.2f} | "
                  f"3D Pitches: {data['pitches_3d']:3} | "
                  f"Consec Days: {data['consecutive_days']}")
