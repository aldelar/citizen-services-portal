# UI Wireframes: Projects Panel

This document defines the project list, creation flow, and project management features in the left panel, implemented with NiceGUI native components.

**Related User Stories:** See [User Stories - Project Panel](../7-user-stories.md#project-panel)

---

## NiceGUI Components Used

| Feature | NiceGUI Element |
|---------|-----------------|
| Projects container | `ui.column()` with `ui.scroll_area()` |
| Project cards | `ui.card()` |
| Status icons | `ui.icon()` |
| Add button | `ui.button(icon='add')` |
| Editable title | `ui.input()` with inline editing |
| Context menu | `ui.menu()` + `ui.menu_item()` |
| Confirmation dialog | `ui.dialog()` |
| Empty state | `ui.card()` with centered content |

---

## Overview

The Projects Panel is the left-side navigation area where users manage their projects. Each project represents a conversation thread with the AI agent around a specific city service need.

**Key Features:**
- Create new projects with auto-generated titles (U1)
- View project status at a glance via icons (U2)
- Cancel projects to make them read-only (U3)
- Mark projects as complete (U4)
- Projects sorted by most recent activity (U5)
- Scrollable list for many projects (U6)
- Editable project titles (U7)

---

## Project List Layout (U5, U6)

### Visual Reference

```
┌──────────────────────────────┐
│  PROJECTS                [+] │  ← Fixed header (U1: + button)
├──────────────────────────────┤
│  ╭────────────────────────╮  │  ↑
│  │ 🔄 Solar Installation  │  │  │
│  │ Updated 2 hours ago    │  │  │
│  ╰────────────────────────╯  │  │
│                              │  │  Scrollable area (U6)
│  ┌────────────────────────┐  │  │  Sorted by updated_at (U5)
│  │ ✓ Bulk Pickup          │  │  │
│  │ Completed yesterday    │  │  │
│  └────────────────────────┘  │  │
│                              │  │
│  ┌────────────────────────┐  │  │
│  │ ✘ Business License     │  │  │
│  │ Cancelled 3 days ago   │  │  ↓
│  └────────────────────────┘  │
└──────────────────────────────┘
```

### NiceGUI Implementation

```python
# Project list panel with fixed header and scrollable list
with ui.column().classes('projects-panel h-full bg-gray-100 border-r'):
    # Fixed header - does NOT scroll (U6)
    with ui.row().classes('w-full items-center p-4 border-b bg-white'):
        ui.label('PROJECTS').classes('text-sm font-bold text-gray-500 flex-grow')
        ui.button(icon='add', on_click=create_new_project).props('round flat size=sm color=primary')
    
    # Scrollable project list (U6)
    with ui.scroll_area().classes('flex-grow w-full'):
        projects_container = ui.column().classes('w-full p-2 gap-2')
        
        # Projects sorted by updated_at descending (U5)
        for project in sorted(projects, key=lambda p: p.updated_at, reverse=True):
            render_project_card(project)
```

---

## Project Creation (U1)

When the user clicks the "+" button, a new project is immediately created.

### Behavior

1. User clicks "+" button
2. New project is created with auto-generated title: `YYMMDD-HHMM` format (e.g., "260126-1430")
3. Project is persisted to CosmosDB
4. New project appears at the top of the list (most recent)
5. Project is automatically selected
6. Chat panel opens ready for user input

### Visual Flow

```
Before:                          After:
┌─────────────────────┐          ┌─────────────────────┐
│ PROJECTS        [+] │  Click   │ PROJECTS        [+] │
├─────────────────────┤  ───►    ├─────────────────────┤
│                     │          │ ╭─────────────────╮ │
│ 🔄 Solar Install    │          │ │ 🔄 260126-1430  │ │ ← NEW (selected)
│                     │          │ │ Just now        │ │
│ ✓ Bulk Pickup       │          │ ╰─────────────────╯ │
│                     │          │                     │
└─────────────────────┘          │ 🔄 Solar Install    │
                                 │                     │
                                 │ ✓ Bulk Pickup       │
                                 └─────────────────────┘
```

### NiceGUI Implementation

```python
async def create_new_project():
    """Create a new project and select it. (U1)"""
    # Generate title with YYMMDD-HHMM format
    title = datetime.now().strftime('%y%m%d-%H%M')
    
    # Create project in CosmosDB
    project_data = await project_service.create_project(
        user_id=user_id,
        title=title,
        status='in_progress'
    )
    
    # Add to list and select
    new_project = convert_to_ui_project(project_data)
    projects.insert(0, new_project)  # Add to top (most recent)
    await select_project(new_project.id)
```

---

## Project Status Icons (U2)

Each project displays a status icon indicating its current state.

### Status Definitions

| Status | Icon | Color | Meaning |
|--------|------|-------|---------|
| In Progress | `sync` | Blue (`primary`) | Active project, user can chat |
| Completed | `check_circle` | Green (`positive`) | User marked complete, read-only |
| Cancelled | `cancel` | Gray (`grey`) | User cancelled, read-only |

### Visual Reference

```
┌────────────────────────────┐
│ 🔄 Home Renovation         │  ← In Progress (blue icon)
│ Updated 2 hours ago        │
└────────────────────────────┘

┌────────────────────────────┐
│ ✓ Bulk Pickup              │  ← Completed (green icon)
│ Completed yesterday        │
└────────────────────────────┘

┌────────────────────────────┐
│ ✘ Business License         │  ← Cancelled (gray icon, faded)
│ Cancelled 3 days ago       │
└────────────────────────────┘
```

### NiceGUI Implementation

```python
STATUS_ICONS = {
    'in_progress': 'sync',
    'completed': 'check_circle',
    'cancelled': 'cancel',
}

STATUS_COLORS = {
    'in_progress': 'primary',
    'completed': 'positive',
    'cancelled': 'grey',
}

def render_project_card(project: Project, is_selected: bool = False):
    """Render a project card with status icon. (U2)"""
    
    # Cancelled projects appear faded (U3)
    card_classes = 'w-full cursor-pointer transition-all mb-2 p-3'
    if is_selected:
        card_classes += ' border-2 border-blue-500 bg-blue-50'
    elif project.status == 'cancelled':
        card_classes += ' opacity-60'
    else:
        card_classes += ' hover:shadow-md hover:bg-gray-50'
    
    with ui.card().classes(card_classes) as card:
        card.on('click', lambda: select_project(project.id))
        
        with ui.row().classes('items-center gap-2 w-full'):
            # Status icon (U2)
            ui.icon(
                STATUS_ICONS[project.status],
                color=STATUS_COLORS[project.status]
            )
            
            with ui.column().classes('flex-grow gap-0'):
                # Title (may be struck through if cancelled)
                title_classes = 'font-semibold truncate'
                if project.status == 'cancelled':
                    title_classes += ' line-through text-gray-500'
                ui.label(project.title).classes(title_classes)
                
                # Relative timestamp
                ui.label(format_relative_time(project.updated_at)).classes('text-xs text-gray-400')
```

---

## Cancel Project (U3)

Users can cancel a project to close it and make the chat read-only.

### Trigger

- Right-click context menu on project card → "Cancel Project"
- Or via menu icon on project card

### Confirmation Dialog

```
┌─────────────────────────────────────────┐
│  Cancel Project?                    [X] │
├─────────────────────────────────────────┤
│                                         │
│  Are you sure you want to cancel this   │
│  project? You will no longer be able    │
│  to send messages.                      │
│                                         │
│  This action cannot be undone.          │
│                                         │
│           [Cancel]  [Confirm Cancel]    │
└─────────────────────────────────────────┘
```

### After Cancellation

- Project card shows gray `cancel` icon
- Project card appears faded (reduced opacity)
- Title has strikethrough styling
- Chat panel shows disabled input with message: "This project has been cancelled"

### NiceGUI Implementation

```python
async def confirm_cancel_project(project: Project):
    """Show confirmation dialog for cancelling a project. (U3)"""
    
    with ui.dialog() as dialog, ui.card():
        ui.label('Cancel Project?').classes('text-lg font-bold')
        ui.label(
            'Are you sure you want to cancel this project? '
            'You will no longer be able to send messages.'
        ).classes('text-gray-600 my-4')
        ui.label('This action cannot be undone.').classes('text-sm text-red-600')
        
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            ui.button(
                'Confirm Cancel',
                on_click=lambda: cancel_project(project, dialog)
            ).props('color=negative')
    
    dialog.open()

async def cancel_project(project: Project, dialog):
    """Cancel a project and make it read-only. (U3)"""
    project.status = 'cancelled'
    project.updated_at = datetime.now(timezone.utc)
    
    await project_service.update_project(project.id, {
        'status': 'cancelled',
        'updated_at': project.updated_at.isoformat()
    })
    
    dialog.close()
    await refresh_ui()
```

### Read-Only Chat State

```python
# In chat panel, when project is cancelled or completed
if selected_project.status in ('cancelled', 'completed'):
    with ui.row().classes('w-full p-4 bg-gray-100 border-t'):
        ui.icon('lock', color='grey').classes('mr-2')
        status_msg = 'cancelled' if selected_project.status == 'cancelled' else 'completed'
        ui.label(f'This project has been {status_msg}').classes('text-gray-500')
else:
    # Normal input area
    with ui.row().classes('w-full p-4 border-t items-end gap-2'):
        message_input = ui.textarea(placeholder='Type your message...').classes('flex-grow')
        send_button = ui.button(icon='send', on_click=send_message).props('round color=primary')
```

---

## Mark Project Complete (U4)

Users can mark a project as complete when they've accomplished their goal.

### Trigger

- Right-click context menu on project card → "Mark as Complete"
- Or via menu icon on project card

### Confirmation Dialog

```
┌─────────────────────────────────────────┐
│  Mark as Complete?                  [X] │
├─────────────────────────────────────────┤
│                                         │
│  Mark this project as complete?         │
│  You will no longer be able to send     │
│  messages.                              │
│                                         │
│  This action cannot be undone.          │
│                                         │
│            [Cancel]  [Mark Complete]    │
└─────────────────────────────────────────┘
```

### After Completion

- Project card shows green `check_circle` icon
- Chat panel shows disabled input with message: "This project has been completed"

### NiceGUI Implementation

```python
async def confirm_complete_project(project: Project):
    """Show confirmation dialog for completing a project. (U4)"""
    
    with ui.dialog() as dialog, ui.card():
        ui.label('Mark as Complete?').classes('text-lg font-bold')
        ui.label(
            'Mark this project as complete? '
            'You will no longer be able to send messages.'
        ).classes('text-gray-600 my-4')
        ui.label('This action cannot be undone.').classes('text-sm text-orange-600')
        
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            ui.button(
                'Mark Complete',
                on_click=lambda: complete_project(project, dialog)
            ).props('color=positive')
    
    dialog.open()

async def complete_project(project: Project, dialog):
    """Mark a project as complete. (U4)"""
    project.status = 'completed'
    project.updated_at = datetime.now(timezone.utc)
    
    await project_service.update_project(project.id, {
        'status': 'completed',
        'updated_at': project.updated_at.isoformat()
    })
    
    dialog.close()
    await refresh_ui()
```

---

## Project Context Menu (U3, U4)

Right-click on a project card shows available actions.

### Visual Reference

```
┌────────────────────────────┐
│ 🔄 Home Renovation         │
│ Updated 2 hours ago        │
└────────────────────────────┘
         │
         ▼
    ┌─────────────────────┐
    │ ✓ Mark as Complete  │
    │ ─────────────────── │
    │ ✘ Cancel Project    │
    └─────────────────────┘
```

### Available Actions by Status

| Current Status | Available Actions |
|----------------|-------------------|
| In Progress | Mark as Complete, Cancel Project |
| Completed | *(no actions - read-only)* |
| Cancelled | *(no actions - read-only)* |

### NiceGUI Implementation

```python
def render_project_card(project: Project, is_selected: bool = False):
    """Render project card with context menu. (U3, U4)"""
    
    with ui.card().classes(card_classes) as card:
        # ... card content ...
        
        # Context menu (only for in_progress projects)
        if project.status == 'in_progress':
            with ui.menu().props('context-menu'):
                ui.menu_item(
                    '✓ Mark as Complete',
                    on_click=lambda: confirm_complete_project(project)
                )
                ui.separator()
                ui.menu_item(
                    '✘ Cancel Project',
                    on_click=lambda: confirm_cancel_project(project)
                ).classes('text-red-600')
```

---

## Edit Project Title (U7)

Users can edit the project title by clicking on it in the chat header.

### Visual Reference

```
Before click:                    After click (editing):
┌─────────────────────────────┐  ┌─────────────────────────────┐
│ 💬 260126-1430         [✏️] │  │ 💬 [Solar Panel Project  ] │
│                             │  │    ↑ Input field with focus │
└─────────────────────────────┘  └─────────────────────────────┘

After save:
┌─────────────────────────────┐
│ 💬 Solar Panel Project [✏️] │
│                             │
└─────────────────────────────┘
```

### Behavior

1. Click on title (or edit icon) → Title becomes an input field
2. Input is pre-filled with current title and focused
3. User types new title
4. **Save:** Press Enter or click outside
5. **Cancel:** Press Escape (reverts to previous title)
6. Empty titles are not allowed (revert to previous)
7. Maximum 100 characters
8. Title change updates `updated_at` (project moves to top of list per U5)
9. Edit is disabled for completed/cancelled projects

### NiceGUI Implementation

```python
def render_chat_header(project: Project):
    """Render chat header with editable title. (U7)"""
    
    is_editable = project.status == 'in_progress'
    editing = {'active': False, 'previous_title': project.title}
    
    with ui.row().classes('w-full items-center p-4 bg-gray-50 border-b gap-2'):
        ui.icon('chat').classes('text-xl text-primary')
        
        # Title display (click to edit if allowed)
        title_container = ui.row().classes('flex-grow items-center gap-2')
        
        with title_container:
            if is_editable:
                # Editable title
                title_label = ui.label(project.title).classes(
                    'font-semibold cursor-pointer hover:text-blue-600'
                )
                edit_icon = ui.icon('edit', size='xs').classes('text-gray-400 cursor-pointer')
                
                # Hidden input for editing
                title_input = ui.input(value=project.title).classes('hidden')
                title_input.props('dense outlined maxlength=100')
                
                async def start_editing():
                    editing['active'] = True
                    editing['previous_title'] = project.title
                    title_label.classes('hidden', add=True)
                    edit_icon.classes('hidden', add=True)
                    title_input.classes('hidden', remove=True)
                    title_input.run_method('focus')
                
                async def save_title():
                    new_title = title_input.value.strip()
                    if not new_title:
                        new_title = editing['previous_title']  # Revert if empty
                    
                    if new_title != project.title:
                        await project_service.update_project(project.id, {
                            'title': new_title,
                            'updated_at': datetime.now(timezone.utc).isoformat()
                        })
                        project.title = new_title
                    
                    editing['active'] = False
                    title_label.set_text(new_title)
                    title_label.classes('hidden', remove=True)
                    edit_icon.classes('hidden', remove=True)
                    title_input.classes('hidden', add=True)
                    await refresh_projects_list()  # Re-sort by updated_at
                
                async def cancel_editing():
                    editing['active'] = False
                    title_input.set_value(editing['previous_title'])
                    title_label.classes('hidden', remove=True)
                    edit_icon.classes('hidden', remove=True)
                    title_input.classes('hidden', add=True)
                
                title_label.on('click', start_editing)
                edit_icon.on('click', start_editing)
                title_input.on('blur', save_title)
                title_input.on('keydown.enter', save_title)
                title_input.on('keydown.escape', cancel_editing)
            else:
                # Read-only title for completed/cancelled projects
                ui.label(project.title).classes('font-semibold text-gray-500')
                ui.icon('lock', size='xs').classes('text-gray-400')
```

---

## Empty State

When the user has no projects yet.

### Visual Reference

```
┌──────────────────────────────┐
│  PROJECTS                [+] │
├──────────────────────────────┤
│                              │
│           📂                 │
│                              │
│      No projects yet         │
│                              │
│    Click + to start a new    │
│       conversation           │
│                              │
└──────────────────────────────┘
```

### NiceGUI Implementation

```python
def render_empty_state():
    """Render empty state when no projects exist."""
    with ui.column().classes('items-center justify-center p-4 text-center h-full'):
        ui.icon('folder_open', size='xl').classes('text-gray-400')
        ui.label('No projects yet').classes('text-gray-500 mt-4 font-semibold')
        ui.label('Click + to start a new conversation').classes('text-xs text-gray-400 mt-1')
```

---

## CSS Styles

```css
/* Projects panel layout */
.projects-panel {
    width: 300px;
    min-width: 300px;
}

/* Ensure scroll area fills available space */
.projects-scroll {
    flex: 1;
    overflow-y: auto;
}

/* Project card hover effect */
.project-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Selected project card */
.project-card-selected {
    border: 2px solid #1976d2;
    background-color: #e3f2fd;
}

/* Cancelled project styling */
.project-card-cancelled {
    opacity: 0.6;
}

.project-card-cancelled .project-title {
    text-decoration: line-through;
    color: #9e9e9e;
}
```

---

## Data Model

```python
class ProjectStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Project:
    id: str
    user_id: str
    title: str                    # Editable (U7)
    status: ProjectStatus         # in_progress, completed, cancelled (U2, U3, U4)
    created_at: datetime
    updated_at: datetime          # Used for sorting (U5)
    description: Optional[str]    # Optional subtitle
```

---

## Related Documentation

- [User Stories - Project Panel](../7-user-stories.md#project-panel) - Detailed acceptance criteria
- [Overview](ui-wireframes-overview.md) - Overall layout structure
- [Chat Interface](ui-wireframes-chat.md) - Message handling
- [Plan Widget](ui-wireframes-plan-widget.md) - Project plan visualization
