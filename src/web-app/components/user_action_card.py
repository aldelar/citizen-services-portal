"""User action card component for the Citizen Services Portal."""

from nicegui import ui
from models.project import UserTask, UserTaskType
from typing import Callable, Optional


# Action type icons and verbs
ACTION_ICONS = {
    UserTaskType.PHONE_CALL: ('phone', 'Call'),
    UserTaskType.EMAIL: ('email', 'Email'),
    UserTaskType.IN_PERSON: ('business', 'Visit'),
    UserTaskType.ONLINE_PORTAL: ('language', 'Go to'),
    'phone_call': ('phone', 'Call'),
    'email': ('email', 'Email'),
    'in_person': ('business', 'Visit'),
    'online_portal': ('language', 'Go to'),
}


def user_action_card(
    user_task: UserTask,
    on_complete: Optional[Callable] = None,
) -> ui.card:
    """Render a UserActionResponse card.
    
    Args:
        user_task: The user task containing action details.
        on_complete: Callback when user marks the action as complete.
        
    Returns:
        A NiceGUI card element for the user action.
    """
    # Get action type info
    task_type = user_task.type
    task_type_key = task_type.value if isinstance(task_type, UserTaskType) else task_type
    icon, verb = ACTION_ICONS.get(task_type, ACTION_ICONS.get(task_type_key, ('help', 'Complete')))
    
    with ui.card().classes('border-2 border-orange-400 bg-orange-50 w-full') as card:
        # Header
        with ui.row().classes('items-center gap-2 w-full'):
            ui.icon('bolt', color='warning')
            ui.label('USER ACTION NEEDED').classes('font-bold text-orange-700 flex-grow')
        
        ui.separator()
        
        # Primary action line
        with ui.row().classes('items-center gap-2'):
            ui.icon(icon, color='warning')
            ui.label(f'{verb} {user_task.target}').classes('text-lg font-semibold')
        
        # Reason
        if user_task.reason:
            ui.label(f'Why: {user_task.reason}').classes('text-sm text-gray-600 italic')
        
        # Phone script (collapsible)
        if user_task.phone_script:
            with ui.expansion('Phone Script', icon='description').classes('w-full'):
                with ui.card().classes('bg-gray-50 p-3'):
                    ui.label(user_task.phone_script).classes('font-mono text-sm whitespace-pre-wrap')
                    ui.button('Copy', icon='content_copy').props('flat size=sm').classes('mt-2')
        
        # Email draft (collapsible)
        if user_task.email_draft:
            with ui.expansion('Email Draft', icon='email').classes('w-full'):
                with ui.card().classes('bg-gray-50 p-3'):
                    ui.label(user_task.email_draft).classes('text-sm whitespace-pre-wrap')
                    ui.button('Copy', icon='content_copy').props('flat size=sm').classes('mt-2')
        
        # Checklist (collapsible)
        if user_task.checklist:
            with ui.expansion('Have These Ready', icon='checklist', value=True).classes('w-full'):
                for item in user_task.checklist:
                    ui.checkbox(item).classes('text-sm')
        
        # Contact information
        if user_task.contact_info:
            with ui.row().classes('gap-4 text-sm text-gray-600 mt-4'):
                if user_task.contact_info.get('phone'):
                    with ui.row().classes('items-center gap-1'):
                        ui.icon('phone', size='xs')
                        ui.label(user_task.contact_info['phone'])
                if user_task.contact_info.get('hours'):
                    with ui.row().classes('items-center gap-1'):
                        ui.icon('schedule', size='xs')
                        ui.label(user_task.contact_info['hours'])
        
        ui.separator()
        
        # Completion button
        def handle_complete():
            if on_complete:
                on_complete()
            ui.notify('Action marked as complete!', type='positive')
        
        ui.button(
            "I've Completed This",
            icon='check_circle',
            on_click=handle_complete
        ).props('color=warning').classes('w-full')
    
    return card
