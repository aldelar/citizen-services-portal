# UI Wireframes: User Account Management

This document defines the user account creation and management features for the Citizen Services Portal.

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

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ Citizen Services Portal                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│                      ┌─────────────────────────────────────┐                   │
│                      │                                     │                   │
│                      │    🏛️ Create Your Account          │                   │
│                      │                                     │                   │
│                      │    Full Name                        │                   │
│                      │    ┌─────────────────────────────┐  │                   │
│                      │    │ John Smith                  │  │                   │
│                      │    └─────────────────────────────┘  │                   │
│                      │                                     │                   │
│                      │    Email                            │                   │
│                      │    ┌─────────────────────────────┐  │                   │
│                      │    │ john@example.com            │  │                   │
│                      │    └─────────────────────────────┘  │                   │
│                      │                                     │                   │
│                      │    Password                         │                   │
│                      │    ┌─────────────────────────────┐  │                   │
│                      │    │ ••••••••••••                │  │                   │
│                      │    └─────────────────────────────┘  │                   │
│                      │                                     │                   │
│                      │    ┌─────────────────────────────┐  │                   │
│                      │    │     Create Account          │  │                   │
│                      │    └─────────────────────────────┘  │                   │
│                      │                                     │                   │
│                      │    Already have an account?         │                   │
│                      │    [Sign In]                        │                   │
│                      │                                     │                   │
│                      └─────────────────────────────────────┘                   │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Step 2: Profile Setup (Optional, Can Skip)

After account creation, users can optionally add more details:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ Citizen Services Portal                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│                      ┌─────────────────────────────────────┐                   │
│                      │                                     │                   │
│                      │    📍 Add Your Address              │                   │
│                      │                                     │                   │
│                      │    This helps us pre-fill forms     │                   │
│                      │    and find relevant services.      │                   │
│                      │                                     │                   │
│                      │    Street Address                   │                   │
│                      │    ┌─────────────────────────────┐  │                   │
│                      │    │ 123 Main St                 │  │                   │
│                      │    └─────────────────────────────┘  │                   │
│                      │                                     │                   │
│                      │    City                             │                   │
│                      │    ┌─────────────────────────────┐  │                   │
│                      │    │ Los Angeles                 │  │                   │
│                      │    └─────────────────────────────┘  │                   │
│                      │                                     │                   │
│                      │    ZIP Code                         │                   │
│                      │    ┌─────────────────────────────┐  │                   │
│                      │    │ 90012                       │  │                   │
│                      │    └─────────────────────────────┘  │                   │
│                      │                                     │                   │
│                      │    Phone (optional)                 │                   │
│                      │    ┌─────────────────────────────┐  │                   │
│                      │    │ (555) 123-4567              │  │                   │
│                      │    └─────────────────────────────┘  │                   │
│                      │                                     │                   │
│                      │    ┌──────────────────────────────┐ │                   │
│                      │    │       Save & Continue        │ │                   │
│                      │    └──────────────────────────────┘ │                   │
│                      │              [Skip for now]         │                   │
│                      │                                     │                   │
│                      └─────────────────────────────────────┘                   │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## User Profile Settings

### Accessing Profile

From the header user menu:

```
┌─────────────────────────────────────────┐
│                          [John S. ▼]    │
│                          ┌──────────────┤
│                          │ 👤 Profile   │
│                          │ ⚙️ Settings  │
│                          │ ───────────  │
│                          │ 🚪 Sign Out  │
│                          └──────────────┘
```

### Profile Page

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ Citizen Services Portal                              [John S. ▼]           │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                           │ │
│  │  👤 Your Profile                                                         │ │
│  │                                                                           │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │ │
│  │  │ PERSONAL INFORMATION                                         [Edit] │  │ │
│  │  ├─────────────────────────────────────────────────────────────────────┤  │ │
│  │  │                                                                     │  │ │
│  │  │  Name:     John Smith                                               │  │ │
│  │  │  Email:    john@example.com                                         │  │ │
│  │  │  Phone:    (555) 123-4567                                           │  │ │
│  │  │                                                                     │  │ │
│  │  └─────────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                           │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │ │
│  │  │ ADDRESS                                                      [Edit] │  │ │
│  │  ├─────────────────────────────────────────────────────────────────────┤  │ │
│  │  │                                                                     │  │ │
│  │  │  123 Main St                                                        │  │ │
│  │  │  Los Angeles, CA 90012                                              │  │ │
│  │  │                                                                     │  │ │
│  │  └─────────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                           │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
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

```
Agent: "I'll start the permit application. I'm using the address 
        on your profile (123 Main St, Los Angeles, CA 90012). 
        Is this correct?"

User: "Yes, that's right."

Agent: "Great! I've submitted the application using your citizen ID."
```

---

## Privacy & Security

| Concern | Handling |
|---------|----------|
| Citizen ID | System-generated, used internally for agency coordination |
| Address data | Only used for pre-filling, user confirms each use |
| Data deletion | "Delete Account" option removes all user data |

---

## Mobile View

Profile page adapts to mobile:

```
┌─────────────────────────────────────────┐
│ ← Profile                               │
├─────────────────────────────────────────┤
│                                         │
│  👤 John Smith                          │
│  john@example.com                       │
│  (555) 123-4567                         │
│                                         │
│  ─────────────────────────────────────  │
│                                         │
│  📍 ADDRESS                      [Edit] │
│  123 Main St                            │
│  Los Angeles, CA 90012                  │
│                                         │
├─────────────────────────────────────────┤
│ [📋 Projects] [💬 Chat] [📊 Plan]       │
└─────────────────────────────────────────┘
```

---

## Related Documentation

- [Overview](ui-wireframes-overview.md) - Layout structure
- [Chat Interface](ui-wireframes-chat.md) - How profile data is used in conversation
- [Projects](ui-wireframes-projects.md) - Project list associated with user

