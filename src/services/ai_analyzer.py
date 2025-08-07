import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def analyze_player_performance(player_name: str, player_data: dict) -> str:
    prompt = f"""
    You are a professional baseball analyst. Analyze this player's current performance:
    
    Player: {player_name.title()}
    Recent Performance: {player_data['recent_games']}
    Season Stats: {player_data['season_stats']}
    Context: {player_data['context']}
    Advanced Metrics: {player_data['advanced']}
    
    Provide a concise analysis covering:
    1. Current form and trends
    2. Strengths and areas of concern  
    3. How they compare to their typical performance
    4. Key takeaways for fantasy/betting consideration
    
    Keep it under 200 words and make it engaging.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error analyzing player performance: {e}")
        return f"Error analyzing {player_name.title()}: {str(e)}"
