"""Chat panel component for the Citizen Services Portal."""

from nicegui import ui
from models.message import Message, MessageType
from models.project import Project, StepStatus
from components.user_action_card import user_action_card
from typing import Callable, Optional, Awaitable, Union


def format_timestamp(timestamp) -> str:
    """Format a timestamp for display in chat messages."""
    if not timestamp:
        return ""
    return timestamp.strftime("%I:%M %p")


def chat_panel(
    project: Optional[Project],
    messages: list[Message],
    on_send: Optional[Callable[[str], Awaitable[None]]] = None,
    scroll_area_ref: Optional[list] = None,
) -> ui.column:
    """Render the chat panel (center content).
    
    Args:
        project: The currently selected project.
        messages: List of messages to display.
        on_send: Async callback when a message is sent.
        scroll_area_ref: Optional list to store scroll area reference for external updates.
        
    Returns:
        A NiceGUI column element containing the chat panel.
    """
    with ui.column().classes('w-full h-full min-h-0') as panel:
        if project:
            # Header with project context
            with ui.row().classes('w-full items-center p-4 bg-gray-50 border-b'):
                ui.icon('chat').classes('text-xl text-primary')
                with ui.column().classes('flex-grow gap-0'):
                    ui.label(project.title).classes('font-semibold')
                    if project.description:
                        ui.label(project.description).classes('text-sm text-gray-500')
            
            # Scrollable message history
            with ui.scroll_area().classes('flex-grow p-4 min-h-0') as scroll:
                if scroll_area_ref is not None:
                    scroll_area_ref.clear()
                    scroll_area_ref.append(scroll)
                    
                for message in messages:
                    is_user = message.message_type == MessageType.USER
                    ui.chat_message(
                        text=message.content,
                        name=message.sender_name or ('You' if is_user else 'Agent'),
                        stamp=format_timestamp(message.timestamp),
                        sent=is_user,
                    )
                
                # Show user action card if there's a pending action
                if project.plan and project.plan.steps:
                    for step in project.plan.steps:
                        if step.status == StepStatus.AWAITING_USER and step.user_task:
                            with ui.element('div').classes('w-full max-w-lg mt-4'):
                                user_action_card(step.user_task)
                            break  # Only show first pending action
            
            # Input area
            with ui.row().classes('w-full p-4 border-t items-end gap-2'):
                message_input = ui.textarea(
                    placeholder='Type your message...'
                ).classes('flex-grow').props('autogrow rows=1 outlined')
                
                async def send_message():
                    text = message_input.value
                    if text and text.strip():
                        message_input.value = ''
                        if on_send:
                            await on_send(text.strip())
                
                ui.button(icon='send', on_click=send_message).props('round color=primary')
        else:
            # Welcome empty state (no project selected)
            with ui.column().classes('w-full h-full items-center justify-center p-8'):
                ui.icon('account_balance', size='xl').classes('text-primary text-6xl')
                ui.label('Welcome to the Citizen Services Portal').classes('text-2xl font-bold text-center mt-4')
                ui.label(
                    "I'm your AI assistant for navigating LA city services. "
                    "Select a project from the left panel, or start a new conversation."
                ).classes('text-center text-gray-600 mt-2 max-w-md')
    
    return panel
