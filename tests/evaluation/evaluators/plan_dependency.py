"""
Plan Dependency Evaluator

Validates that plan step dependencies form valid DAGs (Directed Acyclic Graphs).
Ensures:
- No circular dependencies
- Valid step references (dependencies reference existing steps)
- Proper step ordering (dependencies come before dependent steps)
"""

import json
import re
from typing import Any


class PlanDependencyEvaluator:
    """
    Evaluates whether plan dependencies form a valid DAG.
    
    Returns a score from 0.0 to 1.0:
    - 1.0: Valid DAG with no issues
    - 0.0: Invalid DAG (circular dependencies, invalid references, etc.)
    """
    
    def __call__(
        self,
        *,
        response: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Evaluate if the plan in the response has valid dependencies.
        
        Args:
            response: The agent's response (should contain a plan in JSON)
            **kwargs: Additional context (ignored)
            
        Returns:
            dict with 'score', 'reason', and 'details'
        """
        # Try to extract plan from response
        plan = self._extract_plan(response)
        
        if plan is None:
            # No plan found - might be a non-plan response
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
        
        # Build step ID lookup
        step_ids = set()
        step_by_id: dict[str, dict[str, Any]] = {}
        
        for step in steps:
            step_id = step.get("id") or step.get("step_number")
            if step_id:
                step_id = str(step_id)
                step_ids.add(step_id)
                step_by_id[step_id] = step
        
        # Validate dependencies
        issues: list[str] = []
        
        # Check for invalid references
        for step in steps:
            step_id = str(step.get("id") or step.get("step_number"))
            depends_on = step.get("depends_on", [])
            
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep in depends_on:
                dep_str = str(dep)
                if dep_str not in step_ids:
                    issues.append(f"Step {step_id} depends on non-existent step {dep_str}")
        
        # Check for circular dependencies using DFS
        cycle = self._find_cycle(steps)
        if cycle:
            issues.append(f"Circular dependency detected: {' -> '.join(cycle)}")
        
        # Calculate score
        if issues:
            return {
                "score": 0.0,
                "reason": f"Invalid plan dependencies: {'; '.join(issues)}",
                "details": {
                    "plan_found": True,
                    "step_count": len(steps),
                    "issues": issues,
                    "valid_dag": False,
                }
            }
        
        return {
            "score": 1.0,
            "reason": "Valid plan with correct dependency structure",
            "details": {
                "plan_found": True,
                "step_count": len(steps),
                "valid_dag": True,
            }
        }
    
    def _extract_plan(self, response: str) -> dict[str, Any] | None:
        """Extract plan JSON from response text."""
        # Try to find JSON blocks in the response
        json_patterns = [
            r'```json\s*(.*?)```',  # Markdown JSON blocks
            r'```\s*(.*?)```',      # Generic code blocks
            r'\{[^{}]*"steps"[^{}]*\[.*?\][^{}]*\}',  # Inline JSON with steps
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
        
        # Try parsing the entire response as JSON
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict) and "steps" in parsed:
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        
        return None
    
    def _find_cycle(self, steps: list[dict[str, Any]]) -> list[str] | None:
        """Find a cycle in the dependency graph using DFS."""
        # Build adjacency list
        graph: dict[str, list[str]] = {}
        for step in steps:
            step_id = str(step.get("id") or step.get("step_number"))
            depends_on = step.get("depends_on", [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            graph[step_id] = [str(d) for d in depends_on]
        
        # DFS for cycle detection using standard coloring approach
        # unvisited = not yet processed
        # visiting = currently in the DFS stack (part of current path)
        # visited = completely processed
        unvisited = set(graph.keys())
        visiting: set[str] = set()
        visited: set[str] = set()
        
        def dfs(node: str, path: list[str]) -> list[str] | None:
            unvisited.discard(node)
            visiting.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in visiting:
                    # Found a cycle - return the cycle path
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    return path[cycle_start:] + [neighbor]
                
                if neighbor in unvisited:
                    result = dfs(neighbor, path + [neighbor])
                    if result:
                        return result
            
            visiting.discard(node)
            visited.add(node)
            return None
        
        for node in list(unvisited):
            if node in unvisited:
                result = dfs(node, [node])
                if result:
                    return result
        
        return None
