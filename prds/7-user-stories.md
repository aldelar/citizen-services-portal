# User Stories

This document captures user stories for the Citizen Services Portal, organized by feature area.

---

## Project Panel

The Project Panel is the left-side navigation area where users manage their projects. Each project represents a conversation thread with the AI agent around a specific city service need.

### U1: Create a New Project

**As a** citizen user  
**I want to** click the "+" button to create a new project  
**So that** I can start a fresh conversation with the agent about a new city service need

**Acceptance Criteria:**
- Clicking the "+" button immediately creates a new project
- The new project is assigned an auto-generated title (format: YYMMDD-HHMM)
- The new project appears at the top of the project list
- The chat panel opens and is ready for the user to type their first message
- The new project is automatically selected (highlighted in the list)
- The project is persisted to CosmosDB upon creation

---

### U2: View Project Status Icons

**As a** citizen user  
**I want to** see a status icon on each project card  
**So that** I can quickly understand the state of each project at a glance

**Acceptance Criteria:**
- Each project displays a status icon based on its current state
- Status icons and their meanings:
  | Status | Icon | Color | Description |
  |--------|------|-------|-------------|
  | In Progress | `sync` | Blue | Active project with ongoing conversation |
  | Completed | `check_circle` | Green | User marked project as complete |
  | Cancelled | `cancel` | Gray | User cancelled the project |
- The status icon appears to the left of the project title
- Status icons are visually distinct and easy to differentiate

---

### U3: Cancel a Project

**As a** citizen user  
**I want to** cancel a project that I no longer need  
**So that** I can close out projects that are no longer relevant while preserving the conversation history

**Acceptance Criteria:**
- User can cancel a project via a context menu or action button
- A confirmation dialog appears before cancellation: "Are you sure you want to cancel this project? You will no longer be able to send messages."
- Once cancelled:
  - The project status changes to "Cancelled"
  - The project card displays the cancelled icon (gray `cancel`)
  - The chat becomes read-only (message input is disabled)
  - A visual indicator shows the chat is read-only (e.g., grayed out input area with text "This project has been cancelled")
  - The project remains visible in the project list for reference
- Cancellation is persisted to CosmosDB
- Cancelled projects cannot be un-cancelled (one-way action)

---

### U4: Mark a Project as Complete

**As a** citizen user  
**I want to** mark a project as complete when I've accomplished my goal  
**So that** I can close out successful projects while preserving the conversation history

**Acceptance Criteria:**
- User can mark a project complete via a context menu or action button
- A confirmation dialog appears: "Mark this project as complete? You will no longer be able to send messages."
- Once completed:
  - The project status changes to "Completed"
  - The project card displays the completed icon (green `check_circle`)
  - The chat becomes read-only (message input is disabled)
  - A visual indicator shows the chat is read-only (e.g., grayed out input area with text "This project has been completed")
  - The project remains visible in the project list for reference
- Completion is persisted to CosmosDB
- Completed projects cannot be re-opened (one-way action)

---

### U5: Projects Ordered by Recent Activity

**As a** citizen user  
**I want to** see my most recently active projects at the top of the list  
**So that** I can quickly access the projects I'm currently working on

**Acceptance Criteria:**
- Projects are sorted by `updated_at` timestamp in descending order (newest first)
- The `updated_at` timestamp is updated whenever:
  - A new message is sent or received in the project
  - The project status changes
  - The project title is edited
- When a project receives new activity, it moves to the top of the list
- The sort order persists across page refreshes
- New projects appear at the top of the list (since they have the most recent creation time)

---

### U6: Scrollable Project List

**As a** citizen user  
**I want to** scroll through my projects when I have many of them  
**So that** I can access all my projects without the panel overflowing or breaking the layout

**Acceptance Criteria:**
- The project list area is scrollable when projects exceed the visible area
- The scroll is contained within the project panel (does not affect the overall page layout)
- The "PROJECTS" header with the "+" button remains fixed at the top (does not scroll)
- Smooth scrolling behavior
- Scrollbar is visible when hovering over the panel (or always visible on touch devices)
- The chat panel and other UI elements are not affected by project list scrolling

---

### U7: Edit Project Title

**As a** citizen user  
**I want to** edit the project title after the project is created  
**So that** I can give my project a meaningful name that reflects its purpose

**Acceptance Criteria:**
- The project title is displayed in the chat header when a project is selected
- Clicking on the title (or an edit icon next to it) enables inline editing
- An input field replaces the title text, pre-filled with the current title
- User can:
  - Type a new title
  - Press Enter or click away to save
  - Press Escape to cancel without saving
- The title is limited to 100 characters
- Empty titles are not allowed (revert to previous title if user clears it)
- The updated title is reflected in:
  - The chat header
  - The project card in the project list
- The title change updates the `updated_at` timestamp (moving the project up in the list per U5)
- The new title is persisted to CosmosDB
- Title editing is disabled for cancelled and completed projects (read-only)

---

## Future Sections

*(Additional user story sections will be added here as features are defined)*

- Chat Interface
- Plan Widget
- User Account
- Agency Integration
