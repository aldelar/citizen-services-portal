# UI Wireframes: Chat Interface

This document defines the chat interface in the center panel, including message types, streaming behavior, and input handling.

---

## NiceGUI Components Used

| Feature | NiceGUI Element |
|---------|----------------|
| Message Bubbles | `ui.chat_message()` |
| Message Container | `ui.scroll_area()` |
| Text Input | `ui.input()` or `ui.textarea()` |
| Send Button | `ui.button()` |
| Typing Indicator | `ui.spinner('dots', size='sm')` |
| Markdown Content | `text_html=True` with sanitization |
| Timestamps | `stamp` parameter |

---

## Overview

The Chat Interface is the **primary interaction point** between the citizen and the AI agent. All communication flows through this panel—the agent guides users, answers questions, executes actions, and requests user tasks.

---

## Chat Panel Structure

```python
# Chat panel using NiceGUI native components
with ui.column().classes('w-full h-full'):
    # Header with project context
    with ui.row().classes('w-full items-center p-4 bg-gray-50 border-b'):
        ui.icon('chat').classes('text-xl')
        ui.label('Home Renovation - 123 Main St').classes('font-semibold flex-grow')
        with ui.button(icon='more_vert').props('flat round'):
            with ui.menu():
                ui.menu_item('Export Conversation')
                ui.menu_item('Start New Topic')
                ui.menu_item('Chat Settings')
    
    # Scrollable message history
    message_container = ui.scroll_area().classes('flex-grow p-4')
    
    # Input area
    with ui.row().classes('w-full p-4 border-t gap-2'):
        message_input = ui.input(placeholder='Type your message...').classes('flex-grow')
        ui.button(icon='send', on_click=send_message).props('round color=primary')
```

---

## Message Types

Based on the MCP server specifications and architecture, the chat must handle these message types:

### 1. User Message

Standard message from the citizen using `ui.chat_message()` with `sent=True`:

```python
ui.chat_message(
    'I want to install solar panels and battery storage on my house at 123 Main St',
    name='John Smith',
    stamp='10:30 AM',
    avatar='https://robohash.org/user',
    sent=True  # Right-aligned, sent style
)
```

#### NiceGUI Properties
- `sent=True`: Right-aligned with "sent" styling
- `avatar`: URL to user avatar image
- `stamp`: Timestamp string
- `name`: Optional author name

---

### 2. Agent Text Response

Standard response from the AI agent using `ui.chat_message()` (default is received style):

```python
from html_sanitizer import Sanitizer

agent_message = '''I'd be happy to help you with solar installation!

Based on your address, you'll need:
- Electrical permit from LADBS
- Interconnection agreement with LADWP  
- Possibly a building permit for roof work

Let me check the specific requirements for your area.'''

ui.chat_message(
    agent_message,
    name='Agent',
    stamp='10:31 AM',
    avatar='https://robohash.org/agent',
    text_html=True,
    sanitize=Sanitizer().sanitize
)
```

#### NiceGUI Properties
- `sent=False` (default): Left-aligned received style
- `text_html=True`: Enables markdown/HTML rendering
- `sanitize`: Required function for HTML sanitization
- Multi-part messages: Pass a list of strings for multiple bubbles

---

### 3. Agent Thinking/Processing

Shown when the agent is executing tools or processing using `ui.chat_message` with a spinner:

```python
# Create a thinking indicator that can be removed
with ui.chat_message(name='Agent', avatar='https://robohash.org/agent') as thinking_msg:
    ui.spinner('dots', size='md', color='primary')

# When response arrives, delete the thinking indicator
async def on_response_start():
    thinking_msg.delete()
    # Add actual response message
```

#### NiceGUI Implementation
- Use `ui.spinner('dots')` inside a `ui.chat_message` container
- Delete the spinner message when response starts
- Spinner types: 'dots', 'audio', 'ball', 'bars', 'box', etc.

---

### 4. Knowledge Citation

When the agent references indexed documents, use `ui.chat_message` with HTML content:

```python
from html_sanitizer import Sanitizer

citation_html = '''
According to LADBS requirements, solar PV systems require:

<blockquote class="border-l-4 border-primary pl-4 italic bg-gray-50 p-2 my-2">
"For systems over 10kW, a structural engineering analysis is required to verify roof capacity"
</blockquote>

<div class="text-sm text-gray-500 mt-2">
    <span class="mr-2">📄</span>
    Source: LADBS Solar Permit Guide, Section 3.2
    <a href="#" class="text-primary underline ml-2">View source ↗</a>
</div>
'''

ui.chat_message(
    citation_html,
    name='Agent',
    stamp='10:32 AM',
    text_html=True,
    sanitize=Sanitizer().sanitize
)
```

#### NiceGUI Implementation
- Use Tailwind classes for blockquote styling
- `text_html=True` enables rich formatting
- Links can navigate to source documents

---

### 5. Status Update

System notifications about process changes use `ui.chat_message` with `label` parameter:

```python
# Status update as a centered label message
ui.chat_message(label='✅ Status Update').classes('text-center')

# Or as a custom card within chat
with message_container:
    with ui.card().classes('mx-auto my-2 bg-green-50 border-green-200'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('check_circle', color='green')
            ui.label('Permit P1 submitted successfully').classes('font-semibold')
        ui.separator()
        with ui.column().classes('text-sm'):
            ui.label('Permit #: 2026-001234')
            ui.label('Status: Under Review')
            ui.label('Estimated review time: 4-6 weeks')
        ui.label('10:45 AM').classes('text-xs text-gray-400 mt-2')
```

#### NiceGUI Implementation
- Use `label` parameter for section headers
- Or use `ui.card` nested in message container for rich status
- Style with Tailwind color classes

---

### 6. Error Message

When something fails, use `ui.notify` for toast and/or inline error card:

```python
# Toast notification for errors
ui.notify(
    'Failed to connect to LADWP service',
    type='negative',
    close_button=True,
    position='top'
)

# Inline error in chat
with message_container:
    with ui.card().classes('mx-auto my-2 bg-red-50 border border-red-200'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('error', color='red')
            ui.label('Failed to connect to LADWP service').classes('font-semibold text-red-700')
        ui.label('The LADWP system is temporarily unavailable.').classes('text-sm text-gray-600')
        ui.button('Retry', on_click=retry_connection).props('color=negative outline')
        ui.label('10:48 AM').classes('text-xs text-gray-400 mt-2')
```

#### NiceGUI Implementation
- `ui.notify(type='negative')` for toast notifications
- `ui.card` with red styling for inline errors
- Include retry button where applicable

---

### 7. UserActionResponse Card (Critical)

When a tool returns a `UserActionResponse` indicating the user must take action.

**This is the most important message type to design correctly.**

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   🤖  Your electrical permit has been approved! 🎉           │
│                                                               │
│       Now you need to schedule the rough inspection.         │
│       This requires a phone call to 311.                     │
│                                                               │
│   ┌───────────────────────────────────────────────────────┐   │
│   │ ⚡ USER ACTION NEEDED                                  │   │
│   ├───────────────────────────────────────────────────────┤   │
│   │                                                       │   │
│   │  📞 Call 311 to schedule inspection                   │   │
│   │                                                       │   │
│   │  Why: LADBS inspection scheduling is only available   │   │
│   │       via phone                                       │   │
│   │                                                       │   │
│   │  ┌───────────────────────────────────────────────┐    │   │
│   │  │ 📋 Phone Script                          [▼] │    │   │
│   │  │ ─────────────────────────────────────────── │    │   │
│   │  │ "I need to schedule a rough electrical      │    │   │
│   │  │ inspection for permit #2026-001234 at       │    │   │
│   │  │ 123 Main St, Los Angeles. My name is        │    │   │
│   │  │ John Smith, phone 555-0123."                │    │   │
│   │  │                                  [📋 Copy]  │    │   │
│   │  └───────────────────────────────────────────────┘    │   │
│   │                                                       │   │
│   │  ┌───────────────────────────────────────────────┐    │   │
│   │  │ ✓ Checklist                              [▼] │    │   │
│   │  │ ─────────────────────────────────────────── │    │   │
│   │  │ ☐ Have permit number ready: 2026-001234     │    │   │
│   │  │ ☐ Confirm work is ready for inspection      │    │   │
│   │  │ ☐ Request morning slot if preferred         │    │   │
│   │  └───────────────────────────────────────────────┘    │   │
│   │                                                       │   │
│   │  📞 Contact: 311 (24/7)                               │   │
│   │                                                       │   │
│   ├───────────────────────────────────────────────────────┤   │
│   │            [ ✅ I've Completed This ]                 │   │
│   └───────────────────────────────────────────────────────┘   │
│                                                     11:00 AM │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

See [User Actions](6-ui-wireframes-user-actions.md) for complete UserActionResponse documentation.

---

## Message Components Detail

### Message Bubble Layout

```
┌─────────────────────────────────────────────────────────────┐
│ ┌────┐                                                      │
│ │ 🤖 │  Agent Name (optional)                              │
│ └────┘                                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                                                         │ │
│ │   Message content goes here. It can be multiple         │ │
│ │   lines and include formatting like **bold** and        │ │
│ │   bullet points.                                        │ │
│ │                                                         │ │
│ │   • Item one                                            │ │
│ │   • Item two                                            │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                   10:30 AM  │
└─────────────────────────────────────────────────────────────┘
```

### Timestamp Display

| Mode | Display |
|------|---------|
| Recent (today) | Time only: "10:30 AM" |
| Yesterday | "Yesterday, 10:30 AM" |
| This week | "Tuesday, 10:30 AM" |
| Older | "Jan 15, 10:30 AM" |
| Hover/expand | Full date-time |

---

## Streaming Support

NiceGUI supports real-time updates for streaming responses:

```python
# Create a message that will be updated as tokens arrive
streaming_message = None

async def handle_streaming_response():
    global streaming_message
    
    # Show typing indicator
    with message_container:
        thinking = ui.chat_message(name='Agent')
        with thinking:
            ui.spinner('dots', size='md')
    
    # Accumulate response
    full_response = ''
    
    async for token in agent.stream_response():
        if streaming_message is None:
            thinking.delete()
            streaming_message = ui.chat_message('', name='Agent', stamp=get_timestamp())
        
        full_response += token
        # Update message content
        streaming_message.props(f'text="{full_response}"')
        await asyncio.sleep(0)  # Allow UI to update
    
    # Finalize message
    streaming_message = None
    await message_container.scroll_to(percent=100)
```

### Streaming Behavior

| Behavior | NiceGUI Implementation |
|----------|------------------------|
| Typing indicator | `ui.spinner('dots')` in chat_message |
| Auto-scroll | `scroll_area.scroll_to(percent=100)` |
| Progressive update | Update element props/content |
| Completion | Delete spinner, finalize message |

---

## Input Area

Use `ui.textarea` with auto-grow and a send button:

```python
# Input area with NiceGUI
with ui.row().classes('w-full p-4 border-t items-end gap-2'):
    # Multiline input with auto-expand
    message_input = ui.textarea(
        placeholder='Type your message...'
    ).classes('flex-grow').props('autogrow rows=1 max-rows=6')
    
    # Send button - enabled only when input has content
    send_btn = ui.button(
        icon='send',
        on_click=send_message
    ).props('round color=primary')
    
    # Bind button enabled state to input content
    send_btn.bind_enabled_from(message_input, 'value', lambda v: bool(v and v.strip()))

# Handle Enter to send, Shift+Enter for newline
message_input.on('keydown.enter', lambda e: send_message() if not e.args.get('shiftKey') else None)
```

### Input States

| State | NiceGUI Implementation |
|-------|------------------------|
| Empty | `placeholder` prop, button disabled via `bind_enabled_from` |
| Typing | Default active styling (Quasar) |
| Disabled | `.props('disable')` during streaming |
| Error | `.props('error error-message=\"...\"')` |

---

## Chat Header

Use `ui.row` with `ui.button` and `ui.menu` for header:

```python
# Chat header with NiceGUI
with ui.row().classes('w-full items-center p-4 bg-gray-50 border-b'):
    ui.icon('chat').classes('text-xl text-primary')
    
    with ui.column().classes('flex-grow gap-0'):
        ui.label('Home Renovation - 123 Main St').classes('font-semibold')
        with ui.row().classes('text-sm text-gray-500 gap-2'):
            ui.chip('In Progress', color='primary').props('outline size=sm')
            ui.label('• Started Jan 15')
    
    # Header menu
    with ui.button(icon='more_vert').props('flat round'):
        with ui.menu():
            ui.menu_item('Export Conversation', on_click=export_chat)
            ui.menu_item('Start New Topic', on_click=new_topic)
            ui.menu_item('Chat Settings', on_click=open_settings)
            ui.separator()
            ui.menu_item('About this assistant', on_click=show_about)
```

### Header Components

| Component | NiceGUI Element |
|-----------|----------------|
| Chat icon | `ui.icon('chat')` |
| Project title | `ui.label().classes('font-semibold')` |
| Status chip | `ui.chip('In Progress')` |
| Menu button | `ui.button(icon='more_vert')` |
| Menu items | `ui.menu()` + `ui.menu_item()` |

---

## Scroll Behavior

NiceGUI's `ui.scroll_area` provides scroll control:

```python
# Scroll area with control
message_area = ui.scroll_area().classes('flex-grow p-4')

# Track if user scrolled up
user_scrolled_up = False

# New messages indicator (hidden by default)
new_messages_btn = ui.button(
    '↓ New messages',
    on_click=scroll_to_bottom
).classes('absolute bottom-20 left-1/2 -translate-x-1/2 z-10')
new_messages_btn.set_visibility(False)

async def scroll_to_bottom():
    await message_area.scroll_to(percent=100)
    new_messages_btn.set_visibility(False)

async def on_new_message():
    if user_scrolled_up:
        new_messages_btn.set_visibility(True)
    else:
        await scroll_to_bottom()
```

### Auto-scroll Rules

| Event | NiceGUI Implementation |
|-------|------------------------|
| New message | `scroll_area.scroll_to(percent=100)` |
| User scrolls up | Track with scroll event listener |
| Show indicator | `button.set_visibility(True)` |
| Return to bottom | `scroll_area.scroll_to(percent=100)` |

---

## Message Actions

Show action buttons on hover using `ui.element` with CSS hover states:

```python
# Message with hover actions
with ui.chat_message(name='Agent', stamp='10:31 AM') as msg:
    ui.markdown('Based on your address, you'll need permits...')
    
    # Action buttons (shown on hover via CSS)
    with ui.row().classes('gap-1 mt-1 opacity-0 hover-parent:opacity-100 transition-opacity'):
        ui.button(icon='content_copy', on_click=lambda: copy_text(msg)).props('flat round size=sm')
        ui.button(icon='thumb_up', on_click=lambda: feedback('good')).props('flat round size=sm')
        ui.button(icon='thumb_down', on_click=lambda: feedback('bad')).props('flat round size=sm')
```

### Action Types

| Action | Icon | NiceGUI Element |
|--------|------|-----------------|
| Copy | `content_copy` | `ui.button(icon='content_copy')` |
| Good response | `thumb_up` | `ui.button(icon='thumb_up')` |
| Bad response | `thumb_down` | `ui.button(icon='thumb_down')` |

---

## Mobile Chat View

On mobile, use full-screen layout with bottom navigation:

```python
# Mobile chat layout
@ui.page('/chat/{project_id}')
def mobile_chat(project_id: str):
    # Responsive - hide on larger screens
    with ui.column().classes('h-screen w-full lg:hidden'):
        # Header with back button
        with ui.row().classes('w-full items-center p-4 bg-gray-50 border-b'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat round')
            ui.label('Home Renovation').classes('flex-grow font-semibold')
            with ui.button(icon='more_vert').props('flat round'):
                with ui.menu():
                    ui.menu_item('Export')
                    ui.menu_item('Settings')
        
        # Messages
        message_area = ui.scroll_area().classes('flex-grow p-4')
        
        # Input
        with ui.row().classes('w-full p-4 border-t items-end gap-2'):
            ui.textarea(placeholder='Type your message...').classes('flex-grow').props('autogrow')
            ui.button(icon='send').props('round color=primary')
        
        # Bottom navigation
        with ui.row().classes('w-full border-t justify-around py-2'):
            ui.button('Projects', icon='folder', on_click=lambda: ui.navigate.to('/projects')).props('flat')
            ui.button('Chat', icon='chat').props('flat color=primary')
            ui.button('Plan', icon='timeline', on_click=lambda: ui.navigate.to('/plan')).props('flat')
---

## Related Documentation

- [Overview](ui-wireframes-overview.md) - Layout structure
- [Projects](ui-wireframes-projects.md) - Project navigation
- [Plan Widget](ui-wireframes-plan-widget.md) - Plan visualization
- [User Actions](ui-wireframes-user-actions.md) - UserActionResponse handling
- [Components](ui-wireframes-components.md) - Reusable components
