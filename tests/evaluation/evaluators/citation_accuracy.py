"""
Citation Accuracy Evaluator

Validates that json:references blocks in responses match actual queryKB results.
Ensures the agent properly cites sources from the knowledge base.
"""

import json
import re
from typing import Any


class CitationAccuracyEvaluator:
    """
    Evaluates whether citations in responses are accurate and properly formatted.
    
    Returns a score from 0.0 to 1.0:
    - 1.0: All citations are valid and properly formatted
    - 0.0 to <1.0: Some citations are invalid (proportional score)
    """
    
    def __call__(
        self,
        *,
        response: str,
        context: str | None = None,
        expected_sources: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Evaluate if citations in the response are accurate.
        
        Args:
            response: The agent's response
            context: Optional context/KB results to validate against
            expected_sources: Optional list of expected source references
            **kwargs: Additional context (ignored)
            
        Returns:
            dict with 'score', 'reason', and 'details'
        """
        # Extract citations from response
        citations = self._extract_citations(response)
        
        if not citations:
            # Check if response should have citations (mentions facts/data)
            should_cite = self._should_have_citations(response)
            
            if should_cite:
                return {
                    "score": 0.5,
                    "reason": "Response contains factual claims but no citations",
                    "details": {
                        "citations_found": 0,
                        "should_have_citations": True,
                    }
                }
            else:
                return {
                    "score": 1.0,
                    "reason": "No citations needed for this response type",
                    "details": {
                        "citations_found": 0,
                        "should_have_citations": False,
                    }
                }
        
        # Validate citation format
        valid_citations: list[dict[str, Any]] = []
        invalid_citations: list[dict[str, Any]] = []
        issues: list[str] = []
        
        for citation in citations:
            validation = self._validate_citation(citation, context, expected_sources)
            if validation["valid"]:
                valid_citations.append(citation)
            else:
                invalid_citations.append(citation)
                issues.append(validation["reason"])
        
        total = len(valid_citations) + len(invalid_citations)
        score = len(valid_citations) / total if total > 0 else 1.0
        
        if score == 1.0:
            return {
                "score": 1.0,
                "reason": f"All {len(valid_citations)} citations are valid",
                "details": {
                    "citations_found": total,
                    "valid_citations": len(valid_citations),
                    "invalid_citations": 0,
                }
            }
        else:
            return {
                "score": score,
                "reason": f"Some citations invalid: {'; '.join(issues)}",
                "details": {
                    "citations_found": total,
                    "valid_citations": len(valid_citations),
                    "invalid_citations": len(invalid_citations),
                    "issues": issues,
                }
            }
    
    def _extract_citations(self, response: str) -> list[dict[str, Any]]:
        """Extract json:references blocks from response."""
        citations: list[dict[str, Any]] = []
        
        # Pattern for json:references blocks
        patterns = [
            r'```json:references\s*(.*?)```',
            r'\[json:references\](.*?)\[/json:references\]',
            r'"references":\s*\[(.*?)\]',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse as JSON array
                    if match.strip().startswith('['):
                        parsed = json.loads(match)
                    else:
                        parsed = json.loads(f'[{match}]')
                    
                    if isinstance(parsed, list):
                        citations.extend(parsed)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return citations
    
    def _should_have_citations(self, response: str) -> bool:
        """Determine if response contains claims that should be cited."""
        # Keywords that suggest factual claims requiring citation
        factual_patterns = [
            r'\$\d+',  # Dollar amounts
            r'\d+\s*(?:days?|weeks?|months?)',  # Time periods
            r'requires?\s+(?:a\s+)?permit',  # Permit requirements
            r'fee\s+(?:is|of)',  # Fee information
            r'according\s+to',  # Direct claims
            r'as\s+of\s+\d{4}',  # Date-specific info
            r'rate\s+(?:is|of)',  # Rate information
            r'rebate\s+(?:of|up\s+to)',  # Rebate amounts
        ]
        
        for pattern in factual_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_citation(
        self,
        citation: dict[str, Any],
        context: str | None,
        expected_sources: list[str] | None,
    ) -> dict[str, Any]:
        """Validate a single citation."""
        # Check required fields
        required_fields = ["source", "title"]
        missing_fields = [f for f in required_fields if f not in citation]
        
        if missing_fields:
            return {
                "valid": False,
                "reason": f"Citation missing required fields: {missing_fields}"
            }
        
        source = citation.get("source", "")
        title = citation.get("title", "")
        
        # Validate source is not empty
        if not source or not title:
            return {
                "valid": False,
                "reason": "Citation has empty source or title"
            }
        
        # If expected sources provided, check if citation matches
        if expected_sources:
            source_lower = source.lower()
            matched = any(
                exp.lower() in source_lower or source_lower in exp.lower()
                for exp in expected_sources
            )
            if not matched:
                return {
                    "valid": False,
                    "reason": f"Citation source '{source}' not in expected sources"
                }
        
        # If context provided, check if citation content exists in context
        if context:
            # Check if key parts of the citation appear in context
            content = citation.get("content", citation.get("excerpt", ""))
            if content and content not in context and title.lower() not in context.lower():
                return {
                    "valid": False,
                    "reason": f"Citation content not found in KB context"
                }
        
        return {"valid": True, "reason": "Citation is valid"}
