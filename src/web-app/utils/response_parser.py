"""Utility functions for parsing agent responses.

These functions extract structured data from agent responses including:
- Plan update signals (<<PLAN_UPDATED:project-id>>)
- Plan JSON blocks (json:plan)
- Action cards (json:action)
- References (json:references)
"""

import re
import json
from typing import Optional


def extract_plan_updated_signal(response_text: str) -> tuple[str, bool]:
    """Extract plan update signal from response.
    
    Looks for <<PLAN_UPDATED>> pattern.
    
    Args:
        response_text: The raw agent response text
        
    Returns:
        Tuple of (cleaned_text, signal_found) where:
        - cleaned_text: Response with signal replaced by visual indicator
        - signal_found: True if the signal was found, False otherwise
        
    Examples:
        >>> extract_plan_updated_signal("Plan created!\\n<<PLAN_UPDATED>>")
        ('Plan created!\\n\\n📋 *Plan updated*', True)
        
        >>> extract_plan_updated_signal("Just some info")
        ('Just some info', False)
    """
    pattern = r'<<PLAN_UPDATED>>'
    match = re.search(pattern, response_text)
    
    if match:
        # Replace the signal with a visual indicator
        cleaned_text = re.sub(pattern, '\n\n📋 *Plan updated*\n\n', response_text)
        return cleaned_text.strip(), True
    
    return response_text, False


def has_plan_updated_signal(response_text: str) -> bool:
    """Check if response contains a PLAN_UPDATED signal.
    
    Convenience function that returns True if signal found.
    
    Args:
        response_text: The raw agent response text
        
    Returns:
        True if signal found, False otherwise
    """
    _, found = extract_plan_updated_signal(response_text)
    return found


def has_embedded_plan_json(response_text: str) -> bool:
    """Check if response contains embedded json:plan block.
    
    The agent should NOT embed plan JSON in responses - it should use
    MCP tools instead. This function detects the anti-pattern.
    
    Args:
        response_text: The raw agent response text
        
    Returns:
        True if json:plan block is found (BAD), False otherwise (GOOD)
    """
    pattern = re.compile(r'```json:plan', re.IGNORECASE)
    return pattern.search(response_text) is not None


def detect_verbose_patterns(response_text: str) -> list[str]:
    """Detect verbose phrases that the agent should avoid.
    
    Returns a list of matched verbose patterns found in the response.
    Empty list means the response is appropriately concise.
    
    Args:
        response_text: The agent response text
        
    Returns:
        List of matched verbose phrases
    """
    verbose_patterns = [
        r"let me (?:look|search|research|check|find)",
        r"i'?ll (?:look|search|research|check|find) that",
        r"i'?m going to (?:search|research|look)",
        r"give me a moment",
        r"searching (?:for|the)",
        r"querying the knowledge base",
        r"great question!?",
        r"i'?d be happy to help",
        r"absolutely!",
        r"that's a (?:great|wonderful|good) (?:question|goal)",
    ]
    
    matches = []
    response_lower = response_text.lower()
    
    for pattern in verbose_patterns:
        if re.search(pattern, response_lower):
            match = re.search(pattern, response_lower)
            if match:
                matches.append(match.group(0))
    
    return matches
