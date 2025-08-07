import statsapi
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import re

# Set up logging
logger = logging.getLogger(__name__)


class MLBDataService:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)

    def get_player_data(self, player_name: str) -> Optional[Dict]:
        try:
            cache_key = f"player_{player_name.lower().strip()}"
            if self.is_cached_and_fresh(cache_key):
                return self.cache[cache_key]["data"]

            player_id = self._get_player_id(player_name)
            if not player_id:
                logger.warning(f"Player not found: {player_name}")
                return None

            player_data = self._fetch_player_stats(player_id)
            if not player_data:
                logger.warning(f"No stats found for {player_name}")
                return None

            formatted_data = self._format_player_data(player_data, player_name)

            self.cache[cache_key] = {"data": formatted_data, "timestamp": datetime.now()}
            return formatted_data
        except Exception as e:
            logger.error(f"Error fetching {player_name} data: {e}")
            return None

    def _get_player_id(self, player_name: str) -> Optional[int]:
        try:
            players = statsapi.lookup_player(player_name)
            if players:
                return players[0]["id"]

            variations = self._generate_name_variations(player_name)
            for variation in variations:
                players = statsapi.lookup_player(variation)
                if players:
                    return players[0]["id"]
            return None
        except Exception as e:
            logger.error(f"Error looking up {player_name} data: {e}")
            return None

    def _generate_name_variations(self, player_name: str) -> List[str]:
        variations = []
        player_name = player_name.lower().strip()

        variations.append(player_name.replace("jr", "").replace("Jr", ""))

        name_parts = player_name.split()
        if len(name_parts) > 1:
            variations.append(f"{name_parts[0]} {name_parts[-1]}")

        if len(name_parts) == 2:
            variations.append(f"{name_parts[1]} {name_parts[0]}")

        return list(set(variations))

    def _fetch_player_stats(self, player_id: int) -> Optional[Dict]:
        try:
            # Get current season stats
            season_stats = statsapi.player_stat_data(
                player_id, group="hitting,pitching,fielding", type="season"
            )

            # Get recent game log (last 15 games)
            try:
                game_log = statsapi.player_stat_data(
                    player_id, group="hitting,pitching", type="gameLog"
                )
            except:
                game_log = None

            # Get player info
            player_info = statsapi.lookup_player("", player_id)

            return {
                "season_stats": season_stats,
                "game_log": game_log,
                "player_info": player_info[0] if player_info else None,
            }

        except Exception as e:
            logger.error(f"Error fetching stats for player ID {player_id}: {e}")
            return None

    def _format_player_data(self, raw_data: Dict, player_name: str) -> Dict:
        try:
            season_stats = raw_data.get("season_stats", {})
            game_log = raw_data.get("game_log", {})
            player_info = raw_data.get("player_info", {})

            hitting_season = season_stats.get("hitting", {}).get("season", {})
            hitting_recent = self._extract.recent_performance(game_log)

            pitching_season = season_stats.get("pitching", {}).get("season", {})

            is_pitcher = bool(pitching_season.get("games_pitched", 0) > 0)

            formatted_data = {
                "recent_games": self._format_recent_games(hitting_recent, is_pitcher),
                "season_stats": self._format_season_stats(
                    hitting_season, pitching_season, is_pitcher
                ),
                "context": self._generate_context(player_info, hitting_season, pitching_season),
                "advanced": self._format_advanced_metrics(
                    hitting_season, hitting_recent, is_pitcher
                ),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "player_info": {
                    "position": player_info.get("primaryPosition", {}).get("abbreviation", "N/A"),
                    "team": player_info.get("primaryPosition", {}).get("name", "N/A"),
                    "age": self._calculate_age(player_info.get("birthDate", "")),
                },
            }

            return formatted_data

        except Exception as e:
            logger.error(f"Error formatting data for {player_name}: {e}")

            return {
                "recent_games": "Recent performance data unavailable",
                "season_stats": "Season statistics unavailable",
                "context": "Player context unavailable",
                "advanced": "Advanced metrics unavailable",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "player_info": {"position": "N/A", "team": "N/A", "age": "N/A"},
            }

    def _extract_recent_performance(self, game_log: Optional[Dict]) -> Dict:
        if not game_log or "hitting" not in game_log:
            return {}

        try:
            recent_games = game_log["hitting"]["gameLog"][:15]
            if not recent_games:
                return {}

            total_ab = sum(game.get("atBats", 0) for game in recent_games)
            total_hits = sum(game.get("hits", 0) for game in recent_games)
            total_hr = sum(game.get("homeRuns", 0) for game in recent_games)
            total_rbi = sum(game.get("runsBattedIn", 0) for game in recent_games)

            avg = round(total_hits / total_ab, 3) if total_ab > 0 else 0

            return {
                "games": len(recent_games),
                "avg": avg,
                "hr": total_hr,
                "rbi": total_rbi,
                "hits": total_hits,
                "ab": total_ab,
            }
        except Exception as e:
            logger.error(f"Error extracting recent performance: {e}")

    def _format_recent_games(self, recent_data: Dict, is_pitcher: bool) -> str:
        if not recent_data:
            return "No recent games data available"

        games = recent_data.get("games", 0)

        if games == 0:
            return "No recent games data available"

        if is_pitcher:
            return "Player is a pitcher, no recent games data available"
        else:
            avg = recent_data.get("avg", 0)
            hr = recent_data.get("hr", 0)
            rbi = recent_data.get("rbi", 0)
            hits = recent_data.get("hits", 0)
            ab = recent_data.get("ab", 0)

            return f"Last {games} games: .{int(avg*1000):03d} avg, {hr} HR, {rbi} RBI {hits} hits, {ab} AB"

    def _format_season_stats(self, hitting: Dict, pitching: Dict, is_pitcher: bool) -> str:
        current_year = datetime.now().year

        if is_pitcher and pitching:
            wins = pitching.get("wins", 0)
            losses = pitching.get("losses", 0)
            era = round(pitching.get("era", 0), 2)
            innings = round(pitching.get("inningsPitched", 0), 1)
            strikeouts = pitching.get("strikeouts", 0)
            walks = pitching.get("walks", 0)
            hits = pitching.get("hits", 0)
            earned_runs = pitching.get("earnedRuns", 0)

            return f"Season {current_year}: {wins}-{losses}, {era} ERA, {innings} IP, {strikeouts} K, {walks} BB, {hits} H, {earned_runs} ER"

        elif hitting:
            avg = hitting.get("avg", 0)
            hr = hitting.get("homeRuns", 0)
            rbi = hitting.get("rbi", 0)
            games = hitting.get("gamesPlayed", 0)
            return f"{current_year}: .{int(float(avg)*1000):03d} avg, {hr} HR, {rbi} RBI in {games} games"

        return f"{current_year}: Statistics unavailable"

    def _generate_context(self, player_info: Dict, hitting: Dict, pitching: Dict) -> str:
        """Generate contextual information about the player"""
        contexts = []

        # Team info
        team = player_info.get("currentTeam", {}).get("name", "")
        if team:
            contexts.append(f"Currently with {team}")

        # Performance context
        if hitting:
            avg = float(hitting.get("avg", 0))

            # MLB average is .240
            if avg > 0.300:
                contexts.append("Excellent batting average this season")
            elif avg > 0.270:
                contexts.append("Hitting well this season")
            elif avg > 0.240:
                contexts.append("Hitting OK this season")
            elif avg > 0.210:
                contexts.append("Hitting mid-range this season")
            else:
                contexts.append("Struggling at the plate this season")

        # Add more contextual insights based on available data
        if not contexts:
            contexts.append("Active MLB player")

        return ". ".join(contexts)

    def _format_advanced_metrics(self, hitting: Dict, pitching: Dict, is_pitcher: bool) -> str:
        """Format advanced metrics string"""
        metrics = []

        if is_pitcher and pitching:
            whip = pitching.get("whip", 0)
            if whip:
                metrics.append(f"WHIP: {whip:.2f}")

            bb9 = pitching.get("walksPer9Inn", 0)
            if bb9:
                metrics.append(f"BB/9: {bb9:.1f}")

        elif hitting:
            ops = hitting.get("ops", 0)
            if ops:
                metrics.append(f"OPS: {ops:.3f}")

            obp = hitting.get("obp", 0)
            if obp:
                metrics.append(f"OBP: {obp:.3f}")

            slg = hitting.get("slg", 0)
            if slg:
                metrics.append(f"SLG: {slg:.3f}")

        return ", ".join(metrics) if metrics else "Advanced metrics unavailable"

    def _calculate_age(self, birth_date: str) -> str:
        """Calculate player age from birth date"""
        try:
            if not birth_date:
                return "N/A"

            birth = datetime.strptime(birth_date[:10], "%Y-%m-%d")
            today = datetime.now()
            age = today.year - birth.year

            if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
                age -= 1

            return str(age)
        except:
            return "N/A"

    def _is_cached_and_fresh(self, cache_key: str) -> bool:
        """Check if cached data exists and is still fresh"""
        if cache_key not in self.cache:
            return False

        cache_time = self.cache[cache_key]["timestamp"]
        return datetime.now() - cache_time < self.cache_duration

    def get_team_roster(self, team_name: str) -> Optional[List[Dict]]:
        """Get team roster - useful for team-based queries"""
        try:
            teams = statsapi.lookup_team(team_name)
            if not teams:
                return None

            team_id = teams[0]["id"]
            roster = statsapi.roster(team_id)
            return roster

        except Exception as e:
            logger.error(f"Error fetching roster for {team_name}: {e}")
            return None

    def search_players(self, query: str) -> List[Dict]:
        """Search for multiple players - useful for disambiguation"""
        try:
            players = statsapi.lookup_player(query)
            return players[:5]  # Return top 5 matches
        except Exception as e:
            logger.error(f"Error searching players with query '{query}': {e}")
            return []


def get_player_data(player_name: str) -> Optional[Dict]:
    """Legacy function for backward compatibility"""
    service = MLBDataService()
    return service.get_player_data(player_name)
