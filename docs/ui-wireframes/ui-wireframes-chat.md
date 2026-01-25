# UI Wireframes: Chat Interface

This document defines the chat interface in the center panel, including message types, streaming behavior, and input handling.

---

## Overview

The Chat Interface is the **primary interaction point** between the citizen and the AI agent. All communication flows through this panel—the agent guides users, answers questions, executes actions, and requests user tasks.

---

## Chat Panel Structure

```
┌───────────────────────────────────────────────────────────────┐
│ 💬 Home Renovation - 123 Main St                      [⋮]    │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│   Message History (scrollable)                                │
│   ┌─────────────────────────────────────────────────────────┐ │
│   │                                                         │ │
│   │   [Messages render here]                                │ │
│   │                                                         │ │
│   └─────────────────────────────────────────────────────────┘ │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────┬───┐ │
│ │ Type your message...                                  │ → │ │
│ └───────────────────────────────────────────────────────┴───┘ │
└───────────────────────────────────────────────────────────────┘
```

---

## Message Types

Based on the MCP server specifications and architecture, the chat must handle these message types:

### 1. User Message

Standard message from the citizen.

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│                     I want to install solar panels and      │ │
│                     battery storage on my house at           │ │
│                     123 Main St                        👤    │
│                                                     10:30 AM │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

#### Visual Treatment
- Right-aligned
- User avatar (initials or image)
- Background: user color (blue tint)
- Timestamp below or on hover

---

### 2. Agent Text Response

Standard response from the AI agent.

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   🤖  I'd be happy to help you with solar installation!     │
│                                                               │
│       Based on your address, you'll need:                    │
│       • Electrical permit from LADBS                         │
│       • Interconnection agreement with LADWP                 │
│       • Possibly a building permit for roof work             │
│                                                               │
│       Let me check the specific requirements for your area.  │
│                                                     10:31 AM │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

#### Visual Treatment
- Left-aligned
- Agent avatar (🤖 or branded icon)
- Background: neutral (light gray)
- Supports markdown formatting

---

### 3. Agent Thinking/Processing

Shown when the agent is executing tools or processing.

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   🤖  ●●●              │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

#### Visual Treatment
- Animated dots or spinner
- Disappears when response starts streaming

---

### 4. Knowledge Citation

When the agent references indexed documents.

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   🤖  According to LADBS requirements, solar PV systems      │
│       require:                                               │
│                                                               │
│       > "For systems over 10kW, a structural engineering     │
│       > analysis is required to verify roof capacity"        │
│                                                               │
│       📄 Source: LADBS Solar Permit Guide, Section 3.2       │
│          [View source ↗]                                     │
│                                                               │
│                                                     10:32 AM │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

#### Visual Treatment
- Quote block with distinct styling
- Source attribution with link
- Expandable to show more context

---

### 5. Status Update

System notifications about process changes.

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   ────────────── ✅ Status Update ──────────────             │
│                                                               │
│   📋 Permit P1 submitted successfully                        │
│      Permit #: 2026-001234                                   │
│      Status: Under Review                                    │
│      Estimated review time: 4-6 weeks                        │
│                                                     10:45 AM │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

#### Visual Treatment
- Centered with divider lines
- Success: green accent
- Info: blue accent
- Icon indicates update type

---

### 6. Error Message

When something fails.

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   ────────────── ⚠️ Error ──────────────                     │
│                                                               │
│   ❌ Failed to connect to LADWP service                      │
│                                                               │
│      The LADWP system is temporarily unavailable.            │
│                                                               │           │
│                                                     10:48 AM │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

#### Visual Treatment
- Red/orange accent
- Error icon
- Actionable buttons when possible
- Technical details expandable

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

When the agent generates responses, text streams token-by-token:

### Typing Indicator (Before Response)

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   🤖  ● ● ●                                                  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Streaming Response

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   🤖  Based on your address, I can see that you'll need▌     │
│                                                               │
└───────────────────────────────────────────────────────────────┘

        ↓ (tokens continue arriving)

┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   🤖  Based on your address, I can see that you'll need      │
│       to work with three agencies:                           │
│                                                               │
│       • LADBS for permits▌                                   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Streaming Behavior

| Behavior | Implementation |
|----------|----------------|
| Cursor indicator | Blinking cursor at stream end |
| Auto-scroll | Keep latest content visible |
| "New messages" | Button appears when paused and new content arrives |
| Completion | Remove cursor, finalize message |

---

## Input Area

### Standard Input

```
┌───────────────────────────────────────────────────────────────┐
│ ┌───────────────────────────────────────────────────────┬───┐ │
│ │ Type your message...                                  │ → │ │
│ └───────────────────────────────────────────────────────┴───┘ │
└───────────────────────────────────────────────────────────────┘
```

### Expanded Input (Multiline)

```
┌───────────────────────────────────────────────────────────────┐
│ ┌───────────────────────────────────────────────────────┬───┐ │
│ │ I have some details about my project. The property    │   │ │
│ │ is a 2-story home built in 1985. I want to:          │   │ │
│ │                                                       │   │ │
│ │ - Install solar panels (8-10 kW system)              │   │ │
│ │ - Add battery storage                                 │   │ │
│ │ - Replace gas furnace with heat pump                 │ → │ │
│ └───────────────────────────────────────────────────────┴───┘ │
└───────────────────────────────────────────────────────────────┘
```

### Input States

| State | Visual Treatment |
|-------|------------------|
| Empty | Placeholder text, send disabled |
| Typing | Active border, send enabled |
| Disabled | Grayed out (during streaming or processing) |
| Error | Red border, error message above |

---

## Chat Header

### Header Components

```
┌───────────────────────────────────────────────────────────────┐
│ 💬 Home Renovation - 123 Main St                      [⋮]    │
│    In Progress • Started Jan 15                              │
└───────────────────────────────────────────────────────────────┘
```

| Component | Purpose |
|-----------|---------|
| Chat icon | Visual identifier |
| Project title | Context |
| Status | Current project state |
| Menu (⋮) | Actions: Export, Clear, Settings |

### Header Menu

```
┌─────────────────────────────┐
│ 📤 Export Conversation      │
│ 🔄 Start New Topic          │
│ ⚙️ Chat Settings            │
│ ─────────────────────────── │
│ ℹ️ About this assistant     │
└─────────────────────────────┘
```

---

## Scroll Behavior

### Auto-scroll Rules

1. **On new message**: Scroll to bottom if user is near bottom (within 100px)
2. **User scrolls up**: Pause auto-scroll
3. **New message while paused**: Show "New messages ↓" button
4. **Click button or scroll to bottom**: Resume auto-scroll

### New Messages Indicator

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   [Older messages above...]                                  │
│                                                               │
│   ┌─────────────────────────────────────────────────────────┐ │
│   │              ↓ New messages (3)                        │ │
│   └─────────────────────────────────────────────────────────┘ │
│                                                               │
│   🤖  Here's what I found...                                 │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────┬───┐ │
│ │ Type your message...                                  │ → │ │
│ └───────────────────────────────────────────────────────┴───┘ │
└───────────────────────────────────────────────────────────────┘
```

---

## Message Actions

### Hover Actions

Appear on message hover:

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   🤖  Based on your address, you'll need permits...         │
│                                               [📋] [👍] [👎] │
│                                                     10:31 AM │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

| Action | Icon | Purpose |
|--------|------|---------|
| Copy | 📋 | Copy message text |
| Good response | 👍 | Positive feedback |
| Bad response | 👎 | Negative feedback |

---

## Mobile Chat View

Full-screen chat with simplified controls:

```
┌─────────────────────────────────────────┐
│ ← Home Renovation                   [⋮] │
├─────────────────────────────────────────┤
│                                         │
│   🤖 Welcome back, John! I see you     │
│      have a pending task...             │
│                                         │
│                                         │
│         Yes, I called 311 and      👤  │
│         scheduled for Feb 15            │
│                                         │
│                                         │
│   🤖 Perfect! ✅ I've updated your     │
│      plan. The inspection is set        │
│      for Feb 15, 2026.                  │
│                                         │
│      What would you like to work        │
│      on next?                           │
│                                         │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────┬───┐ │
│ │ Type your message...            │ → │ │
│ └─────────────────────────────────┴───┘ │
├─────────────────────────────────────────┤
│ [📋 Projects] [💬 Chat] [📊 Plan]       │
└─────────────────────────────────────────┘
```

---

## Related Documentation

- [Overview](ui-wireframes-overview.md) - Layout structure
- [Projects](ui-wireframes-projects.md) - Project navigation
- [Plan Widget](ui-wireframes-plan-widget.md) - Plan visualization
- [User Actions](ui-wireframes-user-actions.md) - UserActionResponse handling
- [Components](ui-wireframes-components.md) - Reusable components
