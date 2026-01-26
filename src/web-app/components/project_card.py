"""Project card component for the Citizen Services Portal."""

from nicegui import ui
from models.project import Project, ProjectStatus, StepStatus
from datetime import datetime, timedelta
from typing import Callable, Optional


def format_relative_time(dt: Optional[datetime]) -> str:
    """Format a datetime as a human-readable relative time string."""
    if not dt:
        return "Unknown"
    
    now = datetime.now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = int(diff.days)
        if days == 1:
            return "Yesterday"
        return f"{days} days ago"
    else:
        return dt.strftime("%b %d")


def get_project_status_info(project: Project) -> tuple[str, str, str]:
    """Get status icon, color, and label for a project.
    
    Returns:
        Tuple of (icon_name, color, status_label)
    """
    # Check for pending user actions
    has_action = False
    if project.plan and project.plan.steps:
        has_action = any(
            step.status == StepStatus.AWAITING_USER 
            for step in project.plan.steps
        )
    
    if has_action:
        return ('bolt', 'warning', 'Action Needed')
    
    if project.status == ProjectStatus.COMPLETED:
        return ('check_circle', 'positive', 'Completed')
    elif project.status == ProjectStatus.CANCELLED:
        return ('cancel', 'grey', 'Cancelled')
    elif project.progress >= 1.0:
        return ('check_circle', 'positive', 'Completed')
    else:
        return ('sync', 'primary', 'In Progress')


def project_card(
    project: Project,
    is_selected: bool = False,
    on_click: Optional[Callable] = None,
) -> ui.card:
    """Render a project card.
    
    Args:
        project: The project to display.
        is_selected: Whether this project is currently selected.
        on_click: Callback function when the card is clicked.
        
    Returns:
        A NiceGUI card element representing the project.
    """
    icon, color, status_label = get_project_status_info(project)
    
    # Card styling based on selection state
    card_classes = 'w-full cursor-pointer transition-all mb-2'
    if is_selected:
        card_classes += ' border-2 border-blue-500 bg-blue-50'
    else:
        card_classes += ' hover:shadow-md'
    
    # Check for action needed
    has_action = icon == 'bolt'
    if has_action and not is_selected:
        card_classes += ' border-l-4 border-orange-400 bg-orange-50'
    
    with ui.card().classes(card_classes) as card:
        if on_click:
            card.on('click', on_click)
        
        # Header row: icon, title, status chip
        with ui.row().classes('items-center gap-2 w-full'):
            ui.icon(icon, color=color)
            ui.label(project.title).classes('font-semibold flex-grow truncate')
            ui.chip(status_label, color=color).props('size=sm')
        
        # Description
        if project.description:
            ui.label(project.description).classes('text-sm text-gray-600 truncate')
        
        # Progress bar
        with ui.row().classes('items-center gap-2 mt-2 w-full'):
            ui.linear_progress(
                value=project.progress,
            ).props(f'color={color}').classes('flex-grow')
            ui.label(f'{int(project.progress * 100)}%').classes('text-xs text-gray-500 w-8 text-right')
        
        # Last updated
        ui.label(f'Updated {format_relative_time(project.updated_at)}').classes('text-xs text-gray-400 mt-1')
    
    return card
