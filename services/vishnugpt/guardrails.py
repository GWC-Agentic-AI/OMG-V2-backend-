"""
app/services/guardrails.py - Input validation and safety checks
"""
from typing import Tuple


class GuardrailService:
    """Service for validating user input and applying safety rules"""
    
    # Forbidden phrases that indicate prompt injection attempts
    FORBIDDEN_PHRASES = [
        "ignore previous",
        "ignore all previous",
        "system prompt",
        "reset instructions",
        "developer mode",
        "admin mode",
        "bypass",
        "jailbreak",
        "pretend you are",
        "act as if",
        "forget everything",
        "disregard",
        "override"
    ]
    
    # Maximum allowed query length
    MAX_QUERY_LENGTH = 2000
    
    @staticmethod
    def validate_query(query: str) -> Tuple[bool, str]:
        """
        Validate user query against safety rules
        
        Args:
            query: User's input query
            
        Returns:
            Tuple of (is_valid, error_message)
            If valid: (True, "")
            If invalid: (False, "error description")
        """
        # Check if empty
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        # Check length
        if len(query) > GuardrailService.MAX_QUERY_LENGTH:
            return False, f"Query too long. Maximum {GuardrailService.MAX_QUERY_LENGTH} characters allowed"
        
        # Check for prompt injection attempts
        query_lower = query.lower()
        for phrase in GuardrailService.FORBIDDEN_PHRASES:
            if phrase in query_lower:
                return False, "Query contains forbidden content"
        
        return True, ""
    
    @staticmethod
    def get_rejection_message() -> str:
        """Standard message when query is rejected"""
        return "Beloved one, let us remain focused on the path of Dharma. How can I guide your soul today?"


# Singleton instance
guardrail_service = GuardrailService()