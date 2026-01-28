"""
Agency Boundary Evaluator

Validates that agent responses stay within the scope of supported agencies:
- LADBS (Los Angeles Department of Building and Safety)
- LADWP (Los Angeles Department of Water and Power)
- LASAN (LA Sanitation & Environment)

The agent should not discuss out-of-scope agencies like DMV, courts, or federal agencies.
"""

import re
from typing import Any


# Agencies that are IN SCOPE for the CSP Agent
IN_SCOPE_AGENCIES = {
    "ladbs", "ladwp", "lasan",
    "los angeles department of building and safety",
    "los angeles department of water and power", 
    "la sanitation",
    "la sanitation & environment",
    "building and safety",
    "water and power",
    "sanitation",
}

# Agencies and topics that are OUT OF SCOPE
OUT_OF_SCOPE_PATTERNS = [
    r"\bdmv\b",
    r"\bdriver'?s?\s*license\b",
    r"\bmotor\s*vehicle\b",
    r"\bfederal\s+(?:tax|agency|government)\b",
    r"\birs\b",
    r"\bfbi\b",
    r"\bcourts?\b",
    r"\bjudge\b",
    r"\battorney\b",
    r"\blawyer\b",
    r"\bimmigration\b",
    r"\bpassport\b",
    r"\bsocial\s*security\b",
    r"\bmedicare\b",
    r"\bmedicaid\b",
    r"\bunemployment\s*(?:insurance|benefits)\b",
    r"\bwelfare\b",
    r"\bsnap\b",
    r"\bfood\s*stamps\b",
]

# Redirect phrases indicate proper handling of out-of-scope requests
REDIRECT_PATTERNS = [
    r"i\s+(?:can'?t|cannot|am\s+not\s+able\s+to)\s+help\s+with",
    r"(?:this|that)\s+is\s+(?:not|outside)\s+(?:within\s+)?(?:my|the)\s+scope",
    r"i\s+specialize\s+in",
    r"please\s+contact",
    r"you\s+(?:should|may\s+want\s+to)\s+contact",
    r"for\s+(?:this|that),?\s+(?:please\s+)?contact",
    r"outside\s+(?:my|the)\s+(?:scope|area)",
    r"not\s+(?:one\s+of\s+)?the\s+agencies\s+i\s+(?:support|cover)",
]


class AgencyBoundaryEvaluator:
    """
    Evaluates whether agent responses stay within the scope of supported agencies.
    
    Returns a score from 0.0 to 1.0:
    - 1.0: Response properly stays in scope or correctly redirects out-of-scope requests
    - 0.0: Response discusses out-of-scope topics without proper redirection
    """
    
    def __init__(self) -> None:
        self.out_of_scope_re = [re.compile(p, re.IGNORECASE) for p in OUT_OF_SCOPE_PATTERNS]
        self.redirect_re = [re.compile(p, re.IGNORECASE) for p in REDIRECT_PATTERNS]
    
    def __call__(
        self,
        *,
        query: str,
        response: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Evaluate if the response stays within agency boundaries.
        
        Args:
            query: The user's original query
            response: The agent's response
            **kwargs: Additional context (ignored)
            
        Returns:
            dict with 'score', 'reason', and 'details'
        """
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Check if the query is asking about out-of-scope topics
        query_is_out_of_scope = self._contains_out_of_scope(query_lower)
        
        # Check if the response mentions out-of-scope agencies
        response_mentions_out_of_scope = self._contains_out_of_scope(response_lower)
        
        # Check if the response properly redirects
        response_redirects = self._contains_redirect(response_lower)
        
        # Scoring logic
        if query_is_out_of_scope:
            # For out-of-scope queries, the agent should redirect
            if response_redirects:
                return {
                    "score": 1.0,
                    "reason": "Correctly redirected out-of-scope request",
                    "details": {
                        "query_out_of_scope": True,
                        "properly_redirected": True,
                    }
                }
            elif response_mentions_out_of_scope and not response_redirects:
                return {
                    "score": 0.0,
                    "reason": "Discussed out-of-scope topic without redirecting",
                    "details": {
                        "query_out_of_scope": True,
                        "properly_redirected": False,
                    }
                }
            else:
                # Might be declining without explicit redirect - partial credit
                return {
                    "score": 0.5,
                    "reason": "Unclear handling of out-of-scope request",
                    "details": {
                        "query_out_of_scope": True,
                        "properly_redirected": False,
                    }
                }
        else:
            # For in-scope queries, response should stay in scope
            if response_mentions_out_of_scope:
                return {
                    "score": 0.5,
                    "reason": "Response mentioned out-of-scope agencies for in-scope query",
                    "details": {
                        "query_out_of_scope": False,
                        "response_stayed_in_scope": False,
                    }
                }
            else:
                return {
                    "score": 1.0,
                    "reason": "Response properly stayed within agency scope",
                    "details": {
                        "query_out_of_scope": False,
                        "response_stayed_in_scope": True,
                    }
                }
    
    def _contains_out_of_scope(self, text: str) -> bool:
        """Check if text contains out-of-scope agency/topic mentions."""
        for pattern in self.out_of_scope_re:
            if pattern.search(text):
                return True
        return False
    
    def _contains_redirect(self, text: str) -> bool:
        """Check if text contains proper redirect phrases."""
        for pattern in self.redirect_re:
            if pattern.search(text):
                return True
        return False
