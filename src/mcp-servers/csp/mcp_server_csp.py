"""CSP MCP Server - Plan lifecycle management.

This MCP server provides:
1. Plan Lifecycle Tools - plan.get, plan.create, plan.update

The agent uses these tools to manage project plans. Plans are passed as JSON strings
for simplicity - the agent generates the plan JSON per the system prompt schema.
"""

# Load environment variables FIRST, before any other imports
from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import logging

from fastmcp import FastMCP

from src.tools import CSPTools

# Setup logging - suppress verbose Azure SDK logs
logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("CSP")

# Initialize tools
tools = CSPTools()


# =============================================================================
# Plan Lifecycle Tools
# =============================================================================


@mcp.tool(title="Get Plan", name="plan.get")
async def plan_get(
    project_id: str,
    user_id: str,
) -> str:
    """
    Get the full plan for a project.

    Use this to retrieve the current plan state before making updates.
    Always call this first when working with an existing project plan.

    Args:
        project_id: The project UUID
        user_id: The user ID (partition key)

    Returns:
        Complete plan with all steps, statuses, and timing data as JSON
    """
    logger.info(f"[CSP] 🔧 plan.get(project_id=\"{project_id}\")")
    result = await tools.plan_get(
        project_id=project_id,
        user_id=user_id,
    )
    step_count = len(result.get("plan", {}).get("steps", [])) if result.get("plan") else 0
    logger.info(f"[CSP]    ↳ plan has {step_count} steps")
    return json.dumps(result, indent=2)


@mcp.tool(title="Create Plan", name="plan.create")
async def plan_create(
    project_id: str,
    user_id: str,
    plan_json: str,
) -> str:
    """
    Create a new plan for a project.

    The plan_json should be a JSON string with an array of steps:
    {
      "steps": [
        {"id": "P1", "title": "Submit permit", "agency": "LADBS", "step_type": "permits.submit", "automated": true, "depends_on": []},
        {"id": "I1", "title": "Schedule inspection", "agency": "LADBS", "step_type": "inspection.schedule", "automated": true, "depends_on": ["P1"]}
      ]
    }

    Args:
        project_id: The project UUID
        user_id: The user ID (partition key)
        plan_json: JSON string containing the plan steps

    Returns:
        Created plan with step IDs and confirmation
    """
    # Parse the plan JSON
    try:
        plan_data = json.loads(plan_json)
    except json.JSONDecodeError as e:
        logger.error(f"[CSP] ❌ plan.create failed: Invalid JSON - {e}")
        return json.dumps({"error": True, "message": f"Invalid plan JSON: {e}"})

    steps = plan_data.get("steps", [])
    logger.info(f"[CSP] 🔧 plan.create(project_id=\"{project_id}\", user_id=\"{user_id}\", steps={len(steps)})")

    result = await tools.plan_create(
        project_id=project_id,
        user_id=user_id,
        plan_json=plan_json,
    )
    if result.get('success'):
        logger.info(f"[CSP]    ↳ ✅ created plan with {len(result.get('plan', {}).get('steps', []))} steps")
    else:
        logger.error(f"[CSP]    ↳ ❌ failed: {result.get('message')}")
    return json.dumps(result, indent=2)


@mcp.tool(title="Update Plan", name="plan.update")
async def plan_update(
    project_id: str,
    user_id: str,
    plan_json: str,
) -> str:
    """
    Update the plan for a project.

    Pass the complete updated plan JSON. The service will:
    1. Compare with existing plan to detect status changes
    2. Log step completions for analytics when steps move to 'completed'
    3. Preserve timing data for unchanged steps

    Typical workflow:
    1. Call plan.get() to retrieve current plan
    2. Modify the plan JSON as needed (update step statuses, add steps, etc.)
    3. Call plan.update() with the complete updated plan

    Args:
        project_id: The project UUID
        user_id: The user ID (partition key)
        plan_json: JSON string containing the updated plan steps

    Returns:
        Updated plan with confirmation
    """
    # Parse the plan JSON
    try:
        plan_data = json.loads(plan_json)
    except json.JSONDecodeError as e:
        logger.error(f"[CSP] ❌ plan.update failed: Invalid JSON - {e}")
        return json.dumps({"error": True, "message": f"Invalid plan JSON: {e}"})

    steps = plan_data.get("steps", [])
    logger.info(f"[CSP] 🔧 plan.update(project_id=\"{project_id}\", steps={len(steps)})")

    result = await tools.plan_update(
        project_id=project_id,
        user_id=user_id,
        plan_json=plan_json,
    )
    if result.get('success'):
        logger.info(f"[CSP]    ↳ updated plan with {len(result.get('plan', {}).get('steps', []))} steps")
    else:
        logger.error(f"[CSP]    ↳ ❌ failed: {result.get('message')}")
    return json.dumps(result, indent=2)


@mcp.tool(title="Update Step", name="plan.updateStep")
async def plan_update_step(
    project_id: str,
    user_id: str,
    step_id: str,
    status: str,
    result: str = None,
    notes: str = None,
) -> str:
    """
    Update a single step's status in a plan.

    This is the PREFERRED method for updating step status after executing
    a tool or when a user confirms completion. Much simpler than plan.update().

    Use this tool:
    - After successfully executing an agency tool (ladbs.submit_permit, etc.)
    - When a user confirms they completed a user_action step
    - To mark a step as scheduled, in_progress, completed, or needs_rework

    Args:
        project_id: The project UUID
        user_id: The user ID (partition key)
        step_id: The step ID to update (e.g., "PRM-1", "INS-2")
        status: New status - one of: "defined", "scheduled", "in_progress", "completed", "needs_rework", "rejected"
        result: Optional JSON string with result data (e.g., {"permit_number": "B2024-12345"})
        notes: Optional notes about the step completion

    Returns:
        Updated step with confirmation
    """
    # Log all parameters for debugging
    params = [f'project_id="{project_id}"', f'step_id="{step_id}"', f'status="{status}"']
    if result:
        params.append(f'result={result}')
    if notes:
        params.append(f'notes="{notes}"')
    logger.info(f"[CSP] 🔧 plan.updateStep({', '.join(params)})")

    step_result = await tools.plan_updateStep(
        project_id=project_id,
        user_id=user_id,
        step_id=step_id,
        status=status,
        result=result,
        notes=notes,
    )
    
    if step_result.get('success'):
        logger.info(f"[CSP]    ↳ ✅ step {step_id} updated to '{status}'")
    else:
        logger.error(f"[CSP]    ↳ ❌ failed: {step_result.get('message')}")
    
    return json.dumps(step_result, indent=2)


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", "8000"))
    # Use streamable-http transport with stateless_http=True for scalability
    # stateless mode creates fresh transport per request, avoiding session timeout issues
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=port, transport="streamable-http", stateless_http=True))
