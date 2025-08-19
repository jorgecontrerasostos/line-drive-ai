import openai
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any
from datetime import datetime

load_dotenv()

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")


class BaseballAnalyzer:
    def __init__(self):
        self.model = "gpt-4o"
        self.temperature = 0.7
        self.max_tokens = 300
        self.max_retries = 2

    def _analyze_player_performance(self, player_name: str, player_data: Dict[str, Any]) -> str:
        """
        Generate comprehensive AI analysis of player performance

        Args:
            player_name: Player's name
            player_data: Structured player data from MLB API

        Returns:
            AI-generated analysis string
        """
        try:
            if not self._validate_player_data(player_data):
                return self._generate_fallback_analysis(player_name)

            prompt = self._create_analysis_prompt(player_name, player_data)

            analysis = self._get_ai_response(prompt)

            if not analysis or len(analysis.strip()) < 50:
                return self._generate_fallback_analysis(player_name)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing player {player_name}: {str(e)}")
            return self._generate_error_analysis(player_name, str(e))

    def _validate_player_data(self, player_data: Dict[str, Any]) -> bool:
        if not isinstance(player_data, dict):
            return False

        if "comparison_data" in player_data:
            return True

        required_fields = ["recent_games", "season_stats", "context", "advanced"]
        return any(field in player_data for field in required_fields)

    def _create_analysis_prompt(self, player_name: str, player_data: Dict[str, Any]) -> str:
        """
        Create structured prompt for AI analysis

        Args:
            player_name: Player's name
            player_data: Structured player data from MLB API
        """
        if "comparison_data" in player_data:
            return self._create_comparison_prompt(player_data["comparison_data"])

        current_date = datetime.now().strftime("%B %Y")

        prompt = """
        You are a professional baseball analyst with expertise in modern analytics and player evaluation. Analyze this player's current performance:

        Player: {player_name.title()}
        Date: {current_date}

        PERFORMANCE DATA:
        Recent Games: {player_data.get('recent_games', 'No recent data available')}
        Season Stats: {player_data.get('season_stats', 'Season stats unavailable')}
        Context: {player_data.get('context', 'No additional context')}
        Advanced Metrics: {player_data.get('advanced', 'Advanced metrics unavailable')}

        PLAYER INFO:
        Position: {player_data.get('player_info', {}).get('position', 'N/A')}
        Team: {player_data.get('player_info', {}).get('team', 'N/A')}
        Age: {player_data.get('player_info', {}).get('age', 'N/A')}

        ANALYSIS REQUIREMENTS:
        Provide a comprehensive analysis covering:

        1. **Current Form Assessment**: Evaluate recent performance trends and hot/cold streaks
        2. **Season Performance**: How they're performing relative to expectations and career norms
        3. **Strengths & Concerns**: Key positive trends and areas of worry
        4. **Fantasy/Betting Insights**: Actionable insights for fantasy players and sports bettors
        5. **Key Takeaway**: One-sentence bottom line assessment

        IMPORTANT GUIDELINES:
        - Use specific statistical context when available
        - Compare to league averages where relevant (league avg batting ~.248, ERA ~4.00)
        - Consider position and age context
        - Be engaging but analytically rigorous
        - Keep total response under 300 words
        - Focus on actionable insights

        Provide your analysis now:
        """
        return prompt

    def _create_comparison_prompt(self, comparison_data: str) -> str:
        """Create prompt for player comparison analysis"""
        return f"""
                You are a professional baseball analyst. Provide a detailed comparison analysis:

                {comparison_data}

                COMPARISON ANALYSIS REQUIREMENTS:
                1. **Head-to-Head Stats**: Direct statistical comparison
                2. **Strengths of Each Player**: What each player does better
                3. **Current Form**: Who's performing better recently
                4. **Context Considerations**: Age, team, position factors
                5. **Bottom Line**: Which player you'd prefer and why

                Keep analysis under 250 words and focus on practical insights for fantasy and betting decisions.
                """

    def _get_ai_response(self, prompt: str) -> str:
        """Get AI response with error handling and retries"""
        for attempt in range(self.max_retries + 1):
            try:
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                content = response.choices[0].message.content.strip()

                if content and len(content) > 50:
                    return content
                else:
                    logger.warning(f"Short AI response received (attempt {attempt + 1})")

            except openai.AuthenticationError:
                logger.error("OpenAI authentication failed")
                return "Analysis service authentication error - please check API configuration"

            except openai.RateLimitError:
                logger.warning(f"Rate limit hit (attempt {attempt + 1})")
                if attempt == self.max_retries:
                    return "Analysis service temporarily busy - please try again in a moment"
