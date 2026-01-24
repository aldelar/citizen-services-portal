# CosmosDB Specification

This document provides detailed specifications for the Azure Cosmos DB data layer, including database structure, container schemas, partition strategies, and access patterns. Use this as the source of truth when implementing data operations.

---

## Overview

The Citizen Services Portal uses Azure Cosmos DB with the NoSQL API to store:
- User profiles
- Projects with embedded plans
- Conversation history (messages)
- Step completion metrics for reporting

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
