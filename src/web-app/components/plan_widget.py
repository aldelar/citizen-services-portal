"""Plan widget component for the Citizen Services Portal."""

from nicegui import ui
from models.project import Project, PlanStep, StepStatus, ActionType
from typing import Optional


# Mermaid styling for different step statuses
STATUS_STYLES = {
    StepStatus.NOT_STARTED: 'fill:#f5f5f5,stroke:#9ca3af,stroke-dasharray:5',
    StepStatus.BLOCKED: 'fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5',
    StepStatus.READY: 'fill:#dbeafe,stroke:#3b82f6',
    StepStatus.IN_PROGRESS: 'fill:#bfdbfe,stroke:#2563eb',
    StepStatus.AWAITING_USER: 'fill:#fed7aa,stroke:#ea580c,stroke-width:3',
    StepStatus.COMPLETED: 'fill:#bbf7d0,stroke:#16a34a',
    'not_started': 'fill:#f5f5f5,stroke:#9ca3af,stroke-dasharray:5',
    'blocked': 'fill:#e5e7eb,stroke:#6b7280,stroke-dasharray:5',
    'ready': 'fill:#dbeafe,stroke:#3b82f6',
    'in_progress': 'fill:#bfdbfe,stroke:#2563eb',
    'awaiting_user': 'fill:#fed7aa,stroke:#ea580c,stroke-width:3',
    'completed': 'fill:#bbf7d0,stroke:#16a34a',
    'failed': 'fill:#fecaca,stroke:#dc2626',
}

# Icons for action types (used in node labels)
ACTION_TYPE_ICONS = {
    ActionType.AUTOMATED: '🤖',
    ActionType.USER_ACTION: '👤',
    ActionType.INFORMATION: 'ℹ️',
    'automated': '🤖',
    'user_action': '👤',
    'information': 'ℹ️',
}


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
    
    for step in steps:
        # Get action type icon
        action_type = getattr(step, 'action_type', None)
        if action_type:
            action_key = action_type.value if hasattr(action_type, 'value') else action_type
        else:
            action_key = 'automated'
        icon = ACTION_TYPE_ICONS.get(action_type, ACTION_TYPE_ICONS.get(action_key, ''))
        
        # Node with label including action type icon
        # Escape quotes and special characters in title
        safe_title = step.title.replace('"', "'")
        if icon:
            lines.append(f'    {step.id}["{icon} {safe_title}"]')
        else:
            lines.append(f'    {step.id}["{safe_title}"]')
        
        # Edges from dependencies
        depends = step.depends_on or []
        for dep_id in depends:
            lines.append(f'    {dep_id} --> {step.id}')
        
        # Status styling
        status = step.status
        status_key = status.value if isinstance(status, StepStatus) else status
        style = STATUS_STYLES.get(status, STATUS_STYLES.get(status_key, ''))
        if style:
            lines.append(f'    style {step.id} {style}')
    
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
                    ui.label('Status:').classes('text-xs text-gray-500 font-semibold')
                    with ui.row().classes('gap-4 flex-wrap'):
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-green-200 border border-green-600')
                            ui.label('Completed').classes('text-xs')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-blue-200 border border-blue-600')
                            ui.label('In Progress').classes('text-xs')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-orange-200 border-2 border-orange-600')
                            ui.label('Action Needed').classes('text-xs')
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded bg-gray-200 border border-gray-500 border-dashed')
                            ui.label('Blocked').classes('text-xs')
                    
                    ui.label('Step Type:').classes('text-xs text-gray-500 font-semibold mt-2')
                    with ui.row().classes('gap-4 flex-wrap'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label('🤖').classes('text-sm')
                            ui.label('Automated').classes('text-xs')
                        with ui.row().classes('items-center gap-1'):
                            ui.label('👤').classes('text-sm')
                            ui.label('User Action').classes('text-xs')
                        with ui.row().classes('items-center gap-1'):
                            ui.label('ℹ️').classes('text-sm')
                            ui.label('Information').classes('text-xs')
            
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
