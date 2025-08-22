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

        prompt = f"""
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
                    
            except Exception as e:
                logger.error(f"Unexpected error in AI response (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries:
                    return "Analysis service error - please try again later"
        
        return "Unable to generate analysis after multiple attempts"

    def _extract_player_names(self, question: str, data_service) -> list:
        """
        Extract and validate player names from the question using MLB search API
        
        Args:
            question: User's question text
            data_service: MLBDataService instance for validation
            
        Returns:
            List of confirmed player names
        """
        import re
        
        # Method 1: Try to find obvious name patterns (capitalized words)
        name_matches = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', question)
        potential_names = [name.strip() for name in name_matches]
        
        # Method 2: For lowercase questions, check adjacent word pairs
        words = question.split()
        for i in range(len(words) - 1):
            # Check two-word combinations
            name_candidate = f"{words[i]} {words[i+1]}".title()
            if name_candidate not in potential_names:
                potential_names.append(name_candidate)
            
            # Check three-word combinations (for names like "Vladimir Guerrero Jr")
            if i < len(words) - 2:
                three_word_name = f"{words[i]} {words[i+1]} {words[i+2]}".title()
                if three_word_name not in potential_names:
                    potential_names.append(three_word_name)
        
        # Validate each potential name with MLB search API
        confirmed_players = []
        for name in potential_names:
            # Skip common non-name words
            if name.lower() in ['home runs', 'batting average', 'runs batted', 'how many', 'what is', 'who has']:
                continue
                
            try:
                search_results = data_service.search_players(name)
                if search_results:  # If MLB API finds results, it's a real player
                    confirmed_players.append(name)
                    if len(confirmed_players) >= 2:  # Limit to 2 players max
                        break
            except Exception as e:
                logger.warning(f"Error searching for player '{name}': {e}")
                continue
        
        return confirmed_players

    def _answer_baseball_question(self, question: str) -> str:
        """
        Answer natural language questions about baseball players by:
        1. Parsing the question to extract player names and requested stats
        2. Fetching relevant player data 
        3. Providing a direct answer
        """
        try:
            # Import here to avoid circular imports
            from src.services.data_service import MLBDataService
            import re
            
            data_service = MLBDataService()
            
            # Extract player names using our new dynamic method
            found_players = self._extract_player_names(question, data_service)
            
            if not found_players:
                return "I couldn't identify any player names in your question. Please mention a specific player name (e.g., 'aaron judge', 'Mike Trout', 'shohei ohtani')."
            
            # Fetch data for the identified players
            player_data = {}
            for player_name in found_players:
                data = data_service.get_player_data(player_name)
                if data:
                    player_data[player_name] = data
            
            if not player_data:
                return f"I couldn't find current data for: {', '.join(found_players)}. They might not be active players or the name might need adjustment."
            
            # Provide direct answers with extracted stats
            question_lower = question.lower()
            
            if len(player_data) == 1:
                player_name = list(player_data.keys())[0]
                data = player_data[player_name]
                season_stats = data.get('season_stats', 'N/A')
                
                # Extract specific stats based on question keywords
                if any(keyword in question_lower for keyword in ['hr', 'home run', 'homer']):
                    # Extract HR count from season stats
                    import re
                    hr_match = re.search(r'(\d+) HR', season_stats)
                    if hr_match:
                        hr_count = hr_match.group(1)
                        return f"{player_name} has {hr_count} home runs this season (2025). Full stats: {season_stats}"
                
                elif any(keyword in question_lower for keyword in ['avg', 'average', 'batting']):
                    avg_match = re.search(r'(\.\d+) avg', season_stats)
                    if avg_match:
                        avg = avg_match.group(1)
                        return f"{player_name} is batting {avg} this season. Full stats: {season_stats}"
                
                elif any(keyword in question_lower for keyword in ['rbi', 'runs batted in', 'runs batted']):
                    rbi_match = re.search(r'(\d+) RBI', season_stats)
                    if rbi_match:
                        rbi = rbi_match.group(1)
                        return f"{player_name} has {rbi} RBIs this season. Full stats: {season_stats}"
                
                # Default response with all stats
                return f"Here are {player_name}'s current stats: {season_stats}. Recent performance: {data.get('recent_games', 'N/A')}"
            
            else:
                # Multiple players - provide comparison
                result = "Here are the stats for the players mentioned:\n\n"
                for player_name, data in player_data.items():
                    result += f"{player_name}: {data.get('season_stats', 'N/A')}\n"
                return result
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"I encountered an error trying to answer your question: {str(e)}"

    def _generate_fallback_analysis(self, player_name: str) -> str:
        """Generate fallback analysis when data is insufficient"""
        return f"Unable to provide detailed analysis for {player_name} due to insufficient data. Please try again later."
    
    def _generate_error_analysis(self, player_name: str, error: str) -> str:
        """Generate error analysis when something goes wrong"""
        return f"Error analyzing {player_name}: {error}. Please try again or contact support if the issue persists."
