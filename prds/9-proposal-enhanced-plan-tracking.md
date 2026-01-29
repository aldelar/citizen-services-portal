# Proposal: Enhanced Plan Step Tracking & History

## Overview

This proposal enhances the Project Plan to serve as the **single source of truth** for everything that happens during a project. Every automated action, user task, and completion event will be captured with full context, making the plan a complete history/audit trail.

Additionally, this proposal standardizes how **Action Cards** are emitted by the agent and rendered in the chat, making them visually prominent and ensuring the corresponding step is automatically updated to `AWAITING_USER`.

---

## Agent Behavior: Planning Guidelines

### Problem: Agent Replans Too Often

The agent currently tends to output updated plans prematurely while still discussing options. This leads to:
- Confusion when plan changes multiple times
- User uncertainty about which version is "real"
- Wasted plan renders in the UI

### New Behavior: Ask First, Plan After

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT PLANNING FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. GATHER INFORMATION                                                  │
│     └─ Ask clarifying questions about user's situation                  │
│                                                                         │
│  2. IDENTIFY OPTIONS (if multiple paths exist)                          │
│     └─ Present options A vs B vs C with pros/cons                       │
│     └─ ❌ DO NOT output a plan yet                                       │
│     └─ Ask: "Which approach would you prefer?"                          │
│                                                                         │
│  3. USER CONFIRMS DIRECTION                                             │
│     └─ Wait for explicit user choice                                    │
│                                                                         │
│  4. GENERATE/UPDATE PLAN                                                │
│     └─ ✅ NOW output ```json:plan block                                  │
│     └─ Plan is committed based on user's choices                        │
│                                                                         │
│  5. EXECUTE PLAN                                                        │
│     └─ Work through steps, only update plan when steps complete         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Rules for Agent (System Prompt Addition)

```markdown
## Planning Behavior

1. **Ask before planning**: When there are multiple approaches or unclear requirements,
   ask clarifying questions BEFORE generating a plan. Present options and get user buy-in.

2. **One plan output per decision**: Only emit a ```json:plan block when:
   - Initial plan after user confirms approach
   - Step status changes (completed, blocked)
   - User explicitly requests plan update
   
3. **Don't replan while brainstorming**: If discussing possibilities, use prose.
   Reserve the formal plan block for committed decisions.

4. **Plan updates are minimal**: When updating, only change the affected steps.
   Don't regenerate the entire plan for minor status changes.

5. **When emitting action cards**: Always include the step_id. The step will 
   automatically be set to AWAITING_USER status.
```

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

### 2.1 Streaming Action Card Detection & Rendering

Action cards follow the same pattern as `json:plan` and `json:references` - they're embedded in the agent's streaming response and detected/replaced with rich UI components.

#### Agent Output Format

```markdown
I've determined that you need to call 311 to schedule your inspection.

```json:action
{
  "step_id": "I1",
  "card_type": "phone_call",
  "title": "Schedule Rough Electrical Inspection",
  "instructions": "Call 311 and request a rough electrical inspection for your permit.",
  "contact_phone": "311",
  "contact_name": "LA City Services",
  "phone_script": "Hi, I'd like to schedule a rough electrical inspection for permit #ELEC-2026-567890 at 123 Main St, Los Angeles 90012. My name is John Smith and my callback number is 555-1234.",
  "checklist": [
    "Have your permit number ready",
    "Confirm the inspection address",
    "Note the confirmation number they give you"
  ],
  "estimated_duration": "5-10 minutes on hold, then 2-3 minutes to schedule"
}
```

I'll update step I1 in your plan to show this is awaiting your action.
```

#### Detection Pattern

```python
def extract_action_card_from_response(response_text: str) -> tuple[str, ActionCardData | None]:
    """Extract action card JSON from response and return cleaned text + ActionCardData.
    
    Looks for ```json:action ... ``` blocks in the response.
    If found:
    1. Extracts the JSON
    2. Converts to ActionCardData model
    3. Replaces the block with a visual card placeholder
    4. Returns step_id so the step can be updated to AWAITING_USER
    """
    pattern = r'```json:action\s*([\s\S]*?)```'
    match = re.search(pattern, response_text)
    
    if match:
        try:
            raw_json = match.group(1)
            action_json = json.loads(raw_json)
            action_card = ActionCardData.model_validate(action_json)
            
            # Replace JSON block with placeholder (will be rendered as card component)
            cleaned_text = re.sub(pattern, '<!-- ACTION_CARD_PLACEHOLDER -->', response_text)
            return cleaned_text, action_card
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error parsing action card JSON: {e}")
            pass
    
    return response_text, None
```

#### Chat Rendering

The action card is rendered as a prominent inline card in the chat:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 💬 Agent                                                                │
├─────────────────────────────────────────────────────────────────────────┤
│ I've determined that you need to call 311 to schedule your inspection. │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ ⚡ ACTION NEEDED: Schedule Rough Electrical Inspection              │ │
│ │ Step: I1                                                            │ │
│ ├─────────────────────────────────────────────────────────────────────┤ │
│ │ 📞 PHONE CALL to 311 (LA City Services)                            │ │
│ │                                                                     │ │
│ │ Call 311 and request a rough electrical inspection for your permit.│ │
│ │                                                                     │ │
│ │ ┌─ Phone Script ──────────────────────────────────────────────────┐ │ │
│ │ │ "Hi, I'd like to schedule a rough electrical inspection for     │ │ │
│ │ │  permit #ELEC-2026-567890 at 123 Main St, Los Angeles 90012..." │ │ │
│ │ └─────────────────────────────────────────────────────────── [📋] ┘ │ │
│ │                                                                     │ │
│ │ ☑ Have your permit number ready                                    │ │
│ │ ☑ Confirm the inspection address                                   │ │
│ │ ☑ Note the confirmation number they give you                       │ │
│ │                                                                     │ │
│ │ ⏱ Estimated: 5-10 minutes on hold, then 2-3 minutes to schedule    │ │
│ │                                                                     │ │
│ │                          [✓ Mark Complete]  [💬 Need Help]          │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ I'll update step I1 in your plan to show this is awaiting your action. │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Automatic Step Status Update

When an action card is detected, the system MUST:

1. **Update the step status** to `AWAITING_USER`
2. **Store the card** in `step.user_action_card`
3. **Add history event** documenting the card assignment
4. **Refresh the plan widget** to show the orange "Action Needed" styling

```python
async def handle_action_card(
    project_id: str, 
    user_id: str, 
    action_card: ActionCardData
) -> None:
    """Process an action card from agent response."""
    
    # Convert to storage model
    user_action_card = UserActionCard(
        card_type=action_card.card_type,
        title=action_card.title,
        instructions=action_card.instructions,
        phone_script=action_card.phone_script,
        email_draft=action_card.email_draft,
        checklist=action_card.checklist,
        contact_phone=action_card.contact_phone,
        contact_email=action_card.contact_email,
        contact_name=action_card.contact_name,
        action_url=action_card.action_url,
        estimated_duration=action_card.estimated_duration,
        assigned_at=datetime.now(timezone.utc)
    )
    
    # Update the step
    await project_repo.update_plan_step(
        project_id=project_id,
        user_id=user_id,
        step_id=action_card.step_id,
        updates={
            "status": StepStatus.AWAITING_USER,
            "user_action_card": user_action_card.model_dump(),
            "started_at": datetime.now(timezone.utc)
        }
    )
    
    # Add history event
    await add_step_history_event(
        project_id=project_id,
        step_id=action_card.step_id,
        event_type="card_assigned",
        actor="agent",
        summary=f"Action card assigned: {action_card.title}"
    )
```

#### NiceGUI Component for Inline Action Card

```python
def render_inline_action_card(
    action_card: ActionCardData,
    on_complete: Callable[[str], Awaitable[None]],
    on_help: Callable[[], Awaitable[None]]
) -> ui.card:
    """Render an action card inline in the chat."""
    
    # Icon mapping
    ICONS = {
        "phone_call": ("call", "warning"),
        "email": ("email", "primary"),
        "form_submission": ("description", "primary"),
        "in_person": ("business", "warning"),
        "upload": ("cloud_upload", "primary")
    }
    icon, color = ICONS.get(action_card.card_type, ("bolt", "warning"))
    
    with ui.card().classes('w-full border-2 border-orange-400 bg-orange-50') as card:
        # Header
        with ui.row().classes('items-center gap-2 w-full'):
            ui.icon('bolt', color='warning')
            ui.label('ACTION NEEDED').classes('font-bold text-orange-700')
            ui.label(f'Step: {action_card.step_id}').classes('ml-auto text-sm text-gray-500')
        
        ui.separator()
        
        # Action type header
        with ui.row().classes('items-center gap-2'):
            ui.icon(icon, color=color).classes('text-xl')
            action_label = {
                "phone_call": f"PHONE CALL to {action_card.contact_phone}",
                "email": f"EMAIL to {action_card.contact_email}",
                "form_submission": "FORM SUBMISSION",
                "in_person": f"VISIT {action_card.contact_name}",
                "upload": "UPLOAD DOCUMENT"
            }.get(action_card.card_type, "ACTION")
            ui.label(action_label).classes('font-semibold')
            if action_card.contact_name:
                ui.label(f"({action_card.contact_name})").classes('text-gray-500')
        
        # Title and instructions
        ui.label(action_card.title).classes('text-lg font-medium mt-2')
        ui.markdown(action_card.instructions).classes('text-sm text-gray-700')
        
        # Phone script (collapsible)
        if action_card.phone_script:
            with ui.expansion('📝 Phone Script', icon='description').classes('w-full mt-2'):
                with ui.card().classes('bg-white p-3'):
                    ui.label(action_card.phone_script).classes('font-mono text-sm whitespace-pre-wrap')
                    ui.button('Copy', icon='content_copy', on_click=lambda: ui.clipboard.write(action_card.phone_script)).props('flat size=sm')
        
        # Email draft (collapsible)
        if action_card.email_draft:
            with ui.expansion('📧 Email Draft', icon='email').classes('w-full mt-2'):
                with ui.card().classes('bg-white p-3'):
                    ui.markdown(action_card.email_draft).classes('text-sm')
                    ui.button('Copy', icon='content_copy', on_click=lambda: ui.clipboard.write(action_card.email_draft)).props('flat size=sm')
        
        # Checklist
        if action_card.checklist:
            ui.label('Checklist:').classes('font-medium mt-3')
            for item in action_card.checklist:
                with ui.row().classes('items-center gap-2'):
                    ui.icon('check_box_outline_blank', size='xs').classes('text-gray-400')
                    ui.label(item).classes('text-sm')
        
        # Estimated duration
        if action_card.estimated_duration:
            with ui.row().classes('items-center gap-2 mt-3 text-sm text-gray-600'):
                ui.icon('schedule', size='xs')
                ui.label(f'Estimated: {action_card.estimated_duration}')
        
        ui.separator().classes('mt-4')
        
        # Action buttons
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Need Help', icon='help', on_click=on_help).props('flat')
            ui.button('Mark Complete', icon='check', color='positive', 
                      on_click=lambda: on_complete(action_card.step_id)).props('unelevated')
    
    return card
```

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

### Phase 1: Core Models (Priority: High) ✅ IMPLEMENTED
- Add new model classes to `src/shared/cosmos/models.py`
  - `ToolExecutionRecord`
  - `UserActionCard`
  - `CompletionRecord`
  - `StepEvent`
- Add new model classes to `src/web-app/models/project.py`
- Update `PlanStep` with new optional fields
- Update repository methods for step updates

### Phase 2: Streaming Action Card Detection (Priority: High) ✅ IMPLEMENTED
- Add `extract_action_card_from_response()` function in `main.py`
- Pattern: `\`\`\`json:action ... \`\`\``
- Auto-update step to `AWAITING_USER` when action card detected
- Store card in step's `user_action_card` field

### Phase 3: Agent Behavior Updates (Priority: High) ✅ IMPLEMENTED
- Update agent system prompt with planning guidelines
- Agent should ask clarifying questions before planning
- Agent should only output plan when user confirms direction
- Agent must include `step_id` in action card JSON
- Update agent to emit `json:action` blocks (not inline markdown)

### Phase 4: UI - Inline Action Card Component (Priority: High) ✅ IMPLEMENTED
- Create `render_inline_action_card()` component
- Prominent orange styling with header, script, checklist
- "Mark Complete" and "Need Help" buttons
- Integrate into chat message rendering

### Phase 5: UI - Plan Widget Enhancements (Priority: Medium)
- Show `execution_record` with clickable request IDs
- Show action needed badge on steps with `user_action_card`
- Add collapsible history timeline view
- Update step card click to show full details

### Phase 6: Mark Complete Flow (Priority: Medium) ✅ IMPLEMENTED
- "Mark Complete" dialog with optional message/data input
- API endpoint `POST /projects/{id}/steps/{step_id}/complete`
- Store `completion_record` in step
- Add history event
- Refresh plan widget
- Notify agent of completion

### Phase 7: Agent Verification (Priority: Low)
- Agent can query for pending completions
- Agent can verify and add verification notes
- History captures verification events

---

## Implementation Status

**Implemented (Jan 2026):**
- ✅ New Cosmos models: `ToolExecutionRecord`, `UserActionCard`, `CompletionRecord`, `StepEvent`
- ✅ Updated `PlanStep` with new fields: `execution_record`, `user_action_card`, `completion_record`, `history`
- ✅ Web-app models updated to match
- ✅ `extract_action_card_from_response()` function for streaming detection
- ✅ `render_inline_action_card()` component with orange styling
- ✅ `create_mark_complete_dialog()` for user completion flow
- ✅ `update_step_with_action_card()` in project service
- ✅ `complete_step()` in project service
- ✅ Agent system prompt updated with planning guidelines and action card format

**Files Modified:**
- `src/shared/cosmos/models.py` - New model classes and PlanStep fields
- `src/web-app/models/project.py` - Matching UI models
- `src/web-app/main.py` - Action card extraction and integration
- `src/web-app/components/inline_action_card.py` - New component (created)
- `src/web-app/services/project_service.py` - Step update and complete methods
- `src/web-app/services/agent_service.py` - Updated system prompt

---

## Summary of Streaming Detection Patterns

| Pattern | Purpose | Action |
|---------|---------|--------|
| `\`\`\`json:plan` | Plan update | Extract plan, save to project, render Mermaid |
| `\`\`\`json:references` | KB citations | Extract refs, render as clickable badges |
| `\`\`\`json:action` | User action card | Extract card, update step status, render inline card |

All three patterns:
1. Detected via regex during streaming
2. JSON extracted and validated
3. Block replaced with visual placeholder or component
4. Associated data stored (project plan, message refs, step card)

---

## Open Questions

1. **History Retention**: Should we limit history entries per step? (Suggest: no, storage is cheap)
2. **File Attachments**: Should completion records support file uploads? (Suggest: Phase 2)
3. **Notifications**: Should user get reminders for AWAITING_USER steps? (Suggest: future enhancement)
4. **Action Card Expiry**: Should cards have a TTL after which agent re-evaluates? (Suggest: future)
5. **Multiple Action Cards**: Can agent assign cards to multiple steps in one response? (Suggest: yes, parse all matches)
