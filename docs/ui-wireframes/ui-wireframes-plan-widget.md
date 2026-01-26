# UI Wireframes: Plan Widget (Dynamic Graph)

This document defines the Plan Widget in the right panel—a **dynamic graph visualization** that renders any project plan regardless of complexity.

---

## NiceGUI Components Used

| Feature | NiceGUI Element |
|---------|-----------------|
| Plan container | `ui.right_drawer()` or `ui.column()` |
| Graph visualization | `ui.mermaid()` for DAG diagrams |
| Timeline alternative | `ui.timeline()` for linear flows |
| Progress overview | `ui.linear_progress()` |
| Step cards | `ui.card()` |
| Status indicators | `ui.chip()`, `ui.icon()` |
| Action buttons | `ui.button()` |
| Tooltips | `.tooltip()` method |

### Visualization Strategy

NiceGUI's `ui.mermaid()` provides native graph rendering without custom JavaScript:

```python
# Dynamic graph using Mermaid
def render_plan_graph(steps: list):
    mermaid_code = 'graph TD\n'
    
    for step in steps:
        # Node with status styling
        node_id = step.id
        label = f"{step.title}"
        mermaid_code += f'    {node_id}["{label}"]\n'
        
        # Edges from dependencies
        for dep_id in step.depends_on:
            mermaid_code += f'    {dep_id} --> {node_id}\n'
        
        # Status-based styling
        style = STATUS_STYLES.get(step.status, '')
        if style:
            mermaid_code += f'    style {node_id} {style}\n'
    
    ui.mermaid(mermaid_code).classes('w-full')

STATUS_STYLES = {
    'not_started': 'fill:#f5f5f5,stroke:#9ca3af,stroke-dasharray:5',
    'blocked': 'fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5',
    'ready': 'fill:#dbeafe,stroke:#3b82f6',
    'in_progress': 'fill:#bfdbfe,stroke:#2563eb',
    'awaiting_user': 'fill:#fed7aa,stroke:#ea580c,stroke-width:3',
    'completed': 'fill:#bbf7d0,stroke:#16a34a',
    'failed': 'fill:#fecaca,stroke:#dc2626',
    'skipped': 'fill:#e5e7eb,stroke:#6b7280',
}
```

---

## ⚠️ Critical Understanding

The plan is **NOT a fixed list of steps**. It is a **dynamic graph** that:

1. **Varies by project type**: Home renovation, business license, utility connection—each has different steps
2. **Is generated dynamically**: The agent builds the plan based on conversation
3. **Has dependencies**: Steps are nodes with edges representing dependencies (`dependsOn[]`)
4. **Evolves over time**: New steps added, steps skipped, dependencies modified

### Data Model Reference

From the CosmosDB specification, each step is a node:

```python
class PlanStep(BaseModel):
    id: str                         # Step ID (e.g., "P1", "U1", "I1")
    title: str                      # Human-readable title
    agency: str                     # LADBS, LADWP, LASAN, or any agency
    tool_name: str                  # MCP tool used
    status: StepStatus              # not_started, in_progress, awaiting_user, completed, blocked
    depends_on: List[str] = []      # IDs of prerequisite steps (GRAPH EDGES)
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict]
    user_task: Optional[UserTask]
```

#### Step ID Convention

Step IDs are short, unique identifiers within a plan. While the format is flexible, the demo uses a convention:

| Prefix | Category | Examples |
|--------|----------|----------|
| P | Permits | P1, P2, P3 |
| U | Utility | U1, U2 |
| I | Inspection | I1, I2 |
| D | Disposal | D1, D2 |
| F | Final | F1 |
| R | Rebate | R1 |

> **Note:** Step IDs are dynamically generated. The UI should display the `title` as the primary label, with `id` shown as a secondary reference.

The `depends_on` field creates the graph edges. The widget must render these relationships visually.

---

## Plan Widget Structure

### Visual Reference

```
┌────────────────────────────────────────┐
│ 📊 PROJECT PLAN               [⚙️]  │
├────────────────────────────────────────┤
│ Progress: ████████░░  8/10 steps │
├────────────────────────────────────────┤
│                                        │
│     ┌─────┐    ┌─────┐    ┌─────┐  │
│     │ P1  │    │ P2  │    │ P3  │  │
│     │  ✓  │    │  ✓  │    │  ✓  │  │
│     └──┬──┘    └──┬──┘    └──┬──┘  │
│        │          │          │      │
│        └──────────┼──────────┘      │
│                   ▼                    │
│            ╭───────╮                  │
│            │  I1   │                  │
│            │  ⚡   │  ← Action needed │
│            ╰───────╯                  │
│                   │                    │
│                   ▼                    │
│            ┌╌╌╌╌╌╌╌┐                  │
│            ╌  F1   ╌  ← Blocked       │
│            ╌  🔒   ╌                  │
│            └╌╌╌╌╌╌╌┘                  │
│                                        │
├────────────────────────────────────────┤
│ ⚡ 1 action needs your attention       │
│                       [View Task]      │
└────────────────────────────────────────┘
```

### NiceGUI Implementation

```python
# Plan Widget using NiceGUI
with ui.right_drawer(value=True).classes('w-96 bg-gray-50'):
    # Header
    with ui.row().classes('w-full items-center p-4 border-b'):
        ui.icon('timeline').classes('text-xl')
        ui.label('PROJECT PLAN').classes('font-bold flex-grow')
        with ui.button(icon='settings').props('flat round size=sm'):
            with ui.menu():
                ui.menu_item('Toggle View')
                ui.menu_item('Zoom to Fit')
    
    # Progress summary
    with ui.row().classes('w-full items-center px-4 py-2 gap-2'):
        ui.label('Progress:').classes('text-sm text-gray-500')
        ui.linear_progress(value=progress, show_value=True).classes('flex-grow')
        ui.label(f'{completed}/{total} steps').classes('text-xs text-gray-500')
    
    # Graph container
    with ui.scroll_area().classes('flex-grow p-4'):
        render_plan_graph(steps)  # Mermaid diagram
    
    # Action needed footer (if applicable)
    if action_needed_count > 0:
        with ui.card().classes('mx-4 mb-4 bg-orange-50 border-orange-300'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('bolt', color='warning')
                ui.label(f'{action_needed_count} action{"s" if action_needed_count > 1 else ""} needs your attention').classes('text-sm')
            ui.button('View Task', on_click=show_pending_action).props('flat color=warning')
```

---

## Graph Visualization

### Step Node Rendering with NiceGUI

Each step can be rendered as a card for list view, or as a Mermaid node for graph view:

```python
# Card view of a step (for list/timeline mode)
def render_step_card(step: PlanStep, on_click: Callable):
    status_colors = {
        'not_started': ('grey', 'radio_button_unchecked'),
        'blocked': ('grey', 'lock'),
        'ready': ('primary', 'play_arrow'),
        'in_progress': ('primary', 'pending'),
        'awaiting_user': ('warning', 'bolt'),
        'completed': ('positive', 'check_circle'),
        'failed': ('negative', 'error'),
        'skipped': ('grey', 'block'),
    }
    
    color, icon = status_colors.get(step.status, ('grey', 'help'))
    
    # Card styling based on status
    card_classes = 'w-full cursor-pointer transition-all'
    if step.status == 'awaiting_user':
        card_classes += ' border-2 border-orange-400 bg-orange-50'
    elif step.status == 'in_progress':
        card_classes += ' border-l-4 border-blue-500'
    elif step.status == 'completed':
        card_classes += ' border-l-4 border-green-500'
    
    with ui.card().classes(card_classes).on('click', lambda: on_click(step)):
        with ui.row().classes('items-center gap-2'):
            ui.chip(step.agency, color='grey').props('outline size=sm')
            ui.icon(icon, color=color).classes('ml-auto')
        
        ui.label(step.title).classes('font-semibold')
        
        if step.result and step.result.get('permit_number'):
            ui.label(f"#{step.result['permit_number']}").classes('text-sm text-gray-500')
        
        # Automation indicator
        if step.user_task:
            with ui.row().classes('items-center gap-1 text-sm'):
                ui.icon('person', size='xs')
                ui.label('User Action')
        else:
            with ui.row().classes('items-center gap-1 text-sm text-gray-400'):
                ui.icon('bolt', size='xs')
                ui.label('Automated')
```

### Mermaid Graph View

For complex dependency graphs, use `ui.mermaid`:

```python
# Full graph example
ui.mermaid('''
graph TD
    P1[Electrical Permit<br/>LADBS] --> I1[Rough Inspection]
    P2[Building Permit<br/>LADBS] --> I1
    U1[Interconnection<br/>LADWP] --> I2[Final Inspection]
    I1 --> I2
    I2 --> F1[Final Sign-off]
    
    style P1 fill:#bbf7d0,stroke:#16a34a
    style P2 fill:#bfdbfe,stroke:#2563eb
    style U1 fill:#fed7aa,stroke:#ea580c,stroke-width:3
    style I1 fill:#f5f5f5,stroke:#9ca3af,stroke-dasharray:5
    style I2 fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5
    style F1 fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5
''').classes('w-full')

---

## Node States

Use Mermaid styling classes for different step statuses:

### Status Styling Table

| Status | Mermaid Style | NiceGUI Card Classes |
|--------|--------------|---------------------|
| `not_started` | `fill:#f5f5f5,stroke:#9ca3af,stroke-dasharray:5` | `border-dashed border-gray-300` |
| `blocked` | `fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5` | `border-dashed border-gray-400 bg-gray-100` |
| `ready` | `fill:#dbeafe,stroke:#3b82f6` | `border-blue-500 bg-blue-50` |
| `in_progress` | `fill:#bfdbfe,stroke:#2563eb` | `border-l-4 border-blue-600 bg-blue-50` |
| `awaiting_user` | `fill:#fed7aa,stroke:#ea580c,stroke-width:3` | `border-2 border-orange-500 bg-orange-50` |
| `completed` | `fill:#bbf7d0,stroke:#16a34a` | `border-l-4 border-green-500` |
| `failed` | `fill:#fecaca,stroke:#dc2626` | `border-red-500 bg-red-50` |
| `skipped` | `fill:#e5e7eb,stroke:#6b7280` | `opacity-60 line-through` |

### Interactive Cards

For detailed step information, use clickable cards:

```python
# Awaiting User Action - highlighted with click handler
with ui.card().classes('border-2 border-orange-400 bg-orange-50 cursor-pointer').on('click', show_action):
    with ui.row().classes('items-center gap-2'):
        ui.chip('LADBS').props('outline size=sm')
        ui.icon('bolt', color='warning')
    ui.label('Schedule Inspection').classes('font-semibold')
    ui.label('Action needed').classes('text-sm text-orange-700')
    with ui.row().classes('items-center gap-1 text-sm text-orange-600'):
        ui.icon('person', size='xs')
        ui.label('Call 311')

# Blocked step - dashed border with lock indicator
with ui.card().classes('border-dashed border-2 border-gray-400 bg-gray-100 opacity-80'):
    with ui.row().classes('items-center gap-2'):
        ui.chip('LADBS').props('outline size=sm')
        ui.icon('lock', color='grey')
    ui.label('Final Inspection').classes('font-semibold text-gray-600')
    ui.label('Waiting for: I1').classes('text-xs text-gray-500')
    with ui.row().classes('items-center gap-1 text-xs text-gray-400'):
        ui.icon('person', size='xs')
        ui.label('User Action')

# Ready step - blue border with play icon
with ui.card().classes('border-2 border-blue-500 bg-blue-50 cursor-pointer'):
    with ui.row().classes('items-center gap-2'):
        ui.chip('LADWP').props('outline size=sm')
        ui.icon('play_arrow', color='primary')
    ui.label('TOU Enrollment').classes('font-semibold')
    with ui.row().classes('items-center gap-1 text-xs text-blue-500'):
        ui.icon('bolt', size='xs')
        ui.label('Automated')

# In Progress step - with spinner
with ui.card().classes('border-l-4 border-blue-500 bg-blue-50'):
    with ui.row().classes('items-center gap-2'):
        ui.chip('LADBS').props('outline size=sm')
        ui.spinner(size='sm', color='primary')
    ui.label('Electrical Permit').classes('font-semibold')
    ui.label('Under Review').classes('text-xs text-blue-600')
    ui.linear_progress(indeterminate=True).props('color=primary size=xs')

# Completed step - green left border with check
with ui.card().classes('border-l-4 border-green-500'):
    with ui.row().classes('items-center gap-2'):
        ui.chip('LADBS').props('outline size=sm')
        ui.icon('check_circle', color='positive')
    ui.label('Electrical Permit').classes('font-semibold')
    ui.label('#2026-001234').classes('text-xs text-gray-500')

# Failed step - red border with retry button
with ui.card().classes('border-2 border-red-500 bg-red-50'):
    with ui.row().classes('items-center gap-2'):
        ui.chip('LADWP').props('outline size=sm')
        ui.icon('error', color='negative')
    ui.label('Interconnection Submit').classes('font-semibold')
    ui.label('Connection failed').classes('text-xs text-red-600')
    ui.button('Retry', on_click=retry_step).props('flat dense color=negative size=sm')

# Skipped step - grayed out with strikethrough
with ui.card().classes('opacity-60 bg-gray-100'):
    with ui.row().classes('items-center gap-2'):
        ui.chip('LADBS').props('outline size=sm')
        ui.icon('block', color='grey')
    ui.label('Building Permit').classes('font-semibold line-through text-gray-500')
    ui.label('Skipped - Not required').classes('text-xs text-gray-400')
```

---

## Status Action Summary

| Status | NiceGUI Card Classes | Icon | Click Handler |
|--------|---------------------|------|---------------|
| `not_started` | `border-dashed border-gray-300` | `radio_button_unchecked` | `show_step_details(step)` |
| `blocked` | `border-dashed border-gray-400 bg-gray-100` | `lock` | `show_blocking_steps(step)` |
| `ready` | `border-2 border-blue-500 bg-blue-50` | `play_arrow` | `show_step_details(step)` |
| `in_progress` | `border-l-4 border-blue-500 bg-blue-50` | `ui.spinner()` | `show_progress(step)` |
| `awaiting_user` | `border-2 border-orange-400 bg-orange-50` | `bolt` | `show_user_action(step)` |
| `completed` | `border-l-4 border-green-500` | `check_circle` | `show_result(step)` |
| `failed` | `border-2 border-red-500 bg-red-50` | `error` | `show_error_with_retry(step)` |
| `skipped` | `opacity-60 bg-gray-100` | `block` | `show_skip_reason(step)` |

---

## Edge (Dependency) Design with Mermaid

Mermaid handles edge styling through link definitions:

```python
# Edge styling in Mermaid based on source status
def get_edge_style(source_status: str) -> str:
    """Return Mermaid linkStyle for edges based on source step status."""
    styles = {
        'completed': 'stroke:#16a34a,stroke-width:2',      # Green solid
        'in_progress': 'stroke:#2563eb,stroke-dasharray:5', # Blue dashed  
        'not_started': 'stroke:#9ca3af,stroke-dasharray:3', # Gray dotted
        'blocked': 'stroke:#6b7280,stroke-dasharray:3',     # Gray dotted
        'failed': 'stroke:#dc2626,stroke-dasharray:5',      # Red dashed
    }
    return styles.get(source_status, 'stroke:#9ca3af')

# Example: Parallel dependencies merging to single step
ui.mermaid('''
graph TD
    P1[Electrical Permit] --> I1[Inspection]
    P2[Building Permit] --> I1
    U1[Interconnection] --> I1
    
    style P1 fill:#bbf7d0,stroke:#16a34a
    style P2 fill:#bbf7d0,stroke:#16a34a
    style U1 fill:#bfdbfe,stroke:#2563eb
    style I1 fill:#f5f5f5,stroke:#9ca3af,stroke-dasharray:5
    
    linkStyle 0 stroke:#16a34a,stroke-width:2
    linkStyle 1 stroke:#16a34a,stroke-width:2
    linkStyle 2 stroke:#2563eb,stroke-dasharray:5
''')
```

---

## Graph Layout

Mermaid `graph TD` (top-down) creates hierarchical DAG layouts automatically:

```python
# Example: Complex dependency graph
ui.mermaid('''
graph TD
    subgraph Permits
        P1[Electrical<br/>LADBS]
        P2[Mechanical<br/>LADBS]
        P3[Building<br/>LADBS]
    end
    
    subgraph Utilities
        U1[TOU Rate<br/>LADWP]
        U2[Interconnection<br/>LADWP]
    end
    
    P1 --> I1[Inspection<br/>LADBS]
    P2 --> I1
    P3 --> I1
    U1 --> I2[Final Check<br/>LADWP]
    U2 --> I2
    I1 --> F1[Final Signoff]
    I2 --> F1
    
    %% Status styling
    style P1 fill:#bbf7d0,stroke:#16a34a
    style P2 fill:#bbf7d0,stroke:#16a34a
    style P3 fill:#bbf7d0,stroke:#16a34a
    style U1 fill:#bbf7d0,stroke:#16a34a
    style U2 fill:#bfdbfe,stroke:#2563eb
    style I1 fill:#fed7aa,stroke:#ea580c,stroke-width:3
    style I2 fill:#f5f5f5,stroke:#9ca3af,stroke-dasharray:5
    style F1 fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5
''').classes('w-full')

---

## Wireframes by Complexity

### Empty State (New Project)

```
┌────────────────────────────────────────┐
│ 📊 PROJECT PLAN               [⚙️]  │
├────────────────────────────────────────┤
│                                        │
│                                        │
│               📋                       │
│                                        │
│          No plan yet                   │
│                                        │
│    ────────────────────────             │
│                                        │
│    As we discuss your project,         │
│    I'll build a step-by-step           │
│    plan here showing:                  │
│                                        │
│    • What permits you need             │
│    • Which agencies to work with       │
│    • Dependencies between steps        │
│    • Your progress                      │
│                                        │
└────────────────────────────────────────┘
```

```python
# Empty state when no plan exists yet
with ui.right_drawer(value=True).classes('w-96 bg-gray-50'):
    with ui.row().classes('w-full items-center p-4 border-b'):
        ui.icon('timeline').classes('text-xl')
        ui.label('PROJECT PLAN').classes('font-bold')
    
    # Empty state card
    with ui.card().classes('m-4 text-center'):
        ui.icon('assignment', size='xl').classes('text-gray-400 mb-4')
        ui.label('No plan yet').classes('text-lg font-medium text-gray-600')
        ui.separator().classes('my-4')
        with ui.column().classes('gap-2 text-sm text-gray-500 text-left'):
            ui.label("As we discuss your project, I'll build a step-by-step plan here showing:")
            with ui.column().classes('pl-4 gap-1'):
                ui.label('• What permits you need')
                ui.label('• Which agencies to work with')
                ui.label('• Dependencies between steps')
                ui.label('• Your progress')
```

### Simple Linear Plan (3-4 Steps)

```
┌────────────────────────────────────────┐
│ 📊 PROJECT PLAN               [⚙️]  │
├────────────────────────────────────────┤
│ Progress: ████░░░░░░  1/3 steps     │
├────────────────────────────────────────┤
│                                        │
│           ┌──────────────────┐         │
│           │ D1 Check         │         │
│           │ Eligibility  ✓   │         │
│           │ LASAN            │         │
│           └────────┬─────────┘         │
│                    │                   │
│                    ▼                   │
│           ╭──────────────────╮         │
│           │ D2 Schedule      │         │
│           │ Pickup       ⚡  │  ← Action│
│           │ LASAN            │         │
│           ╰────────┬─────────╯         │
│                    │                   │
│                    ▼                   │
│           ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐         │
│           ╌ D3 Confirm       ╌         │
│           ╌ Pickup       🔒  ╌← Blocked │
│           ╌ LASAN            ╌         │
│           └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘         │
│                                        │
├────────────────────────────────────────┤
│ ⚡ 1 action needs your attention       │
│                       [View Task]      │
└────────────────────────────────────────┘
```

```python
# Simple linear plan - e.g., Bulk pickup request
with ui.right_drawer(value=True).classes('w-96 bg-gray-50'):
    with ui.row().classes('w-full items-center p-4 border-b'):
        ui.icon('timeline')
        ui.label('PROJECT PLAN').classes('font-bold flex-grow')
    
    with ui.row().classes('px-4 py-2 gap-2'):
        ui.label('Progress:').classes('text-sm text-gray-500')
        ui.linear_progress(value=0.4, show_value=True).classes('flex-grow')
        ui.label('1/3 steps').classes('text-xs text-gray-500')
    
    with ui.scroll_area().classes('flex-grow p-4'):
        # Mermaid for linear flow
        ui.mermaid('''
graph TD
    D1[Check Eligibility<br/>LASAN] --> D2[Schedule Pickup<br/>LASAN]
    D2 --> D3[Confirm Pickup<br/>LASAN]
    
    style D1 fill:#bbf7d0,stroke:#16a34a
    style D2 fill:#fed7aa,stroke:#ea580c,stroke-width:3
    style D3 fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5
    
    linkStyle 0 stroke:#16a34a,stroke-width:2
    linkStyle 1 stroke:#9ca3af,stroke-dasharray:3
''').classes('w-full')
    
    # Action needed footer
    with ui.card().classes('mx-4 mb-4 bg-orange-50 border-orange-300'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('bolt', color='warning')
            ui.label('1 action needs your attention').classes('text-sm')
        ui.button('View Task', on_click=show_pending).props('flat color=warning')
```

### Medium Complexity (John's Renovation ~10 Steps)

```
┌───────────────────────────────────────────────────────────────┐
│                    ╔═══════════ Permits ══════════╗              │
│                    ║                                   ║              │
│      ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│      │ P1 Elec  │  │ P2 Mech  │  │ P3 Build │              │
│      │ ✓ LADBS  │  │ ✓ LADBS  │  │ ✓ LADBS  │              │
│      └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│           │            │            │                    │
│           └────────────┼────────────┘                    │
│                        │                                  │
│      ┌──────────┐        │        ┌──────────┐            │
│      │ U1 TOU   │        │        │ U2 Inter │            │
│      │ ✓ LADWP  │        │        │ ◐ LADWP  │            │
│      └────┬─────┘        │        └────┬─────┘            │
│           │              │              │                  │
│           └──────────────┼──────────────┘                  │
│                          ▼                                │
│              ╭─────────────────╮                            │
│              │ I1 Inspection  │  ← Action needed           │
│              │ ⚡ LADBS        │                            │
│              ╰────────┬────────╯                            │
│                      │                                     │
│           ┌──────────┴───────────┐                        │
│           ▼                      ▼                        │
│  ┌╌╌╌╌╌╌╌╌╌╌╌╌┐  ┌╌╌╌╌╌╌╌╌╌╌╌╌┐  ┌╌╌╌╌╌╌╌╌╌╌╌╌┐          │
│  ╌ D1 Bulky   ╌  ╌ D2 E-waste  ╌  ╌ F1 Final   ╌          │
│  ╌ ○ LASAN    ╌  ╌ ○ LASAN    ╌  ╌ 🔒 LADWP    ╌          │
│  └╌╌╌╌╌╌╌╌╌╌╌╌┘  └╌╌╌╌╌╌╌╌╌╌╌╌┘  └╌╌╌╌╌╌╌╌╌╌╌╌┘          │
│                                                           │
└───────────────────────────────────────────────────────────────┘

Legend: ✓ Completed | ◐ In Progress | ⚡ Action Needed | ○ Not Started | 🔒 Blocked
```

```python
# Medium complexity plan with branching
ui.mermaid('''
graph TD
    subgraph Permits
        P1[Electrical<br/>✓ LADBS]
        P2[Mechanical<br/>✓ LADBS]
        P3[Building<br/>✓ LADBS]
    end
    
    subgraph Utilities
        U1[TOU Rate<br/>✓ LADWP]
        U2[Interconnection<br/>◐ LADWP]
    end
    
    P1 --> I1
    P2 --> I1
    P3 --> I1
    U1 --> I1[Inspection<br/>⚡ LADBS]
    U2 --> I1
    
    I1 --> D1[Bulky Pickup<br/>○ LASAN]
    I1 --> D2[E-waste<br/>○ LASAN]
    
    D1 --> F1[Final Check<br/>🔒 LADWP]
    D2 --> F1
    
    F1 --> R1[Rebate<br/>🔒 LADWP]
    
    style P1 fill:#bbf7d0,stroke:#16a34a
    style P2 fill:#bbf7d0,stroke:#16a34a
    style P3 fill:#bbf7d0,stroke:#16a34a
    style U1 fill:#bbf7d0,stroke:#16a34a
    style U2 fill:#bfdbfe,stroke:#2563eb
    style I1 fill:#fed7aa,stroke:#ea580c,stroke-width:3
    style D1 fill:#f5f5f5,stroke:#9ca3af,stroke-dasharray:5
    style D2 fill:#f5f5f5,stroke:#9ca3af,stroke-dasharray:5
    style F1 fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5
    style R1 fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5
''').classes('w-full')

# Zoom controls below graph
with ui.row().classes('w-full justify-center gap-2 py-2'):
    ui.button(icon='zoom_out').props('flat round size=sm')
    ui.button(icon='zoom_in').props('flat round size=sm')
    ui.button('Fit', on_click=fit_to_view).props('flat size=sm')
```

### Complex Plan (15+ Steps)

For very large plans, enable pan/zoom with container controls:

```python
with ui.right_drawer(value=True).classes('w-96 bg-gray-50'):
    with ui.row().classes('w-full items-center p-4 border-b'):
        ui.icon('timeline')
        ui.label('PROJECT PLAN').classes('font-bold flex-grow')
        with ui.button(icon='settings').props('flat round size=sm'):
            with ui.menu():
                ui.menu_item('Toggle View')
                ui.menu_item('Zoom to Fit')
    
    with ui.row().classes('px-4 py-2 gap-2 items-center'):
        ui.label('Progress:').classes('text-sm text-gray-500')
        ui.linear_progress(value=0.25).classes('flex-grow')
        ui.label('5/20').classes('text-xs text-gray-500')
        with ui.select(['DAG', 'Timeline']).props('dense borderless').classes('w-20'):
            pass
    
    with ui.scroll_area().classes('flex-grow p-4'):
        ui.mermaid(large_plan_mermaid_string).classes('min-w-full')
    
    # Zoom controls
    with ui.row().classes('w-full justify-center gap-2 py-2 border-t'):
        ui.button(icon='remove').props('flat round size=sm')
        ui.button(icon='add').props('flat round size=sm')
        ui.button('Fit', on_click=fit_to_view).props('flat size=sm')
        ui.button('Reset', on_click=reset_view).props('flat size=sm')
    
    # Footer with status summary
    with ui.row().classes('w-full px-4 py-2 gap-4 text-sm border-t bg-gray-100'):
        with ui.row().classes('items-center gap-1'):
            ui.icon('bolt', size='xs', color='warning')
            ui.label('1 action')
        with ui.row().classes('items-center gap-1'):
            ui.icon('pending', size='xs', color='primary')
            ui.label('3 waiting')
        with ui.row().classes('items-center gap-1'):
            ui.icon('lock', size='xs', color='grey')
            ui.label('8 blocked')
    
    ui.button('View Tasks', on_click=show_tasks).props('flat color=warning').classes('mx-4 mb-4')
```

---

## Dynamic Behavior

### Plan Building (Steps Appear During Conversation)

As the agent identifies steps, nodes are dynamically added to the Mermaid diagram:

```python
# Dynamically update the plan as steps are identified
class PlanManager:
    def __init__(self):
        self.steps: List[PlanStep] = []
        self.mermaid_container = None
    
    def add_step(self, step: PlanStep):
        """Add a new step and re-render the graph."""
        self.steps.append(step)
        self._render()
    
    def _generate_mermaid(self) -> str:
        """Generate Mermaid diagram from current steps."""
        if not self.steps:
            return ''
        
        lines = ['graph TD']
        for step in self.steps:
            # Node definition
            lines.append(f'    {step.id}[{step.title}<br/>{step.agency}]')
            # Dependencies
            for dep_id in step.depends_on:
                lines.append(f'    {dep_id} --> {step.id}')
            # Styling
            lines.append(f'    style {step.id} {STATUS_STYLES.get(step.status, "")}')
        
        return '\n'.join(lines)
    
    def _render(self):
        """Re-render the Mermaid diagram."""
        self.mermaid_container.clear()
        with self.mermaid_container:
            if self.steps:
                ui.mermaid(self._generate_mermaid()).classes('w-full')
            else:
                # Empty state
                with ui.card().classes('text-center p-8'):
                    ui.icon('assignment', size='xl').classes('text-gray-400')
                    ui.label('No plan yet').classes('text-gray-600')

# Usage in page:
plan_manager = PlanManager()
with ui.scroll_area().classes('flex-grow') as container:
    plan_manager.mermaid_container = container
```

### Plan Updates (Status Changes)

When a step status changes, update the graph with visual feedback:

```python
async def update_step_status(step_id: str, new_status: str, result: dict = None):
    """Update step status with animation feedback."""
    step = get_step_by_id(step_id)
    old_status = step.status
    step.status = new_status
    step.result = result
    
    # Show brief notification
    if new_status == 'completed':
        ui.notify(f'✓ {step.title} completed', type='positive')
    elif new_status == 'awaiting_user':
        ui.notify(f'⚡ {step.title} needs your action', type='warning')
    
    # Re-render graph (Mermaid will show new styling)
    plan_manager._render()
    
    # If dependencies are unlocked, they become 'ready'
    for dependent in get_dependents(step_id):
        if all_dependencies_complete(dependent):
            await update_step_status(dependent.id, 'ready')
```

---

## Interactivity

### Node Click Behavior

Use `ui.dialog` for step details:

```python
def show_step_details(step: PlanStep):
    """Show step details in a dialog."""
    with ui.dialog() as dialog, ui.card().classes('w-80'):
        # Header
        with ui.row().classes('items-center gap-2 w-full'):
            ui.chip(step.agency).props('outline size=sm')
            ui.icon(get_status_icon(step.status), color=get_status_color(step.status))
            ui.button(icon='close', on_click=dialog.close).props('flat round size=sm').classes('ml-auto')
        
        ui.label(step.title).classes('text-lg font-semibold')
        ui.separator()
        
        # Status-specific content
        if step.status == 'completed':
            ui.label(f"Status: ✓ Completed").classes('text-green-600')
            if step.result:
                if step.result.get('permit_number'):
                    ui.label(f"Permit #: {step.result['permit_number']}")
                if step.started_at:
                    ui.label(f"Submitted: {step.started_at.strftime('%b %d, %Y')}")
                if step.completed_at:
                    ui.label(f"Approved: {step.completed_at.strftime('%b %d, %Y')}")
        
        elif step.status == 'blocked':
            ui.label("Status: 🔒 Blocked").classes('text-gray-600')
            ui.label("Waiting for:")
            for dep_id in step.depends_on:
                dep = get_step_by_id(dep_id)
                with ui.row().classes('items-center gap-2 pl-4'):
                    ui.icon(get_status_icon(dep.status), size='xs')
                    ui.label(dep.title).classes('text-sm')
        
        elif step.status == 'awaiting_user':
            ui.label("Status: ⚡ Action needed").classes('text-orange-600')
            if step.user_task:
                ui.label(step.user_task.instructions).classes('text-sm')
            ui.button('View Task', on_click=lambda: show_user_action(step)).props('color=warning')
        
        elif step.status == 'failed':
            ui.label("Status: ✗ Failed").classes('text-red-600')
            ui.label(step.result.get('error', 'An error occurred')).classes('text-sm text-red-500')
            ui.button('Retry', on_click=lambda: retry_step(step)).props('color=negative')
        
        # View in chat link
        ui.separator()
        ui.button('View in Chat', on_click=lambda: scroll_to_message(step.id)).props('flat')
    
    dialog.open()
```

### Node Action Summary

| Node State | Click Handler | Dialog Content |
|------------|---------------|----------------|
| Not Started | `show_step_details(step)` | "This step will begin when dependencies complete" |
| Blocked | `show_blocking_steps(step)` | List of blocking steps with status icons |
| Ready | `show_step_details(step)` | "Ready to start" with details |
| In Progress | `show_progress(step)` | Progress details, spinner |
| Awaiting User | `show_user_action(step)` | UserTask card with action button |
| Completed | `show_result(step)` | Permit number, dates, result details |
| Failed | `show_error_with_retry(step)` | Error message, Retry button |

### Pan and Zoom

For complex graphs, Mermaid diagrams are rendered inside a `ui.scroll_area` which provides native scrolling. For additional zoom controls:

```python
# Zoom controls for complex graphs
class GraphViewer:
    def __init__(self, container):
        self.container = container
        self.zoom_level = 1.0
    
    def zoom_in(self):
        self.zoom_level = min(2.0, self.zoom_level + 0.1)
        self._apply_zoom()
    
    def zoom_out(self):
        self.zoom_level = max(0.5, self.zoom_level - 0.1)
        self._apply_zoom()
    
    def fit_to_view(self):
        self.zoom_level = 1.0
        self._apply_zoom()
    
    def _apply_zoom(self):
        self.container.style(f'transform: scale({self.zoom_level}); transform-origin: top left')

# Control bar
with ui.row().classes('w-full justify-center gap-2 py-2 border-t'):
    ui.button(icon='remove', on_click=viewer.zoom_out).props('flat round size=sm')
    ui.button(icon='add', on_click=viewer.zoom_in).props('flat round size=sm')
    ui.button('Fit', on_click=viewer.fit_to_view).props('flat size=sm')
```

| Control | NiceGUI Implementation |
|---------|----------------------|
| Scroll | `ui.scroll_area()` |
| Zoom in/out | Button handlers with CSS transform |
| Fit to view | Reset zoom to 1.0 |
| Touch gestures | Native browser support |

---

## Widget Header Actions

Settings menu using `ui.menu`:

```python
with ui.row().classes('w-full items-center p-4 border-b'):
    ui.icon('timeline').classes('text-xl')
    ui.label('PROJECT PLAN').classes('font-bold flex-grow')
    
    with ui.button(icon='settings').props('flat round'):
        with ui.menu():
            ui.label('Display').classes('text-xs font-medium text-gray-500 px-4 pt-2')
            ui.menu_item('Show source indicators', on_click=toggle_sources, auto_close=False)
            ui.menu_item('Show automation level', on_click=toggle_automation, auto_close=False)
            ui.menu_item('Compact mode', on_click=toggle_compact, auto_close=False)
            ui.separator()
            ui.menu_item('Export as PDF', on_click=export_pdf)
```

---

## Source Indicators

Nodes display the MCP server source in a muted badge (e.g., "via ladbs"). This provides transparency about where data comes from without requiring users to understand the technical details. All source badges use the same muted gray styling for simplicity.

```python
# Source indicator in step card
with ui.card():
    with ui.row().classes('items-center gap-2'):
        ui.chip(step.agency).props('outline size=sm color=grey')
        ui.label(f'via {step.source_mcp}').classes('text-xs text-gray-400 italic')
```

---

## Mobile Plan View

On mobile, the plan widget becomes a full-screen tab accessible via bottom navigation:

### Visual Reference

```
┌─────────────────────────────────────────┐
│ ← Project Plan                  [⚙️]  │
├─────────────────────────────────────────┤
│ Progress: ████████░░ 80%              │
├─────────────────────────────────────────┤
│                                         │
│        ┌─────┐   ┌─────┐   ┌─────┐   │
│        │ P1  │   │ P2  │   │ P3  │   │
│        │  ✓  │   │  ✓  │   │  ✓  │   │
│        └──┬──┘   └──┬──┘   └──┬──┘   │
│           │         │         │       │
│           └─────────┼─────────┘       │
│                     ▼                   │
│             ╭─────────╮                 │
│             │   I1    │                 │
│             │   ⚡    │                 │
│             ╰─────────╯                 │
│                     │                   │
│                     ▼                   │
│             ┌╌╌╌╌╌╌╌╌╌┐                 │
│             ╌   F1    ╌                 │
│             ╌   🔒    ╌                 │
│             └╌╌╌╌╌╌╌╌╌┘                 │
│                                         │
├─────────────────────────────────────────┤
│ ⚡ 1 action needs your attention        │
│                        [View Task]      │
├─────────────────────────────────────────┤
│  [📁 Projects]  [💬 Chat]  [📊 Plan]   │
└─────────────────────────────────────────┘
```

### NiceGUI Implementation

```python
# Mobile plan view as a page
@ui.page('/plan')
def mobile_plan_page():
    # Back button header
    with ui.header().classes('bg-white shadow'):
        with ui.row().classes('w-full items-center px-4 py-3'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.back()).props('flat round')
            ui.label('Project Plan').classes('font-bold flex-grow')
            with ui.button(icon='settings').props('flat round'):
                with ui.menu():
                    ui.menu_item('Toggle View')
    
    # Progress bar
    with ui.row().classes('w-full px-4 py-2 gap-2'):
        ui.linear_progress(value=0.8, show_value=True).classes('flex-grow')
    
    # Full-height scrollable Mermaid graph
    with ui.scroll_area().classes('flex-grow p-4'):
        ui.mermaid(plan_mermaid_string).classes('w-full')
    
    # Action footer if needed
    if action_needed_count > 0:
        with ui.card().classes('mx-4 mb-16 bg-orange-50 border-orange-300'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('bolt', color='warning')
                ui.label(f'{action_needed_count} action needs your attention').classes('text-sm')
            ui.button('View Task', on_click=show_pending).props('flat color=warning')
    
    # Bottom navigation
    with ui.footer().classes('bg-white shadow fixed bottom-0 w-full'):
        with ui.row().classes('w-full justify-around py-2'):
            ui.button('Projects', icon='folder', on_click=lambda: ui.navigate.to('/projects')).props('flat')
            ui.button('Chat', icon='chat', on_click=lambda: ui.navigate.to('/chat')).props('flat')
            ui.button('Plan', icon='timeline').props('flat color=primary')
```

---

## Alternative: Timeline View

For linear or simple plans, use `ui.timeline` as an alternative to Mermaid DAG:

```python
# Timeline view for linear flows
with ui.timeline(side='right'):
    for step in sorted_steps:
        icon = get_status_icon(step.status)
        color = get_status_color(step.status)
        
        with ui.timeline_entry(
            title=step.title,
            subtitle=step.agency,
            icon=icon,
            color=color
        ):
            if step.status == 'completed' and step.result:
                ui.label(f"#{step.result.get('permit_number', '')}").classes('text-sm text-gray-500')
            elif step.status == 'awaiting_user':
                ui.button('Take Action', on_click=lambda s=step: show_user_action(s)).props('flat dense color=warning size=sm')
            elif step.status == 'blocked':
                ui.label(f"Waiting for: {', '.join(step.depends_on)}").classes('text-xs text-gray-400')
```

---

## Accessibility

| Requirement | NiceGUI Implementation |
|-------------|----------------------|
| Keyboard Navigation | Tab through cards, Enter to activate |
| Screen Reader | Step cards with proper semantic labels |
| High Contrast | Status colors + icons (not color-only) |
| Focus Indicators | Quasar's built-in focus rings via `.props()` |
| Alternative View | `ui.timeline` for linear, accessible layout |

```python
# Accessible step card
with ui.card().props('tabindex=0').on('keydown.enter', lambda: on_click(step)):
    ui.label(f"{step.title} - {step.status}").props('aria-label')
```

---

## Related Documentation

- [Overview](ui-wireframes-overview.md) - Layout structure
- [Chat Interface](ui-wireframes-chat.md) - Where plan updates originate
- [User Actions](ui-wireframes-user-actions.md) - Handling awaiting_user steps
- [Components](ui-wireframes-components.md) - Node and badge components
