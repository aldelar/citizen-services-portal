# UI Wireframes: Overview

This document defines the overall layout structure, navigation patterns, and responsive behavior for the Citizen Services Portal.

---

## Design Philosophy

The Citizen Services Portal is a **chat-first, project-centric** application that helps citizens navigate multi-agency government processes. The UI must be:

1. **Generic**: Render any project type (home renovation, business license, utility connection, etc.)
2. **Dynamic**: Handle plans with 3 steps or 30+ steps
3. **Agent-Driven**: The AI orchestrator builds and updates plans through conversation
4. **Action-Oriented**: Clearly surface what needs user attention

---

## Three-Panel Layout (Desktop)

The primary layout consists of three panels optimized for the chat-first experience:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ Citizen Services Portal                               [John Smith ▼] [?]   │
├───────────────┬─────────────────────────────────────┬─────────────────────────┤
│               │                                     │                         │
│   LEFT PANEL  │           CENTER PANEL              │      RIGHT PANEL        │
│   (240-320px) │           (flexible)                │      (320-400px)        │
│               │                                     │                         │
│   Project     │           Chat Interface            │      Plan Graph         │
│   Navigation  │                                     │      Widget             │
│               │                                     │                         │
│   • List      │   • Messages                        │   • Visual graph        │
│   • Search    │   • Streaming responses             │   • Step statuses       │
│   • Create    │   • UserAction cards                │   • Dependencies        │
│               │   • Input area                      │   • Quick actions       │
│               │                                     │                         │
└───────────────┴─────────────────────────────────────┴─────────────────────────┘
```

### Panel Sizes

| Panel | Min Width | Max Width | Default | Collapsible |
|-------|-----------|-----------|---------|-------------|
| Left (Projects) | 200px | 360px | 280px | Yes |
| Center (Chat) | 400px | Unlimited | Flexible | No |
| Right (Plan) | 280px | 480px | 360px | Yes |

### Panel Collapse Behavior

- **Left panel**: Collapses to narrow strip showing project status indicators
- **Right panel**: Can be hidden entirely or collapsed to summary bar (48px)
- **Toggle controls**: Use panel header buttons to collapse/expand

---

## Header Bar

The header provides global navigation and user context.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ Citizen Services Portal          [Current Project Title]    [👤 Name ▼] [?]│
└────────────────────────────────────────────────────────────────────────────────┘
```

### Header Components

| Component | Purpose | Behavior |
|-----------|---------|----------|
| Logo/Brand | Identity | Click returns to project list |
| Project Title | Context | Shows current project name; hidden if no project selected |
| User Menu | Account | Dropdown: Profile, Settings, Sign Out (see [User Account](ui-wireframes-user-account.md)) |
| Help | Assistance | Opens help panel/modal |

---

## Responsive Breakpoints

The portal adapts to different screen sizes:

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Desktop Large | ≥1440px | 3-panel, all visible |
| Desktop | 1024-1439px | 3-panel, plan panel collapsible |
| Tablet | 768-1023px | 2-panel, plan as overlay |
| Mobile | <768px | Single panel, tab navigation |

### Desktop (≥1024px)

Full three-panel layout with resizable dividers.

```
┌─────────────────────────────────────────────────────────────────┐
│ Header                                                          │
├──────────┬──────────────────────────────┬──────────────────────┤
│ Projects │           Chat               │      Plan Graph      │
│          │                              │                      │
└──────────┴──────────────────────────────┴──────────────────────┘
```

### Tablet (768-1023px)

Two panels with plan as slide-over overlay.

```
┌─────────────────────────────────────────────────────────────────┐
│ Header                                              [Plan 📊]   │
├──────────┬──────────────────────────────────────────────────────┤
│ Projects │           Chat                                       │
│ (narrow) │                                                      │
└──────────┴──────────────────────────────────────────────────────┘
                                                        ┌─────────┐
                                                        │ Plan    │
                                     Overlay on tap --> │ Graph   │
                                                        │ Widget  │
                                                        └─────────┘
```

### Mobile (<768px)

Single-panel with bottom tab navigation.

```
┌─────────────────────────────────────────┐
│ Header (compact)                        │
├─────────────────────────────────────────┤
│                                         │
│                                         │
│          Active Tab Content             │
│          (Projects / Chat / Plan)       │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│ [📋 Projects] [💬 Chat] [📊 Plan]       │
└─────────────────────────────────────────┘
```

#### Mobile Tab Content

| Tab | Content |
|-----|---------|
| Projects | Full project list with cards |
| Chat | Full chat interface |
| Plan | Plan graph (scrollable, zoomable) |

---

## Navigation Flow

### Primary Navigation Paths

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Landing/Login ─────► Project List ─────► Chat + Plan           │
│       │                    │                   │                │
│       ▼                    ▼                   ▼                │
│   Sign In             Create New          Interact with         │
│   Sign Up             Project             Agent                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### User Journey States

| State | What User Sees | Primary Action |
|-------|---------------|----------------|
| First Visit | Empty state, welcome message | Create first project |
| Has Projects | Project list with statuses | Select or create project |
| In Project | Chat + Plan | Converse with agent |
| Action Needed | UserAction card prominent | Complete user action |
| Project Done | Completed badge, read-only | View summary, start new |

---

## Empty States

### No Projects (First Visit)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ Citizen Services Portal                                    [👤 Name ▼] [?] │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│                                                                                │
│                      ┌─────────────────────────────────────┐                   │
│                      │                                     │                   │
│                      │    🏛️ Welcome to the                │                   │
│                      │    Citizen Services Portal          │                   │
│                      │                                     │                   │
│                      │    I'm your AI assistant for        │                   │
│                      │    navigating LA city services.     │                   │
│                      │                                     │                   │
│                      │    Tell me what you need help       │                   │
│                      │    with, and I'll guide you         │                   │
│                      │    through the process.             │                   │
│                      │                                     │                   │
│                      │    ┌─────────────────────────────┐  │                   │
│                      │    │ Start a conversation...     │  │                   │
│                      │    └─────────────────────────────┘  │                   │
│                      │                                     │                   │
│                      │    Examples:                        │                   │
│                      │    • "I want to install solar"     │                   │
│                      │    • "How do I get a business       │                   │
│                      │      license?"                      │                   │
│                      │    • "I need to schedule a bulk     │                   │
│                      │      pickup"                        │                   │
│                      │                                     │                   │
│                      └─────────────────────────────────────┘                   │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Project Selected, No Plan Yet

```
┌──────────────┬──────────────────────────────────────┬────────────────────────┐
│ PROJECTS     │              CHAT                    │     PROJECT PLAN       │
├──────────────┼──────────────────────────────────────┼────────────────────────┤
│              │                                      │                        │
│ ● New        │  🤖 Hi! I'm here to help you with   │  ┌────────────────────┐ │
│   Project    │     your home renovation project.    │  │                    │ │
│              │                                      │  │  📋 No plan yet    │ │
│              │     Tell me about what you're        │  │                    │ │
│              │     planning, and I'll help you      │  │  As we discuss     │ │
│              │     figure out what's needed.        │  │  your project,     │ │
│              │                                      │  │  I'll build a      │ │
│              │  👤 I want to install solar panels   │  │  step-by-step      │ │
│              │     and battery storage at my home   │  │  plan here.        │ │
│              │                                      │  │                    │ │
│              │  🤖 Great! I'll help you with that.  │  │  [Steps will       │ │
│              │     Let me ask a few questions...    │  │   appear as we     │ │
│              │                                      │  │   identify them]   │ │
│              │                                      │  │                    │ │
│              │                                      │  └────────────────────┘ │
│              │  ┌────────────────────────────────┐  │                        │
│              │  │ Type your message...       [→] │  │                        │
│              │  └────────────────────────────────┘  │                        │
└──────────────┴──────────────────────────────────────┴────────────────────────┘
```

---

## Loading States

### Initial Page Load

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ Citizen Services Portal                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│                                                                                │
│                                                                                │
│                              ┌─────────────────┐                               │
│                              │                 │                               │
│                              │    🏛️           │                               │
│                              │   Loading...    │                               │
│                              │                 │                               │
│                              └─────────────────┘                               │
│                                                                                │
│                                                                                │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Project Loading

Left panel shows skeleton cards while fetching project list.

### Message Streaming

Chat shows typing indicator while agent generates response (see Chat wireframe doc).

---

## Accessibility Requirements

| Requirement | Implementation |
|-------------|----------------|
| Keyboard Navigation | Full keyboard support, visible focus states |
| Screen Reader | ARIA labels, live regions for updates |
| Color Contrast | WCAG 2.1 AA compliance (4.5:1 text, 3:1 UI) |
| Focus Management | Logical tab order, skip links |
| Reduced Motion | Respect `prefers-reduced-motion` |
| Text Scaling | Support up to 200% zoom |

> **Implementation Note:** All color combinations in the wireframes (especially status indicators, agency badges, and themed elements) must be validated against WCAG contrast ratios during implementation. Status indicators should not rely solely on color—use icons, text labels, and patterns as additional differentiators.

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
