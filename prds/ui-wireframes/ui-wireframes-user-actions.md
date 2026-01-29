# UI Wireframes: User Actions

This document defines the design for UserActionResponse cards—when the AI agent delegates tasks that require the citizen to take action outside the system.

## NiceGUI Component Mapping

| UI Element | NiceGUI Component | Styling |
|------------|------------------|---------|
| Action Card | `ui.card()` | `border-2 border-orange-400 bg-orange-50` |
| Collapsible Sections | `ui.expansion()` | `.props('expand-icon-toggle')` |
| Script/Draft Text | `ui.card()` + `ui.label()` | `bg-gray-50 font-mono` |
| Checklist Items | `ui.checkbox()` | Default styling |
| Copy Button | `ui.button()` | `.props('flat size=sm')` |
| Completion Form | `ui.dialog()` + `ui.input()` | Modal dialog |
| Date Picker | `ui.date()` | Native date picker |
| Action Icons | `ui.icon()` | `phone`, `email`, `business`, `language` |

---

## Overview

When an MCP tool returns a `UserActionResponse`, the system cannot automate the action. Instead, it prepares materials for the user and tracks task completion.

### UserActionResponse Pattern

From the MCP server specifications:

```python
class UserActionResponse(BaseModel):
    requires_user_action: bool = True
    action_type: str              # "phone_call", "email", "in_person", "online_portal"
    target: str                   # "311", email address, URL, office location
    reason: str                   # Why this can't be automated
    
    prepared_materials: PreparedMaterials
    on_complete: OnCompletePrompt

class PreparedMaterials(BaseModel):
    phone_script: Optional[str]   # What to say on phone
    email_draft: Optional[str]    # Draft email content
    checklist: List[str]          # Items to have ready
    contact_info: Optional[dict]  # Phone, hours, address
    documents_needed: List[str]   # Documents to prepare

class OnCompletePrompt(BaseModel):
    prompt: str                   # Question to ask
    expected_info: List[str]      # Fields to collect
```

---

## Action Types

The system handles four action types:

| Action Type | Icon | NiceGUI Icon Name | Example Target |
|-------------|------|-------------------|----------------|
| `phone_call` | 📞 | `phone` | 311 |
| `email` | 📧 | `email` | solar@ladwp.com |
| `in_person` | 🏢 | `business` | LADBS Office |
| `online_portal` | 🌐 | `language` | ladwp.com/NEM |

---

## UserAction Card Design

### Complete Card Structure with NiceGUI

#### Visual Reference

```
┌───────────────────────────────────────────────────────────┐
│  ⚡ USER ACTION NEEDED                           [?]   │
├───────────────────────────────────────────────────────────┤
│                                                         │
│  📞 Call 311 to schedule inspection                     │
│                                                         │
│  Why: LADBS inspection scheduling is only available     │
│       via phone                                         │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ ▶ Phone Script                                  [▼]  │  │
│  │ ───────────────────────────────────────────────  │  │
│  │ "I need to schedule a rough electrical             │  │
│  │  inspection for permit #2026-001234 at             │  │
│  │  123 Main St, Los Angeles. My name is              │  │
│  │  John Smith, phone 555-0123."                      │  │
│  │                                          [📋 Copy]  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ ▶ Have These Ready                            [▼]  │  │
│  │ ───────────────────────────────────────────────  │  │
│  │ ☐ Have permit number ready: 2026-001234           │  │
│  │ ☐ Confirm work is ready for inspection            │  │
│  │ ☐ Know your preferred time slot                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  📞 311 (24/7)  🕒 Mon-Fri 8am-5pm                       │
│                                                         │
├───────────────────────────────────────────────────────────┤
│               [ ✅ I've Completed This ]                 │
└───────────────────────────────────────────────────────────┘
```

#### NiceGUI Implementation

```python
def render_user_action_card(action: UserActionResponse, on_complete: Callable):
    """Render a UserActionResponse card."""
    
    # Action type icons
    ACTION_ICONS = {
        'phone_call': ('phone', 'Call'),
        'email': ('email', 'Email'),
        'in_person': ('business', 'Visit'),
        'online_portal': ('language', 'Go to'),
    }
    icon, verb = ACTION_ICONS.get(action.action_type, ('help', 'Complete'))
    
    with ui.card().classes('border-2 border-orange-400 bg-orange-50 w-full'):
        # Header
        with ui.row().classes('items-center gap-2 w-full'):
            ui.icon('bolt', color='warning')
            ui.label('USER ACTION NEEDED').classes('font-bold text-orange-700 flex-grow')
            with ui.button(icon='help_outline').props('flat round size=sm'):
                ui.tooltip(action.reason)
        
        ui.separator()
        
        # Primary action line
        with ui.row().classes('items-center gap-2'):
            ui.icon(icon, color='warning')
            ui.label(f'{verb} {action.target}').classes('text-lg font-semibold')
        
        # Reason
        ui.label(f'Why: {action.reason}').classes('text-sm text-gray-600 italic')
        
        # Prepared materials (collapsible sections)
        materials = action.prepared_materials
        
        if materials.phone_script:
            with ui.expansion('Phone Script', icon='description').classes('w-full'):
                with ui.card().classes('bg-gray-50'):
                    ui.label(materials.phone_script).classes('font-mono text-sm whitespace-pre-wrap')
                    ui.button('Copy', icon='content_copy', on_click=lambda: copy_to_clipboard(materials.phone_script)).props('flat size=sm').classes('mt-2')
        
        if materials.email_draft:
            with ui.expansion('Email Draft', icon='email').classes('w-full'):
                with ui.card().classes('bg-gray-50'):
                    ui.label(f"To: {materials.email_to}").classes('text-sm font-medium')
                    ui.label(f"Subject: {materials.email_subject}").classes('text-sm')
                    ui.separator()
                    ui.label(materials.email_draft).classes('text-sm whitespace-pre-wrap')
                    with ui.row().classes('gap-2 mt-2'):
                        ui.button('Copy All', icon='content_copy', on_click=lambda: copy_to_clipboard(materials.email_draft)).props('flat size=sm')
                        ui.button('Open Email Client', icon='open_in_new', on_click=lambda: open_mailto(materials)).props('flat size=sm')
        
        if materials.checklist:
            with ui.expansion('Have These Ready', icon='checklist').classes('w-full'):
                for item in materials.checklist:
                    ui.checkbox(item).classes('text-sm')
        
        if materials.documents_needed:
            with ui.expansion('Documents Needed', icon='attach_file').classes('w-full'):
                for doc in materials.documents_needed:
                    ui.checkbox(doc).classes('text-sm')
        
        # Contact information
        if materials.contact_info:
            with ui.row().classes('gap-4 text-sm text-gray-600 mt-4'):
                if materials.contact_info.get('phone'):
                    with ui.row().classes('items-center gap-1'):
                        ui.icon('phone', size='xs')
                        ui.label(materials.contact_info['phone'])
                if materials.contact_info.get('hours'):
                    with ui.row().classes('items-center gap-1'):
                        ui.icon('schedule', size='xs')
                        ui.label(materials.contact_info['hours'])
                if materials.contact_info.get('url'):
                    ui.link(materials.contact_info['url'], materials.contact_info['url'], new_tab=True).classes('text-blue-600')
        
        ui.separator()
        
        # Completion button
        ui.button("I've Completed This", icon='check_circle', on_click=on_complete).props('color=warning').classes('w-full')
```

---

## Card Components

### Header with NiceGUI

```python
# Header row with icon, title, and help button
with ui.row().classes('items-center gap-2 w-full'):
    ui.icon('bolt', color='warning')
    ui.label('USER ACTION NEEDED').classes('font-bold text-orange-700 flex-grow')
    with ui.button(icon='help_outline').props('flat round size=sm'):
        ui.tooltip('This action cannot be automated and requires you to complete it directly.')
```

### Primary Action Line

Format: `[Action Type Icon] [Action Verb] [Target] to [Purpose]`

```python
# Action line based on type
ACTION_CONFIG = {
    'phone_call': ('phone', 'Call'),
    'email': ('email', 'Email'),
    'in_person': ('business', 'Visit'),
    'online_portal': ('language', 'Go to'),
}

icon_name, verb = ACTION_CONFIG.get(action.action_type, ('help', 'Complete'))

with ui.row().classes('items-center gap-2'):
    ui.icon(icon_name, color='warning').classes('text-xl')
    ui.label(f'{verb} {action.target}').classes('text-lg font-semibold')
```

### Reason Line

```python
# Explanation of why automation isn't possible
ui.label(f'Why: {action.reason}').classes('text-sm text-gray-600 italic pl-8')
```

---

## Prepared Materials Sections

### Phone Script (Collapsible)

```python
# Phone script with copy button
with ui.expansion('Phone Script', icon='description').props('expand-icon-toggle').classes('w-full'):
    with ui.card().classes('bg-gray-50'):
        script_text = '''
"I need to schedule a rough electrical inspection for 
permit number 2026-001234 at 123 Main St, Los Angeles. 
My name is John Smith and my phone number is 555-0123."
'''
        ui.label(script_text).classes('font-mono text-sm whitespace-pre-wrap')
        
        async def copy_script():
            await ui.run_javascript(f'navigator.clipboard.writeText({repr(script_text)})')
            ui.notify('Copied to clipboard!', type='positive', icon='check')
        
        ui.button('Copy', icon='content_copy', on_click=copy_script).props('flat size=sm').classes('mt-2')
```

### Email Draft (Collapsible)

```python
# Email draft with copy and mailto options
with ui.expansion('Email Draft', icon='email').props('expand-icon-toggle').classes('w-full'):
    with ui.card().classes('bg-gray-50'):
        # Email header
        ui.label('To: SolarCoordinator@ladwp.com').classes('text-sm font-medium')
        ui.label('Subject: Interconnection Agreement - 123 Main St').classes('text-sm text-gray-600')
        ui.separator().classes('my-2')
        
        # Email body
        email_body = '''Dear LADWP Solar Coordination Team,

I am requesting an interconnection agreement for my solar
PV system installation at:

Address: 123 Main St, Los Angeles, CA 90012
System Size: 8.5 kW
LADBS Permit #: 2026-001234

Please find attached:
- Single-line electrical diagram
- Equipment specifications
- Site plan

Thank you,
John Smith
555-0123'''
        
        ui.label(email_body).classes('text-sm whitespace-pre-wrap')
        
        with ui.row().classes('gap-2 mt-3'):
            ui.button('Copy All', icon='content_copy', on_click=copy_all).props('flat size=sm')
            ui.button('Open Email Client', icon='open_in_new', on_click=open_mailto).props('flat size=sm')
```

### Checklist (Collapsible)

```python
# Checklist with interactive checkboxes
with ui.expansion('Have These Ready', icon='checklist').props('expand-icon-toggle').classes('w-full'):
    checklist_items = [
        'Have permit number ready: 2026-001234',
        'Confirm work is ready for inspection (wiring accessible)',
        'Know your preferred time slot (morning/afternoon)',
        'Have contractor contact info if needed',
    ]
    
    for item in checklist_items:
        ui.checkbox(item).classes('text-sm')
```

### Documents Needed (Collapsible)

```python
# Document checklist with helpful tip
with ui.expansion('Documents Needed', icon='attach_file').props('expand-icon-toggle').classes('w-full'):
    documents = [
        'Single-line electrical diagram (PDF)',
        'Equipment specifications (solar panels, inverter, battery)',
        'Site plan showing panel layout',
        'Structural calculations (if roof-mounted)',
    ]
    
    for doc in documents:
        ui.checkbox(doc).classes('text-sm')
    
    ui.separator().classes('my-2')
    with ui.row().classes('items-center gap-2 text-sm text-gray-500'):
        ui.icon('lightbulb', size='xs')
        ui.label('Tip: These should have been prepared for your permit application. Check with your contractor if missing.')
```

### Contact Information

```python
# Contact info row
with ui.row().classes('gap-4 text-sm text-gray-600 flex-wrap'):
    if contact_info.get('phone'):
        with ui.row().classes('items-center gap-1'):
            ui.icon('phone', size='xs')
            ui.label(contact_info['phone'])
    
    if contact_info.get('hours'):
        with ui.row().classes('items-center gap-1'):
            ui.icon('schedule', size='xs')
            ui.label(contact_info['hours'])
    
    if contact_info.get('url'):
        with ui.row().classes('items-center gap-1'):
            ui.icon('link', size='xs')
            ui.link(contact_info['url'], contact_info['url'], new_tab=True).classes('text-blue-600')
```

---

## Completion Flow

### Step 1: User Clicks "I've Completed This"

```python
# Completion button triggers dialog
ui.button("I've Completed This", icon='check_circle', on_click=show_completion_form).props('color=warning').classes('w-full')
```

### Step 2: Confirmation Form Dialog

Based on `on_complete.expected_info`:

```
┌─────────────────────────────────────────────┐
│  ✓ Great! Just a few details...        [×]  │
├─────────────────────────────────────────────┤
│                                             │
│  What date was it scheduled for?            │
│  ┌─────────────────────────────────────┐  │
│  │ Feb 15, 2026                   [📅] │  │
│  └─────────────────────────────────────┘  │
│                                             │
│  What time window was assigned?             │
│  ┌─────────────────────────────────────┐  │
│  │ 8am-12pm                           ▼ │  │
│  └─────────────────────────────────────┘  │
│                                             │
│  What confirmation number did you receive?  │
│  ┌─────────────────────────────────────┐  │
│  │ INS-789456                            │  │
│  └─────────────────────────────────────┘  │
│                                             │
├─────────────────────────────────────────────┤
│                   [Cancel]  [Submit Details] │
└─────────────────────────────────────────────┘
```

```python
async def show_completion_form(action: UserActionResponse):
    """Show completion form in dialog."""
    form_data = {}
    
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        with ui.row().classes('items-center gap-2 w-full'):
            ui.icon('check_circle', color='positive')
            ui.label('Great! Just a few details...').classes('font-semibold flex-grow')
            ui.button(icon='close', on_click=dialog.close).props('flat round size=sm')
        
        ui.separator()
        
        # Dynamic form fields based on expected_info
        for field in action.on_complete.expected_info:
            ui.label(get_field_prompt(field)).classes('text-sm font-medium mt-4')
            
            if field == 'scheduled_date':
                form_data[field] = ui.date(placeholder='Select date...').classes('w-full')
            elif field == 'time_window':
                form_data[field] = ui.select(
                    options=['8am-12pm', '12pm-4pm', 'All day'],
                    label='Time window (optional)'
                ).classes('w-full')
            elif field == 'amount':
                form_data[field] = ui.number(format='%.2f', prefix='$').classes('w-full')
            else:
                form_data[field] = ui.input(placeholder=get_field_placeholder(field)).classes('w-full')
        
        ui.separator().classes('mt-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            ui.button('Submit Details', on_click=lambda: submit_completion(form_data, dialog)).props('color=primary')
    
    dialog.open()

# Field configuration
FIELD_CONFIG = {
    'scheduled_date': ('What date was the inspection scheduled for?', 'Feb 15, 2026'),
    'confirmation_number': ('What confirmation number did you receive?', 'e.g., INS-789456'),
    'time_window': ('What time window was assigned?', 'e.g., 8am-12pm'),
    'amount': ('What was the total amount?', '1250.00'),
    'reference_number': ('What reference number did you receive?', 'e.g., 2026-005678'),
}

def get_field_prompt(field: str) -> str:
    return FIELD_CONFIG.get(field, (field.replace('_', ' ').title(), ''))[0]

def get_field_placeholder(field: str) -> str:
    return FIELD_CONFIG.get(field, ('', field))[1]
```

### Step 3: Confirmation Message

After submission, send chat message:

```python
async def submit_completion(form_data: dict, dialog: ui.dialog):
    """Submit completion and update chat."""
    values = {k: v.value for k, v in form_data.items()}
    
    dialog.close()
    ui.notify('Task marked as complete!', type='positive')
    
    # Add confirmation message to chat
    with chat_container:
        ui.chat_message(
            f'''Perfect! ✅ I've updated your plan.

Inspection scheduled: {values.get('scheduled_date', 'N/A')} ({values.get('confirmation_number', 'N/A')})
Time window: {values.get('time_window', 'N/A')}

I'll follow up after the scheduled date to see how it went.
In the meantime, let's look at your next steps...''',
            name='Agent',
            avatar='🤖',
            sent=False
        )
```

---

## Action Card by Type

### Phone Call Card

```python
# Phone call action card
def render_phone_action(action: UserActionResponse):
    with ui.card().classes('border-2 border-orange-400 bg-orange-50 w-full'):
        # Header
        with ui.row().classes('items-center gap-2'):
            ui.icon('bolt', color='warning')
            ui.label('USER ACTION NEEDED').classes('font-bold text-orange-700')
        
        ui.separator()
        
        # Action
        with ui.row().classes('items-center gap-2'):
            ui.icon('phone', color='warning').classes('text-xl')
            ui.label(f'Call {action.target}').classes('text-lg font-semibold')
        
        ui.label(f'Why: {action.reason}').classes('text-sm text-gray-600 italic')
        
        # Phone script
        with ui.expansion('Phone Script', icon='description').classes('w-full'):
            with ui.card().classes('bg-gray-50'):
                ui.label(action.prepared_materials.phone_script).classes('font-mono text-sm whitespace-pre-wrap')
                ui.button('Copy', icon='content_copy', on_click=copy_script).props('flat size=sm')
        
        # Contact info
        with ui.row().classes('gap-3 text-sm text-gray-600'):
            with ui.row().classes('items-center gap-1'):
                ui.icon('phone', size='xs')
                ui.label(action.target)
            with ui.row().classes('items-center gap-1'):
                ui.icon('schedule', size='xs')
                ui.label(action.prepared_materials.contact_info.get('hours', '24/7'))
        
        ui.separator()
        ui.button("I've Completed This", icon='check_circle', on_click=on_complete).props('color=warning').classes('w-full')
```

### Email Card

```python
# Email action card
def render_email_action(action: UserActionResponse):
    with ui.card().classes('border-2 border-orange-400 bg-orange-50 w-full'):
        # Header
        with ui.row().classes('items-center gap-2'):
            ui.icon('bolt', color='warning')
            ui.label('USER ACTION NEEDED').classes('font-bold text-orange-700')
        
        ui.separator()
        
        with ui.row().classes('items-center gap-2'):
            ui.icon('email', color='warning').classes('text-xl')
            ui.label(f'Email {action.target}').classes('text-lg font-semibold')
        
        ui.label(f'Why: {action.reason}').classes('text-sm text-gray-600 italic')
        
        # Email draft
        with ui.expansion('Email Draft', icon='email').classes('w-full'):
            with ui.card().classes('bg-gray-50'):
                ui.label(f"To: {action.prepared_materials.email_to}").classes('text-sm font-medium')
                ui.label(f"Subject: {action.prepared_materials.email_subject}").classes('text-sm')
                ui.separator()
                ui.label(action.prepared_materials.email_draft).classes('text-sm whitespace-pre-wrap')
                with ui.row().classes('gap-2 mt-2'):
                    ui.button('Copy All', icon='content_copy').props('flat size=sm')
                    ui.button('Open Email Client', icon='open_in_new').props('flat size=sm')
        
        # Documents needed
        if action.prepared_materials.documents_needed:
            with ui.expansion('Documents Needed', icon='attach_file').classes('w-full'):
                for doc in action.prepared_materials.documents_needed:
                    ui.checkbox(doc).classes('text-sm')
        
        ui.separator()
        ui.button("I've Completed This", icon='check_circle', on_click=on_complete).props('color=warning').classes('w-full')
```

### In-Person Visit Card

```python
# In-person visit action card
def render_in_person_action(action: UserActionResponse):
    with ui.card().classes('border-2 border-orange-400 bg-orange-50 w-full'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('bolt', color='warning')
            ui.label('USER ACTION NEEDED').classes('font-bold text-orange-700')
        
        ui.separator()
        
        with ui.row().classes('items-center gap-2'):
            ui.icon('business', color='warning').classes('text-xl')
            ui.label(f'Visit {action.target}').classes('text-lg font-semibold')
        
        ui.label(f'Why: {action.reason}').classes('text-sm text-gray-600 italic')
        
        # Location with map link
        contact = action.prepared_materials.contact_info
        with ui.card().classes('bg-white mt-4'):
            ui.label('📍 Location:').classes('font-medium')
            ui.label(contact.get('name', '')).classes('font-semibold')
            ui.label(contact.get('address', '')).classes('text-sm')
            ui.button('Open in Maps', icon='map', on_click=lambda: open_maps(contact['address'])).props('flat size=sm').classes('mt-2')
        
        with ui.row().classes('items-center gap-1 text-sm text-gray-600'):
            ui.icon('schedule', size='xs')
            ui.label(contact.get('hours', 'Mon-Fri 8am-5pm'))
        
        # Checklist
        if action.prepared_materials.checklist:
            with ui.expansion('Bring With You', icon='checklist').classes('w-full'):
                for item in action.prepared_materials.checklist:
                    ui.checkbox(item).classes('text-sm')
        
        ui.separator()
        ui.button("I've Completed This", icon='check_circle', on_click=on_complete).props('color=warning').classes('w-full')
```

### Online Portal Card

```python
# Online portal action card  
def render_portal_action(action: UserActionResponse):
    with ui.card().classes('border-2 border-orange-400 bg-orange-50 w-full'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('bolt', color='warning')
            ui.label('USER ACTION NEEDED').classes('font-bold text-orange-700')
        
        ui.separator()
        
        with ui.row().classes('items-center gap-2'):
            ui.icon('language', color='warning').classes('text-xl')
            ui.label('Complete on website').classes('text-lg font-semibold')
        
        ui.label(f'Why: {action.reason}').classes('text-sm text-gray-600 italic')
        
        # Portal link button
        with ui.card().classes('bg-white mt-4 text-center'):
            ui.label(f'Go to: {action.target}').classes('text-sm')
            ui.button('Open Portal', icon='open_in_new', on_click=lambda: ui.navigate.to(action.target, new_tab=True)).props('color=primary').classes('mt-2')
        
        # Steps to complete
        if action.prepared_materials.checklist:
            with ui.expansion('Steps to Complete', icon='format_list_numbered').classes('w-full'):
                for i, step in enumerate(action.prepared_materials.checklist, 1):
                    ui.label(f'{i}. {step}').classes('text-sm')
        
        ui.separator()
        ui.button("I've Completed This", icon='check_circle', on_click=on_complete).props('color=warning').classes('w-full')
```

---

## Pending Actions Indicator

### In Plan Widget

```python
# Pending actions summary in plan widget footer
if pending_actions:
    with ui.card().classes('bg-orange-50 border-orange-300 mx-4 mb-4'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('bolt', color='warning')
            ui.label(f'{len(pending_actions)} action{"s" if len(pending_actions) > 1 else ""} need{"" if len(pending_actions) > 1 else "s"} your attention').classes('text-sm font-medium flex-grow')
        
        for action in pending_actions[:3]:  # Show first 3
            with ui.row().classes('items-center gap-2 pl-6'):
                ui.icon(ACTION_ICONS[action.action_type][0], size='xs')
                ui.label(action.title).classes('text-sm')
                ui.button('View', on_click=lambda a=action: show_action(a)).props('flat dense size=sm')
```

### In Chat (Return Visit)

```python
# Welcome back message with pending tasks
if pending_actions:
    ui.chat_message(
        f'''Welcome back, {user.name}! I see you have {len(pending_actions)} pending task{"s" if len(pending_actions) > 1 else ""}:

''' + '\n'.join([f'{i+1}. {ACTION_ICONS[a.action_type][0]} {a.title}' for i, a in enumerate(pending_actions)]) + '''

Have you had a chance to complete any of these?''',
        name='Agent',
        avatar='🤖',
        sent=False
    )
    
    # Quick action buttons
    with ui.row().classes('gap-2 ml-12'):
        ui.button('Yes, I completed one', on_click=show_completion_selector).props('flat')
        ui.button('Not yet', on_click=acknowledge).props('flat')
        ui.button('Show me the details', on_click=expand_pending).props('flat')
```

---

## Card States

### Collapsed Card (In Chat History)

```
┌───────────────────────────────────────────────────────────┐
┃ ✓ COMPLETED: 📞 Call 311  Feb 15  (INS-789456)  [Expand] │
└───────────────────────────────────────────────────────────┘
```

```python
# Collapsed completed action card
def render_collapsed_action(action: UserActionResponse, result: dict):
    with ui.card().classes('border-l-4 border-green-500 bg-green-50'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('check_circle', color='positive')
            ui.label(f'COMPLETED: {ACTION_ICONS[action.action_type][1]} {action.target}').classes('text-sm font-medium')
            ui.label(f'{result.get("scheduled_date", "")} ({result.get("confirmation_number", "")})').classes('text-xs text-gray-500 flex-grow')
            ui.button('Expand', on_click=expand_action).props('flat dense size=sm')
```

### Expired/Overdue Card

```
┌───────────────────────────────────────────────────────────┐
│  ⚠️ ACTION PENDING (5 days)                              │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  📞 Call 311 to schedule inspection                       │
│                                                           │
│  🕒 This task was assigned 5 days ago.                    │
│     Would you like help completing it?                    │
│                                                           │
│  [View Details]  [Reschedule]  [Mark Complete]            │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

```python
# Overdue action card with warning styling
def render_overdue_action(action: UserActionResponse, days_pending: int):
    with ui.card().classes('border-2 border-amber-500 bg-amber-50 w-full'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('warning', color='warning')
            ui.label(f'ACTION PENDING ({days_pending} days)').classes('font-bold text-amber-700')
        
        ui.separator()
        
        with ui.row().classes('items-center gap-2'):
            ui.icon(ACTION_ICONS[action.action_type][0])
            ui.label(f'{ACTION_ICONS[action.action_type][1]} {action.target}').classes('font-medium')
        
        with ui.row().classes('items-center gap-1 text-sm text-amber-700'):
            ui.icon('schedule', size='xs')
            ui.label(f'This task was assigned {days_pending} days ago. Would you like help completing it?')
        
        with ui.row().classes('gap-2 mt-4'):
            ui.button('View Details', on_click=show_details).props('flat')
            ui.button('Reschedule', on_click=reschedule).props('flat')
            ui.button('Mark Complete', on_click=on_complete).props('color=warning')
```

---

## Mobile Action Card

### Visual Reference

```
┌─────────────────────────────────────────┐
┃ ⚡ ACTION NEEDED                           │
├─────────────────────────────────────────┤
│  📞 311                                    │
│  Schedule inspection                       │
│                                             │
│  Why: Only available via phone              │
│                                             │
│  ▶ Script                             [▼]  │
│  ▶ Checklist                          [▼]  │
│                                             │
│  📞 311 • 24/7                              │
│                                             │
├─────────────────────────────────────────┤
│        [ ✅ I've Completed This ]           │
└─────────────────────────────────────────┘
```

### NiceGUI Implementation

```python
# Mobile-optimized action card (full-width)
def render_mobile_action(action: UserActionResponse, on_complete: Callable):
    with ui.card().classes('border-t-4 border-orange-400 bg-orange-50 w-full rounded-none'):
        # Compact header
        with ui.row().classes('items-center gap-2'):
            ui.icon('bolt', color='warning')
            ui.label('ACTION NEEDED').classes('font-bold text-orange-700 text-sm')
        
        ui.separator()
        
        # Action (stacked layout)
        with ui.column().classes('gap-1'):
            with ui.row().classes('items-center gap-2'):
                ui.icon(ACTION_ICONS[action.action_type][0], color='warning')
                ui.label(action.target).classes('font-semibold')
            ui.label(action.title).classes('text-sm text-gray-600')
        
        ui.label(f'Why: {action.reason}').classes('text-xs text-gray-500')
        
        # Collapsed sections
        if action.prepared_materials.phone_script:
            with ui.expansion('Script', icon='description').props('dense').classes('w-full'):
                ui.label(action.prepared_materials.phone_script).classes('text-xs font-mono')
        
        if action.prepared_materials.checklist:
            with ui.expansion('Checklist', icon='checklist').props('dense').classes('w-full'):
                for item in action.prepared_materials.checklist:
                    ui.checkbox(item).props('dense').classes('text-xs')
        
        # Contact inline
        with ui.row().classes('gap-2 text-xs text-gray-600'):
            if action.prepared_materials.contact_info.get('phone'):
                ui.label(f"📞 {action.prepared_materials.contact_info['phone']}")
            if action.prepared_materials.contact_info.get('hours'):
                ui.label(f"• {action.prepared_materials.contact_info['hours']}")
        
        ui.separator()
        ui.button("I've Completed This", icon='check_circle', on_click=on_complete).props('color=warning').classes('w-full')
```

---

## Accessibility

| Requirement | NiceGUI Implementation |
|-------------|----------------------|
| Screen Reader | Clear action descriptions via `aria-label` props |
| Keyboard | Tab through sections, `ui.expansion` handles Enter/Space |
| Copy Buttons | `ui.notify()` for confirmation, screen reader accessible |
| Forms | `ui.input(label=...)` with proper labels |
| Focus | Quasar dialog manages focus trap automatically |

```python
# Accessible copy button with notification
async def copy_to_clipboard(text: str):
    await ui.run_javascript(f'navigator.clipboard.writeText({repr(text)})')
    ui.notify('Copied to clipboard!', type='positive', icon='check')

# Accessible form field
ui.input(
    label='Confirmation Number',
    placeholder='e.g., INS-789456',
    validation={'required': lambda v: len(v) > 0 or 'Required'}
).props('aria-required=true')
```

---

## Related Documentation

- [Chat Interface](ui-wireframes-chat.md) - Where cards appear
- [Plan Widget](ui-wireframes-plan-widget.md) - Step status updates
- [Components](ui-wireframes-components.md) - Reusable elements
