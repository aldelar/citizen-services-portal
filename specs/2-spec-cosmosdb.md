# CosmosDB Specification

This document provides detailed specifications for the Azure Cosmos DB data layer, including database structure, container schemas, partition strategies, and access patterns. Use this as the source of truth when implementing data operations.

---

## Multi-Database Architecture

The Citizen Services Portal uses a multi-database architecture where each major component has its own dedicated database within a shared CosmosDB account.

### Databases Overview

| Database | Owner | Purpose |
|----------|-------|---------|
| `citizen-services` | Agent Orchestrator | User profiles, projects, messages, step completions |
| `ladbs` | LADBS MCP Server | Permit applications, inspection records |
| `ladwp` | LADWP MCP Server | Interconnection applications, rebates, TOU enrollments |
| `lasan` | LASAN MCP Server | Pickup requests and status |

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Shared CosmosDB account** | For MVP, all databases share one account for simplified management and cost efficiency |
| **Separate databases per agency** | Enables future separation where each agency could host their own CosmosDB account |
| **Database definitions in MCP server folders** | Each agency's database Bicep is defined in `/src/mcp-servers/{agency}/infra/` |
| **User reference pattern** | Agency databases reference `userId` from the central orchestrator (no duplicate user storage) |

### Future Considerations

- Each agency can migrate to their own CosmosDB account without schema changes
- Cross-database references use `userId` as the linking key
- No user PII is duplicated across databases; only `userId` is stored

---

## Overview

The Citizen Services Portal uses Azure Cosmos DB with the NoSQL API to store:
- User profiles
- Projects with embedded plans
- Conversation history (messages)
- Step completion metrics for reporting
- Agency-specific data (permits, interconnections, pickups, etc.)

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Plan inside Project** | Simpler than separate collection; one read gets everything |
| **Messages separate** | Conversations can grow large; efficient pagination |
| **One conversation per project** | All context in one thread; user returns and continues |
| **Anonymized metrics** | Step completions contain no PII, only timing data |

---

## Database Configuration

### Account Settings

| Setting | Value | Rationale |
|---------|-------|-----------|
| **API** | NoSQL (Core) | Best for document-oriented data with flexible schemas |
| **Capacity Mode** | Serverless | Cost-effective for demo/MVP with variable workloads |
| **Consistency Level** | Session | Balances consistency with performance; user sees their own writes |
| **Region** | Single region | Sufficient for demo; expand for production |
| **Automatic Failover** | Disabled | Not needed for serverless in single region |

### Database

| Property | Value |
|----------|-------|
| **Database Name** | `citizen-services` |
| **Throughput** | Serverless (automatic) |

---

## Containers

### Container Summary

| Container | Partition Key | Purpose | TTL |
|-----------|---------------|---------|-----|
| `users` | `/id` | User profiles | None |
| `projects` | `/userId` | Projects with inline plans | None |
| `messages` | `/projectId` | Conversation history | Optional (365 days for completed projects) |
| `step_completions` | `/toolName` | Anonymized step timing for reporting | 180 days |

---

## Container: `users`

Stores user profile information.

### Partition Strategy

- **Partition Key:** `/id`
- **Rationale:** Each user is accessed independently; user ID provides excellent distribution

### Schema

```json
{
  "id": "user-uuid",
  "email": "john@example.com",
  "name": "John Smith",
  "phone": "555-0123",
  "createdAt": "2026-01-15T10:00:00Z",
  "lastLoginAt": "2026-02-01T14:30:00Z",
  "preferences": {
    "notificationEmail": true,
    "preferredContactMethod": "email"
  }
}
```

### Model Definition

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserPreferences(BaseModel):
    """User preferences for notifications and contact."""
    notification_email: bool = True
    preferred_contact_method: str = "email"  # "email", "phone", "sms"

class User(BaseModel):
    """User profile document."""
    id: str                           # UUID, also partition key
    email: EmailStr                   # User's email address
    name: str                         # Display name
    phone: Optional[str] = None       # Phone number
    created_at: datetime              # Account creation time
    last_login_at: Optional[datetime] = None  # Last login timestamp
    preferences: UserPreferences = UserPreferences()
```

### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Get user by ID | Point read by `id` | 1 RU |
| Get user by email | Query `WHERE c.email = @email` | 3-5 RU |
| Update last login | Point write by `id` | 5-10 RU |

### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/email/?" },
      { "path": "/createdAt/?" }
    ],
    "excludedPaths": [
      { "path": "/preferences/*" },
      { "path": "/_etag/?" }
    ]
  }
}
```

---

## Container: `projects`

Stores projects with embedded plans. This is the primary container for tracking user journeys.

### Partition Strategy

- **Partition Key:** `/userId`
- **Rationale:** All projects for a user are co-located; enables efficient "list my projects" queries

### Schema

```json
{
  "id": "project-uuid",
  "userId": "user-uuid",
  "title": "Home Renovation - 123 Main St",
  "status": "active",
  "createdAt": "2026-01-15T10:00:00Z",
  "updatedAt": "2026-02-01T14:30:00Z",
  
  "context": {
    "address": "123 Main St, Los Angeles, CA 90012",
    "projectType": "home_renovation",
    "description": "Solar panels, battery, heat pumps, metal roof"
  },
  
  "plan": {
    "id": "plan-uuid",
    "title": "Home Renovation - Solar & Heat Pumps",
    "status": "active",
    "steps": [
      {
        "id": "P1",
        "title": "Electrical Permit",
        "agency": "LADBS",
        "toolName": "permits.submit",
        "status": "completed",
        "dependsOn": [],
        "startedAt": "2026-01-15T10:00:00Z",
        "completedAt": "2026-01-28T14:30:00Z",
        "result": {
          "permitNumber": "2026-001234"
        }
      },
      {
        "id": "I1",
        "title": "Schedule Rough Inspection",
        "agency": "LADBS",
        "toolName": "inspections.schedule",
        "status": "awaiting_user",
        "dependsOn": ["P1"],
        "userTask": {
          "type": "phone_call",
          "target": "311",
          "assignedAt": "2026-02-01T10:00:00Z"
        }
      }
    ]
  },
  
  "references": {
    "permits": {
      "electrical": "2026-001234",
      "mechanical": "2026-001235"
    },
    "accounts": {
      "ladwp": "1234567890"
    }
  },
  
  "summary": {
    "totalSteps": 10,
    "completed": 4,
    "awaitingUser": 2,
    "notStarted": 4
  }
}
```

### Model Definitions

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class ProjectStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class StepStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AWAITING_USER = "awaiting_user"
    COMPLETED = "completed"
    BLOCKED = "blocked"

class Agency(str, Enum):
    LADBS = "LADBS"
    LADWP = "LADWP"
    LASAN = "LASAN"

class UserTaskType(str, Enum):
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    IN_PERSON = "in_person"
    ONLINE_PORTAL = "online_portal"

class UserTask(BaseModel):
    """Details for user-action steps."""
    type: UserTaskType
    target: str                        # "311", email, URL, or location
    assigned_at: datetime
    prepared_materials: Optional[Dict[str, Any]] = None

class PlanStep(BaseModel):
    """A single step in the project plan."""
    id: str                            # Short ID (P1, U1, I1, etc.)
    title: str                         # Human-readable step name
    agency: Agency                     # Which agency this step involves
    tool_name: str                     # Normalized MCP tool name (e.g., "permits.submit")
    status: StepStatus
    depends_on: List[str] = []         # IDs of prerequisite steps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None  # Outcome data (permit numbers, etc.)
    user_task: Optional[UserTask] = None     # Present when status is awaiting_user
    blocked_reason: Optional[str] = None     # Present when status is blocked

class Plan(BaseModel):
    """The project plan with all steps."""
    id: str
    title: str
    status: str                        # "active", "completed"
    steps: List[PlanStep]

class ProjectContext(BaseModel):
    """Context information about the project."""
    address: str
    project_type: str                  # "home_renovation", "business_permit", etc.
    description: Optional[str] = None

class ProjectSummary(BaseModel):
    """Quick summary of plan progress."""
    total_steps: int
    completed: int
    awaiting_user: int
    not_started: int

class ProjectReferences(BaseModel):
    """Quick lookup of key identifiers."""
    permits: Dict[str, str] = {}       # {"electrical": "2026-001234"}
    accounts: Dict[str, str] = {}      # {"ladwp": "1234567890"}
    applications: Dict[str, str] = {}  # {"interconnection": "IA-2026-123"}

class Project(BaseModel):
    """Project document with embedded plan."""
    id: str
    user_id: str                       # Partition key
    title: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    context: ProjectContext
    plan: Plan
    references: ProjectReferences = ProjectReferences()
    summary: ProjectSummary
```

### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Get project by ID | Point read with partition key `userId` | 1 RU |
| List user's projects | Query `WHERE c.userId = @userId` | 3-10 RU |
| List active projects | Query `WHERE c.userId = @userId AND c.status = "active"` | 3-10 RU |
| Update plan step | Partial update (patch) by `id` | 10-20 RU |
| Get project by permit | Query `WHERE c.references.permits.electrical = @permitNum` | 5-15 RU |

### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/userId/?" },
      { "path": "/status/?" },
      { "path": "/createdAt/?" },
      { "path": "/updatedAt/?" },
      { "path": "/context/address/?" },
      { "path": "/references/permits/*/?" },
      { "path": "/plan/steps/[]/status/?" }
    ],
    "excludedPaths": [
      { "path": "/plan/steps/[]/userTask/*" },
      { "path": "/plan/steps/[]/result/*" },
      { "path": "/_etag/?" }
    ],
    "compositeIndexes": [
      [
        { "path": "/userId", "order": "ascending" },
        { "path": "/status", "order": "ascending" },
        { "path": "/updatedAt", "order": "descending" }
      ]
    ]
  }
}
```

---

## Container: `messages`

Stores conversation history for each project.

### Partition Strategy

- **Partition Key:** `/projectId`
- **Rationale:** All messages for a conversation are co-located; enables efficient history retrieval

### Schema

#### User Message

```json
{
  "id": "msg-uuid",
  "projectId": "project-uuid",
  "role": "user",
  "content": "Yes! Scheduled for Feb 15, confirmation INS-789456",
  "timestamp": "2026-02-01T14:32:00Z"
}
```

#### Assistant Message

```json
{
  "id": "msg-uuid-2",
  "projectId": "project-uuid",
  "role": "assistant",
  "content": "Perfect! ✅ I've updated your plan. Inspection scheduled: Feb 15, 2026 (INS-789456)",
  "timestamp": "2026-02-01T14:32:05Z",
  "toolCalls": [
    {
      "tool": "inspections.scheduled",
      "input": { "permitNumber": "2026-001234" },
      "output": { 
        "inspections": [
          {
            "inspection_id": "INS-789456",
            "scheduled_date": "2026-02-15",
            "type": "rough_electrical"
          }
        ]
      },
      "duration_ms": 245
    }
  ],
  "model": "gpt-4o",
  "tokens": {
    "prompt": 1250,
    "completion": 180
  }
}
```

### Model Definitions

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

class ToolCall(BaseModel):
    """Record of a tool invocation during message generation."""
    tool: str                          # MCP tool name (e.g., "permits.search")
    input: Dict[str, Any]              # Input parameters
    output: Dict[str, Any]             # Tool response
    duration_ms: int                   # Execution time

class TokenUsage(BaseModel):
    """Token usage for assistant messages."""
    prompt: int
    completion: int

class Message(BaseModel):
    """Chat message document."""
    id: str
    project_id: str                    # Partition key
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    
    # Assistant message fields (optional)
    tool_calls: Optional[List[ToolCall]] = None
    model: Optional[str] = None        # Model used (e.g., "gpt-4o")
    tokens: Optional[TokenUsage] = None
```

### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Get recent messages | Query `WHERE c.projectId = @id ORDER BY c.timestamp DESC` with LIMIT | 3-10 RU |
| Get full history | Query `WHERE c.projectId = @id ORDER BY c.timestamp ASC` | 10-50 RU |
| Append message | Point write | 5-10 RU |
| Count messages | Query `SELECT VALUE COUNT(1) FROM c WHERE c.projectId = @id` | 3-5 RU |

### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/projectId/?" },
      { "path": "/timestamp/?" },
      { "path": "/role/?" }
    ],
    "excludedPaths": [
      { "path": "/content/?" },
      { "path": "/toolCalls/*" },
      { "path": "/_etag/?" }
    ]
  }
}
```

### TTL Policy

For completed projects, messages can be retained for a defined period:

```json
{
  "defaultTtl": -1,
  "analyticalStorageTtl": -1
}
```

- **Active projects:** No TTL (defaultTtl = -1)
- **Completed projects:** Optionally set `ttl` field on documents to 31536000 (365 days)

---

## Container: `step_completions`

Stores anonymized step completion records for reporting. Used by the Reporting MCP Server.

### Partition Strategy

- **Partition Key:** `/toolName`
- **Rationale:** Queries aggregate by tool type; co-locates all completions for a given tool

### Schema

```json
{
  "id": "completion-uuid",
  "toolName": "permits.submit",
  "city": "Los Angeles",
  "startedAt": "2026-01-15T10:00:00Z",
  "completedAt": "2026-01-28T14:30:00Z",
  "durationDays": 13.2,
  "ttl": 15552000
}
```

### Model Definition

```python
from pydantic import BaseModel
from datetime import datetime

class StepCompletion(BaseModel):
    """Anonymized step completion record for reporting."""
    id: str
    tool_name: str                     # Partition key, normalized MCP tool name
    city: str                          # Geographic filter
    started_at: datetime
    completed_at: datetime
    duration_days: float               # Calculated: (completed_at - started_at).days
    ttl: int = 15552000                # 180 days in seconds
```

### Normalized Tool Names

Step completions use normalized MCP tool names for consistent aggregation:

| toolName | Description |
|----------|-------------|
| `permits.submit` | Permit application (any type) |
| `permits.getStatus` | Permit status check |
| `inspections.schedule` | Schedule an inspection |
| `tou.enroll` | TOU rate enrollment |
| `interconnection.submit` | Solar interconnection application |
| `rebates.apply` | Rebate application |
| `pickup.schedule` | Waste pickup scheduling |

### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Log completion | Point write | 5-10 RU |
| Get average duration | Aggregate query (see below) | 10-30 RU |

### Average Duration Query

```sql
SELECT 
  AVG(c.durationDays) AS avgDays, 
  COUNT(1) AS sampleCount
FROM c
WHERE c.toolName = @toolName
  AND c.city = @city
  AND c.completedAt > @sixMonthsAgo
```

### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/toolName/?" },
      { "path": "/city/?" },
      { "path": "/completedAt/?" },
      { "path": "/durationDays/?" }
    ],
    "excludedPaths": [
      { "path": "/_etag/?" }
    ]
  }
}
```

### TTL Policy

```json
{
  "defaultTtl": 15552000
}
```

Records automatically expire after 180 days (6 months) to keep the dataset relevant.

---

## LADBS Database

The LADBS (Los Angeles Department of Building and Safety) database stores permit applications and inspection records.

### Database Configuration

| Property | Value |
|----------|-------|
| **Database Name** | `ladbs` |
| **Throughput** | Serverless (automatic) |

### Container Summary

| Container | Partition Key | Purpose | TTL |
|-----------|---------------|---------|-----|
| `permits` | `/userId` | Permit applications and status | None |
| `inspections` | `/permitNumber` | Inspection records linked to permits | None |

---

### Container: `permits`

Stores permit applications and their status.

#### Partition Strategy

- **Partition Key:** `/userId`
- **Rationale:** Users typically query their own permits; enables efficient "list my permits" queries

#### Schema

```json
{
  "id": "permit-uuid",
  "userId": "user-uuid",
  "permitNumber": "2026-001234",
  "permitType": "electrical",
  "status": "submitted",
  "address": "123 Main St, Los Angeles, CA 90012",
  "workDescription": "Solar PV installation with battery storage",
  "estimatedCost": 25000.00,
  "applicant": {
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "555-0123",
    "contractorLicense": "C10-123456"
  },
  "documents": ["site-plan.pdf", "single-line-diagram.pdf"],
  "fees": {
    "planCheck": 450.00,
    "permitFee": 800.00,
    "otherFees": 0.00,
    "total": 1250.00
  },
  "submittedAt": "2026-01-15T10:00:00Z",
  "approvedAt": null,
  "expiresAt": null,
  "nextSteps": "Awaiting plan check review",
  "createdAt": "2026-01-15T10:00:00Z",
  "updatedAt": "2026-01-15T10:00:00Z"
}
```

#### Model Definition

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PermitType(str, Enum):
    """Type of building permit."""
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    BUILDING = "building"
    PLUMBING = "plumbing"


class PermitStatus(str, Enum):
    """Status of a permit application."""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CORRECTIONS_REQUIRED = "corrections_required"
    APPROVED = "approved"
    ISSUED = "issued"
    EXPIRED = "expired"
    REJECTED = "rejected"


class PermitApplicant(BaseModel):
    """Applicant information for a permit."""
    name: str
    email: str
    phone: str
    contractor_license: Optional[str] = None


class PermitFees(BaseModel):
    """Fee breakdown for a permit."""
    plan_check: float
    permit_fee: float
    other_fees: float = 0.0
    total: float


class PermitDocument(BaseModel):
    """Permit document stored in the database."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    user_id: str = Field(alias="userId")
    permit_number: str = Field(alias="permitNumber")
    permit_type: PermitType = Field(alias="permitType")
    status: PermitStatus
    address: str
    work_description: str = Field(alias="workDescription")
    estimated_cost: float = Field(alias="estimatedCost")
    applicant: PermitApplicant
    documents: List[str] = Field(default_factory=list)
    fees: Optional[PermitFees] = None
    submitted_at: Optional[datetime] = Field(default=None, alias="submittedAt")
    approved_at: Optional[datetime] = Field(default=None, alias="approvedAt")
    expires_at: Optional[datetime] = Field(default=None, alias="expiresAt")
    next_steps: Optional[str] = Field(default=None, alias="nextSteps")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
```

#### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Get permit by ID | Point read with partition key `userId` | 1 RU |
| List user's permits | Query `WHERE c.userId = @userId` | 3-10 RU |
| Get by permit number | Query `WHERE c.permitNumber = @permitNumber` | 5-10 RU |
| Search by address | Query `WHERE c.address = @address` | 5-15 RU |
| Update status | Point write by `id` | 5-10 RU |

#### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/userId/?" },
      { "path": "/permitNumber/?" },
      { "path": "/status/?" },
      { "path": "/address/?" },
      { "path": "/permitType/?" },
      { "path": "/submittedAt/?" },
      { "path": "/createdAt/?" }
    ],
    "excludedPaths": [
      { "path": "/applicant/*" },
      { "path": "/documents/*" },
      { "path": "/fees/*" },
      { "path": "/_etag/?" }
    ]
  }
}
```

---

### Container: `inspections`

Stores inspection records linked to permits.

#### Partition Strategy

- **Partition Key:** `/permitNumber`
- **Rationale:** Inspections are typically queried by permit; enables efficient "list inspections for permit" queries

#### Schema

```json
{
  "id": "inspection-uuid",
  "permitNumber": "2026-001234",
  "userId": "user-uuid",
  "inspectionId": "INS-789456",
  "inspectionType": "rough_electrical",
  "status": "scheduled",
  "address": "123 Main St, Los Angeles, CA 90012",
  "scheduledDate": "2026-02-15",
  "scheduledTimeWindow": "8am-12pm",
  "completedAt": null,
  "result": null,
  "inspectorNotes": null,
  "contactName": "John Smith",
  "contactPhone": "555-0123",
  "createdAt": "2026-02-01T10:00:00Z",
  "updatedAt": "2026-02-01T10:00:00Z"
}
```

#### Model Definition

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class InspectionType(str, Enum):
    """Type of building inspection."""
    ROUGH_ELECTRICAL = "rough_electrical"
    FINAL_ELECTRICAL = "final_electrical"
    ROUGH_MECHANICAL = "rough_mechanical"
    FINAL_MECHANICAL = "final_mechanical"
    FRAMING = "framing"
    FINAL = "final"


class InspectionStatus(str, Enum):
    """Status of an inspection."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InspectionDocument(BaseModel):
    """Inspection document stored in the database."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    permit_number: str = Field(alias="permitNumber")
    user_id: str = Field(alias="userId")
    inspection_id: str = Field(alias="inspectionId")
    inspection_type: InspectionType = Field(alias="inspectionType")
    status: InspectionStatus
    address: str
    scheduled_date: Optional[str] = Field(default=None, alias="scheduledDate")
    scheduled_time_window: Optional[str] = Field(default=None, alias="scheduledTimeWindow")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt")
    result: Optional[str] = None
    inspector_notes: Optional[str] = Field(default=None, alias="inspectorNotes")
    contact_name: str = Field(alias="contactName")
    contact_phone: str = Field(alias="contactPhone")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
```

#### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Get inspection by ID | Point read with partition key `permitNumber` | 1 RU |
| List inspections for permit | Query `WHERE c.permitNumber = @permitNumber` | 3-10 RU |
| Search by address | Query `WHERE c.address = @address` | 5-15 RU |
| Update status | Point write by `id` | 5-10 RU |

#### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/permitNumber/?" },
      { "path": "/userId/?" },
      { "path": "/inspectionId/?" },
      { "path": "/status/?" },
      { "path": "/address/?" },
      { "path": "/scheduledDate/?" },
      { "path": "/createdAt/?" }
    ],
    "excludedPaths": [
      { "path": "/_etag/?" }
    ]
  }
}
```

---

## LADWP Database

The LADWP (Los Angeles Department of Water and Power) database stores interconnection applications, rebate applications, and TOU enrollments.

### Database Configuration

| Property | Value |
|----------|-------|
| **Database Name** | `ladwp` |
| **Throughput** | Serverless (automatic) |

### Container Summary

| Container | Partition Key | Purpose | TTL |
|-----------|---------------|---------|-----|
| `interconnections` | `/userId` | Solar interconnection applications | None |
| `rebates` | `/userId` | Rebate applications | None |
| `tou_enrollments` | `/accountNumber` | TOU rate plan enrollments | None |

---

### Container: `interconnections`

Stores solar interconnection applications.

#### Partition Strategy

- **Partition Key:** `/userId`
- **Rationale:** Users query their own interconnection applications

#### Schema

```json
{
  "id": "interconnection-uuid",
  "userId": "user-uuid",
  "applicationId": "IA-2026-12345",
  "address": "123 Main St, Los Angeles, CA 90012",
  "systemSizeKw": 8.5,
  "batterySizeKwh": 13.5,
  "status": "submitted",
  "applicant": {
    "name": "John Smith",
    "email": "john@example.com"
  },
  "equipment": {
    "inverter": "SolarEdge SE7600H",
    "panels": "REC Alpha Pure 400W x 22",
    "battery": "Tesla Powerwall 2"
  },
  "ladbsPermitNumber": "2026-001234",
  "submittedAt": "2026-01-20T10:00:00Z",
  "approvedAt": null,
  "ptoDate": null,
  "nextSteps": "Awaiting engineering review",
  "createdAt": "2026-01-20T10:00:00Z",
  "updatedAt": "2026-01-20T10:00:00Z"
}
```

#### Model Definition

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class InterconnectionStatus(str, Enum):
    """Status of solar interconnection application."""
    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    ENGINEERING_REVIEW = "engineering_review"
    APPROVED = "approved"
    PTO_ISSUED = "pto_issued"
    DENIED = "denied"


class InterconnectionApplicant(BaseModel):
    """Applicant information for interconnection."""
    name: str
    email: str


class InterconnectionEquipment(BaseModel):
    """Equipment details for interconnection."""
    inverter: str
    panels: str
    battery: Optional[str] = None


class InterconnectionDocument(BaseModel):
    """Interconnection document stored in the database."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    user_id: str = Field(alias="userId")
    application_id: str = Field(alias="applicationId")
    address: str
    system_size_kw: float = Field(alias="systemSizeKw")
    battery_size_kwh: Optional[float] = Field(default=None, alias="batterySizeKwh")
    status: InterconnectionStatus
    applicant: InterconnectionApplicant
    equipment: InterconnectionEquipment
    ladbs_permit_number: Optional[str] = Field(default=None, alias="ladbsPermitNumber")
    submitted_at: Optional[datetime] = Field(default=None, alias="submittedAt")
    approved_at: Optional[datetime] = Field(default=None, alias="approvedAt")
    pto_date: Optional[datetime] = Field(default=None, alias="ptoDate")
    next_steps: Optional[str] = Field(default=None, alias="nextSteps")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
```

#### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Get interconnection by ID | Point read with partition key `userId` | 1 RU |
| List user's interconnections | Query `WHERE c.userId = @userId` | 3-10 RU |
| Get by application ID | Query `WHERE c.applicationId = @applicationId` | 5-10 RU |
| Update status | Point write by `id` | 5-10 RU |

#### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/userId/?" },
      { "path": "/applicationId/?" },
      { "path": "/status/?" },
      { "path": "/address/?" },
      { "path": "/submittedAt/?" },
      { "path": "/createdAt/?" }
    ],
    "excludedPaths": [
      { "path": "/applicant/*" },
      { "path": "/equipment/*" },
      { "path": "/_etag/?" }
    ]
  }
}
```

---

### Container: `rebates`

Stores rebate applications.

#### Partition Strategy

- **Partition Key:** `/userId`
- **Rationale:** Users query their own rebate applications

#### Schema

```json
{
  "id": "rebate-uuid",
  "userId": "user-uuid",
  "applicationId": "CRP-2026-1234",
  "accountNumber": "1234567890",
  "equipmentType": "heat_pump_hvac",
  "status": "submitted",
  "equipmentDetails": "Mitsubishi 3-zone ductless heat pump, 3 tons",
  "purchaseDate": "2026-01-10",
  "invoiceTotal": 15000.00,
  "ahriCertificate": "AHRI-12345678",
  "ladbsPermitNumber": "2026-001235",
  "estimatedRebate": 7500.00,
  "approvedAmount": null,
  "denialReason": null,
  "paidAt": null,
  "submittedAt": "2026-01-15T10:00:00Z",
  "createdAt": "2026-01-15T10:00:00Z",
  "updatedAt": "2026-01-15T10:00:00Z"
}
```

#### Model Definition

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class EquipmentType(str, Enum):
    """Type of equipment eligible for rebates."""
    HEAT_PUMP_HVAC = "heat_pump_hvac"
    HEAT_PUMP_WATER_HEATER = "heat_pump_water_heater"
    SMART_THERMOSTAT = "smart_thermostat"


class RebateStatus(str, Enum):
    """Status of a rebate application."""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"


class RebateDocument(BaseModel):
    """Rebate document stored in the database."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    user_id: str = Field(alias="userId")
    application_id: str = Field(alias="applicationId")
    account_number: str = Field(alias="accountNumber")
    equipment_type: EquipmentType = Field(alias="equipmentType")
    status: RebateStatus
    equipment_details: str = Field(alias="equipmentDetails")
    purchase_date: str = Field(alias="purchaseDate")
    invoice_total: float = Field(alias="invoiceTotal")
    ahri_certificate: Optional[str] = Field(default=None, alias="ahriCertificate")
    ladbs_permit_number: Optional[str] = Field(default=None, alias="ladbsPermitNumber")
    estimated_rebate: float = Field(alias="estimatedRebate")
    approved_amount: Optional[float] = Field(default=None, alias="approvedAmount")
    denial_reason: Optional[str] = Field(default=None, alias="denialReason")
    paid_at: Optional[datetime] = Field(default=None, alias="paidAt")
    submitted_at: datetime = Field(alias="submittedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
```

#### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Get rebate by ID | Point read with partition key `userId` | 1 RU |
| List user's rebates | Query `WHERE c.userId = @userId` | 3-10 RU |
| Get by application ID | Query `WHERE c.applicationId = @applicationId` | 5-10 RU |
| Update status | Point write by `id` | 5-10 RU |

#### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/userId/?" },
      { "path": "/applicationId/?" },
      { "path": "/accountNumber/?" },
      { "path": "/status/?" },
      { "path": "/equipmentType/?" },
      { "path": "/submittedAt/?" },
      { "path": "/createdAt/?" }
    ],
    "excludedPaths": [
      { "path": "/_etag/?" }
    ]
  }
}
```

---

### Container: `tou_enrollments`

Stores Time-of-Use rate plan enrollments.

#### Partition Strategy

- **Partition Key:** `/accountNumber`
- **Rationale:** Enrollments are queried by utility account

#### Schema

```json
{
  "id": "enrollment-uuid",
  "userId": "user-uuid",
  "accountNumber": "1234567890",
  "confirmationNumber": "TOU-2026-78901",
  "ratePlan": "TOU-D-A",
  "previousPlan": "standard",
  "status": "pending",
  "effectiveDate": "2026-02-01",
  "meterSwapRequired": true,
  "meterSwapDate": "2026-01-28",
  "enrolledAt": "2026-01-20T10:00:00Z",
  "createdAt": "2026-01-20T10:00:00Z",
  "updatedAt": "2026-01-20T10:00:00Z"
}
```

#### Model Definition

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class TOURatePlan(str, Enum):
    """LADWP TOU rate plan options."""
    TOU_D_A = "TOU-D-A"
    TOU_D_B = "TOU-D-B"
    TOU_D_PRIME = "TOU-D-PRIME"


class TOUEnrollmentStatus(str, Enum):
    """Status of TOU enrollment."""
    PENDING = "pending"
    ACTIVE = "active"
    CANCELLED = "cancelled"


class TOUEnrollmentDocument(BaseModel):
    """TOU enrollment document stored in the database."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    user_id: str = Field(alias="userId")
    account_number: str = Field(alias="accountNumber")
    confirmation_number: str = Field(alias="confirmationNumber")
    rate_plan: TOURatePlan = Field(alias="ratePlan")
    previous_plan: str = Field(alias="previousPlan")
    status: TOUEnrollmentStatus
    effective_date: str = Field(alias="effectiveDate")
    meter_swap_required: bool = Field(alias="meterSwapRequired")
    meter_swap_date: Optional[str] = Field(default=None, alias="meterSwapDate")
    enrolled_at: datetime = Field(alias="enrolledAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
```

#### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Get enrollment by ID | Point read with partition key `accountNumber` | 1 RU |
| List account enrollments | Query `WHERE c.accountNumber = @accountNumber` | 3-10 RU |
| Get by confirmation number | Query `WHERE c.confirmationNumber = @confirmationNumber` | 5-10 RU |
| Update status | Point write by `id` | 5-10 RU |

#### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/accountNumber/?" },
      { "path": "/userId/?" },
      { "path": "/confirmationNumber/?" },
      { "path": "/status/?" },
      { "path": "/ratePlan/?" },
      { "path": "/effectiveDate/?" },
      { "path": "/createdAt/?" }
    ],
    "excludedPaths": [
      { "path": "/_etag/?" }
    ]
  }
}
```

---

## LASAN Database

The LASAN (Los Angeles Bureau of Sanitation) database stores pickup requests.

### Database Configuration

| Property | Value |
|----------|-------|
| **Database Name** | `lasan` |
| **Throughput** | Serverless (automatic) |

### Container Summary

| Container | Partition Key | Purpose | TTL |
|-----------|---------------|---------|-----|
| `pickups` | `/userId` | Pickup requests and status | None |

---

### Container: `pickups`

Stores pickup requests (bulky items, e-waste, hazardous).

#### Partition Strategy

- **Partition Key:** `/userId`
- **Rationale:** Users query their own pickup requests

#### Schema

```json
{
  "id": "pickup-uuid",
  "userId": "user-uuid",
  "pickupId": "PU-2026-5678",
  "pickupType": "bulky_item",
  "status": "scheduled",
  "address": "123 Main St, Los Angeles, CA 90012",
  "items": [
    "Old refrigerator",
    "Broken washing machine"
  ],
  "scheduledDate": "2026-02-20",
  "confirmationNumber": "311-CONF-12345",
  "contactName": "John Smith",
  "contactPhone": "555-0123",
  "notes": "Items in front yard",
  "completedAt": null,
  "createdAt": "2026-02-01T10:00:00Z",
  "updatedAt": "2026-02-01T10:00:00Z"
}
```

#### Model Definition

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PickupType(str, Enum):
    """Type of special pickup."""
    BULKY_ITEM = "bulky_item"
    EWASTE = "ewaste"
    HAZARDOUS = "hazardous"


class PickupStatus(str, Enum):
    """Status of a pickup request."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PickupDocument(BaseModel):
    """Pickup document stored in the database."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    user_id: str = Field(alias="userId")
    pickup_id: str = Field(alias="pickupId")
    pickup_type: PickupType = Field(alias="pickupType")
    status: PickupStatus
    address: str
    items: List[str]
    scheduled_date: str = Field(alias="scheduledDate")
    confirmation_number: Optional[str] = Field(default=None, alias="confirmationNumber")
    contact_name: str = Field(alias="contactName")
    contact_phone: str = Field(alias="contactPhone")
    notes: Optional[str] = None
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
```

#### Access Patterns

| Operation | Query | RU Estimate |
|-----------|-------|-------------|
| Get pickup by ID | Point read with partition key `userId` | 1 RU |
| List user's pickups | Query `WHERE c.userId = @userId` | 3-10 RU |
| Get by pickup ID | Query `WHERE c.pickupId = @pickupId` | 5-10 RU |
| Search by address | Query `WHERE c.address = @address` | 5-15 RU |
| Update status | Point write by `id` | 5-10 RU |

#### Indexes

```json
{
  "indexingPolicy": {
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [
      { "path": "/userId/?" },
      { "path": "/pickupId/?" },
      { "path": "/status/?" },
      { "path": "/address/?" },
      { "path": "/pickupType/?" },
      { "path": "/scheduledDate/?" },
      { "path": "/createdAt/?" }
    ],
    "excludedPaths": [
      { "path": "/items/*" },
      { "path": "/_etag/?" }
    ]
  }
}
```

---

## Data Operations

### Create Operations

#### Create User

```python
async def create_user(user: User) -> User:
    """Create a new user profile."""
    container = get_container("users")
    user.created_at = datetime.utcnow()
    result = await container.create_item(body=user.model_dump())
    return User(**result)
```

#### Create Project

```python
async def create_project(user_id: str, context: ProjectContext) -> Project:
    """Create a new project with initial plan."""
    container = get_container("projects")
    
    project = Project(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=f"{context.project_type.title()} - {context.address}",
        status=ProjectStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        context=context,
        plan=Plan(
            id=str(uuid.uuid4()),
            title="",
            status="active",
            steps=[]
        ),
        summary=ProjectSummary(
            total_steps=0,
            completed=0,
            awaiting_user=0,
            not_started=0
        )
    )
    
    result = await container.create_item(
        body=project.model_dump(),
        partition_key=user_id
    )
    return Project(**result)
```

### Read Operations

#### Get User's Projects

```python
async def get_user_projects(
    user_id: str, 
    status: Optional[ProjectStatus] = None
) -> List[Project]:
    """Get all projects for a user, optionally filtered by status."""
    container = get_container("projects")
    
    if status:
        query = """
            SELECT * FROM c 
            WHERE c.userId = @userId AND c.status = @status
            ORDER BY c.updatedAt DESC
        """
        params = [
            {"name": "@userId", "value": user_id},
            {"name": "@status", "value": status.value}
        ]
    else:
        query = """
            SELECT * FROM c 
            WHERE c.userId = @userId
            ORDER BY c.updatedAt DESC
        """
        params = [{"name": "@userId", "value": user_id}]
    
    items = container.query_items(
        query=query,
        parameters=params,
        partition_key=user_id
    )
    
    return [Project(**item) async for item in items]
```

#### Get Conversation History

```python
async def get_messages(
    project_id: str,
    limit: int = 50,
    before: Optional[datetime] = None
) -> List[Message]:
    """Get conversation history for a project with pagination."""
    container = get_container("messages")
    
    query = """
        SELECT * FROM c 
        WHERE c.projectId = @projectId
        AND (@before IS NULL OR c.timestamp < @before)
        ORDER BY c.timestamp DESC
        OFFSET 0 LIMIT @limit
    """
    
    items = container.query_items(
        query=query,
        parameters=[
            {"name": "@projectId", "value": project_id},
            {"name": "@before", "value": before.isoformat() if before else None},
            {"name": "@limit", "value": limit}
        ],
        partition_key=project_id
    )
    
    messages = [Message(**item) async for item in items]
    return list(reversed(messages))  # Return in chronological order
```

### Update Operations

#### Update Plan Step

```python
async def update_plan_step(
    project_id: str,
    user_id: str,
    step_id: str,
    updates: Dict[str, Any]
) -> Project:
    """Update a specific step in the project plan using patch."""
    container = get_container("projects")
    
    # First, get current project to find step index
    project = await get_project(project_id, user_id)
    step_index = next(
        (i for i, s in enumerate(project.plan.steps) if s.id == step_id),
        None
    )
    
    if step_index is None:
        raise ValueError(f"Step {step_id} not found in project")
    
    # Build patch operations
    operations = []
    for key, value in updates.items():
        operations.append({
            "op": "set",
            "path": f"/plan/steps/{step_index}/{key}",
            "value": value
        })
    
    # Always update the updatedAt timestamp
    operations.append({
        "op": "set",
        "path": "/updatedAt",
        "value": datetime.utcnow().isoformat()
    })
    
    result = await container.patch_item(
        item=project_id,
        partition_key=user_id,
        patch_operations=operations
    )
    
    return Project(**result)
```

### Reporting Operations

#### Log Step Completion

```python
async def log_step_completion(
    tool_name: str,
    city: str,
    started_at: datetime,
    completed_at: datetime
) -> StepCompletion:
    """Log a step completion for reporting (anonymized)."""
    container = get_container("step_completions")
    
    duration = (completed_at - started_at).total_seconds() / 86400  # Convert to days
    
    completion = StepCompletion(
        id=str(uuid.uuid4()),
        tool_name=tool_name,
        city=city,
        started_at=started_at,
        completed_at=completed_at,
        duration_days=round(duration, 2)
    )
    
    result = await container.create_item(
        body=completion.model_dump(),
        partition_key=tool_name
    )
    return StepCompletion(**result)
```

#### Get Average Duration

```python
async def get_average_duration(
    tool_name: str,
    city: Optional[str] = None
) -> Dict[str, Any]:
    """Get average duration for a step type."""
    container = get_container("step_completions")
    
    six_months_ago = (datetime.utcnow() - timedelta(days=180)).isoformat()
    
    if city:
        query = """
            SELECT 
                AVG(c.durationDays) AS avgDays,
                COUNT(1) AS sampleCount
            FROM c
            WHERE c.toolName = @toolName
              AND c.city = @city
              AND c.completedAt > @since
        """
        params = [
            {"name": "@toolName", "value": tool_name},
            {"name": "@city", "value": city},
            {"name": "@since", "value": six_months_ago}
        ]
    else:
        query = """
            SELECT 
                AVG(c.durationDays) AS avgDays,
                COUNT(1) AS sampleCount
            FROM c
            WHERE c.toolName = @toolName
              AND c.completedAt > @since
        """
        params = [
            {"name": "@toolName", "value": tool_name},
            {"name": "@since", "value": six_months_ago}
        ]
    
    items = container.query_items(
        query=query,
        parameters=params,
        partition_key=tool_name
    )
    
    result = await items.__anext__()
    return {
        "averageDays": round(result.get("avgDays", 0), 1),
        "sampleCount": result.get("sampleCount", 0)
    }
```

---

## Security & Access Control

### Authentication

The application uses **Azure AD Managed Identity** for Cosmos DB access:

```python
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

credential = DefaultAzureCredential()
client = CosmosClient(
    url=os.environ["COSMOS_ENDPOINT"],
    credential=credential
)
```

### Role-Based Access Control (RBAC)

| Principal | Role | Scope |
|-----------|------|-------|
| Agent Service Identity | Cosmos DB Built-in Data Contributor | Database |
| MCP Server Identities | Cosmos DB Built-in Data Reader | `step_completions` container only |
| Web App Identity | Cosmos DB Built-in Data Contributor | `users`, `projects`, `messages` containers |

### Data Isolation

- **User data isolation:** Partition key `/userId` ensures users only access their own projects
- **Row-level security:** Application layer enforces user ID matching in all queries
- **No cross-partition queries for user data:** All user data queries include partition key

---

## Monitoring & Diagnostics

### Key Metrics

| Metric | Threshold | Action |
|--------|-----------|--------|
| Normalized RU Consumption | > 70% | Consider provisioned throughput |
| Request Rate | > 1000/min sustained | Review indexing efficiency |
| Latency P99 | > 100ms | Check partition hotspots |
| Failed Requests | > 1% | Investigate error codes |

### Diagnostic Settings

Enable diagnostic logs to Log Analytics:

- QueryRuntimeStatistics
- PartitionKeyStatistics
- PartitionKeyRUConsumption
- DataPlaneRequests

---

## Migration & Seeding

### Initial Schema Setup

The Bicep deployment creates the database and containers. Container-specific settings are applied via a post-deployment script.

### Sample Data Seeding

For demo purposes, seed data can be loaded:

```python
async def seed_demo_data():
    """Seed demo user and project data."""
    # Create demo user
    demo_user = User(
        id="demo-user-001",
        email="john.smith@demo.com",
        name="John Smith",
        phone="555-0123",
        created_at=datetime.utcnow()
    )
    await create_user(demo_user)
    
    # Create demo project with sample plan
    context = ProjectContext(
        address="123 Main St, Los Angeles, CA 90012",
        project_type="home_renovation",
        description="Solar panels, battery, heat pumps, metal roof"
    )
    project = await create_project(demo_user.id, context)
    
    # Add sample steps...
```

---

## Best Practices

### Query Efficiency

1. **Always include partition key** in queries for user data
2. **Use point reads** when document ID is known
3. **Prefer patch operations** over full document replacement
4. **Limit result sets** with appropriate OFFSET/LIMIT

### Document Design

1. **Keep documents under 100KB** for optimal performance
2. **Embed related data** when accessed together (plan inside project)
3. **Separate data** when it grows unbounded (messages from project)
4. **Use references** for cross-container lookups

### Error Handling

```python
from azure.cosmos.exceptions import CosmosHttpResponseError

try:
    result = await container.read_item(item=id, partition_key=pk)
except CosmosHttpResponseError as e:
    if e.status_code == 404:
        # Document not found
        return None
    elif e.status_code == 429:
        # Rate limited - retry with backoff
        await asyncio.sleep(e.retry_after or 1)
        return await container.read_item(item=id, partition_key=pk)
    else:
        raise
```

---

## Summary

| Container | Documents | Partition Key | Primary Access Pattern |
|-----------|-----------|---------------|------------------------|
| `users` | ~thousands | `/id` | Point read by ID |
| `projects` | ~10 per user | `/userId` | List by user, point read |
| `messages` | ~100+ per project | `/projectId` | Paginated timeline query |
| `step_completions` | ~millions | `/toolName` | Aggregate queries |

This schema supports the Citizen Services Portal's requirements for:
- Fast user and project lookups
- Efficient conversation history retrieval
- Scalable anonymized metrics collection
- Simple, maintainable data operations

---

*This document defines the data layer specification. Once confirmed, proceed with implementation in the data access layer.*
