"""Citizen Services Portal Web Application - Main Entry Point.

This is the main entry point for the NiceGUI web application.
Run with: uv run python main.py
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import uuid4
import json
import re
from nicegui import ui, app
from config import settings
from services.auth_service import get_current_user
from services.agent_service import get_agent_service
from services.project_service import get_project_service, generate_project_title
from services.user_service import get_user_service
from models.project import Project, ProjectStatus, Plan, PlanStep, StepStatus
from components.plan_widget import plan_widget


def format_relative_time(dt: datetime | None) -> str:
    """Format a datetime as a human-readable relative time string."""
    if not dt:
        return "Unknown"
    
    now = datetime.now(timezone.utc)
    # Ensure dt is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=2):
        return "Yesterday"
    elif diff < timedelta(days=7):
        days = int(diff.days)
        return f"{days} days ago"
    else:
        return dt.strftime("%b %d")


def convert_plan_from_cosmos(plan_data: dict | None) -> Plan | None:
    """Convert plan data from CosmosDB format to UI Plan model.
    
    Handles differences between Cosmos and UI plan/step models.
    """
    if not plan_data:
        print("[DEBUG] convert_plan_from_cosmos: No plan data")
        return None
    
    print(f"[DEBUG] convert_plan_from_cosmos: Got plan data with keys: {plan_data.keys()}")
    
    steps_data = plan_data.get("steps", [])
    if not steps_data:
        print("[DEBUG] convert_plan_from_cosmos: No steps in plan")
        return None
    
    print(f"[DEBUG] convert_plan_from_cosmos: Converting {len(steps_data)} steps")
    
    steps = []
    for step_data in steps_data:
        # Handle status - could be string or dict
        status_val = step_data.get("status", "not_started")
        if isinstance(status_val, dict):
            status_val = status_val.get("value", "not_started")
        try:
            status = StepStatus(status_val)
        except ValueError:
            status = StepStatus.NOT_STARTED
        
        # Handle dependencies vs depends_on (Cosmos uses 'dependencies')
        depends_on = step_data.get("depends_on", step_data.get("dependencies", step_data.get("dependsOn", [])))
        
        step = PlanStep(
            id=step_data.get("id", f"S{len(steps)+1}"),
            title=step_data.get("title", "Untitled Step"),
            agency=step_data.get("agency", "Unknown"),
            status=status,
            depends_on=depends_on,
        )
        steps.append(step)
    
    plan = Plan(
        id=plan_data.get("id", "plan-1"),
        title=plan_data.get("title", "Project Plan"),
        status=plan_data.get("status", "active"),
        steps=steps,
    )
    print(f"[DEBUG] convert_plan_from_cosmos: Created plan '{plan.title}' with {len(plan.steps)} steps")
    return plan


def convert_to_ui_project(project_data: dict) -> Project:
    """Convert project data from CosmosDB to UI Project model."""
    # Convert plan if present
    plan_data = project_data.get("plan")
    plan = convert_plan_from_cosmos(plan_data)
    
    return Project(
        id=project_data.get("id", ""),
        user_id=project_data.get("user_id", project_data.get("userId", "")),
        title=project_data.get("title", "Untitled"),
        description=project_data.get("context", {}).get("project_description"),
        status=ProjectStatus(project_data.get("status", "active")),
        progress=0.0,  # TODO: Calculate from plan steps
        thread_id=project_data.get("thread_id", project_data.get("threadId")),
        created_at=datetime.fromisoformat(project_data["created_at"].replace("Z", "+00:00")) if isinstance(project_data.get("created_at"), str) else project_data.get("created_at"),
        updated_at=datetime.fromisoformat(project_data["updated_at"].replace("Z", "+00:00")) if isinstance(project_data.get("updated_at"), str) else project_data.get("updated_at"),
        plan=plan,
    )


@ui.page('/')
async def main_page():
    """Main application page with three-panel layout."""
    # Get services
    agent_service = get_agent_service()
    project_service = get_project_service()
    user_service = get_user_service()
    user = get_current_user()
    user_id = user.id if user else settings.MOCK_USER_ID
    
    # Load user profile from storage immediately (before rendering UI)
    stored_user = await user_service.get_user(user_id)
    if stored_user:
        user = stored_user
    elif user:
        # Save initial user data to storage
        await user_service.save_user(user)
    
    # State management using app.storage for this session
    selected_project_id = None
    selected_project = None
    projects = []
    messages = []
    
    # UI references for dynamic updates
    projects_container = None
    chat_area = None
    message_input = None
    send_button = None
    chat_header = None
    chat_input_container = None
    plan_container = None
    
    # Profile edit dialog function
    def open_profile_dialog():
        """Open dialog to edit user profile."""
        async def save_profile():
            """Save profile changes."""
            nonlocal user
            updated_user = await user_service.update_user_profile(
                user_id=user_id,
                name=name_input.value.strip() if name_input.value else None,
                email=email_input.value.strip() if email_input.value else None,
                phone=phone_input.value.strip() if phone_input.value else None,
                address=address_input.value.strip() if address_input.value else None,
            )
            if updated_user:
                user = updated_user
                user_name_label.set_text(user.name if user.name else 'Setup Account')
                ui.notify('Profile updated', type='positive')
            dialog.close()
        
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Edit Profile').classes('text-xl font-bold mb-4')
            
            name_input = ui.input('Name', value=user.name if user else '').classes('w-full')
            email_input = ui.input('Email', value=user.email if user else '').classes('w-full')
            phone_input = ui.input('Phone', value=user.phone if user else '').classes('w-full')
            address_input = ui.textarea('Address', value=user.address if user else '').classes('w-full').props('rows=2')
            
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Save', on_click=save_profile).props('color=primary')
        
        dialog.open()
    
    # Header
    with ui.header().classes('items-center justify-between px-4 bg-blue-800 h-14'):
        ui.icon('account_balance').classes('text-2xl text-white')
        ui.label('Citizen Services Portal').classes('text-xl text-white font-bold')
        ui.space()
        if user:
            display_name = user.name if user.name else 'Setup Account'
            user_name_label = ui.label(display_name).classes('text-white text-sm cursor-pointer hover:underline')
            user_name_label.on('click', open_profile_dialog)
    
    # Add custom CSS for better markdown styling in chat
    ui.add_head_html('''
    <style>
        html, body { 
            height: 100vh !important; 
            max-height: 100vh !important;
            margin: 0 !important; 
            padding: 0 !important; 
            overflow: hidden !important; 
        }
        .q-page-container { 
            padding-top: 50px !important; 
            height: 100vh !important;
            max-height: 100vh !important;
            overflow: hidden !important;
        }
        .nicegui-content { 
            height: calc(100vh - 50px) !important;
            max-height: calc(100vh - 50px) !important;
            padding: 0 !important;
            overflow: hidden !important;
        }
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
        .projects-panel { width: 300px; min-width: 300px; height: 100% !important; }
        .main-content { 
            height: 100% !important; 
            max-height: 100% !important;
            min-height: 0 !important; 
            overflow: hidden !important; 
        }
        .chat-column { 
            display: flex !important; 
            flex-direction: column !important; 
            height: 100% !important; 
            max-height: 100% !important;
            min-height: 0 !important; 
            overflow: hidden !important; 
        }
        .chat-scroll { 
            flex: 1 1 0 !important; 
            overflow-y: auto !important; 
            min-height: 0 !important; 
            max-height: 100% !important;
        }
        .chat-input-area { 
            flex-shrink: 0 !important; 
            flex-grow: 0 !important;
        }
        .plan-panel { 
            width: 350px; 
            min-width: 200px;
            max-width: 800px;
            height: 100% !important;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        .resize-handle {
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 6px;
            cursor: col-resize;
            background: transparent;
            z-index: 100;
            transition: background 0.2s;
        }
        .resize-handle:hover,
        .resize-handle.dragging {
            background: rgba(59, 130, 246, 0.5);
        }
    </style>
    ''')
    
    async def load_projects():
        """Load projects from CosmosDB."""
        nonlocal projects
        project_data_list = await project_service.get_user_projects(user_id)
        projects = [convert_to_ui_project(p) for p in project_data_list]
        # Sort by updated_at DESC (newest first)
        projects.sort(key=lambda p: p.updated_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return projects
    
    async def load_messages(project_id: str, thread_id: Optional[str] = None):
        """Load messages for a project."""
        nonlocal messages
        messages = await project_service.get_messages(project_id)
        return messages
    
    async def select_project(project_id: str):
        """Handle project selection."""
        nonlocal selected_project_id, selected_project, messages
        selected_project_id = project_id
        
        # Find project in list
        for p in projects:
            if p.id == project_id:
                selected_project = p
                break
        
        # Load messages for selected project (app-side message history)
        messages = await project_service.get_messages(project_id)
        
        # Refresh the UI
        await refresh_ui()
    
    async def create_new_project():
        """Create a new project and select it."""
        nonlocal selected_project_id, selected_project, projects, messages
        
        # Create project with auto-generated title
        project_data = await project_service.create_project(user_id)
        if project_data:
            new_project = convert_to_ui_project(project_data)
            # Add to beginning of list (will be at top due to recent updated_at)
            projects.insert(0, new_project)
            # Resort to ensure proper ordering
            projects.sort(key=lambda p: p.updated_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            selected_project_id = new_project.id
            selected_project = new_project
            messages = []  # New project has no messages
            
            # Add system message with user context if user has profile info
            if user and user.name:
                user_info_lines = [f"- Name: {user.name}"]
                if user.email:
                    user_info_lines.append(f"- Email: {user.email}")
                if user.phone:
                    user_info_lines.append(f"- Phone: {user.phone}")
                if user.address:
                    user_info_lines.append(f"- Address: {user.address}")
                
                system_content = "You are assisting this User:\n" + "\n".join(user_info_lines)
                system_content += "\n\nPlease use this information when helping them with city services."
                
                await project_service.save_message(new_project.id, "system", system_content)
                messages.append({"role": "system", "content": system_content})
            
            # Refresh the UI
            await refresh_ui()
    
    async def refresh_ui():
        """Refresh the entire UI."""
        # Clear and rebuild projects panel
        projects_container.clear()
        with projects_container:
            render_projects_list()
        
        # Clear and rebuild chat area
        chat_area.clear()
        with chat_area:
            render_messages()
        
        # Update chat header
        chat_header.clear()
        with chat_header:
            render_chat_header()
        
        # Update chat input area
        chat_input_container.clear()
        with chat_input_container:
            render_chat_input()
        
        # Update plan panel
        plan_container.clear()
        with plan_container:
            render_plan_panel()
    
    def render_plan_panel():
        """Render the plan panel content."""
        plan_widget(selected_project)
    
    async def reload_and_update_selected_project():
        """Reload projects from database and update the selected project reference."""
        nonlocal selected_project, projects
        
        # Reload projects to get updated data and sorting
        await load_projects()
        
        # Update selected project reference
        if selected_project_id:
            for p in projects:
                if p.id == selected_project_id:
                    selected_project = p
                    break
        
        # Refresh projects panel to show new data/order
        projects_container.clear()
        with projects_container:
            render_projects_list()
    
    async def cancel_project_with_confirmation(project_id: str):
        """Cancel a project after user confirmation."""
        nonlocal projects, selected_project
        
        # Update project status to cancelled
        updated_project_data = await project_service.update_project(project_id, user_id, {'status': 'cancelled'})
        
        if updated_project_data:
            # Reload projects to get updated data
            await load_projects()
            
            # Update selected project if it's the one being cancelled
            if selected_project_id == project_id:
                for p in projects:
                    if p.id == project_id:
                        selected_project = p
                        break
            
            # Refresh the UI
            await refresh_ui()
    
    async def complete_project_with_confirmation(project_id: str):
        """Mark a project as complete after user confirmation."""
        nonlocal projects, selected_project
        
        # Update project status to completed
        updated_project_data = await project_service.update_project(project_id, user_id, {'status': 'completed'})
        
        if updated_project_data:
            # Reload projects to get updated data
            await load_projects()
            
            # Update selected project if it's the one being completed
            if selected_project_id == project_id:
                for p in projects:
                    if p.id == project_id:
                        selected_project = p
                        break
            
            # Refresh the UI
            await refresh_ui()
    
    def render_projects_list():
        """Render the list of projects."""
        if projects:
            for project in projects:
                is_selected = project.id == selected_project_id
                
                # Determine status icon and color
                status_icons = {
                    ProjectStatus.ACTIVE: 'sync',
                    ProjectStatus.COMPLETED: 'check_circle',
                    ProjectStatus.CANCELLED: 'cancel',
                }
                status_colors = {
                    ProjectStatus.ACTIVE: 'primary',
                    ProjectStatus.COMPLETED: 'positive',
                    ProjectStatus.CANCELLED: 'grey',
                }
                icon = status_icons.get(project.status, 'folder')
                color = status_colors.get(project.status, 'grey')
                
                # Card styling based on selection and status
                card_classes = 'w-full cursor-pointer transition-all mb-2 p-3'
                if is_selected:
                    card_classes += ' border-2 border-blue-500 bg-blue-50'
                else:
                    card_classes += ' hover:shadow-md hover:bg-gray-50'
                
                # Reduced opacity for cancelled projects
                if project.status == ProjectStatus.CANCELLED:
                    card_classes += ' opacity-60'
                
                with ui.card().classes(card_classes) as card:
                    card.on('click', lambda p=project: select_project(p.id))
                    
                    # Add context menu for active projects only
                    if project.status == ProjectStatus.ACTIVE:
                        with card:
                            with ui.menu().props('context-menu'):
                                ui.menu_item(
                                    'Mark as Complete',
                                    on_click=lambda p=project: confirm_complete_dialog(p.id)
                                )
                                ui.menu_item(
                                    'Cancel Project',
                                    on_click=lambda p=project: confirm_cancel_dialog(p.id)
                                )
                    
                    with ui.row().classes('items-center gap-2 w-full'):
                        ui.icon(icon, color=color)
                        with ui.column().classes('flex-grow gap-0'):
                            # Strikethrough for cancelled projects
                            title_classes = 'font-semibold truncate'
                            if project.status == ProjectStatus.CANCELLED:
                                title_classes += ' line-through'
                            ui.label(project.title).classes(title_classes)
                            # Show relative time based on updated_at
                            ui.label(f'Updated {format_relative_time(project.updated_at)}').classes('text-xs text-gray-400')
        else:
            with ui.column().classes('items-center justify-center p-4 text-center'):
                ui.icon('folder_open', size='lg').classes('text-gray-400')
                ui.label('No projects yet').classes('text-gray-500 mt-2')
                ui.label('Click + to start a new conversation').classes('text-xs text-gray-400')
    
    def confirm_cancel_dialog(project_id: str):
        """Show confirmation dialog for cancelling a project."""
        async def do_cancel():
            # Do the work first while dialog context is still valid
            await cancel_project_with_confirmation(project_id)
            # Then close the dialog
            dialog.close()
        
        with ui.dialog() as dialog, ui.card():
            ui.label('Cancel Project?').classes('text-lg font-bold')
            ui.label('Are you sure you want to cancel this project? You will no longer be able to send messages.')
            ui.label('This action cannot be undone.').classes('text-orange-600 font-semibold mt-2')
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Confirm Cancel', on_click=do_cancel).props('color=negative')
        dialog.open()
    
    def confirm_complete_dialog(project_id: str):
        """Show confirmation dialog for marking a project as complete."""
        async def do_complete():
            # Do the work first while dialog context is still valid
            await complete_project_with_confirmation(project_id)
            # Then close the dialog
            dialog.close()
        
        with ui.dialog() as dialog, ui.card():
            ui.label('Mark as Complete?').classes('text-lg font-bold')
            ui.label('Mark this project as complete? You will no longer be able to send messages.')
            ui.label('This action cannot be undone.').classes('text-orange-600 font-semibold mt-2')
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Mark Complete', on_click=do_complete).props('color=positive')
        dialog.open()
    
    async def save_title_edit(project_id: str, new_title: str):
        """Save edited project title."""
        nonlocal projects, selected_project
        
        # Validate title
        if not new_title or not new_title.strip():
            ui.notify('Title cannot be empty', type='warning')
            return False
        
        new_title = new_title.strip()[:100]  # Limit to 100 characters
        
        # Update project title
        updated_project_data = await project_service.update_project(project_id, user_id, {'title': new_title})
        
        if updated_project_data:
            # Reload projects to get updated data and sorting
            await load_projects()
            
            # Update selected project
            if selected_project_id == project_id:
                for p in projects:
                    if p.id == project_id:
                        selected_project = p
                        break
            
            # Refresh the UI
            await refresh_ui()
            ui.notify('Title updated', type='positive')
            return True
        
        return False
    
    def render_chat_header():
        """Render the chat header."""
        if selected_project:
            ui.icon('chat').classes('text-xl text-primary')
            with ui.column().classes('flex-grow gap-0'):
                # Editable title for active projects, locked for others
                if selected_project.status == ProjectStatus.ACTIVE:
                    # Container for both display and edit modes
                    with ui.row().classes('items-center gap-1') as title_display:
                        title_label = ui.label(selected_project.title).classes('font-semibold cursor-pointer hover:bg-gray-100 px-2 py-1 rounded')
                        edit_icon = ui.icon('edit', size='xs').classes('text-gray-400 cursor-pointer hover:text-blue-500')
                    
                    # Hidden input for editing - initially hidden with display:none
                    title_input = ui.input(value=selected_project.title).props('maxlength=100 dense outlined')
                    title_input.style('display: none')
                    
                    def start_edit():
                        title_display.style('display: none')
                        title_input.style('display: block')
                        title_input.run_method('focus')
                    
                    async def finish_edit():
                        new_title = title_input.value
                        if new_title and new_title.strip() and new_title != selected_project.title:
                            await save_title_edit(selected_project.id, new_title)
                        else:
                            # Revert to original and show display
                            title_input.set_value(selected_project.title)
                            title_input.style('display: none')
                            title_display.style('display: flex')
                    
                    def cancel_edit():
                        title_input.set_value(selected_project.title)
                        title_input.style('display: none')
                        title_display.style('display: flex')
                    
                    title_label.on('click', start_edit)
                    edit_icon.on('click', start_edit)
                    title_input.on('keydown.enter.prevent', finish_edit)
                    title_input.on('keydown.escape.prevent', cancel_edit)
                    title_input.on('blur', finish_edit)
                else:
                    with ui.row().classes('items-center gap-2'):
                        ui.label(selected_project.title).classes('font-semibold text-gray-500')
                        ui.icon('lock', size='xs').classes('text-gray-400')
        else:
            ui.label('Select a project or start a new one').classes('text-gray-500')
    
    def render_chat_input():
        """Render the chat input area."""
        nonlocal message_input, send_button
        
        if selected_project and selected_project.status != ProjectStatus.ACTIVE:
            # Show disabled message for non-active projects
            if selected_project.status == ProjectStatus.CANCELLED:
                ui.label('This project has been cancelled. You can no longer send messages.').classes('text-gray-500 italic')
            elif selected_project.status == ProjectStatus.COMPLETED:
                ui.label('This project has been completed. You can no longer send messages.').classes('text-gray-500 italic')
        else:
            # Normal input for active projects or no selection
            message_input = ui.textarea(placeholder='Type your message...').classes('flex-grow')
            message_input.props('autogrow rows=1 outlined')
            send_button = ui.button(icon='send', on_click=send_message).props('round color=primary')
            
            # Handle Enter key
            message_input.on('keydown.enter.prevent', handle_keydown, ['shiftKey'])
    
    def render_messages():
        """Render messages in the chat area."""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Skip system messages - they are sent to agent but not displayed
            if role == "system":
                continue
            
            is_user = role == "user"
            
            with ui.chat_message(
                name='You' if is_user else 'Agent',
                sent=is_user,
            ).props('bg-color=light-blue-2' if not is_user else ''):
                ui.markdown(content).classes('chat-markdown')
    
    def build_agent_messages() -> list[dict]:
        """Build the full message list to send to the agent.
        
        This includes:
        - Full chat history (user/assistant messages from Cosmos)
        - System message with user info (if set)
        - System message with current plan (if any)
        
        System messages are appended at the end and are NOT saved to Cosmos.
        """
        agent_messages = list(messages)  # Copy the chat history
        
        # Add user info system message if user has profile with actual name
        if user and user.name:
            user_info_lines = [f"- Name: {user.name}"]
            if user.email:
                user_info_lines.append(f"- Email: {user.email}")
            if user.phone:
                user_info_lines.append(f"- Phone: {user.phone}")
            if user.address:
                user_info_lines.append(f"- Address: {user.address}")
            
            user_context = "User Information:\n" + "\n".join(user_info_lines)
            agent_messages.append({"role": "system", "content": user_context})
        
        # Add current plan system message if project has a plan
        if selected_project and selected_project.plan and selected_project.plan.steps:
            plan_dict = {
                "id": selected_project.plan.id,
                "title": selected_project.plan.title,
                "status": selected_project.plan.status,
                "steps": [
                    {
                        "id": step.id,
                        "title": step.title,
                        "agency": step.agency,
                        "status": step.status.value if hasattr(step.status, 'value') else step.status,
                        "depends_on": step.depends_on,
                    }
                    for step in selected_project.plan.steps
                ]
            }
            plan_context = f"Current Project Plan:\n```json\n{json.dumps(plan_dict, indent=2)}\n```"
            agent_messages.append({"role": "system", "content": plan_context})
        
        return agent_messages
    
    def convert_plan_dict_to_model(plan_dict: dict) -> Plan:
        """Convert a plan dictionary to a Plan model.
        
        Handles string status values by converting them to StepStatus enums.
        """
        steps = []
        for step_dict in plan_dict.get('steps', []):
            # Convert status string to StepStatus enum
            status_str = step_dict.get('status', 'not_started')
            try:
                status = StepStatus(status_str)
            except ValueError:
                status = StepStatus.NOT_STARTED
            
            step = PlanStep(
                id=step_dict.get('id', f'S{len(steps)+1}'),
                title=step_dict.get('title', 'Untitled Step'),
                agency=step_dict.get('agency', 'Unknown'),
                status=status,
                depends_on=step_dict.get('depends_on', []),
            )
            steps.append(step)
        
        return Plan(
            id=plan_dict.get('id', str(uuid4())[:8]),
            title=plan_dict.get('title', 'Project Plan'),
            status=plan_dict.get('status', 'active'),
            steps=steps,
        )
    
    def convert_plan_to_cosmos_dict(plan: Plan) -> dict:
        """Convert UI Plan model to Cosmos-compatible dict format.
        
        The Cosmos Plan model expects: steps, created_at, updated_at
        Each step needs: id, title, description, agency, status, order, dependencies
        """
        cosmos_steps = []
        for i, step in enumerate(plan.steps):
            cosmos_step = {
                "id": step.id,
                "title": step.title,
                "description": step.title,  # Use title as description
                "agency": step.agency.lower() if step.agency else "unknown",
                "status": step.status.value if hasattr(step.status, 'value') else step.status,
                "order": i + 1,
                "dependencies": step.depends_on or [],
            }
            cosmos_steps.append(cosmos_step)
        
        return {
            "steps": cosmos_steps,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            # Also include id, title, status for UI compatibility when loaded back
            "id": plan.id,
            "title": plan.title,
            "status": plan.status,
        }
    
    def extract_plan_from_response(response_text: str) -> tuple[str, Plan | None]:
        """Extract plan JSON from response and return cleaned text + Plan model.
        
        Looks for ```json:plan ... ``` blocks in the response.
        If found, extracts the JSON, converts to Plan model, and replaces the block with a card placeholder.
        """
        pattern = r'```json:plan\s*([\s\S]*?)```'
        match = re.search(pattern, response_text)
        
        if match:
            try:
                plan_json = json.loads(match.group(1))
                plan_model = convert_plan_dict_to_model(plan_json)
                # Replace the JSON block with a plan update indicator
                cleaned_text = re.sub(
                    pattern, 
                    '\n\n📋 **Plan Updated**\n\n', 
                    response_text
                )
                return cleaned_text.strip(), plan_model
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error parsing plan JSON: {e}")
                pass
        
        return response_text, None
    
    async def send_message():
        """Send a message to the agent."""
        nonlocal selected_project_id, selected_project, messages
        
        text = message_input.value
        if not text or not text.strip():
            return
        
        user_msg = text.strip()
        message_input.set_value('')
        send_button.disable()
        
        # If no project selected, create a new one
        if not selected_project_id:
            project_data = await project_service.create_project(user_id)
            if project_data:
                new_project = convert_to_ui_project(project_data)
                projects.insert(0, new_project)
                selected_project_id = new_project.id
                selected_project = new_project
                messages = []  # New project starts with empty message history
                
                # Refresh projects panel
                projects_container.clear()
                with projects_container:
                    render_projects_list()
        
        # Update local messages list and persist user message (app-side persistence)
        messages.append({"role": "user", "content": user_msg})
        await project_service.save_message(selected_project_id, "user", user_msg)
        # Touch project to update timestamp
        await project_service.touch_project(selected_project_id, user_id)
        
        # Reload projects and update UI to reflect new timestamp/order
        await reload_and_update_selected_project()
        
        # Add user message to UI
        with chat_area:
            ui.chat_message(text=user_msg, name='You', sent=True)
        
        # Add agent response bubble that we'll update as tokens stream in
        with chat_area:
            agent_msg = ui.chat_message(name='Agent', sent=False).props('bg-color=light-blue-2')
            with agent_msg:
                response_label = ui.markdown('⏳ *thinking...*').classes('chat-markdown')
        
        try:
            # Call agent with streaming
            # Build messages with context (user info, current plan) appended
            agent_messages = build_agent_messages()
            response_text = ''
            chunk_count = 0
            
            async for chunk in agent_service.send_message_stream(
                message=user_msg,
                messages=agent_messages,  # Includes history + context system messages
            ):
                response_text += chunk
                chunk_count += 1
                # Update UI every few chunks
                if chunk_count % 3 == 0:
                    response_label.set_content(response_text + '▌')
                    await ui.run_javascript('void(0)')
            
            # Check for plan updates in the response
            display_text, plan_data = extract_plan_from_response(response_text)
            
            # Final update with cleaned text (plan JSON replaced with visual indicator)
            if display_text:
                response_label.set_content(display_text)
                
                # Save the CLEANED text (without JSON plan block) to messages
                # The plan is saved separately in the project, no need to keep JSON in history
                messages.append({"role": "assistant", "content": display_text})
                await project_service.save_message(selected_project_id, "assistant", display_text)
                
                # If plan was extracted, save it to the project and refresh
                if plan_data:
                    print(f"[DEBUG] Plan extracted with {len(plan_data.steps)} steps: {plan_data.title}")
                    # Convert UI Plan model to Cosmos-compatible dict format
                    cosmos_plan_dict = convert_plan_to_cosmos_dict(plan_data)
                    print(f"[DEBUG] Converted to Cosmos format: {len(cosmos_plan_dict.get('steps', []))} steps")
                    await project_service.update_project(
                        selected_project_id, 
                        user_id, 
                        {"plan": cosmos_plan_dict}
                    )
                    print(f"[DEBUG] Plan saved to project {selected_project_id}")
                    # Reload project to get updated plan
                    await reload_and_update_selected_project()
                    print(f"[DEBUG] Project reloaded. Plan exists: {selected_project.plan is not None}")
                    if selected_project and selected_project.plan:
                        print(f"[DEBUG] Reloaded plan has {len(selected_project.plan.steps)} steps")
                    # Refresh the plan panel
                    plan_container.clear()
                    with plan_container:
                        render_plan_panel()
                    print(f"[DEBUG] Plan panel refreshed")
                    ui.notify('Plan updated!', type='positive')
                
                # Touch project to update timestamp
                await project_service.touch_project(selected_project_id, user_id)
                
                # Reload projects and update UI to reflect new timestamp/order
                await reload_and_update_selected_project()
            else:
                response_label.set_content('*(no response)*')
                
        except Exception as e:
            response_label.set_content(f'**Error:** {e}')
        finally:
            send_button.enable()
    
    async def handle_keydown(e):
        """Send on Enter, allow Shift+Enter for new line."""
        if e.args.get('shiftKey', False):
            message_input.value = (message_input.value or '') + '\n'
        else:
            await send_message()
    
    # Load initial data
    await load_projects()
    
    # Main layout - three panel design
    with ui.row().classes('w-full main-content'):
        # Left panel - Projects list
        with ui.column().classes('projects-panel h-full bg-gray-100 border-r'):
            # Projects header
            with ui.row().classes('w-full items-center p-4 border-b bg-white'):
                ui.label('PROJECTS').classes('text-sm font-bold text-gray-500 flex-grow')
                ui.button(icon='add', on_click=create_new_project).props('round flat size=sm color=primary')
            
            # Projects list
            with ui.scroll_area().classes('flex-grow w-full'):
                projects_container = ui.column().classes('w-full p-2')
                with projects_container:
                    render_projects_list()
        
        # Center panel - Chat
        with ui.column().classes('flex-grow chat-column'):
            # Chat header
            chat_header = ui.row().classes('w-full items-center p-4 bg-gray-50 border-b gap-2')
            with chat_header:
                render_chat_header()
            
            # Chat messages area (scrollable)
            with ui.scroll_area().classes('chat-scroll p-4'):
                chat_area = ui.column().classes('w-full gap-2')
                with chat_area:
                    if selected_project:
                        render_messages()
                    else:
                        # Welcome message when no project selected
                        with ui.column().classes('w-full h-full items-center justify-center p-8'):
                            ui.icon('account_balance', size='xl').classes('text-primary text-6xl')
                            ui.label('Welcome to the Citizen Services Portal').classes('text-2xl font-bold text-center mt-4')
                            ui.label(
                                "I'm your AI assistant for navigating LA city services. "
                                "Select a project or click + to start a new conversation."
                            ).classes('text-center text-gray-600 mt-2 max-w-md')
            
            # Input area (fixed at bottom)
            chat_input_container = ui.row().classes('w-full p-4 border-t items-end gap-2 chat-input-area bg-white')
            with chat_input_container:
                render_chat_input()
        
        # Right panel - Plan widget (resizable)
        with ui.column().classes('plan-panel h-full bg-gray-50 border-l') as plan_panel:
            # Resize handle
            ui.html('<div class="resize-handle" id="plan-resize-handle"></div>', sanitize=False)
            plan_container = ui.column().classes('w-full h-full')
            with plan_container:
                render_plan_panel()
    
    # Add JavaScript for resize functionality
    ui.add_body_html('''
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            const handle = document.getElementById('plan-resize-handle');
            const panel = document.querySelector('.plan-panel');
            if (!handle || !panel) return;
            
            let isDragging = false;
            let startX, startWidth;
            
            handle.addEventListener('mousedown', function(e) {
                isDragging = true;
                startX = e.clientX;
                startWidth = panel.offsetWidth;
                handle.classList.add('dragging');
                document.body.style.cursor = 'col-resize';
                document.body.style.userSelect = 'none';
                e.preventDefault();
            });
            
            document.addEventListener('mousemove', function(e) {
                if (!isDragging) return;
                const diff = startX - e.clientX;
                const newWidth = Math.min(Math.max(startWidth + diff, 200), 800);
                panel.style.width = newWidth + 'px';
            });
            
            document.addEventListener('mouseup', function() {
                if (isDragging) {
                    isDragging = false;
                    handle.classList.remove('dragging');
                    document.body.style.cursor = '';
                    document.body.style.userSelect = '';
                }
            });
        }, 500);
    });
    </script>
    ''')


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
