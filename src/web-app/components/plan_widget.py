"""Plan widget component for the Citizen Services Portal."""

from nicegui import ui
from models.project import Project, PlanStep, StepStatus, ActionType
from typing import Optional


# Step type stroke colors (outline) - bolder colors for visibility
STEP_TYPE_STROKES = {
    'PRM': '#2563eb',  # blue-600 - Permit
    'INS': '#16a34a',  # green-600 - Inspection
    'TRD': '#ea580c',  # orange-600 - Trade
    'APP': '#9333ea',  # purple-600 - Application
    'SCH': '#0891b2',  # cyan-600 - Schedule
    'ENR': '#db2777',  # pink-600 - Enroll
    'DOC': '#ca8a04',  # yellow-600 - Document
    'PAY': '#dc2626',  # red-600 - Payment
}

# Status fill colors (background)
STATUS_FILLS = {
    StepStatus.NOT_STARTED: '#f5f5f5',  # gray-100
    StepStatus.BLOCKED: '#e5e7eb',  # gray-200
    StepStatus.READY: '#dbeafe',  # blue-100
    StepStatus.IN_PROGRESS: '#bfdbfe',  # blue-200
    StepStatus.AWAITING_USER: '#fed7aa',  # orange-200
    StepStatus.COMPLETED: '#bbf7d0',  # green-200
    'not_started': '#f5f5f5',
    'blocked': '#e5e7eb',
    'ready': '#dbeafe',
    'in_progress': '#bfdbfe',
    'awaiting_user': '#fed7aa',
    'completed': '#bbf7d0',
    'failed': '#fecaca',  # red-200
}

# Icons for action types (used in node labels) - only two types now
ACTION_TYPE_ICONS = {
    ActionType.AUTOMATED: '🤖',
    ActionType.USER_ACTION: '👤',
    'automated': '🤖',
    'user_action': '👤',
}


def get_step_type_from_id(step_id: str) -> str | None:
    """Extract step type prefix from step ID (e.g., 'PRM-1' -> 'PRM')."""
    if '-' in step_id:
        prefix = step_id.split('-')[0].upper()
        if prefix in STEP_TYPE_STROKES:
            return prefix
    return None


def render_plan_mermaid(steps: list[PlanStep]) -> str:
    """Generate Mermaid diagram code for the plan steps.
    
    Args:
        steps: List of plan steps to visualize.
        
    Returns:
        Mermaid diagram code string.
    """
    lines = ['graph TD']
    
    # Debug: print all steps and their dependencies
    print(f"[DEBUG render_plan_mermaid] Rendering {len(steps)} steps:")
    for s in steps:
        print(f"  Step {s.id}: depends_on={s.depends_on} (type={type(s.depends_on)})")
    
    def mermaid_safe_id(step_id: str) -> str:
        """Convert step ID to Mermaid-safe node ID (replace hyphens with underscores)."""
        return step_id.replace('-', '_')
    
    for step in steps:
        # Get action type icon
        action_type = getattr(step, 'action_type', None)
        if action_type:
            action_key = action_type.value if hasattr(action_type, 'value') else action_type
        else:
            action_key = 'automated'
        icon = ACTION_TYPE_ICONS.get(action_type, ACTION_TYPE_ICONS.get(action_key, ''))
        
        # Use Mermaid-safe ID for node, but show original ID + title in label
        safe_node_id = mermaid_safe_id(step.id)
        # Escape quotes and special characters in title
        safe_title = step.title.replace('"', "'")
        # Include step ID in the label so it's visible
        if icon:
            lines.append(f'    {safe_node_id}["{icon} {step.id}: {safe_title}"]')
        else:
            lines.append(f'    {safe_node_id}["{step.id}: {safe_title}"]')
        
        # Edges from dependencies (also convert dep IDs to safe format)
        depends = step.depends_on or []
        for dep_id in depends:
            safe_dep_id = mermaid_safe_id(dep_id)
            lines.append(f'    {safe_dep_id} --> {safe_node_id}')
        
        # Build combined style: status fill (background) + step type stroke (outline)
        step_type = get_step_type_from_id(step.id)
        status = step.status
        status_key = status.value if isinstance(status, StepStatus) else status
        
        # Get status fill color for background
        fill_color = STATUS_FILLS.get(status, STATUS_FILLS.get(status_key, '#f5f5f5'))
        
        if step_type and step_type in STEP_TYPE_STROKES:
            # Use step type for stroke color (bold, continuous outline)
            stroke_color = STEP_TYPE_STROKES[step_type]
            style = f'fill:{fill_color},stroke:{stroke_color},stroke-width:3'
        else:
            # Fallback to gray outline if step type not recognized
            style = f'fill:{fill_color},stroke:#6b7280,stroke-width:2'
        
        if style:
            lines.append(f'    style {safe_node_id} {style}')
    
    return '\n'.join(lines)


def plan_widget(project: Optional[Project]) -> ui.column:
    """Render the plan widget (right drawer content).
    
    Args:
        project: The currently selected project.
        
    Returns:
        A NiceGUI column element containing the plan widget.
    """
    with ui.column().classes('w-full h-full') as widget:
        # Header
        with ui.row().classes('w-full items-center p-4 border-b'):
            ui.icon('timeline').classes('text-xl')
            ui.label('PROJECT PLAN').classes('font-bold flex-grow')
        
        if project and project.plan and project.plan.steps:
            steps = project.plan.steps
            
            # Calculate progress
            total = len(steps)
            completed = sum(1 for s in steps if s.status == StepStatus.COMPLETED)
            progress = completed / total if total > 0 else 0
            
            # Count actions needed
            actions_needed = sum(1 for s in steps if s.status == StepStatus.AWAITING_USER)
            
            # Progress summary
            with ui.row().classes('w-full items-center px-4 py-2 gap-2'):
                ui.label('Progress:').classes('text-sm text-gray-500')
                ui.linear_progress(value=progress, show_value=False).classes('flex-grow')
                ui.label(f'{completed}/{total} steps').classes('text-xs text-gray-500')
            
            ui.separator()
            
            # Graph container
            with ui.scroll_area().classes('flex-grow p-4'):
                mermaid_code = render_plan_mermaid(steps)
                ui.mermaid(mermaid_code).classes('w-full')
                
                # Legend
                with ui.column().classes('mt-4 gap-2'):
                    ui.label('Status (background):').classes('text-xs text-gray-500 font-semibold')
                    with ui.row().classes('gap-4 flex-wrap'):
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-green-200 border border-gray-400')
                            ui.label('Completed').classes('text-xs')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-blue-200 border border-gray-400')
                            ui.label('In Progress').classes('text-xs')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-orange-200 border border-gray-400')
                            ui.label('Action Needed').classes('text-xs')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-gray-100 border border-gray-400')
                            ui.label('Not Started').classes('text-xs')
                    
                    ui.label('Action Type:').classes('text-xs text-gray-500 font-semibold mt-2')
                    with ui.row().classes('gap-4 flex-wrap'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label('🤖').classes('text-sm')
                            ui.label('Automated').classes('text-xs')
                        with ui.row().classes('items-center gap-1'):
                            ui.label('👤').classes('text-sm')
                            ui.label('User Action').classes('text-xs')
                    
                    ui.label('Step Type (outline):').classes('text-xs text-gray-500 font-semibold mt-2')
                    with ui.row().classes('gap-3 flex-wrap'):
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-white border-2 border-blue-600')
                            ui.label('PRM').classes('text-xs font-mono')
                            ui.label('Permit').classes('text-xs text-gray-500')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-white border-2 border-green-600')
                            ui.label('INS').classes('text-xs font-mono')
                            ui.label('Inspection').classes('text-xs text-gray-500')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-white border-2 border-orange-600')
                            ui.label('TRD').classes('text-xs font-mono')
                            ui.label('Trade').classes('text-xs text-gray-500')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-white border-2 border-purple-600')
                            ui.label('APP').classes('text-xs font-mono')
                            ui.label('Application').classes('text-xs text-gray-500')
                    with ui.row().classes('gap-3 flex-wrap'):
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-white border-2 border-cyan-600')
                            ui.label('SCH').classes('text-xs font-mono')
                            ui.label('Schedule').classes('text-xs text-gray-500')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-white border-2 border-pink-600')
                            ui.label('ENR').classes('text-xs font-mono')
                            ui.label('Enroll').classes('text-xs text-gray-500')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-white border-2 border-yellow-600')
                            ui.label('DOC').classes('text-xs font-mono')
                            ui.label('Document').classes('text-xs text-gray-500')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-white border-2 border-red-600')
                            ui.label('PAY').classes('text-xs font-mono')
                            ui.label('Payment').classes('text-xs text-gray-500')
            
            # Action needed footer
            if actions_needed > 0:
                with ui.card().classes('mx-4 mb-4 bg-orange-50 border border-orange-300'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('bolt', color='warning')
                        action_text = f'{actions_needed} action{"s" if actions_needed > 1 else ""} need{"" if actions_needed > 1 else "s"} your attention'
                        ui.label(action_text).classes('text-sm flex-grow')
                    ui.button('View in Chat', on_click=lambda: None).props('flat color=warning size=sm')
        else:
            # Empty state
            with ui.column().classes('w-full h-full items-center justify-center p-8'):
                ui.icon('assignment', size='xl').classes('text-gray-400')
                ui.label('No plan yet').classes('text-lg font-semibold mt-4 text-gray-500')
                ui.label(
                    "As we discuss your project, I'll build a step-by-step plan here."
                ).classes('text-center text-gray-400 text-sm mt-2')
    
    return widget
