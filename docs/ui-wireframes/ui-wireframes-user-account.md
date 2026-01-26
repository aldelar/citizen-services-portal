# UI Wireframes: User Account Management

This document defines the user account creation and management features for the Citizen Services Portal.

## NiceGUI Component Mapping

| UI Element | NiceGUI Component | Styling |
|------------|------------------|---------|
| Sign Up Card | `ui.card()` | `w-96 mx-auto` |
| Form Inputs | `ui.input()` | `label`, `placeholder`, `validation` |
| Password Field | `ui.input()` | `.props('type=password')` |
| Submit Button | `ui.button()` | `.props('color=primary')` |
| User Menu | `ui.button()` + `ui.menu()` | Avatar with dropdown |
| Profile Sections | `ui.card()` | Grouped content |
| Edit Mode | `ui.input()` with `bind_value` | Inline editing |

---

## Overview

Users need accounts to:
- Save and track their projects across sessions
- Store personal information (name, address) to pre-fill forms
- Receive notifications about project updates

> **Note:** The portal uses a unified citizen ID that works across all agencies, so users don't need to manage separate agency account numbers.

---

## Account Creation Flow

### Step 1: Sign Up Screen

```python
@ui.page('/signup')
def signup_page():
    # Form state
    form_data = {'name': '', 'email': '', 'password': ''}
    
    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gray-100'):
        # Header
        with ui.row().classes('items-center gap-2 mb-8'):
            ui.icon('account_balance', size='lg')
            ui.label('Citizen Services Portal').classes('text-2xl font-bold')
        
        # Sign up card
        with ui.card().classes('w-96'):
            ui.label('Create Your Account').classes('text-xl font-semibold mb-4')
            
            ui.input(
                label='Full Name',
                placeholder='John Smith',
                validation={'required': lambda v: bool(v) or 'Name is required'}
            ).classes('w-full').bind_value(form_data, 'name')
            
            ui.input(
                label='Email',
                placeholder='john@example.com',
                validation={'email': lambda v: '@' in v or 'Valid email required'}
            ).classes('w-full').bind_value(form_data, 'email')
            
            ui.input(
                label='Password',
                placeholder='••••••••',
                validation={'min_length': lambda v: len(v) >= 8 or 'At least 8 characters'}
            ).props('type=password').classes('w-full').bind_value(form_data, 'password')
            
            ui.button('Create Account', on_click=lambda: create_account(form_data)).props('color=primary').classes('w-full mt-4')
            
            ui.separator().classes('my-4')
            
            with ui.row().classes('items-center justify-center gap-1'):
                ui.label('Already have an account?').classes('text-sm text-gray-600')
                ui.link('Sign In', '/login').classes('text-sm text-blue-600')
```

### Step 2: Profile Setup (Optional, Can Skip)

```python
@ui.page('/profile-setup')
def profile_setup_page():
    address_data = {'street': '', 'city': 'Los Angeles', 'zip': '', 'phone': ''}
    
    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gray-100'):
        with ui.card().classes('w-96'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.icon('location_on')
                ui.label('Add Your Address').classes('text-xl font-semibold')
            
            ui.label('This helps us pre-fill forms and find relevant services.').classes('text-sm text-gray-600 mb-4')
            
            ui.input(
                label='Street Address',
                placeholder='123 Main St'
            ).classes('w-full').bind_value(address_data, 'street')
            
            ui.input(
                label='City',
                value='Los Angeles'
            ).classes('w-full').bind_value(address_data, 'city')
            
            ui.input(
                label='ZIP Code',
                placeholder='90012'
            ).classes('w-full').bind_value(address_data, 'zip')
            
            ui.input(
                label='Phone (optional)',
                placeholder='(555) 123-4567'
            ).classes('w-full').bind_value(address_data, 'phone')
            
            ui.button('Save & Continue', on_click=lambda: save_profile(address_data)).props('color=primary').classes('w-full mt-4')
            
            ui.button('Skip for now', on_click=lambda: ui.navigate.to('/projects')).props('flat').classes('w-full')
```

---

## User Profile Settings

### Accessing Profile

From the header user menu:

```python
# User menu in header
with ui.header().classes('bg-white shadow px-4'):
    ui.icon('account_balance')
    ui.label('Citizen Services Portal').classes('font-bold flex-grow')
    
    # User avatar with dropdown menu
    with ui.button(f'{current_user.name[0]}').props('round color=primary'):
        ui.tooltip(current_user.name)
    with ui.menu().props('auto-close'):
        with ui.menu_item(on_click=lambda: ui.navigate.to('/profile')):
            ui.icon('person', size='xs').classes('mr-2')
            ui.label('Profile')
        with ui.menu_item(on_click=lambda: ui.navigate.to('/settings')):
            ui.icon('settings', size='xs').classes('mr-2')
            ui.label('Settings')
        ui.separator()
        with ui.menu_item(on_click=sign_out):
            ui.icon('logout', size='xs').classes('mr-2')
            ui.label('Sign Out')
```

### Profile Page

```python
@ui.page('/profile')
def profile_page():
    user = get_current_user()
    editing_personal = False
    editing_address = False
    
    with ui.column().classes('w-full max-w-2xl mx-auto p-4'):
        with ui.row().classes('items-center gap-2 mb-6'):
            ui.icon('person', size='lg')
            ui.label('Your Profile').classes('text-2xl font-bold')
        
        # Personal Information Section
        with ui.card().classes('w-full mb-4'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.label('PERSONAL INFORMATION').classes('font-semibold text-gray-600 flex-grow')
                ui.button('Edit', icon='edit', on_click=toggle_edit_personal).props('flat size=sm')
            
            if not editing_personal:
                # View mode
                with ui.column().classes('gap-2'):
                    with ui.row().classes('gap-4'):
                        ui.label('Name:').classes('text-gray-500 w-20')
                        ui.label(user.name).classes('font-medium')
                    with ui.row().classes('gap-4'):
                        ui.label('Email:').classes('text-gray-500 w-20')
                        ui.label(user.email).classes('font-medium')
                    with ui.row().classes('gap-4'):
                        ui.label('Phone:').classes('text-gray-500 w-20')
                        ui.label(user.phone or 'Not provided').classes('font-medium')
            else:
                # Edit mode
                ui.input(label='Name', value=user.name).classes('w-full').bind_value(user, 'name')
                ui.input(label='Email', value=user.email).classes('w-full').bind_value(user, 'email')
                ui.input(label='Phone', value=user.phone or '').classes('w-full').bind_value(user, 'phone')
                with ui.row().classes('gap-2 mt-4'):
                    ui.button('Save', on_click=save_personal).props('color=primary')
                    ui.button('Cancel', on_click=toggle_edit_personal).props('flat')
        
        # Address Section
        with ui.card().classes('w-full'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.label('ADDRESS').classes('font-semibold text-gray-600 flex-grow')
                ui.button('Edit', icon='edit', on_click=toggle_edit_address).props('flat size=sm')
            
            if not editing_address:
                # View mode
                if user.address:
                    ui.label(user.address.street).classes('font-medium')
                    ui.label(f'{user.address.city}, {user.address.state} {user.address.zip_code}').classes('text-gray-600')
                else:
                    ui.label('No address saved').classes('text-gray-400 italic')
                    ui.button('Add Address', on_click=toggle_edit_address).props('flat')
            else:
                # Edit mode
                ui.input(label='Street Address').classes('w-full').bind_value(user.address, 'street')
                with ui.row().classes('gap-2 w-full'):
                    ui.input(label='City').classes('flex-grow').bind_value(user.address, 'city')
                    ui.input(label='ZIP').classes('w-24').bind_value(user.address, 'zip_code')
                with ui.row().classes('gap-2 mt-4'):
                    ui.button('Save', on_click=save_address).props('color=primary')
                    ui.button('Cancel', on_click=toggle_edit_address).props('flat')
```

---

## Data Model

### User Profile

```python
class UserProfile(BaseModel):
    id: str                           # Unified citizen ID (works across all agencies)
    email: str                        # Login email
    name: str                         # Full name
    phone: Optional[str]              # Phone number
    address: Optional[Address]        # Primary address
    created_at: datetime
    updated_at: datetime

class Address(BaseModel):
    street: str
    city: str
    state: str = "CA"
    zip_code: str
```

---

## Agent Integration

The agent uses the user's unified citizen ID and profile information when interacting with agencies:

### Example: Pre-filling Forms

```python
# Agent confirming address use in chat
ui.chat_message(
    f'''I'll start the permit application. I'm using the address on your profile:
    
📍 {user.address.street}, {user.address.city}, {user.address.state} {user.address.zip_code}

Is this correct?''',
    name='Agent',
    avatar='🤖',
    sent=False
)

# Quick response buttons
with ui.row().classes('gap-2 ml-12'):
    ui.button("Yes, that's right", on_click=confirm_address).props('flat')
    ui.button('Use different address', on_click=change_address).props('flat')
```

---

## Privacy & Security

| Concern | NiceGUI Implementation |
|---------|----------------------|
| Citizen ID | System-generated, stored in session |
| Address data | Displayed with confirmation before use |
| Data deletion | "Delete Account" in settings with `ui.dialog` confirmation |

```python
# Delete account confirmation dialog
async def show_delete_confirmation():
    with ui.dialog() as dialog, ui.card().classes('w-80'):
        ui.label('Delete Account?').classes('text-lg font-semibold')
        ui.label('This will permanently delete all your data including projects, saved addresses, and conversation history.').classes('text-sm text-gray-600')
        
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            ui.button('Delete Account', on_click=delete_account).props('color=negative')
    
    dialog.open()
```

---

## Mobile View

```python
# Mobile profile page
@ui.page('/profile')
def mobile_profile_page():
    user = get_current_user()
    
    # Back button header
    with ui.header().classes('bg-white shadow'):
        with ui.row().classes('w-full items-center px-4 py-3'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.back()).props('flat round')
            ui.label('Profile').classes('font-bold flex-grow')
    
    with ui.column().classes('p-4'):
        # User info card
        with ui.card().classes('w-full'):
            with ui.row().classes('items-center gap-4'):
                # Avatar
                ui.avatar(user.name[0], color='primary', size='xl')
                with ui.column():
                    ui.label(user.name).classes('font-semibold text-lg')
                    ui.label(user.email).classes('text-sm text-gray-600')
                    ui.label(user.phone or 'No phone').classes('text-sm text-gray-500')
        
        ui.separator()
        
        # Address section
        with ui.row().classes('w-full items-center'):
            ui.icon('location_on').classes('text-gray-500')
            ui.label('ADDRESS').classes('font-semibold text-gray-600 flex-grow')
            ui.button('Edit', on_click=edit_address).props('flat dense')
        
        if user.address:
            ui.label(user.address.street)
            ui.label(f'{user.address.city}, {user.address.state} {user.address.zip_code}').classes('text-gray-600')
        else:
            ui.label('No address saved').classes('text-gray-400 italic')
    
    # Bottom navigation
    with ui.footer().classes('bg-white shadow fixed bottom-0 w-full'):
        with ui.row().classes('w-full justify-around py-2'):
            ui.button('Projects', icon='folder', on_click=lambda: ui.navigate.to('/projects')).props('flat')
            ui.button('Chat', icon='chat', on_click=lambda: ui.navigate.to('/chat')).props('flat')
            ui.button('Plan', icon='timeline', on_click=lambda: ui.navigate.to('/plan')).props('flat')
```

---

## Related Documentation

- [Overview](ui-wireframes-overview.md) - Layout structure
- [Chat Interface](ui-wireframes-chat.md) - How profile data is used in conversation
- [Projects](ui-wireframes-projects.md) - Project list associated with user

