"""Status chip components for the Citizen Services Portal."""

from nicegui import ui
from models.project import StepStatus


# Status configuration: (label, color, icon)
STATUS_CONFIGS = {
    StepStatus.DEFINED: ('Not Started', 'grey', 'radio_button_unchecked'),
    StepStatus.SCHEDULED: ('Scheduled', 'primary', 'schedule'),
    StepStatus.IN_PROGRESS: ('In Progress', 'primary', 'pending'),
    StepStatus.COMPLETED: ('Completed', 'positive', 'check_circle'),
    StepStatus.NEEDS_REWORK: ('Needs Rework', 'warning', 'refresh'),
    StepStatus.REJECTED: ('Rejected', 'negative', 'cancel'),
    'defined': ('Not Started', 'grey', 'radio_button_unchecked'),
    'scheduled': ('Scheduled', 'primary', 'schedule'),
    'in_progress': ('In Progress', 'primary', 'pending'),
    'completed': ('Completed', 'positive', 'check_circle'),
    'needs_rework': ('Needs Rework', 'warning', 'refresh'),
    'rejected': ('Rejected', 'negative', 'cancel'),
}


def status_chip(status: str | StepStatus) -> ui.chip:
    """Create a status chip for a given status.
    
    Args:
        status: The status string or StepStatus enum value.
        
    Returns:
        A NiceGUI chip element styled according to the status.
    """
    # Handle both string and enum
    status_key = status.value if isinstance(status, StepStatus) else status
    
    # Get configuration or default
    config = STATUS_CONFIGS.get(status, STATUS_CONFIGS.get(status_key, ('Unknown', 'grey', 'help')))
    label, color, icon = config
    
    return ui.chip(label, icon=icon, color=color)


# Project status icons mapping
PROJECT_STATUS_ICONS = {
    'active': 'sync',
    'action_needed': 'bolt',
    'waiting': 'hourglass_empty',
    'completed': 'check_circle',
    'cancelled': 'cancel',
    'new': 'article',
}


def get_project_status_icon(status: str, has_action: bool = False) -> str:
    """Get the appropriate icon for a project status.
    
    Args:
        status: The project status string.
        has_action: Whether the project has pending user actions.
        
    Returns:
        Material icon name string.
    """
    if has_action:
        return 'bolt'
    return PROJECT_STATUS_ICONS.get(status, 'article')
