"""Citizen Services Portal Web Application - Main Entry Point.

This is the main entry point for the NiceGUI web application.
Run with: uv run python main.py
"""

from nicegui import ui, app
from config import settings
from services.auth_service import get_current_user
from services.mock_data import get_mock_projects, get_mock_messages, MOCK_PROJECTS
from components.projects_panel import projects_panel
from components.chat_panel import chat_panel
from components.plan_widget import plan_widget


# Application state
class AppState:
    """Simple application state container."""
    def __init__(self):
        self.selected_project_id: str | None = None
        self.projects = []
        self.messages = []
    
    def select_project(self, project_id: str):
        """Select a project and load its data."""
        self.selected_project_id = project_id
        self.messages = get_mock_messages(project_id)
    
    def get_selected_project(self):
        """Get the currently selected project."""
        if not self.selected_project_id:
            return None
        for project in self.projects:
            if project.id == self.selected_project_id:
                return project
        return None


@ui.page('/')
def main_page():
    """Main application page with three-panel layout."""
    # Get current user
    user = get_current_user()
    
    # Initialize state
    state = AppState()
    state.projects = get_mock_projects(user.id if user else 'local-dev-user')
    
    # Select first project by default if available
    if state.projects:
        state.select_project(state.projects[0].id)
    
    # Header
    with ui.header().classes('items-center justify-between px-4 bg-blue-800'):
        with ui.row().classes('items-center gap-4'):
            # Mobile drawer toggle
            left_drawer_toggle = ui.button(icon='menu').props('flat color=white')
            
            # Brand
            ui.icon('account_balance').classes('text-2xl text-white')
            ui.label('Citizen Services Portal').classes('text-xl text-white font-bold hidden sm:block')
        
        # Spacer
        ui.element('div').classes('flex-grow')
        
        # Right side: Plan toggle and user menu
        with ui.row().classes('items-center gap-2'):
            # Plan toggle button
            right_drawer_toggle = ui.button(icon='analytics').props('flat color=white')
            right_drawer_toggle.tooltip('Toggle Plan View')
            
            # User menu
            if user:
                with ui.button(icon='person').props('flat color=white'):
                    with ui.menu():
                        ui.menu_item(f'👤 {user.name}').props('disable')
                        ui.separator()
                        ui.menu_item('Profile', on_click=lambda: ui.notify('Profile coming soon'))
                        ui.menu_item('Settings', on_click=lambda: ui.notify('Settings coming soon'))
                        ui.separator()
                        ui.menu_item('Sign Out', on_click=lambda: ui.notify('Sign out coming soon'))
    
    # Left drawer (Projects panel)
    with ui.left_drawer(value=True).props('width=300 breakpoint=768').classes('bg-gray-50') as left_drawer:
        left_drawer_toggle.on('click', left_drawer.toggle)
        
        def handle_project_select(project_id: str):
            state.select_project(project_id)
            # Refresh the UI
            chat_container.clear()
            plan_container.clear()
            with chat_container:
                chat_panel(
                    project=state.get_selected_project(),
                    messages=state.messages,
                    on_send=lambda msg: ui.notify(f'Mock: "{msg}"'),
                )
            with plan_container:
                plan_widget(state.get_selected_project())
            # Re-render projects to update selection
            projects_container.clear()
            with projects_container:
                projects_panel(
                    projects=state.projects,
                    selected_project_id=state.selected_project_id,
                    on_select=handle_project_select,
                    on_new_project=lambda: ui.notify('New project coming soon'),
                )
        
        with ui.element('div').classes('w-full h-full') as projects_container:
            projects_panel(
                projects=state.projects,
                selected_project_id=state.selected_project_id,
                on_select=handle_project_select,
                on_new_project=lambda: ui.notify('New project coming soon'),
            )
    
    # Right drawer (Plan widget)
    with ui.right_drawer(value=True).props('width=400 breakpoint=1024').classes('bg-white') as right_drawer:
        right_drawer_toggle.on('click', right_drawer.toggle)
        
        with ui.element('div').classes('w-full h-full') as plan_container:
            plan_widget(state.get_selected_project())
    
    # Main content (Chat panel)
    with ui.element('div').classes('w-full h-full') as chat_container:
        chat_panel(
            project=state.get_selected_project(),
            messages=state.messages,
            on_send=lambda msg: ui.notify(f'Mock: "{msg}"'),
        )


def main():
    """Main function to run the application."""
    ui.run(
        host=settings.NICEGUI_HOST,
        port=settings.NICEGUI_PORT,
        title='Citizen Services Portal',
        reload=settings.DEBUG,  # Hot-reload in dev mode
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
