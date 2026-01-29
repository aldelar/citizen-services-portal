# UI Wireframes: Overview

This document defines the overall layout structure, navigation patterns, and responsive behavior for the Citizen Services Portal.

---

## NiceGUI Framework

This portal is built using **NiceGUI** (https://nicegui.io), a Python-based UI framework built on Vue.js and Quasar components. All UI specifications in these wireframes use NiceGUI's native elements exclusively.

**Key NiceGUI concepts used:**
- **Layout Elements**: `ui.header`, `ui.left_drawer`, `ui.right_drawer`, `ui.footer`, `ui.splitter`
- **Styling**: Tailwind CSS classes via `.classes()` and Quasar props via `.props()`
- **Data Binding**: `bind_value`, `bind_visibility` for reactive updates
- **Events**: `on_click`, `on_change` callbacks for interactivity

---

## Design Philosophy

The Citizen Services Portal is a **chat-first, project-centric** application that helps citizens navigate multi-agency government processes. The UI must be:

1. **Generic**: Render any project type (home renovation, business license, utility connection, etc.)
2. **Dynamic**: Handle plans with 3 steps or 30+ steps
3. **Agent-Driven**: The AI orchestrator builds and updates plans through conversation
4. **Action-Oriented**: Clearly surface what needs user attention

---

## Three-Panel Layout (Desktop)

The primary layout uses NiceGUI's native page layout components:

### Visual Reference

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│  🏛️ Citizen Services Portal          Home Renovation - 123 Main St    [👤] [?]   │
├──────────────────┬────────────────────────────────────────┬───────────────────────┤
│  PROJECTS   [+]  │                                        │  PROJECT PLAN         │
│  ──────────────  │  ┌────────────────────────────────┐    │  ─────────────────    │
│                  │  │ 🤖 Agent                       │    │  Progress: ████░ 80% │
│  ┌────────────┐  │  │ I'll help you with your solar  │    │                       │
│  │ 🔄 Home    │  │  │ panel installation...          │    │  ┌─────┐   ┌─────┐   │
│  │ Renovation │  │  └────────────────────────────────┘    │  │ P1  │──▶│ P2  │   │
│  │ ████░ 80%  │  │                                        │  │  ✓  │   │  ◐  │   │
│  └────────────┘  │  ┌────────────────────────────────┐    │  └─────┘   └─────┘   │
│                  │  │ 👤 John                   You  │    │      │         │     │
│  ┌────────────┐  │  │ Yes, that sounds good!         │    │      ▼         ▼     │
│  │ ✓ Bulk     │  │  └────────────────────────────────┘    │  ┌─────────────────┐ │
│  │ Pickup     │  │                                        │  │      I1         │ │
│  │ ████ 100%  │  │  ┌────────────────────────────────┐    │  │      ⚡         │ │
│  └────────────┘  │  │ 🤖 Agent                       │    │  └─────────────────┘ │
│                  │  │ Great! I've started the permit │    │                       │
│                  │  │ application for you...         │    │  ⚡ 1 action needed   │
│                  │  └────────────────────────────────┘    │  [View Task]          │
│                  │                                        │                       │
│                  │  ┌──────────────────────────────────┐  │                       │
│                  │  │ Type your message...      [Send] │  │                       │
│                  │  └──────────────────────────────────┘  │                       │
├──────────────────┴────────────────────────────────────────┴───────────────────────┤
│  Left Drawer         Center Content (Chat)                    Right Drawer       │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### NiceGUI Implementation

```python
# NiceGUI Layout Structure
@ui.page('/')
def main_page():
    with ui.header().classes('items-center justify-between'):
        # Brand, project title, user menu
        
    with ui.left_drawer().classes('bg-gray-100'):
        # Projects panel (navigation)
        
    with ui.right_drawer().classes('bg-white'):
        # Plan widget panel
        
    # Main content area (Chat)
    with ui.column().classes('w-full h-full'):
        # Chat interface
```

### NiceGUI Layout Components

| Panel | NiceGUI Element | Properties |
|-------|-----------------|------------|
| Header | `ui.header()` | `.classes('items-center')` |
| Left (Projects) | `ui.left_drawer(value=True)` | `.classes('bg-gray-100')`, `.props('width=280')` |
| Center (Chat) | `ui.column()` + `ui.scroll_area()` | `.classes('w-full h-full')` |
| Right (Plan) | `ui.right_drawer()` | `.classes('bg-white')`, `.props('width=360')` |

### Drawer Toggle Behavior

NiceGUI drawers have built-in toggle functionality:

```python
left_drawer = ui.left_drawer(value=True)  # Initially open
right_drawer = ui.right_drawer(value=False)  # Initially closed

# Toggle buttons in header
ui.button(icon='menu', on_click=left_drawer.toggle)
ui.button(icon='insights', on_click=right_drawer.toggle)
```

---

## Header Bar

The header uses NiceGUI's `ui.header()` with Quasar/Tailwind styling:

### Visual Reference

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│  🏛️ Citizen Services Portal          Home Renovation - 123 Main St    [👤▼] [?]  │
│                                                                          │        │
│                                                               ┌──────────┴──────┐ │
│                                                               │ 👤 Profile      │ │
│                                                               │ ⚙️ Settings     │ │
│                                                               │ ─────────────── │ │
│                                                               │ 🚪 Sign Out     │ │
│                                                               └─────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### NiceGUI Implementation

```python
with ui.header().classes('items-center justify-between px-4 bg-primary'):
    with ui.row().classes('items-center gap-4'):
        ui.icon('account_balance').classes('text-2xl text-white')
        ui.label('Citizen Services Portal').classes('text-xl text-white font-bold')
        
    # Project title (shown when project selected)
    project_title = ui.label().classes('text-white').bind_visibility_from(state, 'has_project')
    
    with ui.row().classes('items-center gap-2'):
        # User menu using ui.button with ui.menu
        with ui.button(icon='person').props('flat color=white'):
            with ui.menu():
                ui.menu_item('Profile', on_click=show_profile)
                ui.menu_item('Settings', on_click=show_settings)
                ui.separator()
                ui.menu_item('Sign Out', on_click=sign_out)
        
        ui.button(icon='help_outline', on_click=show_help).props('flat color=white')
```

### Header Components

| Component | NiceGUI Element | Purpose |
|-----------|-----------------|---------|
| Logo/Brand | `ui.icon()` + `ui.label()` | Identity |
| Project Title | `ui.label().bind_visibility_from()` | Context (hidden when no project) |
| User Menu | `ui.button()` + `ui.menu()` + `ui.menu_item()` | Account dropdown |
| Help | `ui.button(icon='help_outline')` | Opens help dialog |

---

## Responsive Behavior

NiceGUI drawers have built-in responsive behavior via Quasar props:

```python
# Responsive drawer configuration
with ui.left_drawer(value=True).props('breakpoint=768'):
    # Drawer auto-hides below 768px and shows toggle button
    pass
    
with ui.right_drawer().props('breakpoint=1024 overlay'):
    # Drawer overlays content below 1024px
    pass
```

### Breakpoint Behavior

| Breakpoint | Width | Layout Behavior |
|------------|-------|-----------------|
| Desktop Large | ≥1440px | Both drawers visible, side-by-side |
| Desktop | 1024-1439px | Left drawer visible, right drawer toggle |
| Tablet | 768-1023px | Both drawers as overlays |
| Mobile | <768px | Drawers hidden, use `ui.tabs` for navigation |

### Mobile Layout with Tabs

For mobile, use `ui.tabs` for bottom navigation:

### Visual Reference (Mobile)

```
┌─────────────────────────────────────────┐
│ 🏛️ Citizen Services       [👤]         │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ 🤖 Agent                          │  │
│  │ I'll help you with your solar     │  │
│  │ panel installation...             │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ 👤 John                      You  │  │
│  │ That sounds great!                │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ 🤖 Agent                          │  │
│  │ Perfect! I've started the permit  │  │
│  │ application...                    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Type your message...     [Send] │    │
│  └─────────────────────────────────┘    │
│                                         │
├─────────────────────────────────────────┤
│  [📁 Projects]  [💬 Chat]  [📊 Plan]   │
└─────────────────────────────────────────┘
```

### NiceGUI Implementation

```python
@ui.page('/')
def main_page():
    # Detect mobile via JavaScript or use ui.tabs for all sizes
    with ui.tabs().classes('w-full fixed-bottom').props('dense'):
        projects_tab = ui.tab('Projects', icon='folder')
        chat_tab = ui.tab('Chat', icon='chat')
        plan_tab = ui.tab('Plan', icon='analytics')
    
    with ui.tab_panels(tabs).classes('w-full h-full'):
        with ui.tab_panel(projects_tab):
            # Projects list
            pass
        with ui.tab_panel(chat_tab):
            # Chat interface
            pass
        with ui.tab_panel(plan_tab):
            # Plan widget
            pass
```

---

## Navigation Flow

Navigation is handled through NiceGUI's native routing and state management:

```python
from nicegui import ui, app

# Use app.storage for persistent state
@ui.page('/')
def main_page():
    # Load user's projects
    projects = app.storage.user.get('projects', [])
    selected_project_id = app.storage.user.get('selected_project')
    
    if not projects:
        show_welcome_empty_state()
    else:
        show_project_chat(selected_project_id)
```

### User Journey States

| State | Implementation | Primary Action |
|-------|---------------|----------------|
| First Visit | `if not projects: show_empty_state()` | Create first project |
| Has Projects | Render project list in `ui.left_drawer` | Select or create project |
| In Project | Show chat + plan panels | Converse with agent |
| Action Needed | Highlight with `ui.badge` + `ui.notify` | Complete user action |
| Project Done | Show completed state with `ui.chip` | View summary, start new |

---

## Empty States

Use NiceGUI's native elements for empty states:

### No Projects (First Visit)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                           🏛️                                   │
│                                                                 │
│              Welcome to the Citizen Services Portal             │
│                                                                 │
│          I'm your AI assistant for navigating LA city           │
│          services. Tell me what you need help with,             │
│          and I'll guide you through the process.                │
│                                                                 │
│     ┌───────────────────────────────────────────────────┐       │
│     │ Start a conversation...                    [Send] │       │
│     └───────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

```python
def show_welcome_empty_state():
    with ui.card().classes('max-w-lg mx-auto mt-16 p-8'):
        with ui.column().classes('items-center gap-4'):
            ui.icon('account_balance').classes('text-6xl text-primary')
            ui.label('Welcome to the Citizen Services Portal').classes('text-2xl font-bold text-center')
            ui.label("I'm your AI assistant for navigating LA city services.").classes('text-center text-gray-600')
            ui.label('Tell me what you need help with, and I\'ll guide you through the process.').classes('text-center text-gray-600')
            
            with ui.row().classes('w-full mt-4'):
                message_input = ui.input(placeholder='Start a conversation...').classes('flex-grow')
                ui.button(icon='send', on_click=lambda: start_conversation(message_input.value)).props('round color=primary')
```

### Project Selected, No Plan Yet

```
┌─────────────────────────────────────────┬───────────────────────────┐
│  Chat                                   │  PROJECT PLAN             │
├─────────────────────────────────────────┤  ─────────────────────    │
│                                         │                           │
│  ┌───────────────────────────────────┐  │           📋              │
│  │ 🤖 Agent                          │  │                           │
│  │ Hi! I'm here to help you with     │  │      No plan yet          │
│  │ your home renovation project.     │  │                           │
│  │ Tell me about what you're         │  │  As we discuss your       │
│  │ planning, and I'll help you       │  │  project, I'll build a    │
│  │ figure out what's needed.         │  │  step-by-step plan here.  │
│  └───────────────────────────────────┘  │                           │
│                                         │                           │
│  ┌─────────────────────────────────┐    │                           │
│  │ Type your message...     [Send] │    │                           │
│  └─────────────────────────────────┘    │                           │
└─────────────────────────────────────────┴───────────────────────────┘
```

```python
# Chat panel with welcome and plan panel with empty state
with ui.column().classes('flex-grow'):  # Main chat area
    with ui.scroll_area().classes('flex-grow'):
        ui.chat_message(
            "Hi! I'm here to help you with your home renovation project. "
            "Tell me about what you're planning, and I'll help you figure out what's needed.",
            name='Agent',
            avatar='https://robohash.org/agent'
        )
    # Input area
    with ui.row().classes('w-full p-4'):
        ui.input(placeholder='Type your message...').classes('flex-grow')
        ui.button(icon='send').props('round color=primary')

# Right drawer - Plan empty state
with ui.right_drawer():
    with ui.card().classes('w-full'):
        ui.label('PROJECT PLAN').classes('font-bold text-lg')
        ui.separator()
        with ui.column().classes('items-center py-8 gap-4'):
            ui.icon('assignment').classes('text-4xl text-gray-400')
            ui.label('No plan yet').classes('text-gray-500')
            ui.label("As we discuss your project, I'll build a step-by-step plan here.").classes('text-center text-gray-400 text-sm')
```

---

## Loading States

NiceGUI provides built-in loading components:

```python
# Page loading spinner
with ui.card().classes('max-w-sm mx-auto mt-16 p-8'):
    with ui.column().classes('items-center gap-4'):
        ui.spinner('dots', size='xl', color='primary')
        ui.label('Loading...').classes('text-gray-500')

# Skeleton loading for project cards
ui.skeleton().classes('w-full h-24 mb-2')
ui.skeleton().classes('w-full h-24 mb-2')
ui.skeleton().classes('w-full h-24')
```

### Loading Components

| State | NiceGUI Element |
|-------|-----------------|
| Page Load | `ui.spinner('dots')` |
| Content Loading | `ui.skeleton()` |
| Button Loading | `ui.button(...).props('loading')` |
| Chat Streaming | `ui.spinner('dots', size='sm')` in chat bubble |

---

## Accessibility Requirements

NiceGUI elements have built-in accessibility, enhanced via props:

```python
# Accessible button with ARIA label
ui.button('Submit', on_click=submit).props('aria-label="Submit form"')

# Screen reader announcements via ui.notify
ui.notify('Project saved successfully', type='positive')

# Focus management
input_field = ui.input().props('autofocus')
```

| Requirement | NiceGUI Implementation |
|-------------|------------------------|
| Keyboard Navigation | Built-in via Quasar components |
| Screen Reader | Use `.props('aria-label="..."')` |
| Color Contrast | Use Quasar theme colors (validated) |
| Focus Management | `.props('autofocus')`, tabindex via classes |
| Notifications | `ui.notify()` for announcements |

---

## Theme Support

The portal supports light and dark themes:

| Element | Light Theme | Dark Theme |
|---------|-------------|------------|
| Background | #FFFFFF | #1E1E1E |
| Surface | #F5F5F5 | #2D2D2D |
| Primary | #0066CC | #4DA3FF |
| Text Primary | #1A1A1A | #FAFAFA |
| Text Secondary | #666666 | #B3B3B3 |
| Border | #E0E0E0 | #404040 |
| Success | #28A745 | #34D058 |
| Warning | #FFC107 | #FFD93D |
| Error | #DC3545 | #F85149 |

---

## Related Documentation

- [User Account](ui-wireframes-user-account.md) - Account creation and profile management
- [Projects Panel](ui-wireframes-projects.md) - Project list and creation
- [Chat Interface](ui-wireframes-chat.md) - Message types and input
- [Plan Widget](ui-wireframes-plan-widget.md) - Dynamic graph visualization
- [User Actions](ui-wireframes-user-actions.md) - Action prompts and completion
- [Components](ui-wireframes-components.md) - Reusable UI components
