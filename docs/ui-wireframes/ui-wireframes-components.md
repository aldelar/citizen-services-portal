# UI Wireframes: Components Library

This document defines reusable UI components used across the Citizen Services Portal, mapped to NiceGUI native elements.

---

## NiceGUI Component Mapping

| Wireframe Concept | NiceGUI Element |
|-------------------|-----------------|
| Status Badge | `ui.chip()` or `ui.badge()` |
| Progress Bar | `ui.linear_progress()` |
| Buttons | `ui.button()` with `.props()` |
| Text Input | `ui.input()` |
| Text Area | `ui.textarea()` |
| Dropdown | `ui.select()` |
| Checkbox | `ui.checkbox()` |
| Date Picker | `ui.date_input()` |
| Cards | `ui.card()` |
| Expandable | `ui.expansion()` |
| Modals | `ui.dialog()` |
| Toasts | `ui.notify()` |
| Spinner | `ui.spinner()` |
| Skeleton | `ui.skeleton()` |
| Tooltips | `.tooltip()` method |
| Avatar | `ui.avatar()` |
| Separator | `ui.separator()` |

---

## Overview

The component library ensures consistency across the portal. All components are designed to be:

- **Generic**: Work with any content, agency, or project type
- **Accessible**: Meet WCAG 2.1 AA standards
- **Responsive**: Adapt to different screen sizes (Tailwind breakpoints)
- **Themeable**: Support light and dark modes (Quasar themes)

---

## Source Badges

Use `ui.chip` for source badges that indicate which MCP server provided information:

```python
# Source badge with NiceGUI
ui.chip('via ladbs', icon='info').props('outline size=sm color=grey')

# In a row with content
with ui.row().classes('items-center gap-2'):
    ui.label('Electrical Permit - Submit application')
    ui.chip('via ladbs').props('outline size=sm color=grey')
```

### Usage

| Property | NiceGUI Implementation |
|----------|------------------------|
| Small size | `.props('size=sm')` |
| Muted style | `.props('outline color=grey')` |
| With icon | `icon='info'` parameter |

---

## Status Indicators

Use `ui.chip` for status pills with color variants:

```python
# Status pills using ui.chip
def status_chip(status: str):
    configs = {
        'not_started': ('Not Started', 'grey', 'radio_button_unchecked'),
        'blocked': ('Blocked', 'grey', 'lock'),
        'ready': ('Ready', 'primary', 'play_arrow'),
        'in_progress': ('In Progress', 'primary', 'pending'),
        'action_needed': ('Action Needed', 'warning', 'bolt'),
        'completed': ('Completed', 'positive', 'check_circle'),
        'failed': ('Failed', 'negative', 'error'),
        'skipped': ('Skipped', 'grey', 'block'),
    }
    label, color, icon = configs.get(status, ('Unknown', 'grey', 'help'))
    return ui.chip(label, icon=icon, color=color)

# Usage
status_chip('in_progress')
status_chip('action_needed')
status_chip('completed')
```

### Status Mapping

| Status | Color | Icon |
|--------|-------|------|
| Not Started | `grey` | `radio_button_unchecked` |
| Blocked | `grey` | `lock` |
| Ready | `primary` | `play_arrow` |
| In Progress | `primary` | `pending` |
| Action Needed | `warning` | `bolt` |
| Completed | `positive` | `check_circle` |
| Failed | `negative` | `error` |
| Skipped | `grey` | `block` |

---

## Progress Indicators

Use `ui.linear_progress` for progress bars:

```python
# Standard progress bar
ui.linear_progress(value=0.6, show_value=True).classes('w-full')

# Progress with label
with ui.column().classes('w-full gap-1'):
    with ui.row().classes('w-full justify-between text-sm'):
        ui.label('Progress')
        ui.label('60%')
    ui.linear_progress(value=0.6).classes('w-full')

# Progress with steps
with ui.column().classes('w-full gap-1'):
    with ui.row().classes('w-full justify-between text-sm'):
        ui.label('4 of 10 steps')
        ui.label('40%')
    ui.linear_progress(value=0.4).classes('w-full')

# Circular progress
ui.circular_progress(value=0.75, show_value=True, size='lg')
```

### Progress Types

| Type | NiceGUI Element |
|------|-----------------|
| Linear bar | `ui.linear_progress(value=0.6)` |
| With label | Add `show_value=True` |
| Circular | `ui.circular_progress(value=0.75)` |
| Indeterminate | `ui.linear_progress()` (no value) |

---

## Buttons

Use `ui.button` with Quasar props for different styles:

```python
# Primary button
ui.button('Complete Action', icon='check', on_click=action).props('color=primary')

# Secondary/outline button
ui.button('View Details', on_click=view).props('outline color=primary')

# Ghost/flat button
ui.button('View Details →', on_click=view).props('flat color=primary')

# Danger button
ui.button('Cancel Project', icon='delete', on_click=cancel).props('color=negative')

# Disabled button
ui.button('Not Available').props('disable')

# Loading button
loading_btn = ui.button('Submit', on_click=submit)
# During operation:
loading_btn.props('loading')
```

### Button Variants

| Style | Props |
|-------|-------|
| Primary | `.props('color=primary')` |
| Secondary | `.props('outline color=primary')` |
| Ghost | `.props('flat color=primary')` |
| Danger | `.props('color=negative')` |
| Disabled | `.props('disable')` |
| Loading | `.props('loading')` |
| Icon only | `ui.button(icon='add')` |
| Round | `.props('round')` |

### Button Sizes

| Size | Props |
|------|-------|
| Small | `.props('size=sm')` |
| Medium | (default) |
| Large | `.props('size=lg')` |

---

## Form Inputs

Use NiceGUI form components with Quasar styling:

```python
# Text input with label and validation
email = ui.input(
    label='Email Address',
    placeholder='you@example.com',
    validation={'Email required': lambda v: '@' in v if v else False}
)

# Textarea with auto-grow
description = ui.textarea(
    label='Description',
    placeholder='Enter details...'
).props('autogrow rows=3')

# Date picker
date = ui.date_input(label='Select Date')

# Dropdown/select
option = ui.select(
    label='Select an option',
    options=['Option 1', 'Option 2', 'Option 3'],
    value='Option 1'
)

# Checkbox
agree = ui.checkbox('I agree to the terms')

# Radio buttons
choice = ui.radio(['Option A', 'Option B', 'Option C'], value='Option A')

# Toggle switch
enabled = ui.toggle('Enable notifications')
```

### Input States

| State | NiceGUI Implementation |
|-------|------------------------|
| Default | Standard element |
| Focus | Automatic Quasar styling |
| Error | `validation` parameter or `.props('error error-message=\"...\"')` |
| Disabled | `.props('disable')` |
| Read-only | `.props('readonly')` |

---

## Cards

Use `ui.card` with nested content:

```python
# Basic card
with ui.card().classes('p-4'):
    ui.label('Card Title').classes('text-lg font-semibold')
    ui.label('Card content goes here. Can include text, images, or other components.')
    ui.button('Action', on_click=handle_action).classes('mt-4')

# Card with header and sections
with ui.card():
    with ui.card_section().classes('bg-gray-100'):
        ui.label('Card Header').classes('font-bold')
    with ui.card_section():
        ui.label('Main content area')
    with ui.card_actions().classes('justify-end'):
        ui.button('Cancel').props('flat')
        ui.button('Confirm').props('color=primary')

# Clickable card with hover effect
with ui.card().classes('cursor-pointer hover:shadow-lg transition-shadow') as card:
    card.on('click', handle_card_click)
    ui.label('Click me!')

# Selected state
with ui.card().classes('border-2 border-primary'):
    ui.label('Selected card')
```

### Card Styling

| State | Tailwind Classes |
|-------|------------------|
| Default | `ui.card()` (built-in shadow) |
| Hover | `.classes('hover:shadow-lg')` |
| Selected | `.classes('border-2 border-primary')` |
| Flat | `.props('flat bordered')` |

---

## Expandable Sections

Use `ui.expansion` for collapsible content:

```python
# Basic expansion
with ui.expansion('Section Title', icon='info'):
    ui.label('Section content is now visible.')
    ui.label('Can contain any components.')

# Expansion with custom header
with ui.expansion('Advanced Options', icon='settings').classes('w-full'):
    ui.checkbox('Enable feature A')
    ui.checkbox('Enable feature B')
    ui.input(label='Custom value')

# Multiple expansions (accordion-style)
with ui.column().classes('w-full gap-2'):
    with ui.expansion('General', icon='settings', value=True):  # Open by default
        ui.label('General settings content')
    
    with ui.expansion('Privacy', icon='lock'):
        ui.label('Privacy settings content')
    
    with ui.expansion('Notifications', icon='notifications'):
        ui.label('Notification settings content')
```

### Expansion Properties

| Property | Usage |
|----------|-------|
| `value=True` | Open by default |
| `icon='...'` | Header icon |
| `caption='...'` | Subtitle text |
| `.props('dense')` | Compact style |

---

## Tooltips

Use `.tooltip()` method on any element:

```python
# Simple tooltip
ui.button('Hover me').tooltip('This is helpful information')

# Tooltip on icon
ui.icon('help').tooltip('Click for more details')

# Rich tooltip with card (using menu on hover)
with ui.label('Step Details').classes('cursor-pointer'):
    with ui.menu().props('anchor="top middle" self="bottom middle"'):
        with ui.card().classes('p-3'):
            ui.label('Electrical Permit').classes('font-semibold')
            ui.label('Status: In Review').classes('text-sm text-gray-600')
            ui.button('View in Chat', on_click=view_chat).props('flat size=sm')
```

---

## Modals

Use `ui.dialog` for modals:

```python
# Standard modal
with ui.dialog() as dialog, ui.card().classes('w-96'):
    with ui.row().classes('w-full items-center'):
        ui.label('Modal Title').classes('text-lg font-semibold flex-grow')
        ui.button(icon='close', on_click=dialog.close).props('flat round')
    
    ui.separator()
    
    ui.label('Modal content goes here.')
    ui.label('Can include forms, information, or confirmations.')
    
    ui.separator()
    
    with ui.row().classes('w-full justify-end gap-2'):
        ui.button('Cancel', on_click=dialog.close).props('flat')
        ui.button('Confirm', on_click=handle_confirm).props('color=primary')

# Confirmation modal
def confirm_cancel():
    with ui.dialog() as dialog, ui.card():
        with ui.row().classes('items-center gap-2'):
            ui.icon('warning', color='warning').classes('text-2xl')
            ui.label('Cancel Project?').classes('text-lg font-semibold')
        
        ui.label('Are you sure you want to cancel "Home Renovation - 123 Main St"?')
        ui.label('This cannot be undone.').classes('text-sm text-gray-600')
        
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Keep Project', on_click=dialog.close).props('flat')
            ui.button('Yes, Cancel', on_click=cancel_project).props('color=negative')
    
    dialog.open()
```

### Dialog Props

| Property | Usage |
|----------|-------|
| `.props('persistent')` | Prevent close on backdrop click |
| `.props('full-width')` | Full width dialog |
| `.props('full-height')` | Full height dialog |
| `dialog.open()` | Open programmatically |
| `dialog.close()` | Close programmatically |

---

## Toast Notifications

Use `ui.notify` for toast messages:

```python
# Success toast
ui.notify('Permit submitted successfully', type='positive', close_button=True)

# Error toast with action
ui.notify(
    'Failed to connect to LADWP service',
    type='negative',
    close_button=True,
    actions=[{'label': 'Retry', 'handler': retry_connection}]
)

# Info toast
ui.notify('Your plan has been updated', type='info')

# Warning toast
ui.notify('Some steps may take longer than expected', type='warning')
```

### Notification Types

| Type | Parameter |
|------|-----------|
| Success | `type='positive'` |
| Error | `type='negative'` |
| Info | `type='info'` |
| Warning | `type='warning'` |

### Notification Options

| Option | Usage |
|--------|-------|
| `position` | `'top'`, `'bottom'`, `'top-right'`, etc. |
| `timeout` | Duration in ms (0 = no auto-close) |
| `close_button` | Show close button |
| `actions` | List of action buttons |
| `spinner` | Show spinner |

---

## Loading States

Use `ui.spinner` and `ui.skeleton`:

```python
# Spinner variants
ui.spinner('default', size='lg')
ui.spinner('dots')
ui.spinner('audio')
ui.spinner('ball')
ui.spinner('bars')
ui.spinner('box')

# Loading overlay
with ui.card().classes('relative'):
    ui.label('Content here')
    # Overlay when loading
    with ui.element().classes('absolute inset-0 bg-white/80 flex items-center justify-center'):
        ui.spinner(size='lg')

# Skeleton loading placeholders
with ui.column().classes('w-full gap-2'):
    ui.skeleton('text').classes('w-3/4')
    ui.skeleton('text').classes('w-full')
    ui.skeleton('text').classes('w-1/2')
    ui.skeleton('rect').classes('h-32 w-full')

# Loading button
submit_btn = ui.button('Submit', on_click=handle_submit)
# During submission:
submit_btn.props('loading')
```

### Spinner Sizes

| Size | Parameter |
|------|-----------|
| Extra small | `size='xs'` |
| Small | `size='sm'` |
| Medium | `size='md'` (default) |
| Large | `size='lg'` |
| Extra large | `size='xl'` |

---

## Graph Components

For plan/workflow visualization, use `ui.mermaid` or `ui.timeline`:

```python
# Mermaid diagram for workflow graphs
ui.mermaid('''
graph TD
    A[Submit Application] --> B{Review}
    B -->|Approved| C[Issue Permit]
    B -->|Rejected| D[Revise & Resubmit]
    D --> A
    
    style A fill:#e7f1ff
    style C fill:#d4edda
''')

# Timeline for linear progress
with ui.timeline(side='right'):
    ui.timeline_entry(
        'Application Submitted',
        subtitle='Jan 15, 2026',
        icon='check_circle',
        color='positive'
    )
    ui.timeline_entry(
        'Under Review',
        subtitle='In Progress',
        icon='pending',
        color='primary'
    )
    ui.timeline_entry(
        'Permit Issued',
        subtitle='Pending',
        icon='radio_button_unchecked',
        color='grey'
    )
```

### Mermaid Styling

Use Mermaid's built-in styling for node states:

```python
# Dynamic graph with status colors
def render_plan_graph(steps: list):
    mermaid_code = 'graph TD\n'
    for step in steps:
        style = {
            'completed': 'fill:#d4edda,stroke:#28a745',
            'in_progress': 'fill:#cce0ff,stroke:#0066cc',
            'action_needed': 'fill:#fff3e0,stroke:#bf360c',
            'pending': 'fill:#f5f5f5,stroke:#6c757d'
        }.get(step.status, '')
        
        mermaid_code += f'    {step.id}[{step.title}]\n'
        if style:
            mermaid_code += f'    style {step.id} {style}\n'
    
    ui.mermaid(mermaid_code)
```

---

## Avatars

Use `ui.avatar`:

```python
# Avatar with initials
ui.avatar('JS', color='primary')

# Avatar with icon
ui.avatar(icon='person')

# Avatar with image
ui.avatar().props(f'img="{user.photo_url}"')

# Sizes
ui.avatar('JS', size='sm')  # 24px
ui.avatar('JS', size='md')  # 40px (default)
ui.avatar('JS', size='lg')  # 64px
ui.avatar('JS', size='xl')  # 96px

# Agent avatar
ui.avatar(icon='smart_toy', color='secondary')
```

### Avatar Sizes

| Size | Dimension | Use Case |
|------|-----------|----------|
| sm | 24px | Inline mentions |
| md | 40px | Chat messages (default) |
| lg | 64px | Profile headers |
| xl | 96px | Account pages |

---

## Dividers

Use `ui.separator`:

```python
# Simple horizontal separator
ui.separator()

# Separator with label
with ui.row().classes('w-full items-center gap-4'):
    ui.separator().classes('flex-grow')
    ui.label('Today').classes('text-gray-500 text-sm')
    ui.separator().classes('flex-grow')

# Vertical separator
with ui.row():
    ui.label('Left')
    ui.separator().props('vertical')
    ui.label('Right')
```

---

## Empty States

Use `ui.card` with centered content:

```python
# Generic empty state
with ui.card().classes('w-full p-8 text-center'):
    ui.icon('inbox', size='xl').classes('text-gray-400')
    ui.label('No items found').classes('text-lg font-semibold mt-4')
    ui.label('Description text explaining the empty state and what to do next.').classes('text-gray-600 mt-2')
    ui.button('Create New', icon='add', on_click=create_new).classes('mt-4')

# Empty project list
with ui.card().classes('w-full p-8 text-center'):
    ui.icon('folder_open', size='xl').classes('text-gray-400')
    ui.label('No projects yet').classes('text-lg font-semibold mt-4')
    ui.label('Start by describing your home improvement goal.').classes('text-gray-600 mt-2')
    ui.button('Start a Project', icon='add', on_click=new_project).props('color=primary').classes('mt-4')
```

- Icon: Relevant to context (📋 for lists, 💬 for chat, etc.)
- Title: Brief, clear statement
- Description: Explanation and guidance
- Action: Optional button for next step

---

## Responsive Breakpoints

NiceGUI uses Tailwind CSS breakpoints:

| Breakpoint | Tailwind Prefix | Min Width | Usage |
|------------|-----------------|-----------|-------|
| Default | (none) | 0px | Mobile first |
| sm | `sm:` | 640px | Large mobile |
| md | `md:` | 768px | Tablet |
| lg | `lg:` | 1024px | Desktop |
| xl | `xl:` | 1280px | Large desktop |
| 2xl | `2xl:` | 1536px | Extra large |

```python
# Responsive classes example
ui.card().classes('w-full md:w-1/2 lg:w-1/3')
ui.column().classes('hidden lg:flex')  # Hidden on mobile, visible on desktop
```

---

## Spacing Scale

Use Tailwind spacing utilities via `.classes()`:

| Tailwind | Size | Example |
|----------|------|---------|
| `p-1`, `m-1` | 4px | Tight spacing |
| `p-2`, `m-2` | 8px | Default small |
| `p-3`, `m-3` | 12px | Default medium |
| `p-4`, `m-4` | 16px | Default large |
| `p-6`, `m-6` | 24px | Section spacing |
| `p-8`, `m-8` | 32px | Large section |
| `gap-2`, `gap-4` | Variable | Flex/grid gaps |

```python
# Spacing examples
ui.card().classes('p-4 m-2')
ui.row().classes('gap-4')
ui.column().classes('space-y-2')
```

---

## Typography

Use Tailwind typography classes:

| Element | Tailwind Classes |
|---------|------------------|
| H1 | `.classes('text-2xl font-bold')` |
| H2 | `.classes('text-xl font-bold')` |
| H3 | `.classes('text-lg font-semibold')` |
| H4 | `.classes('text-base font-semibold')` |
| Body | `.classes('text-sm')` (default) |
| Small | `.classes('text-xs')` |
| Muted | `.classes('text-gray-500')` |

```python
ui.label('Main Title').classes('text-2xl font-bold')
ui.label('Subtitle').classes('text-lg text-gray-600')
ui.label('Body text').classes('text-sm')
```

---

## Color Palette

Quasar provides semantic colors via `.props()`:

### Button/Element Colors

| Quasar Color | Usage |
|--------------|-------|
| `primary` | Main actions, links |
| `secondary` | Secondary actions |
| `positive` | Success, completed |
| `negative` | Errors, danger |
| `warning` | Warnings, attention |
| `info` | Information |

### Tailwind Color Classes

| Class | Usage |
|-------|-------|
| `text-primary` | Primary text color |
| `bg-gray-50` | Light background |
| `border-gray-200` | Subtle borders |
| `text-gray-500` | Muted text |
| `text-green-600` | Success text |
| `text-red-600` | Error text |
| `text-orange-500` | Warning text |

```python
# Color examples
ui.button('Submit').props('color=primary')
ui.chip('Success', color='positive')
ui.label('Error message').classes('text-red-600')
ui.card().classes('bg-gray-50 border border-gray-200')
```

---

## Related Documentation

- [Overview](ui-wireframes-overview.md) - Layout structure
- [User Account](ui-wireframes-user-account.md) - Account creation and profile management
- [Projects](ui-wireframes-projects.md) - Project panel components
- [Chat](ui-wireframes-chat.md) - Chat interface components
- [Plan Widget](ui-wireframes-plan-widget.md) - Graph components
- [User Actions](ui-wireframes-user-actions.md) - Action card components
