# UI Wireframes: Plan Widget (Dynamic Graph)

This document defines the Plan Widget in the right panel—a **dynamic graph visualization** that renders any project plan regardless of complexity.

---

## ⚠️ Critical Understanding

The plan is **NOT a fixed list of steps**. It is a **dynamic graph** that:

1. **Varies by project type**: Home renovation, business license, utility connection—each has different steps
2. **Is generated dynamically**: The agent builds the plan based on conversation
3. **Has dependencies**: Steps are nodes with edges representing dependencies (`dependsOn[]`)
4. **Evolves over time**: New steps added, steps skipped, dependencies modified

### Data Model Reference

From the CosmosDB specification, each step is a node:

```python
class PlanStep(BaseModel):
    id: str                         # Step ID (e.g., "P1", "U1", "I1")
    title: str                      # Human-readable title
    agency: str                     # LADBS, LADWP, LASAN, or any agency
    tool_name: str                  # MCP tool used
    status: StepStatus              # not_started, in_progress, awaiting_user, completed, blocked
    depends_on: List[str] = []      # IDs of prerequisite steps (GRAPH EDGES)
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict]
    user_task: Optional[UserTask]
```

#### Step ID Convention

Step IDs are short, unique identifiers within a plan. While the format is flexible, the demo uses a convention:

| Prefix | Category | Examples |
|--------|----------|----------|
| P | Permits | P1, P2, P3 |
| U | Utility | U1, U2 |
| I | Inspection | I1, I2 |
| D | Disposal | D1, D2 |
| F | Final | F1 |
| R | Rebate | R1 |

> **Note:** Step IDs are dynamically generated. The UI should display the `title` as the primary label, with `id` shown as a secondary reference.

The `depends_on` field creates the graph edges. The widget must render these relationships visually.

---

## Plan Widget Structure

```
┌─────────────────────────────────────────┐
│ 📊 PROJECT PLAN                    [⚙️] │
├─────────────────────────────────────────┤
│ Progress: ████████░░ 80% (8/10 steps)  │
├─────────────────────────────────────────┤
│                                         │
│   ┌─────────────────────────────────┐   │
│   │                                 │   │
│   │    GRAPH VISUALIZATION         │   │
│   │    (Nodes and Edges)           │   │
│   │                                 │   │
│   │    - Zoomable                  │   │
│   │    - Pannable                  │   │
│   │    - Interactive               │   │
│   │                                 │   │
│   └─────────────────────────────────┘   │
│                                         │
├─────────────────────────────────────────┤
│ ⚡ 1 action needs your attention        │
│ [View Task]                             │
└─────────────────────────────────────────┘
```

---

## Graph Visualization

### Node (Step) Design

Each step is rendered as a node:

```
┌─────────────────────────────────┐
│  [LADBS]              [Status]  │
│  ───────────────────────────    │
│  Electrical Permit              │
│  #2026-001234                   │
│  ─────────────────              │
│  ⚡ Automated                    │
└─────────────────────────────────┘
```

### Node Anatomy

```
┌─────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                                          ┌────────────┐ │ │
│ │  Step Title (Primary Text)               │ Status     │ │ │
│ │  Reference ID (Secondary, if available)  │ Indicator  │ │ │
│ │                                          └────────────┘ │ │
│ │ ─────────────────────────────────────────────────────── │ │
│ │  Automation Level          via source                   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Node Components

| Component | Description | Source |
|-----------|-------------|--------|
| Status Indicator | Visual state (icon + color) | `step.status` |
| Step Title | Main label | `step.title` |
| Reference ID | Permit/application number | `step.result.permitNumber` etc. |
| Automation Level | ⚡ Automated or 👤 User Action | Derived from `step.user_task` |
| Source Badge | MCP server that handles this step | `step.tool_name` (muted, optional) |

---

## Node States

Each node has distinct visual treatment based on status:

### Not Started

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
  [LASAN]              ○       
  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   
  Bulky Item Pickup            
                               
  👤 User Action               
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

- **Border**: Dashed, gray
- **Background**: White/transparent
- **Status**: Empty circle
- **Color**: Gray

### Blocked

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
  [LADBS]              🔒       
  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   
  Final Inspection             
  Waiting for: I1              
                               
  👤 User Action               
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

- **Border**: Dashed, gray
- **Background**: Light gray
- **Status**: Lock icon
- **Tooltip**: Shows which dependencies are blocking

### Ready (Can Start)

```
┌─────────────────────────────────┐
│  [LADWP]              ▶        │
│  ───────────────────────────    │
│  TOU Enrollment                 │
│                                 │
│  ⚡ Automated                    │
└─────────────────────────────────┘
```

- **Border**: Solid, primary color (blue)
- **Background**: Light blue
- **Status**: Play icon
- **Subtle animation**: Pulse or glow

### In Progress

```
┌─────────────────────────────────┐
│  [LADBS]              ◐        │
│  ═══════════════════════════    │
│  Electrical Permit              │
│  Under Review                   │
│  ⚡ Automated                    │
└─────────────────────────────────┘
```

- **Border**: Solid, blue
- **Background**: Blue tint
- **Status**: Spinner or half-filled circle
- **Accent bar**: Progress indicator at top

### Awaiting User Action

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  [LADBS]              ⚡        ┃
┃  ═══════════════════════════    ┃
┃  Schedule Inspection            ┃
┃  Action needed                  ┃
┃  👤 Call 311                    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

- **Border**: Bold, orange
- **Background**: Orange tint
- **Status**: Alert/lightning icon
- **Click action**: Opens action card in chat

### Completed

```
┌─────────────────────────────────┐
│  [LADBS]              ✓        │
│  ───────────────────────────    │
│  Electrical Permit              │
│  #2026-001234                   │
│  ⚡ Automated                    │
└─────────────────────────────────┘
```

- **Border**: Solid, green
- **Background**: Green tint
- **Status**: Checkmark
- **Reference**: Shows permit/confirmation number

### Failed/Error

```
┌─────────────────────────────────┐
│  [LADWP]              ✗        │
│  ═══════════════════════════    │
│  Interconnection Submit         │
│  Connection failed              │
│  [Retry]                        │
└─────────────────────────────────┘
```

- **Border**: Solid, red
- **Background**: Red tint
- **Status**: X icon
- **Action**: Retry button if applicable

### Skipped

```
┌─────────────────────────────────┐
│  [LADBS]              ⊘        │
│  ───────────────────────────    │
│  ~~Building Permit~~            │
│  Skipped - Not required         │
│                                 │
└─────────────────────────────────┘
```

- **Border**: Solid, gray
- **Background**: Gray
- **Status**: Strikethrough icon
- **Text**: Strikethrough on title

---

## Status Summary Table

| Status | Border | Background | Icon | Action on Click |
|--------|--------|------------|------|-----------------|
| `not_started` | Dashed gray | Transparent | ○ | Show details |
| `blocked` | Dashed gray | Light gray | 🔒 | Show blockers |
| `ready` | Solid blue | Light blue | ▶ | Start step |
| `in_progress` | Solid blue | Blue tint | ◐ | Show progress |
| `awaiting_user` | Bold orange | Orange tint | ⚡ | Open action card |
| `completed` | Solid green | Green tint | ✓ | Show result |
| `failed` | Solid red | Red tint | ✗ | Show error/retry |
| `skipped` | Solid gray | Gray | ⊘ | Show reason |

---

## Edge (Dependency) Design

Edges connect nodes to show dependencies (A must complete before B):

### Arrow Styles

```
Source ──────────────────► Target
       (Step A)            (Step B depends on A)
```

### Edge States

| Source State | Edge Style |
|--------------|------------|
| Completed | Solid line, green |
| In Progress | Dashed line, blue |
| Not Started | Dotted line, gray |
| Blocked | Dotted line, gray |
| Failed | Dashed line, red |

### Parallel Dependencies

When a step has multiple dependencies:

```
    ┌──────────┐
    │    P1    │────┐
    └──────────┘    │
                    ├──────►┌──────────┐
    ┌──────────┐    │       │    I1    │
    │    P2    │────┘       └──────────┘
    └──────────┘    │
                    │
    ┌──────────┐    │
    │    U1    │────┘
    └──────────┘
    
    (I1 depends on P1, P2, and U1 all being complete)
```

---

## Graph Layout

The widget uses a hierarchical/DAG layout where steps flow top-to-bottom based on dependencies:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│            ┌──────────┐                                     │
│            │    P1    │ Electrical Permit                   │
│            └────┬─────┘                                     │
│                 │                                           │
│        ┌────────┼────────┐                                  │
│        │        │        │                                  │
│        ▼        ▼        ▼                                  │
│   ┌────────┐ ┌────────┐ ┌────────┐                          │
│   │   P2   │ │   P3   │ │   U1   │ (Parallel steps)        │
│   └────┬───┘ └────┬───┘ └────┬───┘                          │
│        │          │          │                              │
│        └──────────┼──────────┘                              │
│                   ▼                                         │
│            ┌──────────┐                                     │
│            │    I1    │ Inspection                          │
│            └──────────┘                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Wireframes by Complexity

### Empty State (New Project)

```
┌─────────────────────────────────────────┐
│ 📊 PROJECT PLAN                    [⚙️] │
├─────────────────────────────────────────┤
│                                         │
│                                         │
│    ┌─────────────────────────────────┐  │
│    │                                 │  │
│    │           📋                    │  │
│    │                                 │  │
│    │    No plan yet                  │  │
│    │                                 │  │
│    │    As we discuss your project,  │  │
│    │    I'll build a step-by-step    │  │
│    │    plan here showing:           │  │
│    │                                 │  │
│    │    • What permits you need      │  │
│    │    • Which agencies to work with│  │
│    │    • Dependencies between steps │  │
│    │    • Your progress              │  │
│    │                                 │  │
│    └─────────────────────────────────┘  │
│                                         │
│                                         │
└─────────────────────────────────────────┘
```

### Simple Linear Plan (3-4 Steps)

Example: Bulk pickup request

```
┌─────────────────────────────────────────┐
│ 📊 PROJECT PLAN                    [⚙️] │
├─────────────────────────────────────────┤
│ Progress: ████░░░░░░ 40% (1/3 steps)   │
├─────────────────────────────────────────┤
│                                         │
│           ┌─────────────────┐           │
│           │ [LASAN]      ✓  │           │
│           │ Check Eligibility│          │
│           │ ⚡ Automated      │           │
│           └────────┬────────┘           │
│                    │                    │
│                    ▼                    │
│           ┌─────────────────┐           │
│           │ [LASAN]      ⚡  │           │
│           │ Schedule Pickup │           │
│           │ 👤 Call 311     │           │
│           └────────┬────────┘           │
│                    │                    │
│                    ▼                    │
│           ┌ ─ ─ ─ ─ ─ ─ ─ ─ ┐           │
│             [LASAN]      🔒             │
│             Confirm Pickup              │
│             ⚡ Automated                 │
│           └ ─ ─ ─ ─ ─ ─ ─ ─ ┘           │
│                                         │
├─────────────────────────────────────────┤
│ ⚡ 1 action needs your attention        │
│ [View Task]                             │
└─────────────────────────────────────────┘
```

### Medium Complexity (John's Renovation ~10 Steps)

```
┌─────────────────────────────────────────┐
│ 📊 PROJECT PLAN                    [⚙️] │
├─────────────────────────────────────────┤
│ Progress: ████████░░ 80% (8/10)        │
├─────────────────────────────────────────┤
│                                         │
│     ┌───────┐ ┌───────┐ ┌───────┐      │
│     │P1  ✓  │ │P2  ✓  │ │P3  ✓  │      │
│     │Elect. │ │Mech.  │ │Build. │      │
│     │LADBS  │ │LADBS  │ │LADBS  │      │
│     └───┬───┘ └───┬───┘ └───┬───┘      │
│         │         │         │          │
│         └────┬────┴────┬────┘          │
│              │         │               │
│              ▼         ▼               │
│        ┌───────┐ ┌───────┐             │
│        │U1  ✓  │ │U2  ◐  │             │
│        │TOU    │ │Inter- │             │
│        │LADWP  │ │connect│             │
│        └───┬───┘ └───┬───┘             │
│            │         │                 │
│            └────┬────┘                 │
│                 ▼                      │
│           ┌─────────┐                  │
│           │ I1   ⚡  │ ← ACTION        │
│           │ Inspect │                  │
│           │ LADBS   │                  │
│           └────┬────┘                  │
│        ┌───────┴───────┐               │
│        ▼               ▼               │
│   ┌───────┐       ┌───────┐            │
│   │D1  ○  │       │D2  ○  │            │
│   │Bulky  │       │E-waste│            │
│   │LASAN  │       │LASAN  │            │
│   └───┬───┘       └───┬───┘            │
│       └───────┬───────┘                │
│               ▼                        │
│         ┌───────┐                      │
│         │F1  🔒 │                      │
│         │Final  │                      │
│         │LADWP  │                      │
│         └───┬───┘                      │
│             ▼                          │
│         ┌───────┐                      │
│         │R1  🔒 │                      │
│         │Rebate │                      │
│         │LADWP  │                      │
│         └───────┘                      │
│                                         │
│ [Fit to View] [Zoom In] [Zoom Out]     │
├─────────────────────────────────────────┤
│ ⚡ 1 action needs your attention        │
│ [View Task]                             │
└─────────────────────────────────────────┘
```

### Complex Plan (15+ Steps with Branching)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📊 PROJECT PLAN                                              [⚙️]  │
├─────────────────────────────────────────────────────────────────────┤
│ Progress: ██░░░░░░░░ 25% (5/20)         Layout: [DAG ▼]           │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                                                                 │ │
│ │  START                                                          │ │
│ │    │                                                            │ │
│ │    ├────────────────┬────────────────┬────────────────┐         │ │
│ │    ▼                ▼                ▼                ▼         │ │
│ │  ┌─────┐         ┌─────┐         ┌─────┐         ┌─────┐        │ │
│ │  │ P1 ✓│         │ P2 ✓│         │ P3 ✓│         │ P4 ✓│        │ │
│ │  └──┬──┘         └──┬──┘         └──┬──┘         └──┬──┘        │ │
│ │     │               │               │               │           │ │
│ │     │               └───────┬───────┘               │           │ │
│ │     │                       │                       │           │ │
│ │     ▼                       ▼                       ▼           │ │
│ │  ┌─────┐               ┌─────┐                 ┌─────┐          │ │
│ │  │ U1 ✓│               │ U2 ◐│                 │ Z1 ○│          │ │
│ │  └──┬──┘               └──┬──┘                 └──┬──┘          │ │
│ │     │                     │                      │              │ │
│ │     └─────────┬───────────┘                      │              │ │
│ │               │         ┌────────────────────────┘              │ │
│ │               ▼         ▼                                       │ │
│ │          ┌─────┐     ┌─────┐                                    │ │
│ │          │I1 ⚡│     │ C1 ○│   ... [more nodes]                  │ │
│ │          └─────┘     └─────┘                                    │ │
│ │                                                                 │ │
│ │                      [DRAGGABLE CANVAS - ZOOM/PAN]              │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ [−] [+] [Fit] [Reset]                    Showing 20 steps          │
├─────────────────────────────────────────────────────────────────────┤
│ ⚡ 1 action needs attention   •   ⏳ 3 waiting   •   🔒 8 blocked  │
│ [View Tasks]                                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Dynamic Behavior

### Plan Building (Steps Appear During Conversation)

As the agent identifies steps, nodes animate into the graph:

```
State 1: Initial
┌───────────────────────────┐
│ 📊 PROJECT PLAN           │
│ ──────────────────────    │
│                           │
│    📋 No plan yet         │
│                           │
└───────────────────────────┘

State 2: First step identified (agent says "You'll need an electrical permit")
┌───────────────────────────┐
│ 📊 PROJECT PLAN           │
│ ──────────────────────    │
│                           │
│      ┌───────────┐        │
│      │ P1  ▶    │ ← NEW  │
│      │ Elec Pmt │        │
│      │ LADBS    │        │
│      └───────────┘        │
│                           │
└───────────────────────────┘

State 3: More steps identified
┌───────────────────────────┐
│ 📊 PROJECT PLAN           │
│ ──────────────────────    │
│                           │
│      ┌───────────┐        │
│      │ P1  ▶    │        │
│      └─────┬─────┘        │
│            │              │
│    ┌───────┴───────┐      │
│    ▼               ▼      │
│ ┌───────┐     ┌───────┐   │
│ │ U1 ○ │ NEW │ U2 ○ │NEW│
│ └───────┘     └───────┘   │
│                           │
└───────────────────────────┘
```

### Plan Updates (Status Changes)

When a step completes, the node updates in real-time:

```
Before: Step I1 in progress
┌───────────────────────────┐
│    ┌───────────┐          │
│    │ I1  ◐    │          │
│    │ Scheduling│          │
│    └───────────┘          │
└───────────────────────────┘

Animation: Brief flash/pulse

After: Step I1 completed
┌───────────────────────────┐
│    ┌───────────┐          │
│    │ I1  ✓    │          │
│    │ INS-789456│          │
│    └───────────┘          │
│           │               │
│           ▼               │
│    ┌───────────┐          │
│    │ F1  ▶    │ ← Now    │
│    │ Unlocked  │   ready  │
│    └───────────┘          │
└───────────────────────────┘
```

---

## Interactivity

### Node Click

Clicking a node shows details in a tooltip or side panel:

```
┌───────────────────────────────────────────────────────────────┐
│                               ┌─────────────────────────────┐ │
│   ┌───────────┐               │ STEP DETAILS                │ │
│   │ P1  ✓    │ ◄─────────── │ ───────────────────────────  │ │
│   │ Elec Pmt │               │ Electrical Permit            │ │
│   └───────────┘               │ Status: ✓ Completed         │ │
│                               │ Agency: LADBS               │ │
│                               │                             │ │
│                               │ Permit #: 2026-001234       │ │
│                               │ Submitted: Jan 15, 2026     │ │
│                               │ Approved: Jan 28, 2026      │ │
│                               │                             │ │
│                               │ [View in Chat]              │ │
│                               └─────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Node Actions

| Node State | Click Action |
|------------|--------------|
| Not Started | Show "This step will begin when dependencies complete" |
| Blocked | Show "Waiting for: [list of blocking steps]" |
| Ready | Show "Ready to start - [details]" |
| In Progress | Show progress details |
| Awaiting User | Open UserAction card in chat |
| Completed | Show result details |
| Failed | Show error and retry option |

### Pan and Zoom

For complex graphs:

| Control | Action |
|---------|--------|
| Scroll wheel | Zoom in/out |
| Click + drag | Pan canvas |
| Double-click node | Center on node |
| Pinch (touch) | Zoom in/out |
| Two-finger drag | Pan |

### Zoom Controls

```
┌─────────────────────────────────────────┐
│                                         │
│   [Graph visualization area]            │
│                                         │
├─────────────────────────────────────────┤
│ [−] [○○○○●○○] [+]   [Fit]   [Reset]    │
└─────────────────────────────────────────┘
```

---

## Widget Header Actions

```
┌─────────────────────────────────────────┐
│ 📊 PROJECT PLAN                    [⚙️] │
└─────────────────────────────────────────┘
```

Settings menu (⚙️):

```
┌──────────────────────────────────┐
│ Display                          │
│ ☑ Show source indicators        │
│ ☑ Show automation level         │
│ ☐ Compact mode                  │
├──────────────────────────────────┤
│ [Export as PDF]                  │
└──────────────────────────────────┘
```

---

## Source Indicators

Nodes display the MCP server source in a muted badge (e.g., "via ladbs"). This provides transparency about where data comes from without requiring users to understand the technical details. All source badges use the same muted gray styling for simplicity.

---

## Mobile Plan View

On mobile, the plan widget becomes a full-screen tab:

```
┌─────────────────────────────────────────┐
│ ← Project Plan                     [⚙️] │
├─────────────────────────────────────────┤
│ Progress: ████████░░ 80%                │
├─────────────────────────────────────────┤
│                                         │
│      [Zoomable/Pannable Graph]          │
│                                         │
│            ┌─────┐                      │
│            │ P1 ✓│                      │
│            └──┬──┘                      │
│               │                         │
│         ┌─────┴─────┐                   │
│         ▼           ▼                   │
│      ┌─────┐    ┌─────┐                 │
│      │P2 ✓│    │U1 ⚡│←                 │
│      └─────┘    └─────┘                 │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│ ⚡ 1 action needs your attention        │
│        [View Task]                      │
├─────────────────────────────────────────┤
│ [📋 Projects] [💬 Chat] [📊 Plan]       │
└─────────────────────────────────────────┘
```

---

## Accessibility

| Requirement | Implementation |
|-------------|----------------|
| Keyboard Navigation | Tab through nodes, arrow keys for edges |
| Screen Reader | Each node announced with status |
| High Contrast | Distinct colors, not color-only indicators |
| Focus Indicators | Clear visible focus on selected node |
| Alternative View | List view option for non-visual access |

---

## Related Documentation

- [Overview](ui-wireframes-overview.md) - Layout structure
- [Chat Interface](ui-wireframes-chat.md) - Where plan updates originate
- [User Actions](ui-wireframes-user-actions.md) - Handling awaiting_user steps
- [Components](ui-wireframes-components.md) - Node and badge components
