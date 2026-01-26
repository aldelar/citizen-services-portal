"""Citizen Services Portal Web Application - Main Entry Point.

This is the main entry point for the NiceGUI web application.
Run with: uv run python main.py
"""

from datetime import datetime
from uuid import uuid4
from nicegui import ui, app
from config import settings
from services.auth_service import get_current_user
from services.agent_service import get_agent_service
from services.mock_data import get_mock_projects, get_mock_messages, MOCK_PROJECTS
from models.message import Message, MessageType
from components.projects_panel import projects_panel
from components.chat_panel import chat_panel
from components.plan_widget import plan_widget


@ui.page('/')
def main_page():
    """Main application page with simple chat."""
    # Get agent service
    agent_service = get_agent_service()
    
    # Simple message storage - just a list of dicts for now
    messages = []
    
    # Header
    with ui.header().classes('items-center justify-between px-4 bg-blue-800'):
        ui.icon('account_balance').classes('text-2xl text-white')
        ui.label('Citizen Services Portal').classes('text-xl text-white font-bold')
    
    # Add custom CSS for better markdown styling in chat
    ui.add_head_html('''
    <style>
        .chat-markdown h1 { font-size: 1.25rem; font-weight: 600; margin: 0.5rem 0; }
        .chat-markdown h2 { font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0; }
        .chat-markdown h3 { font-size: 1rem; font-weight: 600; margin: 0.4rem 0; }
        .chat-markdown h4, .chat-markdown h5, .chat-markdown h6 { font-size: 0.95rem; font-weight: 600; margin: 0.3rem 0; }
        .chat-markdown p { margin: 0.3rem 0; }
        .chat-markdown ul, .chat-markdown ol { margin: 0.3rem 0; padding-left: 1.5rem; }
        .chat-markdown li { margin: 0.15rem 0; }
        .chat-markdown code { background: rgba(0,0,0,0.1); padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.9em; }
        .chat-markdown pre { background: rgba(0,0,0,0.1); padding: 0.5rem; border-radius: 5px; overflow-x: auto; }
        .chat-markdown strong { font-weight: 600; }
    </style>
    ''')
    
    # Chat container
    with ui.column().classes('w-full max-w-3xl mx-auto p-4 h-full'):
        # Messages area
        chat_area = ui.column().classes('w-full flex-grow overflow-auto gap-2')
        
        # Input row
        with ui.row().classes('w-full items-end gap-2'):
            message_input = ui.textarea(placeholder='Type your message...').classes('flex-grow')
            message_input.props('autogrow rows=1 outlined')
            send_button = ui.button(icon='send').props('round color=primary')
        
        async def handle_keydown(e):
            """Send on Enter, allow Shift+Enter for new line."""
            if e.args.get('shiftKey', False):
                # Shift+Enter: insert newline
                message_input.value = (message_input.value or '') + '\n'
            else:
                # Enter alone: send message
                await send_message()
        
        # Prevent default Enter behavior and handle manually
        message_input.on('keydown.enter.prevent', handle_keydown, ['shiftKey'])
        
        async def send_message():
            text = message_input.value
            if not text or not text.strip():
                return
            
            user_msg = text.strip()
            message_input.set_value('')  # Clear input properly
            send_button.disable()
            
            # Add user message to UI
            with chat_area:
                ui.chat_message(text=user_msg, name='You', sent=True)
            
            # Add agent response bubble that we'll update as tokens stream in
            with chat_area:
                agent_msg = ui.chat_message(name='Agent', sent=False).props('bg-color=light-blue-2')
                with agent_msg:
                    response_label = ui.markdown('⏳ *thinking...*').classes('chat-markdown')
            
            try:
                # Call agent with streaming and update UI in real-time
                response_text = ''
                chunk_count = 0
                async for chunk in agent_service.send_message_stream(message=user_msg):
                    response_text += chunk
                    chunk_count += 1
                    # Update UI every few chunks to balance responsiveness and performance
                    if chunk_count % 3 == 0:
                        response_label.set_content(response_text + '▌')
                        await ui.run_javascript('void(0)')  # Force UI refresh
                
                # Final update (remove cursor)
                if response_text:
                    response_label.set_content(response_text)
                else:
                    response_label.set_content('*(no response)*')
                    
            except Exception as e:
                response_label.set_content(f'**Error:** {e}')
            finally:
                send_button.enable()
        
        send_button.on('click', send_message)
        message_input.on('keydown.enter', send_message)


def main():
    """Main function to run the application."""
    ui.run(
        host=settings.NICEGUI_HOST,
        port=settings.NICEGUI_PORT,
        title='Citizen Services Portal',
        reload=settings.DEBUG,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
