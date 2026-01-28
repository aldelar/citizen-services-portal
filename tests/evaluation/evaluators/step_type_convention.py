"""
Step Type Convention Evaluator

Validates that plan step IDs follow the CSP naming conventions:
- PRM- : Permit steps
- INS- : Inspection steps
- TRD- : Trade/contractor steps
- APP- : Application steps
- SCH- : Scheduling steps
- ENR- : Enrollment steps
- DOC- : Document steps
- PAY- : Payment steps
"""

import json
import re
from typing import Any


# Valid step type prefixes and their meanings
VALID_PREFIXES = {
    "PRM": "Permit",
    "INS": "Inspection",
    "TRD": "Trade/Contractor",
    "APP": "Application",
    "SCH": "Scheduling",
    "ENR": "Enrollment",
    "DOC": "Document",
    "PAY": "Payment",
    "UTL": "Utility",
    "DSP": "Disposal",
    "REB": "Rebate",
}

# Pattern for valid step IDs: PREFIX-NUMBER
STEP_ID_PATTERN = re.compile(r'^([A-Z]{3})-(\d+)$')


class StepTypeConventionEvaluator:
    """
    Evaluates whether plan step IDs follow naming conventions.
    
    Returns a score from 0.0 to 1.0:
    - 1.0: All step IDs follow conventions
    - 0.0 to <1.0: Some step IDs don't follow conventions (proportional)
    """
    
    def __call__(
        self,
        *,
        response: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Evaluate if plan step IDs follow naming conventions.
        
        Args:
            response: The agent's response (should contain a plan in JSON)
            **kwargs: Additional context (ignored)
            
        Returns:
            dict with 'score', 'reason', and 'details'
        """
        # Try to extract plan from response
        plan = self._extract_plan(response)
        
        if plan is None:
            return {
                "score": 1.0,
                "reason": "No plan found in response (not applicable)",
                "details": {"plan_found": False}
            }
        
        steps = plan.get("steps", [])
        if not steps:
            return {
                "score": 1.0,
                "reason": "Empty plan (no steps to validate)",
                "details": {"plan_found": True, "step_count": 0}
            }
        
        # Validate each step ID
        valid_ids: list[str] = []
        invalid_ids: list[str] = []
        issues: list[str] = []
        
        for step in steps:
            step_id = step.get("id")
            
            if step_id is None:
                # Check for step_number as fallback (older format)
                step_number = step.get("step_number")
                if step_number is not None:
                    invalid_ids.append(f"step_number:{step_number}")
                    issues.append(f"Step uses step_number ({step_number}) instead of typed ID")
                continue
            
            step_id = str(step_id)
            match = STEP_ID_PATTERN.match(step_id)
            
            if match:
                prefix = match.group(1)
                if prefix in VALID_PREFIXES:
                    valid_ids.append(step_id)
                else:
                    invalid_ids.append(step_id)
                    issues.append(f"Unknown prefix '{prefix}' in step {step_id}")
            else:
                invalid_ids.append(step_id)
                issues.append(f"Invalid step ID format: {step_id}")
        
        # Also check step_type field matches the prefix
        for step in steps:
            step_id = step.get("id", "")
            step_type = step.get("step_type", "")
            
            if step_id and step_type:
                match = STEP_ID_PATTERN.match(str(step_id))
                if match:
                    prefix = match.group(1)
                    expected_type = prefix
                    if step_type.upper() != expected_type:
                        issues.append(
                            f"Step {step_id} has mismatched step_type "
                            f"(expected {expected_type}, got {step_type})"
                        )
        
        total_steps = len(valid_ids) + len(invalid_ids)
        if total_steps == 0:
            return {
                "score": 1.0,
                "reason": "No step IDs to validate",
                "details": {"plan_found": True, "step_count": 0}
            }
        
        score = len(valid_ids) / total_steps
        
        if score == 1.0:
            return {
                "score": 1.0,
                "reason": "All step IDs follow naming conventions",
                "details": {
                    "plan_found": True,
                    "step_count": total_steps,
                    "valid_ids": valid_ids,
                }
            }
        else:
            return {
                "score": score,
                "reason": f"Some step IDs don't follow conventions: {'; '.join(issues)}",
                "details": {
                    "plan_found": True,
                    "step_count": total_steps,
                    "valid_ids": valid_ids,
                    "invalid_ids": invalid_ids,
                    "issues": issues,
                }
            }
    
    def _extract_plan(self, response: str) -> dict[str, Any] | None:
        """Extract plan JSON from response text."""
        # Try to find JSON blocks in the response
        json_patterns = [
            r'```json\s*(.*?)```',
            r'```\s*(.*?)```',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if isinstance(parsed, dict) and "steps" in parsed:
                        return parsed
                except (json.JSONDecodeError, TypeError):
                    continue
        
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict) and "steps" in parsed:
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        
        return None
