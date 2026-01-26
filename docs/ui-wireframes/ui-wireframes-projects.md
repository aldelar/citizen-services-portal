# UI Wireframes: Projects Panel

This document defines the project list, creation flow, and project management features in the left panel, implemented with NiceGUI native components.

---

## NiceGUI Components Used

| Feature | NiceGUI Element |
|---------|-----------------|
| Projects container | `ui.left_drawer()` or `ui.column()` |
| Project cards | `ui.card()` |
| Search | `ui.input()` with icon |
| Progress bar | `ui.linear_progress()` |
| Status chips | `ui.chip()` |
| Add button | `ui.button(icon='add')` |
| Context menu | `ui.menu()` + `ui.menu_item()` |
| Empty state | `ui.card()` with centered content |

---

## Overview

The Projects Panel serves as the navigation hub for all user projects. It displays existing projects, allows creation of new projects, and provides filtering/search capabilities.

**Key Principle**: Project types are **discovered through conversation**, not pre-selected. The user starts a conversation, and the agent determines what type of project this is.

---

## Project List (Left Panel)

### Visual Reference

```
┌──────────────────────────────┐
│  PROJECTS                [+]  │
├──────────────────────────────┤
│  ┌────────────────────────┐  │
│  │ 🔍 Search projects...  │  │
│  └────────────────────────┘  │
│                              │
│  ╭────────────────────────╮  │
│  │ 🔄 Home Renovation    │  │  ← Selected
│  │ 123 Main St          │  │
│  │ ████████░░ 80%       │  │
│  │ [Action Needed]      │  │
│  │ Updated 2 hours ago  │  │
│  ╰────────────────────────╯  │
│                              │
│  ┌────────────────────────┐  │
│  │ ✓ Bulk Pickup        │  │
│  │ 456 Oak Ave          │  │
│  │ ██████████ 100%     │  │
│  │ [Completed]          │  │
│  │ Completed yesterday  │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │ ⌛ Business License   │  │
│  │ My Coffee Shop       │  │
│  │ ████░░░░░░ 40%        │  │
│  │ [Waiting]            │  │
│  │ Updated 3 days ago   │  │
│  └────────────────────────┘  │
│                              │
└──────────────────────────────┘
```

### NiceGUI Implementation

```python
# Project list panel using NiceGUI
with ui.left_drawer(value=True).classes('bg-gray-50'):
    # Header
    with ui.row().classes('w-full items-center p-4'):
        ui.label('PROJECTS').classes('text-sm font-bold text-gray-500 flex-grow')
        ui.button(icon='add', on_click=new_project).props('round flat size=sm')
    
    # Search
    with ui.row().classes('px-4 pb-2'):
        search = ui.input(placeholder='Search projects...').props('dense clearable').classes('w-full')
        search.props('prepend-icon=search')
    
    # Project cards list
    project_list = ui.column().classes('w-full gap-2 px-2')
    
    def render_project_card(project, selected=False):
        with ui.card().classes(
            f'w-full cursor-pointer {"border-2 border-primary bg-primary-50" if selected else "hover:shadow-md"}'
        ).on('click', lambda: select_project(project)):
            with ui.row().classes('items-center gap-2'):
                ui.icon(get_status_icon(project.status))
                ui.label(project.title).classes('font-semibold flex-grow truncate')
                status_chip(project.status)
            
            ui.label(project.subtitle).classes('text-sm text-gray-600 truncate')
            
            with ui.row().classes('items-center gap-2 mt-2'):
                ui.linear_progress(value=project.progress).classes('flex-grow')
                ui.label(f'{int(project.progress * 100)}%').classes('text-xs text-gray-500')
            
            ui.label(format_time_ago(project.updated_at)).classes('text-xs text-gray-400 mt-1')
```

### Narrow View

Use responsive classes to show abbreviated content:

```python
# Narrow/collapsed view
with ui.column().classes('w-full gap-1'):
    for project in projects:
        with ui.card().classes('p-2 cursor-pointer').on('click', lambda p=project: select_project(p)):
            with ui.row().classes('items-center gap-1'):
                ui.icon(get_status_icon(project.status), size='xs')
                ui.label(project.title).classes('text-sm truncate flex-grow')
            ui.label(f'{int(project.progress * 100)}%').classes('text-xs text-gray-500')
```

---

## Project Card

Each project is displayed as a card with consistent information:

```python
def render_project_card(project: Project, is_selected: bool = False):
    """Render a project card with all components."""
    
    # Card with selection styling
    card_classes = 'w-full cursor-pointer transition-shadow'
    if is_selected:
        card_classes += ' border-2 border-primary bg-blue-50'
    else:
        card_classes += ' hover:shadow-md'
    
    with ui.card().classes(card_classes).on('click', lambda: select_project(project)):
        # Header row: icon, title, status
        with ui.row().classes('items-center gap-2'):
            ui.icon(STATUS_ICONS[project.status], color=STATUS_COLORS[project.status])
            ui.label(project.title).classes('font-semibold flex-grow truncate')
            ui.chip(
                STATUS_LABELS[project.status],
                color=STATUS_COLORS[project.status]
            ).props('size=sm')
        
        # Subtitle (address or description)
        if project.subtitle:
            ui.label(project.subtitle).classes('text-sm text-gray-600 truncate')
        
        # Progress bar
        with ui.row().classes('items-center gap-2 mt-2'):
            ui.linear_progress(
                value=project.progress,
                color=STATUS_COLORS.get(project.status, 'primary')
            ).classes('flex-grow')
            ui.label(f'{int(project.progress * 100)}%').classes('text-xs text-gray-500 w-8 text-right')
        
        # Status message
        if project.action_count:
            ui.label(f'{project.action_count} action{"s" if project.action_count > 1 else ""} needed').classes('text-sm text-orange-600')
        
        # Last updated
        ui.label(f'Updated {format_relative_time(project.updated_at)}').classes('text-xs text-gray-400 mt-1')
```

### Project Status Icons

```python
STATUS_ICONS = {
    'action_needed': 'bolt',
    'in_progress': 'sync',
    'waiting': 'hourglass_empty',
    'completed': 'check_circle',
    'cancelled': 'cancel',
    'new': 'article',
}

STATUS_COLORS = {
    'action_needed': 'warning',
    'in_progress': 'primary',
    'waiting': 'grey',
    'completed': 'positive',
    'cancelled': 'grey',
    'new': 'info',
}

STATUS_LABELS = {
    'action_needed': 'Action Needed',
    'in_progress': 'In Progress',
    'waiting': 'Waiting',
    'completed': 'Completed',
    'cancelled': 'Cancelled',
    'new': 'New',
}
```

---

## Project States

Projects have distinct visual states using NiceGUI styling:

### Visual Reference

```
┌───────────────────────────────────────────────────────────────────┐
│  ACTIVE - IN PROGRESS                                           │
│  ┃ 🔄 Home Renovation                      [In Progress] │
│  ┃ 123 Main St                                          │
│  ┃ ████████░░ 80%                                        │
├───────────────────────────────────────────────────────────────────┤
│  NEEDS ACTION (Orange highlight)                                 │
│  ┃ ⚡ Home Renovation                      [1 action] !  │
│  ┃ 123 Main St           (orange bg)                    │
│  ┃ ████████░░ 80%                                        │
├───────────────────────────────────────────────────────────────────┤
│  WAITING (Gray)                                                  │
│  │ ⌛ Home Renovation                         [Waiting]  │
│  │ Waiting for agency...                                │
│  │ ████████░░ 80%                                        │
├───────────────────────────────────────────────────────────────────┤
│  COMPLETED (Green)                                               │
│  ┃ ✓ Bulk Pickup                            [Completed] │
│  ┃ 456 Oak Ave                                          │
│  ┃ ██████████ 100%                                       │
├───────────────────────────────────────────────────────────────────┤
│  CANCELLED (Faded, strikethrough)                                │
│    ✘ Business License                       [Cancelled] │
│    My Coffee Shop                  (faded/strikethrough) │
│    ░░░░░░░░░░ 40%                                        │
└───────────────────────────────────────────────────────────────────┘
```

### NiceGUI Implementation

```python
# Active - in progress
with ui.card().classes('border-l-4 border-primary'):
    with ui.row().classes('items-center gap-2'):
        ui.icon('sync', color='primary')
        ui.label('Home Renovation').classes('font-semibold')
    ui.linear_progress(value=0.8, color='primary')
    ui.chip('In Progress', color='primary').props('size=sm')

# Active - needs action (highlighted)
with ui.card().classes('border-l-4 border-orange-500 bg-orange-50'):
    with ui.row().classes('items-center gap-2'):
        ui.icon('bolt', color='warning')
        ui.label('Home Renovation').classes('font-semibold')
        ui.badge('!', color='warning').classes('ml-auto')  # Attention indicator
    ui.linear_progress(value=0.8, color='warning')
    ui.chip('1 action needed', color='warning').props('size=sm')

# Waiting
with ui.card().classes('border-l-4 border-gray-400'):
    with ui.row().classes('items-center gap-2'):
        ui.icon('hourglass_empty', color='grey')
        ui.label('Home Renovation').classes('font-semibold')
    ui.linear_progress(value=0.8, color='grey')
    ui.chip('Waiting for agency', color='grey').props('size=sm')

# Completed
with ui.card().classes('border-l-4 border-green-500'):
    with ui.row().classes('items-center gap-2'):
        ui.icon('check_circle', color='positive')
        ui.label('Bulk Pickup').classes('font-semibold')
    ui.linear_progress(value=1.0, color='positive')
    ui.chip('Completed', color='positive').props('size=sm')

# Cancelled
with ui.card().classes('border-l-4 border-gray-300 opacity-60'):
    with ui.row().classes('items-center gap-2'):
        ui.icon('cancel', color='grey')
        ui.label('Business License').classes('font-semibold line-through')
    ui.linear_progress(value=0.4, color='grey')
    ui.chip('Cancelled', color='grey').props('size=sm')
```

---

## Project Status Indicators

| Status | Icon | Quasar Color | Description |
|--------|------|--------------|-------------|
| In Progress | `sync` | `primary` | Active, steps being worked |
| Action Needed | `bolt` | `warning` | User has pending tasks |
| Waiting | `hourglass_empty` | `grey` | Waiting for agency response |
| Completed | `check_circle` | `positive` | All steps done |
| Cancelled | `cancel` | `grey` | User cancelled project |
| Error | `error` | `negative` | Something failed |

---

## Project Creation Flow

Projects are created through **conversation**, not forms. The user starts talking, and a project is created contextually.

### Step 1: Initiate Conversation

User clicks "+ New" or starts typing in an empty state.

```
┌──────────────────────────────────────────────────────┐
│  🤖 Agent                                          │
│                                                    │
│  Hi! I'm here to help you with LA city services.   │
│  What can I help you with today?                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ I want to install solar panels on my house...      │
└──────────────────────────────────────────────[➤ Send]┘
```

```python
# Welcome message using ui.chat_message
with ui.chat_message(name='Agent'):
    ui.markdown("Hi! I'm here to help you with LA city services.")
    ui.markdown("What can I help you with today?")

# User input
with ui.row().classes('w-full p-4'):
    ui.textarea(placeholder='I want to install solar panels on my house...').classes('flex-grow')
    ui.button(icon='send').props('round color=primary')
```

### Step 2: Agent Creates Project

The agent recognizes the intent and creates a project automatically.

```
┌──────────────────────────────────────────────────────┐
│  🤖 Agent                                          │
│                                                    │
│  I'd be happy to help you with solar installation! │
│  I've started a project to track this.             │
│                                                    │
│  First, I'll need some information:                │
│  📍 What's your property address?                   │
└──────────────────────────────────────────────────────┘
```

```python
# Agent responds and requests info
with ui.chat_message(name='Agent'):
    ui.markdown("I'd be happy to help you with solar panel installation!")
    ui.markdown("I've started a project to track this. First, I'll need some information:")
    ui.markdown("📍 What's your property address?")
```

### Step 3: Project Appears in List

```
┌──────────────────────────┐
│  PROJECTS            [+]  │
├──────────────────────────┤
│                          │
│  ╭────────────────────╮  │
│  │ 📄 Solar         │  │  ← NEW!
│  │ Installation    │  │
│  │ 123 Main St     │  │
│  │ ░░░░░░░░░░ 0%   │  │
│  │ [NEW]           │  │
│  │ Just now        │  │
│  ╰────────────────────╯  │
│                          │
└──────────────────────────┘
```

```python
# New project card appears with 'new' status
with ui.card().classes('border-l-4 border-blue-400 bg-blue-50'):
    with ui.row().classes('items-center gap-2'):
        ui.icon('article', color='info')
        ui.label('Solar Installation').classes('font-semibold')
        ui.chip('NEW', color='info').props('size=sm')
    ui.label('123 Main St').classes('text-sm text-gray-600')
    ui.linear_progress(value=0).classes('mt-2')
    ui.label('Just now').classes('text-xs text-gray-400')
```

---

## Project Selection

The selected project uses highlight styling:

```python
def render_projects(projects: list, selected_id: str):
    for project in projects:
        is_selected = project.id == selected_id
        
        # Selected card has primary border and background tint
        card_classes = 'w-full cursor-pointer transition-all'
        if is_selected:
            card_classes += ' border-2 border-primary bg-primary/10 shadow-md'
        else:
            card_classes += ' hover:shadow-md hover:bg-gray-50'
        
        with ui.card().classes(card_classes).on('click', lambda p=project: select_project(p)):
            render_project_content(project)
```

### Selection Behavior

| Interaction | Result |
|-------------|--------|
| Click project card | Select project, load chat + plan |
| Click current project | No change (already selected) |

---

## Search and Filter

Use `ui.input` with search icon and filter dropdown:

```python
# Search and filter controls
with ui.column().classes('w-full px-4 gap-2'):
    # Search input
    search = ui.input(placeholder='Search projects...').classes('w-full')
    search.props('dense clearable prepend-icon=search')
    search.on('update:model-value', lambda e: filter_projects(e.args))
    
    # Filter dropdown
    with ui.row().classes('items-center gap-2'):
        ui.label('Filter:').classes('text-sm text-gray-500')
        filter_select = ui.select(
            options=['All', 'Active', 'Needs Action', 'Completed', 'Cancelled'],
            value='All'
        ).props('dense').classes('flex-grow')
        filter_select.on('update:model-value', apply_filter)

# Filter logic
def filter_projects(search_term: str):
    for card in project_cards:
        visible = search_term.lower() in card.project.title.lower()
        card.set_visibility(visible)

# Results count
ui.label('2 projects match "permit"').classes('text-xs text-gray-500 px-4')
```

---

## Project Context Menu

Use `ui.menu` attached to cards for context actions:

```python
# Right-click context menu on project card
with ui.card().classes('w-full') as card:
    render_project_content(project)
    
    # Context menu
    with ui.menu().props('context-menu'):
        ui.menu_item('View Details', on_click=lambda: view_details(project))
        ui.menu_item('Rename', on_click=lambda: rename_project(project))
        ui.menu_item('Export Summary', on_click=lambda: export_project(project))
        ui.separator()
        ui.menu_item(
            'Cancel Project',
            on_click=lambda: confirm_cancel(project)
        ).classes('text-red-600')
```

### Context Actions

| Action | NiceGUI Element | Available When |
|--------|-----------------|----------------|
| View Details | `ui.menu_item` → opens `ui.dialog` | Always |
| Rename | `ui.menu_item` → inline edit or dialog | Active/Waiting |
| Export Summary | `ui.menu_item` → triggers download | Always |
| Cancel Project | `ui.menu_item` → confirmation `ui.dialog` | Active/Waiting |

---

## Empty States

Use `ui.card` with centered content for empty states:

### No Projects

```
┌──────────────────────────────┐
│  PROJECTS            [+]  │
├──────────────────────────────┤
│                              │
│          📂                  │
│                              │
│      No projects yet         │
│                              │
│    Start by telling me       │
│    what you need help with   │
│                              │
│      [+ Start New]           │
│                              │
└──────────────────────────────┘
```

```python
# No projects empty state
with ui.column().classes('w-full h-full items-center justify-center p-8'):
    with ui.card().classes('text-center p-8'):
        ui.icon('folder_open', size='xl').classes('text-gray-400')
        ui.label('No projects yet').classes('text-lg font-semibold mt-4')
        ui.label('Start by telling me what you need help with').classes('text-gray-600 mt-2')
        ui.button('+ Start New', icon='add', on_click=new_project).props('color=primary').classes('mt-4')

# No search results
with ui.column().classes('w-full p-4 text-center'):
    ui.label('No projects match').classes('text-gray-500')
    ui.label(f'"{search_term}"').classes('font-semibold')
    ui.button('Clear search', on_click=clear_search).props('flat').classes('mt-2')
```

---

## Mobile View

On mobile, the projects panel becomes a full-screen tab accessible via bottom navigation:

### Visual Reference

```
┌─────────────────────────────────────────┐
│ 📁 Projects                          [+]  │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │ 🔍 Search projects...             │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ 🔄 Home Renovation    [In Progress] │  │
│  │ 123 Main St                       │  │
│  │ ████████░░ 80%                     │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ ✓ Bulk Pickup          [Completed] │  │
│  │ 456 Oak Ave                       │  │
│  │ ██████████ 100%                   │  │
│  └───────────────────────────────────┘  │
│                                         │
├─────────────────────────────────────────┤
│  [📁 Projects]  [💬 Chat]  [📊 Plan]    │
└─────────────────────────────────────────┘
```

### NiceGUI Implementation

```python
# Mobile projects view
@ui.page('/projects')
def mobile_projects_page():
    with ui.column().classes('h-screen w-full lg:hidden'):
        # Header
        with ui.row().classes('w-full items-center p-4 bg-gray-50 border-b'):
            ui.icon('folder').classes('text-xl')
            ui.label('Projects').classes('text-lg font-semibold flex-grow')
            ui.button(icon='add', on_click=new_project).props('round flat')
        
        # Search
        with ui.row().classes('w-full px-4 py-2'):
            ui.input(placeholder='Search projects...').classes('w-full').props('dense clearable prepend-icon=search')
        
        # Project list
        with ui.scroll_area().classes('flex-grow'):
            for project in projects:
                with ui.card().classes('mx-4 mb-2').on('click', lambda p=project: navigate_to_project(p)):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon(STATUS_ICONS[project.status], color=STATUS_COLORS[project.status])
                        ui.label(project.title).classes('font-semibold flex-grow')
                    ui.label(project.subtitle).classes('text-sm text-gray-600')
                    with ui.row().classes('items-center gap-2 mt-2'):
                        ui.linear_progress(value=project.progress).classes('flex-grow')
                        ui.chip(STATUS_LABELS[project.status]).props('size=sm')
        
        # Bottom navigation
        with ui.row().classes('w-full border-t justify-around py-2'):
            ui.button('Projects', icon='folder').props('flat color=primary')
            ui.button('Chat', icon='chat', on_click=lambda: ui.navigate.to('/chat')).props('flat')
            ui.button('Plan', icon='timeline', on_click=lambda: ui.navigate.to('/plan')).props('flat')
```

---

## Related Documentation

- [Overview](ui-wireframes-overview.md) - Overall layout structure
- [User Account](ui-wireframes-user-account.md) - Account creation and profile management
- [Chat Interface](ui-wireframes-chat.md) - Message handling
- [Plan Widget](ui-wireframes-plan-widget.md) - Project plan visualization
