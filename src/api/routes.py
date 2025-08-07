from fastapi import APIRouter
from src.services.data_service import get_player_data
from src.services.ai_analyzer import analyze_player_performance

router = APIRouter()


@router.get("/analyze/{player_name}")
def analyze_player(player_name: str):
    player_data = get_player_data(player_name)
    if not player_data:
        return {"error": "Player not found"}
    analysis = analyze_player_performance(player_name, player_data)

    return {"player": player_name.title(), "analysis": analysis, "source": "Mock Data, Test"}
