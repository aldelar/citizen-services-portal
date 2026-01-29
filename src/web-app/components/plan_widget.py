"""Plan widget component for the Citizen Services Portal."""

from nicegui import ui
from models.project import Project, PlanStep, StepStatus, ActionType, ProjectStatus
from typing import Optional, Callable, Awaitable


# Agency border colors (stroke)
AGENCY_STROKES = {
    'LADBS': '#3b82f6',  # lighter blue (blue-500)
    'LADWP': '#a855f7',  # lighter purple (purple-500)
    'LASAN': '#22c55e',  # lighter green (green-500)
    'ladbs': '#3b82f6',
    'ladwp': '#a855f7',
    'lasan': '#22c55e',
}

# Step type colors (for text coloring)
STEP_TYPE_COLORS = {
    'PRM': '#2563eb',  # blue-600 - Permit
    'INS': '#16a34a',  # green-600 - Inspection
    'TRD': '#ea580c',  # orange-600 - Trade
    'APP': '#9333ea',  # purple-600 - Application
    'PCK': '#0891b2',  # cyan-600 - Pickup
    'ENR': '#db2777',  # pink-600 - Enroll
    'DOC': '#ca8a04',  # yellow-600 - Document
    'PAY': '#dc2626',  # red-600 - Payment
}

# Status fill colors (background)
STATUS_FILLS = {
    StepStatus.DEFINED: '#f5f5f5',  # gray-100
    StepStatus.SCHEDULED: '#dbeafe',  # blue-100
    StepStatus.IN_PROGRESS: '#bfdbfe',  # blue-200
    StepStatus.COMPLETED: '#bbf7d0',  # green-200
    StepStatus.NEEDS_REWORK: '#fed7aa',  # orange-200
    StepStatus.REJECTED: '#fecaca',  # red-200
    'defined': '#f5f5f5',
    'scheduled': '#dbeafe',
    'in_progress': '#bfdbfe',
    'completed': '#bbf7d0',
    'needs_rework': '#fed7aa',
    'rejected': '#fecaca',
}

# Status icons
STATUS_ICONS = {
    StepStatus.DEFINED: 'ℹ️',
    StepStatus.SCHEDULED: '📅',
    StepStatus.IN_PROGRESS: '⏳',
    StepStatus.COMPLETED: '✅',
    StepStatus.NEEDS_REWORK: '⚠️',
    StepStatus.REJECTED: '❌',
    'defined': 'ℹ️',
    'scheduled': '📅',
    'in_progress': '⏳',
    'completed': '✅',
    'needs_rework': '⚠️',
    'rejected': '❌',
}

# Agency icons
AGENCY_ICONS = {
    'LADBS': '🏗️',
    'LADWP': '⚡',
    'LASAN': '♻️',
    'ladbs': '🏗️',
    'ladwp': '⚡',
    'lasan': '♻️',
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
        if prefix in STEP_TYPE_COLORS:
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
        action_icon = ACTION_TYPE_ICONS.get(action_type, ACTION_TYPE_ICONS.get(action_key, ''))
        
        # Get agency icon
        agency = getattr(step, 'agency', None) or ''
        agency_icon = AGENCY_ICONS.get(agency, AGENCY_ICONS.get(agency.lower() if agency else '', ''))
        
        # Extract result reference (permit number, application ID, etc.)
        result_ref = None
        result = getattr(step, 'result', None)
        if result and isinstance(result, dict):
            # Look for common reference fields
            for key in ['permit_number', 'application_id', 'reference_number', 'confirmation_number', 'request_id', 'id']:
                if key in result and result[key]:
                    result_ref = str(result[key])
                    break
        
        # Get estimated duration (only for automated steps)
        est_duration = getattr(step, 'estimated_duration_days', None)
        duration_text = None
        # Skip duration for user-driven steps - timing is up to the user
        is_user_driven = action_key == 'user_action'
        if est_duration is not None and est_duration > 0 and not is_user_driven:
            if est_duration >= 1:
                days = int(est_duration)
                duration_text = f"~{days} day{'s' if days != 1 else ''}"
            else:
                hours = int(est_duration * 24)
                duration_text = f"~{hours} hour{'s' if hours != 1 else ''}"
        
        # Use Mermaid-safe ID for node, but show original ID + title in label
        safe_node_id = mermaid_safe_id(step.id)
        # Escape quotes and special characters in title
        safe_title = step.title.replace('"', "'")
        
        # Color-code the step ID based on step type
        step_type = get_step_type_from_id(step.id)
        if step_type and step_type in STEP_TYPE_COLORS:
            step_color = STEP_TYPE_COLORS[step_type]
            colored_step_id = f"<b style='color:{step_color}'>{step.id}</b>"
        else:
            colored_step_id = f"<b>{step.id}</b>"
        
        # Include action type icon in the label (no agency icon)
        label_prefix = action_icon if action_icon else ''
        
        # Build secondary line with result and/or duration
        secondary_parts = []
        if result_ref:
            secondary_parts.append(f"<b>{result_ref}</b>")
        if duration_text:
            secondary_parts.append(f"<i style='color:#1565C0;font-size:0.85em'>{duration_text}</i>")
        secondary_line = " · ".join(secondary_parts) if secondary_parts else None
        
        # Build label with optional secondary line
        if secondary_line:
            if label_prefix:
                lines.append(f'    {safe_node_id}["{label_prefix} {colored_step_id}: {safe_title}<br/>{secondary_line}"]')
            else:
                lines.append(f'    {safe_node_id}["{colored_step_id}: {safe_title}<br/>{secondary_line}"]')
        else:
            if label_prefix:
                lines.append(f'    {safe_node_id}["{label_prefix} {colored_step_id}: {safe_title}"]')
            else:
                lines.append(f'    {safe_node_id}["{colored_step_id}: {safe_title}"]')
        
        # Edges from dependencies (also convert dep IDs to safe format)
        depends = step.depends_on or []
        for dep_id in depends:
            safe_dep_id = mermaid_safe_id(dep_id)
            lines.append(f'    {safe_dep_id} --> {safe_node_id}')
        
        # Build combined style: status fill (background) + agency stroke (outline)
        status = step.status
        status_key = status.value if isinstance(status, StepStatus) else status
        
        # Get status fill color for background
        fill_color = STATUS_FILLS.get(status, STATUS_FILLS.get(status_key, '#f5f5f5'))
        
        # Get agency stroke color for border
        agency_upper = agency.upper() if agency else ''
        if agency_upper in AGENCY_STROKES:
            stroke_color = AGENCY_STROKES[agency_upper]
            # Lighter border for user action steps
            if action_key == 'user_action':
                style = f'fill:{fill_color},stroke:{stroke_color},stroke-width:2'
            else:
                style = f'fill:{fill_color},stroke:{stroke_color},stroke-width:4'
        else:
            # Fallback to gray outline if agency not recognized
            style = f'fill:{fill_color},stroke:#6b7280,stroke-width:2'
        
        if style:
            lines.append(f'    style {safe_node_id} {style}')
    
    return '\n'.join(lines)


def plan_widget(
    project: Optional[Project],
    on_view_action: Optional[Callable[[], Awaitable[None]]] = None,
    on_step_click: Optional[Callable[[str], Awaitable[None]]] = None,
    on_complete: Optional[Callable[[str, str], Awaitable[None]]] = None,
) -> ui.column:
    """Render the plan widget (right drawer content).
    
    Args:
        project: The currently selected project.
        on_view_action: Callback when "View in Chat" is clicked.
        on_step_click: Callback when a step is clicked, receives step_id.
        on_complete: Callback when action card is marked complete.
        
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
            
            # Count actions needed (steps with action cards in SCHEDULED or IN_PROGRESS state)
            actions_needed = sum(
                1 for s in steps 
                if s.status in [StepStatus.SCHEDULED, StepStatus.IN_PROGRESS] 
                and hasattr(s, 'user_action_card') 
                and s.user_action_card is not None
            )
            
            # Progress summary
            with ui.row().classes('w-full items-center px-4 py-2 gap-2'):
                ui.label('Progress:').classes('text-sm text-gray-500')
                # Use green progress bar for 100% progress
                progress_color = 'positive' if progress >= 1.0 else 'primary'
                ui.linear_progress(value=progress, show_value=False).props(f'color={progress_color}').classes('flex-grow')
                ui.label(f'{completed}/{total} steps').classes('text-xs text-gray-500')
            
            ui.separator()
            
            # Action cards for SCHEDULED or IN_PROGRESS steps with user_action_card
            in_progress_cards = [
                (step, step.user_action_card) 
                for step in steps 
                if step.status in [StepStatus.SCHEDULED, StepStatus.IN_PROGRESS] and step.user_action_card
            ]
            
            if in_progress_cards:
                from components.inline_action_card import render_inline_action_card
                
                with ui.column().classes('w-full px-4 py-2 gap-2 bg-blue-50'):
                    ui.label('Actions Needed').classes('text-xs font-bold text-gray-700 uppercase')
                    
                    for step, action_card in in_progress_cards:
                        try:
                            # Import here to avoid circular dependency
                            from models.project import UserActionCard
                            
                            # Convert dict to UserActionCard if needed
                            if isinstance(action_card, dict):
                                card_obj = UserActionCard(**action_card)
                            else:
                                card_obj = action_card
                            
                            render_inline_action_card(
                                action_card=card_obj,
                                on_complete=on_complete,
                                on_help=None,
                                initially_expanded=False
                            )
                        except Exception as e:
                            print(f"[ERROR plan_widget] Failed to render card: {e}")
                            import traceback
                            traceback.print_exc()
                
                ui.separator()
                        
            # Graph container
            with ui.scroll_area().classes('flex-grow p-4'):
                mermaid_code = render_plan_mermaid(steps)
                ui.mermaid(mermaid_code).classes('w-full')
                
                # Legend - 2x2 Quadrant Layout
                with ui.column().classes('mt-4 gap-3 w-full'):
                    # Top row: Action Type | Agency
                    with ui.row().classes('w-full').style('gap: 1rem;'):
                        # Action Type (left) - takes 50%
                        with ui.column().classes('gap-1').style('width: calc(50% - 0.5rem);'):
                            ui.label('Action Type:').classes('text-xs text-gray-700 font-bold mb-1')
                            with ui.row().classes('gap-3 flex-wrap'):
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('🤖').classes('text-sm')
                                    ui.label('Automated').classes('text-xs')
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('👤').classes('text-sm')
                                    ui.label('User Action').classes('text-xs')
                        
                        # Agency (right) - takes 50%
                        with ui.column().classes('gap-1').style('width: calc(50% - 0.5rem);'):
                            ui.label('Agency:').classes('text-xs text-gray-700 font-bold mb-1')
                            with ui.row().classes('gap-3 flex-wrap'):
                                with ui.row().classes('items-center gap-1'):
                                    ui.element('div').classes('w-2.5 h-2.5 rounded bg-white border-4').style('border-color: #3b82f6')
                                    ui.label('LADBS').classes('text-xs font-mono')
                                with ui.row().classes('items-center gap-1'):
                                    ui.element('div').classes('w-2.5 h-2.5 rounded bg-white border-4').style('border-color: #a855f7')
                                    ui.label('LADWP').classes('text-xs font-mono')
                                with ui.row().classes('items-center gap-1'):
                                    ui.element('div').classes('w-2.5 h-2.5 rounded bg-white border-4').style('border-color: #22c55e')
                                    ui.label('LASAN').classes('text-xs font-mono')
                    
                    ui.separator()
                    
                    # Bottom row: Status | Step Type
                    with ui.row().classes('w-full').style('gap: 1rem;'):
                        # Status (left) - takes 50%
                        with ui.column().classes('gap-1').style('width: calc(50% - 0.5rem);'):
                            ui.label('Status:').classes('text-xs text-gray-700 font-bold mb-1')
                            with ui.row().classes('gap-2 flex-wrap'):
                                with ui.row().classes('items-center gap-1'):
                                    ui.element('div').classes('w-2.5 h-2.5 rounded bg-gray-100 border border-gray-400')
                                    ui.label('Defined').classes('text-xs')
                                with ui.row().classes('items-center gap-1'):
                                    ui.element('div').classes('w-2.5 h-2.5 rounded bg-blue-100 border border-gray-400')
                                    ui.label('Scheduled').classes('text-xs')
                                with ui.row().classes('items-center gap-1'):
                                    ui.element('div').classes('w-2.5 h-2.5 rounded bg-blue-200 border border-gray-400')
                                    ui.label('In Progress').classes('text-xs')
                                with ui.row().classes('items-center gap-1'):
                                    ui.element('div').classes('w-2.5 h-2.5 rounded bg-green-200 border border-gray-400')
                                    ui.label('Completed').classes('text-xs')
                                with ui.row().classes('items-center gap-1'):
                                    ui.element('div').classes('w-2.5 h-2.5 rounded bg-orange-200 border border-gray-400')
                                    ui.label('Needs Rework').classes('text-xs')
                                with ui.row().classes('items-center gap-1'):
                                    ui.element('div').classes('w-2.5 h-2.5 rounded bg-red-200 border border-gray-400')
                                    ui.label('Rejected').classes('text-xs')
                        
                        # Step Type (right) - takes 50%
                        with ui.column().classes('gap-1').style('width: calc(50% - 0.5rem);'):
                            ui.label('Step Type:').classes('text-xs text-gray-700 font-bold mb-1')
                            with ui.row().classes('gap-2 flex-wrap'):
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('PRM').classes('text-xs font-mono font-bold').style('color: #2563eb')
                                    ui.label('Permit').classes('text-xs text-gray-500')
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('INS').classes('text-xs font-mono font-bold').style('color: #16a34a')
                                    ui.label('Inspection').classes('text-xs text-gray-500')
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('TRD').classes('text-xs font-mono font-bold').style('color: #ea580c')
                                    ui.label('Trade').classes('text-xs text-gray-500')
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('APP').classes('text-xs font-mono font-bold').style('color: #9333ea')
                                    ui.label('Application').classes('text-xs text-gray-500')
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('PCK').classes('text-xs font-mono font-bold').style('color: #0891b2')
                                    ui.label('Pickup').classes('text-xs text-gray-500')
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('ENR').classes('text-xs font-mono font-bold').style('color: #db2777')
                                    ui.label('Enroll').classes('text-xs text-gray-500')
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('DOC').classes('text-xs font-mono font-bold').style('color: #ca8a04')
                                    ui.label('Document').classes('text-xs text-gray-500')
                                with ui.row().classes('items-center gap-1'):
                                    ui.label('PAY').classes('text-xs font-mono font-bold').style('color: #dc2626')
                                    ui.label('Payment').classes('text-xs text-gray-500')
            
            # Action needed footer
            if actions_needed > 0:
                with ui.card().classes('mx-4 mb-4 bg-orange-50 border border-orange-300'):
                    with ui.row().classes('items-center gap-2 p-2'):
                        ui.icon('bolt', color='warning')
                        action_text = f'{actions_needed} action{"s" if actions_needed > 1 else ""} need{"" if actions_needed > 1 else "s"} your attention'
                        ui.label(action_text).classes('text-sm flex-grow')
        else:
            # Empty state
            with ui.column().classes('w-full h-full items-center justify-center p-8'):
                ui.icon('assignment', size='xl').classes('text-gray-400')
                ui.label('No plan yet').classes('text-lg font-semibold mt-4 text-gray-500')
                ui.label(
                    "As we discuss your project, I'll build a step-by-step plan here."
                ).classes('text-center text-gray-400 text-sm mt-2')
    
    return widget
