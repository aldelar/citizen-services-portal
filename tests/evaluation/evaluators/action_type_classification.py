"""
Action Type Classification Evaluator

Validates that plan steps correctly classify actions as:
- automated: Agent can execute directly (queryKB, permits.submit, tou.enroll)
- user_action: Citizen must act (call 311, email agencies, visit offices)
- information: Information gathering step

Steps requiring phone calls, emails, or in-person visits MUST be marked as user_action.
"""

import json
import re
from typing import Any


# Tools that can be automated by the agent
AUTOMATED_TOOLS = {
    "querykb",
    "permits.search",
    "permits.submit",
    "permits.getstatus",
    "account.show",
    "plans.list",
    "tou.enroll",
    "rebates.apply",
    "pickup.scheduled",
    "pickup.geteligibility",
}

# Tools that require user action (agent prepares materials but user must act)
USER_ACTION_TOOLS = {
    "inspections.schedule",  # Requires phone call to 311
    "interconnection.submit",  # Requires user email
    "pickup.schedule",  # Requires call to 311
}

# Keywords indicating user action is required
USER_ACTION_KEYWORDS = [
    r'\bcall\s+311\b',
    r'\bcall\s+(?:the\s+)?(?:department|agency|office)\b',
    r'\bphone\s+call\b',
    r'\bemail\s+(?:to|the)\b',
    r'\bvisit\s+(?:the\s+)?office\b',
    r'\bin[- ]person\b',
    r'\bsubmit\s+(?:in\s+person|by\s+mail)\b',
    r'\bcontact\s+(?:the\s+)?(?:department|agency)\b',
    r'\bmail\s+(?:the|your)\b',
]


class ActionTypeClassificationEvaluator:
    """
    Evaluates whether plan steps correctly classify action types.
    
    Returns a score from 0.0 to 1.0:
    - 1.0: All action types correctly classified
    - 0.0 to <1.0: Some misclassifications (proportional)
    """
    
    def __init__(self) -> None:
        self.user_action_patterns = [
            re.compile(p, re.IGNORECASE) for p in USER_ACTION_KEYWORDS
        ]
    
    def __call__(
        self,
        *,
        response: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Evaluate if action types are correctly classified.
        
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
        
        # Validate each step's action_type
        correct_classifications: list[str] = []
        incorrect_classifications: list[str] = []
        issues: list[str] = []
        
        for step in steps:
            step_id = str(step.get("id") or step.get("step_number") or "unknown")
            action_type = step.get("action_type", "").lower()
            tool_name = step.get("tool_name", "").lower()
            description = step.get("description", "")
            title = step.get("title", "")
            full_text = f"{title} {description}".lower()
            
            expected_action_type = self._determine_expected_action_type(
                tool_name, full_text
            )
            
            if action_type == expected_action_type:
                correct_classifications.append(step_id)
            else:
                incorrect_classifications.append(step_id)
                issues.append(
                    f"Step {step_id}: expected '{expected_action_type}', "
                    f"got '{action_type}'"
                )
        
        total = len(correct_classifications) + len(incorrect_classifications)
        score = len(correct_classifications) / total if total > 0 else 1.0
        
        if score == 1.0:
            return {
                "score": 1.0,
                "reason": "All action types correctly classified",
                "details": {
                    "plan_found": True,
                    "step_count": total,
                    "correct_count": len(correct_classifications),
                }
            }
        else:
            return {
                "score": score,
                "reason": f"Misclassified action types: {'; '.join(issues)}",
                "details": {
                    "plan_found": True,
                    "step_count": total,
                    "correct_count": len(correct_classifications),
                    "incorrect_count": len(incorrect_classifications),
                    "issues": issues,
                }
            }
    
    def _determine_expected_action_type(self, tool_name: str, text: str) -> str:
        """Determine the expected action type based on tool and description."""
        # Check if tool explicitly requires user action
        if tool_name in USER_ACTION_TOOLS:
            return "user_action"
        
        # Check if tool is fully automated
        if tool_name in AUTOMATED_TOOLS:
            return "automated"
        
        # Check for user action keywords in description
        for pattern in self.user_action_patterns:
            if pattern.search(text):
                return "user_action"
        
        # Default to automated if no indicators found
        return "automated"
    
    def _extract_plan(self, response: str) -> dict[str, Any] | None:
        """Extract plan JSON from response text."""
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
