# Proposal: Enhanced Plan Step Tracking & History

## Overview

This proposal enhances the Project Plan to serve as the **single source of truth** for everything that happens during a project. Every automated action, user task, and completion event will be captured with full context, making the plan a complete history/audit trail.

---

## Current State

The current `PlanStep` model has:
- `result`: Optional dict for outcome data (permit numbers, etc.)
- `user_task`: Optional object with task details
- `status`: Step status enum

**Gaps:**
1. No structured way to store **request IDs** from automated tool calls
2. No way to store the **"card"** (instructions) shown to users for user-action steps
3. No **completion message** field for user-reported completions
4. No **history/log** of what happened during a step

---

## Proposed Enhancements

### 1. New Field: `execution_record` (Automated Steps)

For steps executed by automated tools (MCP servers), capture the full execution context:

```python
class ToolExecutionRecord(CamelCaseModel):
    """Record of an automated tool execution."""
    
    tool_name: str                          # e.g., "ladbs.submit_permit"
    request_id: Optional[str] = None        # ID returned by the tool (e.g., "REQ-2026-001234")
    reference_number: Optional[str] = None  # Business reference (permit #, application #)
    reference_url: Optional[str] = None     # Deep link to view the request/record
    executed_at: datetime
    input_summary: Optional[Dict[str, Any]] = None  # Key inputs (sanitized)
    output_summary: Optional[Dict[str, Any]] = None # Key outputs (sanitized)
    success: bool = True
    error_message: Optional[str] = None     # If failed
```

**Usage:**
- When agent calls `ladbs.submit_permit`, the tool returns a `request_id`
- Agent stores this in `step.execution_record`
- UI renders `request_id` as a clickable link using `reference_url`

---

### 2. New Field: `user_action_card` (User-Driven Steps)

For steps requiring user action, store the complete "card" that was presented:

```python
class UserActionCard(CamelCaseModel):
    """The action card shown to the user for a user-driven step."""
    
    card_type: str                          # "phone_call", "email", "form_submission", "in_person", "upload"
    title: str                              # Short title for the card
    instructions: str                       # Full markdown instructions
    
    # Prepared materials (agent-generated helpers)
    phone_script: Optional[str] = None      # Script for phone calls
    email_draft: Optional[str] = None       # Pre-drafted email content
    form_data: Optional[Dict[str, Any]] = None  # Pre-filled form fields
    checklist: List[str] = Field(default_factory=list)  # Steps to complete
    
    # Contact/action info
    contact_name: Optional[str] = None      # "LA Building & Safety"
    contact_phone: Optional[str] = None     # "(213) 555-1234"
    contact_email: Optional[str] = None     # "permits@lacity.org"
    action_url: Optional[str] = None        # Portal URL if online action
    
    # Timing
    assigned_at: datetime
    due_by: Optional[datetime] = None       # Deadline if applicable
    estimated_duration: Optional[str] = None  # "15 minutes", "1-2 business days"
```

**Usage:**
- When agent determines user action is needed, it generates the card content
- Card is stored in `step.user_action_card`
- Step status is set to `AWAITING_USER`
- UI renders the card in both the plan widget and chat

---

### 3. New Field: `completion_record` (All Steps)

Capture how and when a step was completed:

```python
class CompletionRecord(CamelCaseModel):
    """Record of step completion - works for both automated and user-driven steps."""
    
    completed_at: datetime
    completed_by: str                       # "agent" or "user:<user_id>"
    
    # For user-driven steps
    user_message: Optional[str] = None      # What the user reported ("Done! Confirmation #123")
    user_provided_data: Optional[Dict[str, Any]] = None  # Structured data from user
    
    # For automated steps (redundant with execution_record but explicit)
    tool_result: Optional[Dict[str, Any]] = None
    
    # Verification (optional)
    verified_by: Optional[str] = None       # "agent" if agent verified completion
    verification_notes: Optional[str] = None
```

**Usage:**
- When user clicks "Mark as Complete" for step XYZ
- UI prompts: "Any confirmation numbers or notes to add?"
- User input stored in `step.completion_record.user_message`
- Agent can optionally verify and add notes

---

### 4. New Field: `history` (Audit Trail)

Capture all events that happen during a step's lifecycle:

```python
class StepEvent(CamelCaseModel):
    """A single event in a step's history."""
    
    timestamp: datetime
    event_type: str                         # See event types below
    actor: str                              # "agent", "user:<id>", "system"
    summary: str                            # Human-readable description
    details: Optional[Dict[str, Any]] = None  # Event-specific data
    message_id: Optional[str] = None        # Link to chat message that triggered this

class StepEventType(str, Enum):
    CREATED = "created"                     # Step was added to plan
    STATUS_CHANGED = "status_changed"       # Status transition
    TOOL_EXECUTED = "tool_executed"         # Automated tool ran
    CARD_ASSIGNED = "card_assigned"         # User action card was assigned
    USER_NOTIFIED = "user_notified"         # User was reminded
    USER_COMPLETED = "user_completed"       # User marked as done
    AGENT_VERIFIED = "agent_verified"       # Agent verified completion
    BLOCKED = "blocked"                     # Step was blocked
    UNBLOCKED = "unblocked"                 # Block was resolved
    NOTE_ADDED = "note_added"               # Note was added
    RETRY_REQUESTED = "retry_requested"     # User/agent requested retry
```

**Usage:**
- Every meaningful action appends to `step.history`
- History is rendered as a collapsible timeline in the plan widget
- Provides full audit trail for compliance/debugging

---

## Updated PlanStep Model

```python
class PlanStep(CamelCaseModel):
    """Plan step within a project - THE source of truth for step history."""

    # Identity
    id: str
    title: str
    description: Optional[str] = None
    agency: Optional[str] = None
    
    # Classification
    action_type: ActionType = ActionType.AUTOMATED  # automated, user_action, information
    tool_name: Optional[str] = None                 # MCP tool name for automated steps
    
    # Status & Dependencies
    status: StepStatus = StepStatus.NOT_STARTED
    order: Optional[int] = None
    depends_on: List[str] = Field(default_factory=list)
    
    # Timing
    estimated_duration_days: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # ========== NEW FIELDS ==========
    
    # For AUTOMATED steps: Record of tool execution
    execution_record: Optional[ToolExecutionRecord] = None
    
    # For USER_ACTION steps: The card shown to the user
    user_action_card: Optional[UserActionCard] = None
    
    # For ALL steps: How it was completed
    completion_record: Optional[CompletionRecord] = None
    
    # Audit trail: All events that happened
    history: List[StepEvent] = Field(default_factory=list)
    
    # ========== EXISTING FIELDS (keep for backward compat) ==========
    result: Optional[Dict[str, Any]] = None      # Legacy - use execution_record
    user_task: Optional[UserTask] = None         # Legacy - use user_action_card
    user_tasks: List[UserTask] = Field(default_factory=list)  # Legacy
    notes: Optional[str] = None
```

---

## UI Changes

### Plan Widget - Step Card

```
┌─────────────────────────────────────────────────────────────────────┐
│ [●] P1: Electrical Permit - LADBS                      ✓ Completed  │
├─────────────────────────────────────────────────────────────────────┤
│ Request ID: REQ-2026-001234  [View Details →]                       │
│ Permit #: ELEC-2026-567890                                          │
│ Completed: Jan 15, 2026 at 2:30 PM (by agent)                       │
│                                                                     │
│ [▼ Show History]                                                    │
│   • Jan 15, 2:30 PM - Tool executed: ladbs.submit_permit            │
│   • Jan 15, 2:30 PM - Status changed: in_progress → completed       │
└─────────────────────────────────────────────────────────────────────┘
```

### Plan Widget - User Action Step

```
┌─────────────────────────────────────────────────────────────────────┐
│ [!] U1: Schedule Rough Inspection - LADBS          ⚠️ Action Needed │
├─────────────────────────────────────────────────────────────────────┤
│ 📞 PHONE CALL REQUIRED                                              │
│                                                                     │
│ Call 311 and request a "Rough Electrical Inspection"                │
│                                                                     │
│ ┌─ Prepared Script ────────────────────────────────────────────────┐│
│ │ "Hi, I'm calling to schedule a rough electrical inspection for  ││
│ │  permit #ELEC-2026-567890 at 123 Main St, Los Angeles 90012..."  ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ Assigned: Jan 16, 2026                                              │
│                                                                     │
│ [✓ Mark Complete]  [💬 Need Help]                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Mark Complete Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│ Mark Step Complete                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ U1: Schedule Rough Inspection                                       │
│                                                                     │
│ Confirmation or notes (optional):                                   │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Scheduled for Jan 20, 2026 between 8am-12pm. Confirmation #A1234 ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ Attach files (optional): [+ Add Files]                              │
│                                                                     │
│                                    [Cancel]  [✓ Mark Complete]      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Agent Behavior Changes

### When Executing Automated Steps

```python
# Pseudocode for agent tool execution
async def execute_step(step: PlanStep, tool_name: str, inputs: dict):
    # 1. Update status
    step.status = StepStatus.IN_PROGRESS
    step.started_at = datetime.now()
    
    # 2. Execute tool
    result = await mcp.call_tool(tool_name, inputs)
    
    # 3. Create execution record
    step.execution_record = ToolExecutionRecord(
        tool_name=tool_name,
        request_id=result.get("request_id"),
        reference_number=result.get("permit_number") or result.get("application_id"),
        reference_url=result.get("view_url"),
        executed_at=datetime.now(),
        input_summary=sanitize(inputs),
        output_summary=sanitize(result),
        success=True
    )
    
    # 4. Add to history
    step.history.append(StepEvent(
        timestamp=datetime.now(),
        event_type="tool_executed",
        actor="agent",
        summary=f"Executed {tool_name}",
        details={"request_id": result.get("request_id")}
    ))
    
    # 5. Create completion record
    step.completion_record = CompletionRecord(
        completed_at=datetime.now(),
        completed_by="agent",
        tool_result=result
    )
    
    # 6. Update status
    step.status = StepStatus.COMPLETED
    step.completed_at = datetime.now()
```

### When Creating User Action Steps

```python
async def assign_user_action(step: PlanStep, card_content: dict):
    # 1. Create the action card
    step.user_action_card = UserActionCard(
        card_type=card_content["type"],
        title=card_content["title"],
        instructions=card_content["instructions"],
        phone_script=card_content.get("phone_script"),
        email_draft=card_content.get("email_draft"),
        checklist=card_content.get("checklist", []),
        contact_phone=card_content.get("contact_phone"),
        action_url=card_content.get("action_url"),
        assigned_at=datetime.now(),
        estimated_duration=card_content.get("estimated_duration")
    )
    
    # 2. Update status
    step.status = StepStatus.AWAITING_USER
    step.started_at = datetime.now()
    
    # 3. Add to history
    step.history.append(StepEvent(
        timestamp=datetime.now(),
        event_type="card_assigned",
        actor="agent",
        summary=f"User action card assigned: {card_content['title']}"
    ))
```

### When User Marks Step Complete

```python
async def user_completes_step(step: PlanStep, user_id: str, user_message: str):
    # 1. Create completion record
    step.completion_record = CompletionRecord(
        completed_at=datetime.now(),
        completed_by=f"user:{user_id}",
        user_message=user_message
    )
    
    # 2. Add to history
    step.history.append(StepEvent(
        timestamp=datetime.now(),
        event_type="user_completed",
        actor=f"user:{user_id}",
        summary=f"User marked complete",
        details={"user_message": user_message}
    ))
    
    # 3. Update status
    step.status = StepStatus.COMPLETED
    step.completed_at = datetime.now()
    
    # 4. Optionally notify agent to verify/proceed
    await notify_agent(f"User completed step {step.id}: {user_message}")
```

---

## API Changes

### New Endpoint: Mark Step Complete

```http
POST /api/projects/{project_id}/steps/{step_id}/complete
Content-Type: application/json

{
    "message": "Scheduled for Jan 20, 2026. Confirmation #A1234",
    "data": {
        "confirmation_number": "A1234",
        "scheduled_date": "2026-01-20"
    }
}
```

### Response

```json
{
    "step": {
        "id": "U1",
        "status": "completed",
        "completion_record": {
            "completed_at": "2026-01-16T15:30:00Z",
            "completed_by": "user:john-doe-123",
            "user_message": "Scheduled for Jan 20, 2026. Confirmation #A1234"
        }
    }
}
```

---

## Benefits

1. **Complete Audit Trail**: Every action, from tool execution to user completion, is logged
2. **Clickable References**: Request IDs and permit numbers link to source systems
3. **User Task Memory**: The exact instructions given to users are preserved
4. **Verification Flow**: Users can report completion with notes; agent can verify
5. **Debugging**: Full history helps troubleshoot issues
6. **Reporting**: Can generate reports on how long each step type takes
7. **Resume Context**: If user returns after days, plan shows exactly what happened

---

## Migration Notes

- `result` field kept for backward compatibility, deprecated in favor of `execution_record`
- `user_task` / `user_tasks` kept for backward compatibility, deprecated in favor of `user_action_card`
- History array starts empty for existing steps; new events appended going forward

---

## Implementation Phases

### Phase 1: Core Models (Priority: High)
- Add new model classes to `src/shared/cosmos/models.py`
- Add new model classes to `src/web-app/models/project.py`
- Update repository methods

### Phase 2: Agent Integration (Priority: High)
- Update agent to populate `execution_record` when calling tools
- Update agent to populate `user_action_card` for user steps
- Add history event logging

### Phase 3: UI Updates (Priority: Medium)
- Update plan widget to show execution records with links
- Add "Mark Complete" dialog with user message input
- Add collapsible history view

### Phase 4: API Endpoints (Priority: Medium)
- Add `POST /projects/{id}/steps/{step_id}/complete` endpoint
- Add history query endpoints if needed

---

## Open Questions

1. **History Retention**: Should we limit history entries per step? (Suggest: no, storage is cheap)
2. **File Attachments**: Should completion records support file uploads? (Suggest: Phase 2)
3. **Notifications**: Should user get reminders for AWAITING_USER steps? (Suggest: future enhancement)
