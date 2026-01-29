"""Inline Action Card component for rendering user action cards in the chat.

This component renders a prominent action card when the agent assigns a user task.
It follows the streaming pattern where ```json:action blocks are detected and 
replaced with this visual component.
"""

from datetime import datetime, timezone
from typing import Callable, Awaitable, Optional
from nicegui import ui
from models.project import UserActionCard


# Icon and color mapping for different action types
ACTION_TYPE_CONFIG = {
    "phone_call": {"icon": "call", "color": "warning", "label": "PHONE CALL"},
    "email": {"icon": "email", "color": "primary", "label": "EMAIL"},
    "form_submission": {"icon": "description", "color": "primary", "label": "FORM SUBMISSION"},
    "in_person": {"icon": "business", "color": "warning", "label": "IN-PERSON VISIT"},
    "upload": {"icon": "cloud_upload", "color": "primary", "label": "UPLOAD DOCUMENT"},
}

# Step type colors (matches plan_widget.py)
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


def render_inline_action_card(
    action_card: UserActionCard,
    on_complete: Optional[Callable[[str, str], Awaitable[None]]] = None,
    on_help: Optional[Callable[[], Awaitable[None]]] = None,
    initially_expanded: bool = True,
) -> ui.card:
    """Render an action card inline in the chat.
    
    Args:
        action_card: The UserActionCard model with all action details.
        on_complete: Async callback when user clicks "Mark Complete". 
                     Receives (step_id, user_message).
        on_help: Async callback when user clicks "Need Help" (deprecated).
        initially_expanded: Whether the card starts expanded (True for chat, False for plan panel).
        
    Returns:
        The NiceGUI card element.
    """
    config = ACTION_TYPE_CONFIG.get(
        action_card.card_type, 
        {"icon": "bolt", "color": "warning", "label": "ACTION"}
    )
    
    # Track expanded/collapsed state
    is_expanded = {'value': initially_expanded}
    
    # Get step type color from step_id (e.g., TRD-1 -> TRD -> orange)
    step_type_prefix = action_card.step_id.split('-')[0] if '-' in action_card.step_id else None
    step_color = STEP_TYPE_COLORS.get(step_type_prefix, '#6b7280')  # default to gray
    
    with ui.card().classes('w-full border-2 my-3').style('border-color: #eab308; background-color: #fefce8;') as card:
        # Header with bolt icon and step ID - always visible
        with ui.row().classes('items-center gap-2 w-full cursor-pointer') as header_row:
            ui.icon('bolt', color='warning').classes('text-xl')
            ui.label('ACTION NEEDED').classes('font-extrabold').style('color: #ca8a04;')
            ui.element('div').classes('flex-grow')
            ui.badge(f'Step: {action_card.step_id}').props('outline').style(f'border-color: {step_color} !important; color: {step_color} !important; font-weight: 600;')
        
        # Container for collapsible content
        content_container = ui.column().classes('w-full')
        content_container.set_visibility(is_expanded['value'])
        
        with content_container:
            ui.separator().classes('my-2')
            
            # Action type header with icon
            with ui.row().classes('items-center gap-2'):
                ui.icon(config["icon"], color=config["color"]).classes('text-2xl')
                
                # Build action label based on type
                if action_card.card_type == "phone_call" and action_card.contact_phone:
                    action_label = f"{config['label']} to {action_card.contact_phone}"
                elif action_card.card_type == "email" and action_card.contact_email:
                    action_label = f"{config['label']} to {action_card.contact_email}"
                elif action_card.card_type == "in_person" and action_card.contact_name:
                    action_label = f"VISIT {action_card.contact_name}"
                else:
                    action_label = config["label"]
                
                ui.label(action_label).classes('font-semibold text-lg')
                
                if action_card.contact_name and action_card.card_type in ["phone_call", "email"]:
                    ui.label(f"({action_card.contact_name})").classes('text-gray-500')
            
            # Title
            ui.label(action_card.title).classes('text-base font-medium mt-2')
            
            # Instructions
            if action_card.instructions:
                ui.markdown(action_card.instructions).classes('text-sm text-gray-700 mt-1')
            
            # Phone script (collapsible)
            if action_card.phone_script:
                with ui.expansion('📝 Phone Script', icon='description').classes('w-full mt-3 bg-white'):
                    with ui.card().classes('bg-gray-50 p-3 w-full'):
                        ui.label(action_card.phone_script).classes(
                            'font-mono text-sm whitespace-pre-wrap'
                        )
                        ui.button(
                            'Copy Script', 
                            icon='content_copy',
                            on_click=lambda: ui.notify('Script copied to clipboard!')
                        ).props('flat size=sm').classes('mt-2')
            
            # Email draft (collapsible)
            if action_card.email_draft:
                with ui.expansion('📧 Email Draft', icon='email').classes('w-full mt-3 bg-white'):
                    with ui.card().classes('bg-gray-50 p-3 w-full'):
                        ui.markdown(action_card.email_draft).classes('text-sm')
                        ui.button(
                            'Copy Draft',
                            icon='content_copy',
                            on_click=lambda: ui.notify('Email draft copied to clipboard!')
                        ).props('flat size=sm').classes('mt-2')
            
            # Checklist
            if action_card.checklist:
                with ui.column().classes('mt-3 gap-1'):
                    ui.label('✓ Checklist:').classes('font-medium text-sm')
                    for item in action_card.checklist:
                        with ui.row().classes('items-center gap-2 ml-2'):
                            ui.icon('check_box_outline_blank', size='xs').classes('text-gray-400')
                            ui.label(item).classes('text-sm')
            
            # Action URL (for online actions)
            if action_card.action_url:
                with ui.row().classes('mt-3 items-center gap-2'):
                    ui.icon('link', size='sm').classes('text-blue-500')
                    ui.link(
                        'Open Portal →', 
                        action_card.action_url, 
                        new_tab=True
                    ).classes('text-blue-600 text-sm font-medium')
            
            # Estimated duration
            if action_card.estimated_duration:
                with ui.row().classes('items-center gap-2 mt-3 text-sm text-gray-600'):
                    ui.icon('schedule', size='xs')
                    ui.label(f'Estimated: {action_card.estimated_duration}')
            
            ui.separator().classes('mt-4 mb-2')
            
            # Action buttons
            with ui.row().classes('w-full justify-end gap-2'):
                def toggle_collapse():
                    is_expanded['value'] = not is_expanded['value']
                    if is_expanded['value']:
                        content_container.set_visibility(True)
                    else:
                        content_container.set_visibility(False)
                
                ui.button(
                    'Close',
                    icon='close',
                    on_click=toggle_collapse
                ).props('flat color=grey')
                
                if on_complete:
                    async def show_complete_dialog():
                        dialog = create_mark_complete_dialog(
                            step_id=action_card.step_id,
                            step_title=action_card.title,
                            on_complete=on_complete
                        )
                        dialog.open()
                    
                    ui.button(
                        'Mark Complete',
                        icon='check_circle',
                        on_click=show_complete_dialog
                    ).props('unelevated color=positive')
        
        # Make header clickable to re-expand
        def toggle_expand():
            is_expanded['value'] = not is_expanded['value']
            if is_expanded['value']:
                content_container.set_visibility(True)
            else:
                content_container.set_visibility(False)
        
        header_row.on('click', toggle_expand)
    
    return card


def create_mark_complete_dialog(
    step_id: str,
    step_title: str,
    on_complete: Callable[[str, str], Awaitable[None]],
) -> ui.dialog:
    """Create a dialog for marking a step as complete.
    
    Args:
        step_id: The ID of the step being completed.
        step_title: The title of the step for display.
        on_complete: Async callback with (step_id, user_message).
        
    Returns:
        The dialog element.
    """
    user_message = {'value': ''}  # Using dict for closure capture
    
    with ui.dialog() as dialog, ui.card().classes('w-[500px] max-w-[90vw]'):
        # Header
        ui.label('Mark Step Complete').classes('text-xl font-bold')
        ui.label(f'{step_id}: {step_title}').classes('text-gray-600')
        
        ui.separator().classes('my-3')
        
        # Message input
        ui.label('Confirmation or notes (optional):').classes('text-sm font-medium')
        message_input = ui.textarea(
            placeholder='e.g., "Scheduled for Jan 20, 2026. Confirmation #A1234"'
        ).classes('w-full').props('outlined')
        
        # Bind input value
        message_input.on('update:model-value', lambda e: user_message.update({'value': e.args}))
        
        ui.separator().classes('my-3')
        
        # Action buttons
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            async def handle_complete():
                # Close dialog first, then notify (notify must happen before dialog context is lost)
                ui.notify(f'Step {step_id} marked as complete!', type='positive')
                dialog.close()
                # Call the completion handler after dialog is closed
                await on_complete(step_id, user_message['value'] or '')
            
            ui.button(
                'Mark Complete',
                icon='check',
                on_click=handle_complete
            ).props('unelevated color=positive')
    
    return dialog


def render_action_card_placeholder(step_id: str) -> ui.element:
    """Render a simple placeholder badge when action card was processed.
    
    This is shown in the chat message text where the JSON block was removed.
    The actual card is rendered separately.
    """
    with ui.row().classes('items-center gap-2 my-2 p-2 bg-orange-100 rounded') as placeholder:
        ui.icon('bolt', color='warning', size='sm')
        ui.label(f'Action card assigned for step {step_id}').classes('text-sm text-orange-700')
        ui.icon('arrow_downward', size='xs').classes('text-orange-400')
    
    return placeholder
