# UI Wireframes: Components Library

This document defines reusable UI components used across the Citizen Services Portal.

---

## Overview

The component library ensures consistency across the portal. All components are designed to be:

- **Generic**: Work with any content, agency, or project type
- **Accessible**: Meet WCAG 2.1 AA standards
- **Responsive**: Adapt to different screen sizes
- **Themeable**: Support light and dark modes

---

## Agency Badges

Agency badges identify which government agency is responsible for a step or action.

### Design

```
┌──────────────┐
│   [LADBS]    │  ← Blue background, white text
└──────────────┘

┌──────────────┐
│   [LADWP]    │  ← Green background, white text
└──────────────┘

┌──────────────┐
│   [LASAN]    │  ← Orange background, white text
└──────────────┘

┌──────────────┐
│   [OTHER]    │  ← Gray background, white text
└──────────────┘
```

### Specifications

| Property | Value |
|----------|-------|
| Font | System font, 11px, bold, uppercase |
| Padding | 2px 6px |
| Border Radius | 4px |
| Min Width | 48px |

### Color Mapping

| Agency | Background | Text |
|--------|------------|------|
| LADBS | `#0066CC` | `#FFFFFF` |
| LADWP | `#28A745` | `#FFFFFF` |
| LASAN | `#FD7E14` | `#FFFFFF` |
| Default/Other | `#6C757D` | `#FFFFFF` |

### Dynamic Agency Support

The system supports any agency. Unknown agencies receive the default gray styling. Colors can be configured per-deployment.

### Usage

```
┌─────────────────────────────────────────┐
│ [LADBS]  Electrical Permit              │
│          Submit application             │
└─────────────────────────────────────────┘
```

---

## Status Indicators

Status indicators show the state of steps, projects, or processes.

### Status Pills

```
┌────────────────┐
│ ○ Not Started  │  Gray text, gray border
└────────────────┘

┌────────────────┐
│ 🔒 Blocked     │  Gray text, gray background
└────────────────┘

┌────────────────┐
│ ▶ Ready        │  Blue text, blue border
└────────────────┘

┌────────────────┐
│ ◐ In Progress  │  Blue text, blue background
└────────────────┘

┌────────────────┐
│ ⚡ Action Needed│  Orange text, orange background
└────────────────┘

┌────────────────┐
│ ✓ Completed    │  Green text, green background
└────────────────┘

┌────────────────┐
│ ✗ Failed       │  Red text, red background
└────────────────┘

┌────────────────┐
│ ⊘ Skipped      │  Gray text, gray background
└────────────────┘
```

### Status Specifications

| Status | Icon | Color | Background |
|--------|------|-------|------------|
| Not Started | ○ | `#6C757D` | Transparent |
| Blocked | 🔒 | `#6C757D` | `#E9ECEF` |
| Ready | ▶ | `#0066CC` | `#E7F1FF` |
| In Progress | ◐ | `#0066CC` | `#CCE0FF` |
| Awaiting User | ⚡ | `#E65100` | `#FFF3E0` |
| Completed | ✓ | `#28A745` | `#D4EDDA` |
| Failed | ✗ | `#DC3545` | `#F8D7DA` |
| Skipped | ⊘ | `#6C757D` | `#E9ECEF` |

### Status Dots

Compact indicators for list views:

```
●  In Progress (blue)
⚡ Action Needed (orange)
✓  Completed (green)
○  Not Started (gray)
```

---

## Progress Indicators

### Progress Bar

```
┌─────────────────────────────────────────┐
│ ████████████████░░░░░░░░░░░░ 60%        │
└─────────────────────────────────────────┘
```

Specifications:
- Height: 8px (standard), 4px (compact)
- Border Radius: 4px
- Fill Color: `#0066CC` (primary)
- Background: `#E9ECEF`
- Label: Percentage text (optional)

### Progress with Steps

```
┌─────────────────────────────────────────┐
│ ████████░░░░░░░░░░░░ 40% (4/10 steps)  │
└─────────────────────────────────────────┘
```

### Circular Progress

For compact spaces:

```
    ╭───╮
    │75%│
    ╰───╯
```

---

## Buttons

### Primary Button

```
┌─────────────────────────────┐
│     ✅ Complete Action      │
└─────────────────────────────┘
```

- Background: `#0066CC`
- Text: `#FFFFFF`
- Hover: `#0052A3`
- Border Radius: 6px
- Padding: 10px 20px

### Secondary Button

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
        View Details          
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

- Background: Transparent
- Text: `#0066CC`
- Border: 1px solid `#0066CC`
- Hover: `#E7F1FF` background

### Ghost Button

```
        View Details →
```

- Background: Transparent
- Text: `#0066CC`
- No border
- Underline on hover

### Danger Button

```
┌─────────────────────────────┐
│      🗑️ Cancel Project       │
└─────────────────────────────┘
```

- Background: `#DC3545`
- Text: `#FFFFFF`

### Disabled Button

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
        Not Available         
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

- Background: `#E9ECEF`
- Text: `#6C757D`
- Cursor: not-allowed

### Button Sizes

| Size | Padding | Font Size |
|------|---------|-----------|
| Small | 6px 12px | 12px |
| Medium | 10px 20px | 14px |
| Large | 14px 28px | 16px |

---

## Form Inputs

### Text Input

```
┌─────────────────────────────────────────┐
│ Label                                   │
│ ┌─────────────────────────────────────┐ │
│ │ Placeholder text...                 │ │
│ └─────────────────────────────────────┘ │
│ Helper text or validation message       │
└─────────────────────────────────────────┘
```

### Input States

```
Default:
┌─────────────────────────────────────────┐
│ Placeholder text...                     │
└─────────────────────────────────────────┘

Focus:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ User input|                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Error:
┌─────────────────────────────────────────┐
│ Invalid input                           │
└─────────────────────────────────────────┘
⚠️ Please enter a valid email address
```

### Date Picker

```
┌─────────────────────────────────────────┐
│ 📅 Select date...                    ▼ │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│      ◀   February 2026   ▶             │
├─────────────────────────────────────────┤
│ Su  Mo  Tu  We  Th  Fr  Sa              │
│                              1                │
│  2   3   4   5   6   7   8              │
│  9  10  11  12  13  14 [15]            │
│ 16  17  18  19  20  21  22              │
│ 23  24  25  26  27  28                  │
└─────────────────────────────────────────┘
```

### Dropdown/Select

```
┌─────────────────────────────────────────┐
│ Select an option...                  ▼ │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│ ○ Option 1                              │
│ ● Option 2 (selected)                   │
│ ○ Option 3                              │
└─────────────────────────────────────────┘
```

### Checkbox

```
☐ Unchecked
☑ Checked
▣ Indeterminate
```

### Radio Button

```
○ Unselected
● Selected
```

---

## Cards

### Basic Card

```
┌─────────────────────────────────────────┐
│                                         │
│  Card Title                             │
│                                         │
│  Card content goes here. Can include    │
│  text, images, or other components.     │
│                                         │
│                          [Action]       │
└─────────────────────────────────────────┘
```

### Card Specifications

| Property | Value |
|----------|-------|
| Background | `#FFFFFF` |
| Border | 1px solid `#E0E0E0` |
| Border Radius | 8px |
| Shadow | 0 2px 4px rgba(0,0,0,0.1) |
| Padding | 16px |

### Card Hover State

```
┌─────────────────────────────────────────┐
│  Card content...                        │
│                                         │  ← Darker shadow
└─────────────────────────────────────────┘
```

### Card Selected State

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Card content...                        ┃  ← Primary color border
┃                                         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Expandable Sections

### Collapsed

```
┌─────────────────────────────────────────┐
│ Section Title                       [▼] │
└─────────────────────────────────────────┘
```

### Expanded

```
┌─────────────────────────────────────────┐
│ Section Title                       [▲] │
├─────────────────────────────────────────┤
│                                         │
│  Section content is now visible.        │
│  Can contain any components.            │
│                                         │
└─────────────────────────────────────────┘
```

---

## Tooltips

### Standard Tooltip

```
    ┌───────────────────────────────────┐
    │ This is helpful information       │
    └───────────────────────────────────┘
                     ▼
              [ Element ]
```

### Tooltip with Actions

```
    ┌───────────────────────────────────┐
    │ Step Details                      │
    │ ───────────────────────────────── │
    │ Electrical Permit                 │
    │ Status: In Review                 │
    │                                   │
    │ [View in Chat]                    │
    └───────────────────────────────────┘
                     ▼
               [ Node ]
```

---

## Modals

### Standard Modal

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Modal Title                                            [×] ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │  Modal content goes here.                                   ││
│  │                                                             ││
│  │  Can include forms, information, or confirmations.          ││
│  │                                                             ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                       [Cancel]  [Confirm]                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ░░░░░░░░░░░░░░░░░░░ (Dimmed background) ░░░░░░░░░░░░░░░░░░░░  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Confirmation Modal

```
  ┌─────────────────────────────────────────┐
  │ ⚠️ Cancel Project?                  [×] │
  ├─────────────────────────────────────────┤
  │                                         │
  │  Are you sure you want to cancel        │
  │  "Home Renovation - 123 Main St"?       │
  │                                         │
  │  This cannot be undone.                 │
  │                                         │
  ├─────────────────────────────────────────┤
  │      [Keep Project]  [Yes, Cancel]      │
  └─────────────────────────────────────────┘
```

---

## Toast Notifications

### Success Toast

```
┌───────────────────────────────────────────────┐
│ ✅ Permit submitted successfully              │  × │
└───────────────────────────────────────────────┘
```

### Error Toast

```
┌───────────────────────────────────────────────┐
│ ❌ Failed to connect to LADWP service         │  × │
│    [Retry]                                    │
└───────────────────────────────────────────────┘
```

### Info Toast

```
┌───────────────────────────────────────────────┐
│ ℹ️ Your plan has been updated                 │  × │
└───────────────────────────────────────────────┘
```

### Toast Specifications

- Position: Top-right or top-center
- Duration: 5 seconds (auto-dismiss), or manual dismiss
- Stack: Multiple toasts stack vertically

---

## Loading States

### Spinner

```
    ⟳
```

Animated rotating circle.

### Skeleton Loading

```
┌─────────────────────────────────────────┐
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░           │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░         │
│ ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░         │
└─────────────────────────────────────────┘
```

Shimmer animation indicates loading content.

### Loading Button

```
┌─────────────────────────────┐
│      ⟳ Submitting...        │
└─────────────────────────────┘
```

---

## Graph Components

### Graph Node

```
┌─────────────────────────────────┐
│ ┌─────┐               ┌─────┐  │
│ │Badge│               │State│  │
│ └─────┘               └─────┘  │
│ ─────────────────────────────  │
│ Step Title                     │
│ Reference ID (optional)        │
│ ─────────────────────────────  │
│ Automation Indicator           │
└─────────────────────────────────┘
```

### Graph Edge (Arrow)

```
Source ──────────────────────────► Target
```

Edge styles by state:
- Completed: Solid line, green
- In Progress: Dashed line, blue
- Pending: Dotted line, gray

### Node Sizes

| Size | Width | Height | Use Case |
|------|-------|--------|----------|
| Compact | 80px | 60px | Complex graphs |
| Standard | 140px | 80px | Default |
| Large | 200px | 100px | Simple graphs |

---

## Avatars

### User Avatar

```
┌─────┐
│ JS  │  ← Initials
└─────┘

┌─────┐
│ 👤 │  ← Default icon
└─────┘

┌─────┐
│ 📷 │  ← Photo
└─────┘
```

### Agent Avatar

```
┌─────┐
│ 🤖 │  ← Robot icon
└─────┘
```

### Avatar Sizes

| Size | Dimension | Use Case |
|------|-----------|----------|
| XS | 24px | Inline mentions |
| SM | 32px | List items |
| MD | 40px | Chat messages |
| LG | 64px | Profile header |

---

## Dividers

### Horizontal Divider

```
───────────────────────────────────────────
```

### Divider with Text

```
─────────────── Today ─────────────────
```

---

## Empty States

### Generic Empty State

```
┌─────────────────────────────────────────┐
│                                         │
│              [  📋  ]                   │
│                                         │
│          No items found                 │
│                                         │
│    Description text explaining the      │
│    empty state and what to do next.     │
│                                         │
│           [Primary Action]              │
│                                         │
└─────────────────────────────────────────┘
```

### Empty State Specifications

- Icon: Relevant to context (📋 for lists, 💬 for chat, etc.)
- Title: Brief, clear statement
- Description: Explanation and guidance
- Action: Optional button for next step

---

## Keyboard Shortcuts Overlay

```
┌───────────────────────────────────────────────────────────────┐
│ Keyboard Shortcuts                                       [×] │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Navigation                                                   │
│  ─────────────────────────────────────────────────────────   │
│  Ctrl+B         Toggle projects panel                        │
│  Ctrl+P         Toggle plan panel                            │
│  ↑ / ↓          Navigate project list                        │
│  Enter          Select item                                   │
│                                                               │
│  Chat                                                         │
│  ─────────────────────────────────────────────────────────   │
│  Enter          Send message                                  │
│  Shift+Enter    New line                                      │
│  Escape         Cancel input                                  │
│                                                               │
│  General                                                      │
│  ─────────────────────────────────────────────────────────   │
│  Ctrl+N         New project                                   │
│  Ctrl+F         Search                                        │
│  ?              Show this overlay                             │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Responsive Breakpoints

| Breakpoint | Name | Min Width | Columns |
|------------|------|-----------|---------|
| xs | Mobile | 0px | 1 |
| sm | Mobile Large | 576px | 1 |
| md | Tablet | 768px | 2 |
| lg | Desktop | 1024px | 3 |
| xl | Desktop Large | 1440px | 3+ |

---

## Spacing Scale

| Token | Size | Usage |
|-------|------|-------|
| space-1 | 4px | Tight spacing |
| space-2 | 8px | Default small |
| space-3 | 12px | Default medium |
| space-4 | 16px | Default large |
| space-5 | 24px | Section spacing |
| space-6 | 32px | Large section |
| space-8 | 48px | Major sections |

---

## Typography

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| H1 | 28px | Bold | 1.2 |
| H2 | 24px | Bold | 1.2 |
| H3 | 20px | SemiBold | 1.3 |
| H4 | 16px | SemiBold | 1.4 |
| Body | 14px | Regular | 1.5 |
| Small | 12px | Regular | 1.5 |
| Caption | 11px | Regular | 1.4 |

---

## Color Palette

### Primary Colors

| Name | Hex | Usage |
|------|-----|-------|
| Primary | `#0066CC` | Links, buttons, active states |
| Primary Hover | `#0052A3` | Hover states |
| Primary Light | `#E7F1FF` | Backgrounds |

### Semantic Colors

| Name | Hex | Usage |
|------|-----|-------|
| Success | `#28A745` | Completed, success messages |
| Warning | `#FFC107` | Warnings, pending |
| Error | `#DC3545` | Errors, failures |
| Info | `#17A2B8` | Information |

### Neutral Colors

| Name | Hex | Usage |
|------|-----|-------|
| Gray-900 | `#1A1A1A` | Primary text |
| Gray-700 | `#4A4A4A` | Secondary text |
| Gray-500 | `#6C757D` | Muted text |
| Gray-300 | `#ADB5BD` | Disabled |
| Gray-200 | `#E0E0E0` | Borders |
| Gray-100 | `#F5F5F5` | Backgrounds |

---

## Related Documentation

- [Overview](6-ui-wireframes-overview.md) - Layout structure
- [Projects](6-ui-wireframes-projects.md) - Project panel components
- [Chat](6-ui-wireframes-chat.md) - Chat interface components
- [Plan Widget](6-ui-wireframes-plan-widget.md) - Graph components
- [User Actions](6-ui-wireframes-user-actions.md) - Action card components
