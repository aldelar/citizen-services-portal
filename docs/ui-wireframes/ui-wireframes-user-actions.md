# UI Wireframes: User Actions

This document defines the design for UserActionResponse cards—when the AI agent delegates tasks that require the citizen to take action outside the system.

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

| Action Type | Icon | Example Target | Use Case |
|-------------|------|----------------|----------|
| `phone_call` | 📞 | 311 | Schedule inspection via 311 |
| `email` | 📧 | solar@ladwp.com | Submit interconnection documents |
| `in_person` | 🏢 | LADBS Office, 201 N Figueroa | Pick up physical permit |
| `online_portal` | 🌐 | ladwp.com/NEM | Complete action on agency website |

---

## UserAction Card Design

### Complete Card Structure

```
┌───────────────────────────────────────────────────────────────────┐
│ ⚡ USER ACTION NEEDED                                      [?]    │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📞 Call 311 to schedule inspection                              │
│                                                                   │
│  ─────────────────────────────────────────────────────────────   │
│                                                                   │
│  Why: LADBS inspection scheduling is only available via phone    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📋 Phone Script                                        [▼] │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │ "I need to schedule a rough electrical inspection for       │  │
│  │ permit number 2026-001234 at 123 Main St, Los Angeles.      │  │
│  │ My name is John Smith and my phone number is 555-0123."     │  │
│  │                                                             │  │
│  │                                                   [📋 Copy] │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ ✓ Have These Ready                                     [▼] │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │ ☐ Have permit number ready: 2026-001234                     │  │
│  │ ☐ Confirm work is ready for inspection                      │  │
│  │ ☐ Request morning slot (8am-12pm) if preferred              │  │
│  │ ☐ Note: 24-48 hours advance notice typically required       │  │
│  │                                                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  📞 Contact: 311                                                  │
│  🕐 Hours: 24/7                                                   │
│  🔗 Alternative: https://ladbs.org/inspections                   │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│              [ ✅ I've Completed This ]                          │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Card Components

### Header

```
┌───────────────────────────────────────────────────────────────────┐
│ ⚡ USER ACTION NEEDED                                      [?]    │
└───────────────────────────────────────────────────────────────────┘
```

- **Icon**: ⚡ (lightning bolt) - attention indicator
- **Title**: "USER ACTION NEEDED" - clear call to action
- **Help button**: Opens tooltip explaining why user action is required

### Primary Action Line

```
┌───────────────────────────────────────────────────────────────────┐
│  📞 Call 311 to schedule inspection                              │
└───────────────────────────────────────────────────────────────────┘
```

Format: `[Action Type Icon] [Action Verb] [Target] to [Purpose]`

| Action Type | Format |
|-------------|--------|
| Phone | 📞 Call [number] to [action] |
| Email | 📧 Email [address] to [action] |
| In Person | 🏢 Visit [location] to [action] |
| Portal | 🌐 Go to [site] to [action] |

### Reason Line

```
┌───────────────────────────────────────────────────────────────────┐
│  Why: LADBS inspection scheduling is only available via phone    │
└───────────────────────────────────────────────────────────────────┘
```

- Explains why automation isn't possible
- Helps user understand the necessity

---

## Prepared Materials Sections

### Phone Script (Collapsible)

```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 Phone Script                                            [▼] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ "I need to schedule a rough electrical inspection for           │
│ permit number 2026-001234 at 123 Main St, Los Angeles.          │
│ My name is John Smith and my phone number is 555-0123."         │
│                                                                 │
│                                                       [📋 Copy] │
└─────────────────────────────────────────────────────────────────┘
```

**Copy button behavior:**
- Copies script text to clipboard
- Shows "Copied!" confirmation briefly
- Icon changes to ✓ temporarily

### Email Draft (Collapsible)

```
┌─────────────────────────────────────────────────────────────────┐
│ 📧 Email Draft                                             [▼] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ To: SolarCoordinator@ladwp.com                                 │
│ Subject: Interconnection Agreement - 123 Main St               │
│                                                                 │
│ ─────────────────────────────────────────────────────────────  │
│                                                                 │
│ Dear LADWP Solar Coordination Team,                            │
│                                                                 │
│ I am requesting an interconnection agreement for my solar      │
│ PV system installation at:                                     │
│                                                                 │
│ Address: 123 Main St, Los Angeles, CA 90012                    │
│ System Size: 8.5 kW                                            │
│ LADBS Permit #: 2026-001234                                    │
│                                                                 │
│ Please find attached:                                          │
│ - Single-line electrical diagram                               │
│ - Equipment specifications                                     │
│ - Site plan                                                    │
│                                                                 │
│ Thank you,                                                     │
│ John Smith                                                     │
│ 555-0123                                                       │
│                                                                 │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ [📋 Copy All]  [📧 Open in Email Client]                 │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Checklist (Collapsible)

```
┌─────────────────────────────────────────────────────────────────┐
│ ✓ Have These Ready                                         [▼] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ☐ Have permit number ready: 2026-001234                         │
│ ☐ Confirm work is ready for inspection (wiring accessible)      │
│ ☐ Know your preferred time slot (morning/afternoon)             │
│ ☐ Have contractor contact info if needed                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Users can check items as they prepare. Checkboxes are optional—not required for completion.

### Documents Needed (Collapsible)

```
┌─────────────────────────────────────────────────────────────────┐
│ 📎 Documents Needed                                        [▼] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ☐ Single-line electrical diagram (PDF)                          │
│ ☐ Equipment specifications (solar panels, inverter, battery)    │
│ ☐ Site plan showing panel layout                                │
│ ☐ Structural calculations (if roof-mounted)                     │
│                                                                 │
│ Tip: These should have been prepared for your permit            │
│ application. Check with your contractor if missing.             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Contact Information

```
┌─────────────────────────────────────────────────────────────────┐
│ 📞 Contact: 311                                                 │
│ 🕐 Hours: 24/7                                                  │
│ 🔗 Alternative: ladbs.org/inspections  [↗]                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Completion Flow

### Step 1: User Clicks "I've Completed This"

```
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│              [ ✅ I've Completed This ]                          │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
```

### Step 2: Confirmation Form Appears

Based on `on_complete.expected_info`:

```
┌───────────────────────────────────────────────────────────────────┐
│ ✅ Great! Just a few details...                                  │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  What date was the inspection scheduled for?                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📅 Select date...                                        ▼ │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  What confirmation number did you receive?                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ e.g., INS-789456                                            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  What time window was assigned? (optional)                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ e.g., 8am-12pm                                              │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│       [Cancel]                           [Submit Details]        │
└───────────────────────────────────────────────────────────────────┘
```

### Field Types by Expected Info

| expected_info | Field Type | Example |
|---------------|------------|---------|
| `scheduled_date` | Date picker | Feb 15, 2026 |
| `confirmation_number` | Text input | INS-789456 |
| `time_window` | Dropdown or text | 8am-12pm |
| `amount` | Number input | $1,250.00 |
| `reference_number` | Text input | 2026-005678 |

### Step 3: Confirmation Message

After submission:

```
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│   🤖  Perfect! ✅ I've updated your plan.                        │
│                                                                   │
│       Inspection scheduled: Feb 15, 2026 (INS-789456)            │
│       Time window: 8am-12pm                                       │
│                                                                   │
│       I'll follow up after Feb 15 to see how it went.            │
│       In the meantime, let's look at your next steps...          │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Action Card by Type

### Phone Call Card

```
┌───────────────────────────────────────────────────────────────────┐
│ ⚡ USER ACTION NEEDED                                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📞 Call 311 to schedule inspection                              │
│                                                                   │
│  Why: LADBS inspection scheduling is only available via phone    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📋 Phone Script                               [📋 Copy] [▼]│  │
│  │ ─────────────────────────────────────────────────────────  │  │
│  │ "I need to schedule a rough electrical inspection for      │  │
│  │ permit #2026-001234 at 123 Main St..."                     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  📞 311  •  🕐 24/7                                               │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│              [ ✅ I've Completed This ]                          │
└───────────────────────────────────────────────────────────────────┘
```

### Email Card

```
┌───────────────────────────────────────────────────────────────────┐
│ ⚡ USER ACTION NEEDED                                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📧 Email LADWP to submit interconnection agreement              │
│                                                                   │
│  Why: Interconnection agreements require document attachments    │
│       that must be submitted via email                           │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📧 Email Draft                                          [▼]│  │
│  │ ─────────────────────────────────────────────────────────  │  │
│  │ To: SolarCoordinator@ladwp.com                             │  │
│  │ Subject: Interconnection Agreement - 123 Main St           │  │
│  │                                                             │  │
│  │ Dear LADWP Solar Coordination Team...                      │  │
│  │                                                             │  │
│  │ [📋 Copy All]  [📧 Open Email Client]                      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📎 Documents Needed                                     [▼]│  │
│  │ ─────────────────────────────────────────────────────────  │  │
│  │ ☐ Single-line diagram  ☐ Equipment specs  ☐ Site plan      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│              [ ✅ I've Completed This ]                          │
└───────────────────────────────────────────────────────────────────┘
```

### In-Person Visit Card

```
┌───────────────────────────────────────────────────────────────────┐
│ ⚡ USER ACTION NEEDED                                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🏢 Visit LADBS office to pick up permit                         │
│                                                                   │
│  Why: Physical permit card must be posted at job site            │
│                                                                   │
│  📍 Location:                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ LADBS Metro Office                                          │  │
│  │ 201 N. Figueroa St., 4th Floor                              │  │
│  │ Los Angeles, CA 90012                                       │  │
│  │                                                             │  │
│  │ [🗺️ Open in Maps]                                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  🕐 Hours: Mon-Fri 8am-4:30pm                                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📋 Bring With You                                       [▼]│  │
│  │ ─────────────────────────────────────────────────────────  │  │
│  │ ☐ Government-issued photo ID                                │  │
│  │ ☐ Permit approval letter (or email confirmation)           │  │
│  │ ☐ Payment for permit fee ($1,250)                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│              [ ✅ I've Completed This ]                          │
└───────────────────────────────────────────────────────────────────┘
```

### Online Portal Card

```
┌───────────────────────────────────────────────────────────────────┐
│ ⚡ USER ACTION NEEDED                                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🌐 Complete on LADWP website                                    │
│                                                                   │
│  Why: TOU rate plan selection requires account verification      │
│       on the LADWP portal                                        │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                                                             │  │
│  │  Go to: ladwp.com/myaccount                                │  │
│  │                                                             │  │
│  │  [🌐 Open Portal]                                          │  │
│  │                                                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📋 Steps to Complete                                    [▼]│  │
│  │ ─────────────────────────────────────────────────────────  │  │
│  │ 1. Log into your LADWP account                              │  │
│  │ 2. Go to "Rate Plans" section                               │  │
│  │ 3. Select "TOU-D-PRIME" for solar customers                 │  │
│  │ 4. Confirm your selection                                   │  │
│  │ 5. Note the confirmation number shown                       │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  You'll need: LADWP account login, your service address          │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│              [ ✅ I've Completed This ]                          │
└───────────────────────────────────────────────────────────────────┘
```

---

## Pending Actions Indicator

When the user has pending actions, they're highlighted:

### In Plan Widget

```
┌─────────────────────────────────────────┐
│ 📊 PROJECT PLAN                         │
│ ...                                     │
├─────────────────────────────────────────┤
│ ⚡ 2 actions need your attention        │
│ ┌─────────────────────────────────────┐ │
│ │ 📞 Schedule Inspection      [View]  │ │
│ │ 📧 Submit IA Documents      [View]  │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### In Chat (Return Visit)

When user returns to chat:

```
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│   🤖  Welcome back, John! I see you have 2 pending tasks:       │
│                                                                   │
│       1. 📞 Schedule rough electrical inspection                 │
│       2. 📧 Submit interconnection documents                     │
│                                                                   │
│       Have you had a chance to complete any of these?           │
│                                                                   │
│       [Yes, I completed one] [Not yet] [Show me the details]    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Card States

### Collapsed Card (In Chat History)

After completion or when scrolled past:

```
┌───────────────────────────────────────────────────────────────────┐
│ ✅ COMPLETED: Call 311 to schedule inspection                    │
│    Scheduled for Feb 15, 2026 (INS-789456)             [Expand] │
└───────────────────────────────────────────────────────────────────┘
```

### Expired/Overdue Card

If action has been pending too long:

```
┌───────────────────────────────────────────────────────────────────┐
│ ⚠️ ACTION PENDING (7 days)                                       │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📞 Call 311 to schedule inspection                              │
│                                                                   │
│  ⏰ This task was assigned 7 days ago.                           │
│     Would you like help completing it?                           │
│                                                                   │
│  [View Details]  [Reschedule]  [Mark Complete]                   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Mobile Action Card

Full-width on mobile:

```
┌─────────────────────────────────────────┐
│ ⚡ ACTION NEEDED                        │
├─────────────────────────────────────────┤
│                                         │
│ 📞 Call 311                             │
│ Schedule rough inspection               │
│                                         │
│ Why: Phone only                         │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 📋 Script                     [▼]  │ │
│ │ "I need to schedule..."             │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ✓ Checklist                   [▼]  │ │
│ │ ☐ Permit # ☐ Work ready            │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ 📞 311 • 24/7                           │
│                                         │
├─────────────────────────────────────────┤
│    [ ✅ I've Completed This ]           │
└─────────────────────────────────────────┘
```

---

## Accessibility

| Requirement | Implementation |
|-------------|----------------|
| Screen Reader | Clear action descriptions, form labels |
| Keyboard | Tab through sections, Enter to expand/collapse |
| Copy Buttons | Confirmation announced to screen reader |
| Forms | Proper input labels and error messages |
| Focus | Focus trap in completion form modal |

---

## Related Documentation

- [Chat Interface](ui-wireframes-chat.md) - Where cards appear
- [Plan Widget](ui-wireframes-plan-widget.md) - Step status updates
- [Components](ui-wireframes-components.md) - Reusable elements
