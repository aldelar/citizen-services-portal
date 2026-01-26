"""Projects panel component for the Citizen Services Portal."""

from nicegui import ui
from models.project import Project
from components.project_card import project_card
from typing import Callable, Optional


def projects_panel(
    projects: list[Project],
    selected_project_id: Optional[str],
    on_select: Callable[[str], None],
    on_new_project: Optional[Callable] = None,
) -> ui.column:
    """Render the projects panel (left drawer content).
    
    Args:
        projects: List of projects to display.
        selected_project_id: ID of the currently selected project.
        on_select: Callback when a project is selected.
        on_new_project: Callback when new project button is clicked.
        
    Returns:
        A NiceGUI column element containing the projects panel.
    """
    with ui.column().classes('w-full h-full') as panel:
        # Header
        with ui.row().classes('w-full items-center p-4'):
            ui.label('PROJECTS').classes('text-sm font-bold text-gray-500 flex-grow')
            if on_new_project:
                ui.button(icon='add', on_click=on_new_project).props('round flat size=sm')
        
        # Search input
        with ui.row().classes('px-4 pb-2 w-full'):
            ui.input(placeholder='Search projects...').props('dense clearable outlined').classes('w-full')
        
        ui.separator()
        
        # Project cards list
        if projects:
            with ui.scroll_area().classes('flex-grow w-full'):
                with ui.column().classes('w-full gap-2 p-2'):
                    for project in projects:
                        is_selected = project.id == selected_project_id
                        project_card(
                            project=project,
                            is_selected=is_selected,
                            on_click=lambda p=project: on_select(p.id),
                        )
        else:
            # Empty state
            with ui.column().classes('w-full h-full items-center justify-center p-8'):
                ui.icon('folder_open', size='xl').classes('text-gray-400')
                ui.label('No projects yet').classes('text-lg font-semibold mt-4')
                ui.label('Start by telling me what you need help with').classes('text-gray-600 mt-2 text-center')
                if on_new_project:
                    ui.button('+ Start New', icon='add', on_click=on_new_project).props('color=primary').classes('mt-4')
    
    return panel
