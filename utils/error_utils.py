import logging

logger = logging.getLogger(__name__)

def format_llm_error(e: Exception) -> str:
    """Format exceptions into user-friendly messages without exposing raw JSON/traces."""
    return parse_llm_response(str(e))

def parse_llm_response(response_text: str) -> str:
    """Parse string response to catch inline API errors returned by the agent framework."""
    error_str = response_text.lower()
    
    if "rate_limit_exceeded" in error_str or "rate limit" in error_str or "429" in error_str:
        return "⚠️ The AI service has temporarily reached its daily usage limit. Please try again later or use a different API key."
    elif "authentication" in error_str or "api_key" in error_str or "401" in error_str or "api key" in error_str:
        return "⚠️ AI service authentication failed. Please verify the API key."
    elif "connection" in error_str or "timeout" in error_str or "network" in error_str or "connect" in error_str:
        return "⚠️ Unable to connect to the AI service. Please try again."
        
    if "error" in error_str and "message" in error_str and "{" in error_str:
        return "⚠️ An unexpected API error occurred. Please try again later."
        
    return response_text

