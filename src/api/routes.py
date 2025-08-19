from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
from datetime import datetime

from src.services.data_service import MLBDataService
from src.services.ai_analyzer import BaseballAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()

mlb_service = MLBDataService()
analyzer = BaseballAnalyzer()


@router.get("/analyze/{player_name}")
def analyze_player(
    player_name: str,
    season: Optional[int] = Query(None, description="Specific season to analyze"),
    include_recent: bool = Query(True, description="Include recent games in analysis"),
):
    """
    Analyze a player's performance with real MLB data

    Args:
        player_name: Player's name (e.g., "Mike Trout", "Shohei Ohtani")
        season: Optional specific season year
        include_recent: Whether to include recent games in analysis
    """
    try:
        if not player_name or len(player_name.strip()) < 2:
            raise HTTPException(
                status_code=400, detail="Player name must be at least 2 characters long"
            )

        cleaned_name = player_name.strip().title()

        logger.info(f"Analyzing player: {cleaned_name}")
        player_data = mlb_service.get_player_data(cleaned_name)

        if not player_data:

            similar_players = mlb_service.search_players(cleaned_name)
            suggestions = [p.get("fullName", "") for p in similar_players[:3]]

            error_details = {
                "error": "Player not found",
                "searched_name": cleaned_name,
                "suggestions": suggestions if suggestions else "No similar players found",
                "tip": "Try searching for a similar player or check for typos",
            }
            return HTTPException(status_code=404, detail=error_details)

        logger.info(f"Generating AI analysis for: {cleaned_name}")
        analysis = analyzer._analyze_player_performance(cleaned_name, player_data)

        response_data = {
            "player": cleaned_name,
            "analysis": analysis,
            "player_info": player_data.get("playerInfo", {}),
            "data_source": "MLB API",
            "last_updated": player_data.get("last_updated"),
            "query_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if include_recent:
            response_data["recent_performance"] = {
                "summary": player_data.get("recent_games"),
                "season_stats": player_data.get("season_stats"),
                "advanced_metrics": player_data.get("advanced"),
            }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error analyzing {player_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Unable to analyze player at this time",
                "player": player_name,
            },
        )


@router.get("/search/{query}")
def search_players(query: str, limit: int = Query(5, ge=1, le=20)):
    """
    Search for players by name

    Args:
        query: Search query
        limit: Maximum number of results to return
    """
    try:
        if len(query.strip()) < 2:
            raise HTTPException(
                status_code=400, detail="Search query must be at least 2 characters long"
            )

        players = mlb_service.search_players(query)

        results = []
        for player in players[:limit]:
            results.append(
                {
                    "id": player.get("id"),
                    "full_name": player.get("fullName"),
                    "position": player.get("primaryPosition", {}).get("abbreviation"),
                    "team": player.get("currentTeam", {}).get("name"),
                    "active": player.get("active", "Player is not active"),
                }
            )

        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching for {query}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Unable to search for players at this time",
                "query": query,
            },
        )


@router.get("/player/{player1}/{player2}")
def compare_players(
    player1: str,
    player2: str,
    stat_focus: str = Query(
        "batting", description="Statistic to focus on (batting, pitching or both)"
    ),
):
    """
    Compare two players' performance

    Args:
        player1: First player's name
        player2: Second player's name
        stat_focus: Which stats to focus on in comparison
    """
    try:

        first_player_data = mlb_service.get_player_data(player1)
        second_player_data = mlb_service.get_player_data(player2)

        if not first_player_data:
            raise HTTPException(status_code=404, detail=f"Player {player1} not found")

        if not second_player_data:
            raise HTTPException(status_code=404, detail=f"Player {player2} not found")
        comparison_prompt = f"""
        Compare these two players:
        
        Player 1: {player1.title()}
        {first_player_data.get('season_stats', 'Stats unavailable')}
        Recent: {first_player_data.get('recent_games', 'No recent data')}
        Advanced: {first_player_data.get('advanced', 'No advanced metrics')}
        
        Player 2: {player2.title()}
        {second_player_data.get('season_stats', 'Stats unavailable')}
        Recent: {second_player_data.get('recent_games', 'No recent data')}
        Advanced: {second_player_data.get('advanced', 'No advanced metrics')}
        """

        comparison_analysis = analyzer._analyze_player_performance(
            f"{player1.title()} vs {player2.title()}", {"comparison_data": comparison_prompt}
        )

        return {
            "comparison": f"{player1.title()} vs {player2.title()}",
            "analysis": comparison_analysis,
            "first_player_info": first_player_data.get("player_info", {}),
            "second_player_info": second_player_data.get("player_info", {}),
            "data_source": "MLB API",
            "comparison_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error comparing {player1} and {player2}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Unable to compare players at this time",
                "players": f"{player1} and {player2}",
            },
        )


@router.get("/team/{team_name}/roster")
def get_team_roster(team_name: str):
    """
    Get a team's currentroster

    Args:
        team_name: Team's name
    """
    try:
        roster = mlb_service.get_team_roster(team_name)

        if not roster:
            raise HTTPException(status_code=404, detail=f"Team {team_name} not found")

        return {
            "team": team_name.title(),
            "roster": roster,
            "roster_size": len(roster),
            "data_source": "MLB Official Stats API",
            "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting {team_name} roster: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Unable to get team roster at this time",
                "team": team_name,
            },
        )


@router.get("/health")
def health_check():
    """
    Check the health of the API
    """
    try:
        test_result = mlb_service.search_players("test")

        return {
            "status": "healthy",
            "mlb_api_status": "connected",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "mlb_api_status": "disconnected",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e),
            },
        )


@router.get("/")
def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "MLB Player Analysis API",
        "description": "Get instant, AI-powered analysis of MLB player performance",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze/{player_name} - Get AI analysis of a player",
            "search": "/search/{query} - Search for players",
            "compare": "/compare/{player1}/{player2} - Compare two players",
            "roster": "/team/{team_name}/roster - Get team roster",
            "health": "/health - API health check",
        },
        "data_source": "MLB Official Stats API",
        "powered_by": "OpenAI GPT-4",
    }
