# UI Wireframes: Projects Panel

This document defines the project list, creation flow, and project management features in the left panel.

---

## Overview

The Projects Panel serves as the navigation hub for all user projects. It displays existing projects, allows creation of new projects, and provides filtering/search capabilities.

**Key Principle**: Project types are **discovered through conversation**, not pre-selected. The user starts a conversation, and the agent determines what type of project this is.

---

## Project List (Left Panel)

### Standard View

```
┌─────────────────────────────┐
│ PROJECTS              [+]   │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ 🔍 Search projects...   │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ ⚡ Home Renovation       │ │
│ │ 123 Main St             │ │
│ │ ████████░░ 80%          │ │
│ │ 1 action needed         │ │
│ │ Updated 2 hours ago     │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ 🔄 Business License     │ │
│ │ Downtown Café           │ │
│ │ ██░░░░░░░░ 20%          │ │
│ │ In progress             │ │
│ │ Updated 1 day ago       │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ ✅ Bulk Pickup          │ │
│ │ 456 Oak Ave             │ │
│ │ ██████████ 100%         │ │
│ │ Completed               │ │
│ │ Completed Dec 15        │ │
│ └─────────────────────────┘ │
│                             │
│        [Load More]          │
└─────────────────────────────┘
```

### Narrow View

The left panel can be resized narrower. In narrow mode, project cards show abbreviated info:

```
┌────────────────────┐
│  +  New            │
├────────────────────┤
│ ⚡ Home Renov...   │
│    80%             │
├────────────────────┤
│ 🔄 Business...     │
│    20%             │
├────────────────────┤
│ ✅ Bulk Pick...    │
│    Done            │
└────────────────────┘
```

---

## Project Card

Each project is displayed as a card with consistent information:

### Card Structure

```
┌───────────────────────────────────────┐
│ [Icon] [Title]                [Status]│
│ [Subtitle/Address]                    │
│ [Progress Bar]         [Percentage]   │
│ [Status Message]                      │
│ [Last Updated]                        │
└───────────────────────────────────────┘
```

### Card Components

| Component | Description | Source |
|-----------|-------------|--------|
| Icon | Project type icon (dynamic) | Inferred from `context.projectType` |
| Title | Project name | `project.title` |
| Subtitle | Address or brief description | `context.address` or `context.description` |
| Progress Bar | Visual completion status | `summary.completed / summary.totalSteps` |
| Status Message | Current state | Derived from step statuses |
| Last Updated | Time since last activity | `project.updatedAt` |

### Project Icons (Status-Based)

Icons indicate project status, not project type (keeping the UI simple for MVP):

| Status | Icon | Meaning |
|--------|------|---------|
| Active (needs action) | ⚡ | User action required |
| Active (in progress) | 🔄 | Work in progress |
| Waiting | ⏳ | Waiting for external response |
| Completed | ✅ | All steps done |
| Cancelled | ❌ | Project cancelled |
| New | 📋 | Just started |

---

## Project States

Projects have distinct visual states:

### Active States

```
┌─────────────────────────────┐
│ 🏠 Home Renovation          │   ← Standard card
│ 123 Main St                 │
│ ████████░░ 80%              │
│ 🔄 In progress              │   ← Blue status
│ Updated 2 hours ago         │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 🏠 Home Renovation      ⚠️  │   ← Orange attention indicator
│ 123 Main St                 │
│ ████████░░ 80%              │
│ ⚡ 1 action needed           │   ← Orange status
│ Updated 2 hours ago         │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 🏠 Home Renovation      ●   │   ← Pulsing dot (waiting)
│ 123 Main St                 │
│ ████████░░ 80%              │
│ ⏳ Waiting for agency        │   ← Gray status
│ Updated 2 days ago          │
└─────────────────────────────┘
```

### Completed State

```
┌─────────────────────────────┐
│ ♻️ Bulk Pickup         ✅   │   ← Green checkmark
│ 456 Oak Ave                 │
│ ██████████ 100%             │   ← Full green bar
│ ✅ Completed                 │   ← Green status
│ Completed Dec 15, 2025      │
└─────────────────────────────┘
```

### Cancelled State

```
┌─────────────────────────────┐
│ 🏢 Business License    ──   │   ← Strike-through indicator
│ Downtown Location           │
│ ████░░░░░░ 40%              │   ← Gray bar
│ ❌ Cancelled                 │   ← Gray status
│ Cancelled Nov 30, 2025      │
└─────────────────────────────┘
```

---

## Project Status Indicators

| Status | Icon | Color | Description |
|--------|------|-------|-------------|
| In Progress | 🔄 | Blue | Active, steps being worked |
| Action Needed | ⚡ | Orange | User has pending tasks |
| Waiting | ⏳ | Gray | Waiting for agency response |
| Completed | ✅ | Green | All steps done |
| Cancelled | ❌ | Gray | User cancelled project |
| Error | ⚠️ | Red | Something failed |

---

## Project Creation Flow

Projects are created through **conversation**, not forms. The user starts talking, and a project is created contextually.

### Step 1: Initiate Conversation

User clicks "+ New" or starts typing in an empty state.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   🤖 Hi! I'm here to help you with LA city services.                        │
│                                                                              │
│      What can I help you with today?                                        │
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │ I want to install solar panels on my house                         │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Step 2: Agent Creates Project

The agent recognizes the intent and creates a project automatically.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   👤 I want to install solar panels on my house                             │
│                                                                              │
│   🤖 I'd be happy to help you with solar panel installation!                │
│                                                                              │
│      I've started a project to track this. First, I'll need                 │
│      some information:                                                       │
│                                                                              │
│      📍 What's your property address?                                        │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │ 123 Main St, Los Angeles                                         │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Step 3: Project Appears in List

```
┌─────────────────────────────┐
│ PROJECTS              [+]   │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ 🏠 Solar Installation   │ │  ← NEW project created
│ │ 123 Main St             │ │
│ │ ░░░░░░░░░░ 0%           │ │
│ │ 🆕 Just started          │ │
│ │ Just now                │ │
│ └─────────────────────────┘ │
│                             │
│ [Previous projects...]      │
└─────────────────────────────┘
```

---

## Project Selection

### Current Project Indication

The selected project is highlighted:

```
┌─────────────────────────────┐
│ PROJECTS              [+]   │
├─────────────────────────────┤
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━┓ │  ← Selected (bold border, 
│ ┃ 🏠 Home Renovation      ┃ │     highlighted background)
│ ┃ 123 Main St             ┃ │
│ ┃ ████████░░ 80%          ┃ │
│ ┃ ⚡ 1 action needed       ┃ │
│ ┃ Updated 2 hours ago     ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                             │
│ ┌─────────────────────────┐ │  ← Unselected (normal border)
│ │ 🏢 Business License     │ │
│ │ Downtown Café           │ │
│ │ ██░░░░░░░░ 20%          │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

### Selection Behavior

| Interaction | Result |
|-------------|--------|
| Click project card | Select project, load chat + plan |
| Click current project | No change (already selected) |

---

## Search and Filter

### Search Box

```
┌─────────────────────────────┐
│ PROJECTS              [+]   │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ 🔍 permit               │ │  ← Active search
│ │                     [×] │ │  ← Clear button
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ 📋 Electrical Permit    │ │  ← Matching projects
│ └─────────────────────────┘ │
│ ┌─────────────────────────┐ │
│ │ 📋 Building Permit      │ │
│ └─────────────────────────┘ │
│                             │
│ 2 projects match "permit"   │
└─────────────────────────────┘
```

### Filter Options

Accessible via dropdown or inline filters:

```
┌─────────────────────────────┐
│ PROJECTS         [⚙️] [+]   │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ 🔍 Search...            │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ Filter: [All ▼]             │
│ ┌─────────────────────────┐ │
│ │ ○ All                   │ │
│ │ ● Active                │ │
│ │ ○ Needs Action          │ │
│ │ ○ Completed             │ │
│ │ ○ Cancelled             │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

---

## Project Context Menu

Right-click or long-press on a project card:

```
┌─────────────────────────────┐
│ 🏠 Home Renovation          │
│ 123 Main St                 │
├─────────────────────────────┤
│ 📋 View Details             │
│ ✏️ Rename                    │
│ 📤 Export Summary           │
│ ─────────────────────────── │
│ 🗑️ Cancel Project            │
└─────────────────────────────┘
```

### Context Actions

| Action | Description | Available When |
|--------|-------------|----------------|
| View Details | Opens project details modal | Always |
| Rename | Edit project title | Active/Waiting |
| Export Summary | Download PDF summary | Always |
| Cancel Project | Cancel with confirmation | Active/Waiting |

---

## Empty States

### No Projects

```
┌─────────────────────────────┐
│ PROJECTS              [+]   │
├─────────────────────────────┤
│                             │
│    ┌─────────────────────┐  │
│    │                     │  │
│    │    📋              │  │
│    │                     │  │
│    │  No projects yet    │  │
│    │                     │  │
│    │  Start by telling   │  │
│    │  me what you need   │  │
│    │  help with          │  │
│    │                     │  │
│    │  [+ Start New]      │  │
│    │                     │  │
│    └─────────────────────┘  │
│                             │
└─────────────────────────────┘
```

### No Search Results

```
┌─────────────────────────────┐
│ PROJECTS              [+]   │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ 🔍 xyzabc          [×]  │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│                             │
│    No projects match        │
│    "xyzabc"                 │
│                             │
│    [Clear search]           │
│                             │
└─────────────────────────────┘
```

---

## Mobile View

On mobile, the projects panel becomes a full-screen tab:

```
┌─────────────────────────────────────────┐
│ 🏛️ Projects                         [+] │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ 🔍 Search projects...               │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ 🏠 Home Renovation                  │ │
│ │ 123 Main St                         │ │
│ │ ████████░░ 80%         ⚡ 1 action  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🏢 Business License                 │ │
│ │ Downtown Café                       │ │
│ │ ██░░░░░░░░ 20%         🔄 Active   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ♻️ Bulk Pickup                      │ │
│ │ 456 Oak Ave                         │ │
│ │ ██████████ 100%        ✅ Done      │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ [📋 Projects] [💬 Chat] [📊 Plan]       │
└─────────────────────────────────────────┘
```

---

## Related Documentation

- [Overview](ui-wireframes-overview.md) - Overall layout structure
- [User Account](ui-wireframes-user-account.md) - Account creation and profile management
- [Chat Interface](ui-wireframes-chat.md) - Message handling
- [Plan Widget](ui-wireframes-plan-widget.md) - Project plan visualization
