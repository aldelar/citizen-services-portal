# MCP Server Specifications

This document provides detailed specifications for each MCP server, including tool signatures, input/output models, and behavior patterns. Use this as the source of truth when implementing the MCP servers.

---

## Common Patterns

### Tool Types

| Type | Behavior | Response Pattern |
|------|----------|------------------|
| **Query** | Read-only, no side effects | Returns data directly |
| **Automated** | Executes action against backend | Returns result with confirmation |
| **User Action** | Cannot be automated | Returns `UserActionResponse` with prepared materials |

### Common Response Models

#### KnowledgeResult

Returned by all `queryKB` tools.

```python
class KnowledgeResult(BaseModel):
    """Result from knowledge base query."""
    query: str                    # Original query
    results: List[DocumentChunk]  # Matching chunks
    total_results: int            # Total matches found

class DocumentChunk(BaseModel):
    """A chunk of document content."""
    content: str                  # Text content
    source: str                   # Source document name
    relevance_score: float        # 0.0 to 1.0
    title: Optional[str]          # Document title (for citations)
    section: Optional[str]        # Section heading where content was found
    page_number: Optional[int]    # Page number (for PDFs)
```

#### UserActionResponse

Returned by tools that require user action (cannot be automated).

```python
class UserActionResponse(BaseModel):
    """Response when user must take action."""
    requires_user_action: bool = True
    action_type: str              # "phone_call", "email", "in_person", "online_portal"
    target: str                   # "311", email address, URL, office location
    reason: str                   # Why this can't be automated
    
    prepared_materials: PreparedMaterials
    on_complete: OnCompletePrompt

class PreparedMaterials(BaseModel):
    """Materials prepared for user action."""
    phone_script: Optional[str]   # What to say on phone
    email_draft: Optional[str]    # Draft email content
    checklist: List[str]          # Items to have ready
    contact_info: Optional[dict]  # Phone, hours, address
    documents_needed: List[str]   # Documents to prepare

class OnCompletePrompt(BaseModel):
    """What to ask user after they complete action."""
    prompt: str                   # Question to ask
    expected_info: List[str]      # Fields to collect (e.g., ["confirmation_number", "scheduled_date"])
```

---

## LADBS MCP Server

**Purpose:** Los Angeles Department of Building and Safety - Permits and Inspections

### Enums

```python
class PermitType(str, Enum):
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    BUILDING = "building"
    PLUMBING = "plumbing"

class PermitStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CORRECTIONS_REQUIRED = "corrections_required"
    APPROVED = "approved"
    ISSUED = "issued"
    EXPIRED = "expired"
    REJECTED = "rejected"

class InspectionType(str, Enum):
    ROUGH_ELECTRICAL = "rough_electrical"
    FINAL_ELECTRICAL = "final_electrical"
    ROUGH_MECHANICAL = "rough_mechanical"
    FINAL_MECHANICAL = "final_mechanical"
    FRAMING = "framing"
    FINAL = "final"

class InspectionStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### Models

```python
class Permit(BaseModel):
    """Permit information."""
    permit_number: str
    permit_type: PermitType
    status: PermitStatus
    address: str
    description: str
    applicant_name: str
    submitted_at: datetime
    approved_at: Optional[datetime]
    expires_at: Optional[datetime]
    fees: Optional[PermitFees]
    next_steps: Optional[str]

class PermitFees(BaseModel):
    """Fee breakdown for permit."""
    plan_check: float
    permit_fee: float
    other_fees: float
    total: float

class Inspection(BaseModel):
    """Inspection information."""
    inspection_id: str
    permit_number: str
    inspection_type: InspectionType
    status: InspectionStatus
    scheduled_date: Optional[datetime]
    scheduled_time_window: Optional[str]  # e.g., "8am-12pm"
    completed_at: Optional[datetime]
    result: Optional[str]
    inspector_notes: Optional[str]

class Applicant(BaseModel):
    """Applicant information for permit submission."""
    name: str
    email: str
    phone: str
    contractor_license: Optional[str]
```

### Tools

---

#### `queryKB`

Search LADBS knowledge base for permit requirements, fees, processes.

**Type:** Query

**Signature:**
```python
async def queryKB(
    query: str,           # Natural language query
    top: int = 5          # Number of results to return
) -> KnowledgeResult
```

**Example:**
```python
# Input
queryKB(query="What documents do I need for an electrical permit with solar panels?", top=5)

# Output
KnowledgeResult(
    query="What documents do I need for an electrical permit with solar panels?",
    results=[
        DocumentChunk(
            content="For electrical permits involving solar PV systems, you need: 1) Site plan showing panel layout, 2) Single-line electrical diagram, 3) Equipment specifications (inverter, panels), 4) Structural calculations for roof mounting, 5) C-10 contractor license...",
            source="ladbs-electrical-permits.pdf",
            relevance_score=0.94
        ),
        # ... more chunks
    ],
    total_results=12
)
```

---

#### `permits.search`

Find existing permits by address or permit number.

**Type:** Query

**Signature:**
```python
async def permits_search(
    user_id: Optional[str] = None,           # User ID for optimized partition-aware query
    address: Optional[str] = None,           # Property address
    permit_number: Optional[str] = None      # Specific permit number
) -> PermitSearchResult

class PermitSearchResult(BaseModel):
    permits: List[Permit]
    total_count: int
```

**Example:**
```python
# Input
permits_search(address="123 Main St, Los Angeles, CA 90012")

# Output
PermitSearchResult(
    permits=[
        Permit(
            permit_number="2026-001234",
            permit_type=PermitType.ELECTRICAL,
            status=PermitStatus.APPROVED,
            address="123 Main St, Los Angeles, CA 90012",
            description="Solar PV installation with battery storage",
            applicant_name="John Smith",
            submitted_at=datetime(2026, 1, 15, 10, 0, 0),
            approved_at=datetime(2026, 1, 28, 14, 30, 0),
            fees=PermitFees(plan_check=450, permit_fee=800, other_fees=0, total=1250),
            next_steps="Schedule rough electrical inspection"
        )
    ],
    total_count=1
)
```

---

#### `permits.submit`

Submit a new permit application.

**Type:** Automated

**Signature:**
```python
async def permits_submit(
    user_id: str,                     # User ID (required for CosmosDB partition key)
    permit_type: PermitType,
    address: str,
    applicant: Applicant,
    work_description: str,
    estimated_cost: float,
    documents: List[str]              # Document references/URLs
) -> PermitSubmitResult

class PermitSubmitResult(BaseModel):
    success: bool
    permit_number: str
    status: PermitStatus
    submitted_at: datetime
    fees: PermitFees
    estimated_review_time: str    # e.g., "4-6 weeks"
    next_steps: str
```

**Example:**
```python
# Input
permits_submit(
    user_id="user-uuid-12345",
    permit_type=PermitType.ELECTRICAL,
    address="123 Main St, Los Angeles, CA 90012",
    applicant=Applicant(
        name="John Smith",
        email="john@example.com",
        phone="555-0123",
        contractor_license="C10-123456"
    ),
    work_description="Solar PV installation (8.5kW) with 13.5kWh battery storage",
    estimated_cost=25000.00,
    documents=["site-plan.pdf", "single-line-diagram.pdf", "equipment-specs.pdf"]
)

# Output
PermitSubmitResult(
    success=True,
    permit_number="2026-001234",
    status=PermitStatus.SUBMITTED,
    submitted_at=datetime(2026, 1, 15, 10, 0, 0),
    fees=PermitFees(plan_check=450, permit_fee=800, other_fees=0, total=1250),
    estimated_review_time="4-6 weeks",
    next_steps="You'll receive email updates on review progress. Plan check fees are due within 30 days."
)
```

---

#### `permits.getStatus`

Check the current status of a permit.

**Type:** Automated

**Signature:**
```python
async def permits_getStatus(
    permit_number: str,
    user_id: Optional[str] = None     # User ID for optimized partition-aware query
) -> Permit
```

**Example:**
```python
# Input
permits_getStatus(permit_number="2026-001234")

# Output
Permit(
    permit_number="2026-001234",
    permit_type=PermitType.ELECTRICAL,
    status=PermitStatus.APPROVED,
    address="123 Main St, Los Angeles, CA 90012",
    description="Solar PV installation with battery storage",
    applicant_name="John Smith",
    submitted_at=datetime(2026, 1, 15, 10, 0, 0),
    approved_at=datetime(2026, 1, 28, 14, 30, 0),
    expires_at=datetime(2027, 1, 28),
    fees=PermitFees(plan_check=450, permit_fee=800, other_fees=0, total=1250),
    next_steps="Schedule rough electrical inspection before starting work"
)
```

---

#### `inspections.scheduled`

View scheduled inspections for a permit or address.

**Type:** Query

**Signature:**
```python
async def inspections_scheduled(
    user_id: Optional[str] = None,           # User ID for optimized queries
    permit_number: Optional[str] = None,
    address: Optional[str] = None
) -> InspectionListResult

class InspectionListResult(BaseModel):
    inspections: List[Inspection]
    total_count: int
```

**Example:**
```python
# Input
inspections_scheduled(permit_number="2026-001234")

# Output
InspectionListResult(
    inspections=[
        Inspection(
            inspection_id="INS-789456",
            permit_number="2026-001234",
            inspection_type=InspectionType.ROUGH_ELECTRICAL,
            status=InspectionStatus.SCHEDULED,
            scheduled_date=datetime(2026, 2, 15),
            scheduled_time_window="8am-12pm",
            completed_at=None,
            result=None,
            inspector_notes=None
        )
    ],
    total_count=1
)
```

---

#### `inspections.schedule`

Prepare materials for scheduling an inspection (requires user action - phone call to 311).

**Type:** User Action

**Signature:**
```python
async def inspections_schedule(
    permit_number: str,
    inspection_type: InspectionType,
    address: str,
    contact_name: str,
    contact_phone: str
) -> UserActionResponse
```

**Example:**
```python
# Input
inspections_schedule(
    permit_number="2026-001234",
    inspection_type=InspectionType.ROUGH_ELECTRICAL,
    address="123 Main St, Los Angeles, CA 90012",
    contact_name="John Smith",
    contact_phone="555-0123"
)

# Output
UserActionResponse(
    requires_user_action=True,
    action_type="phone_call",
    target="311",
    reason="LADBS inspection scheduling is only available via phone or the LADBS website",
    
    prepared_materials=PreparedMaterials(
        phone_script="Call 311 and say: 'I need to schedule a rough electrical inspection for permit number 2026-001234 at 123 Main St, Los Angeles. My name is John Smith and my phone number is 555-0123.'",
        checklist=[
            "Have permit number ready: 2026-001234",
            "Confirm work is ready for inspection (wiring complete, accessible)",
            "Request morning slot (8am-12pm) if preferred",
            "Note: 24-48 hours advance notice typically required"
        ],
        contact_info={
            "phone": "311",
            "hours": "24/7",
            "alternative": "https://www.ladbs.org/inspections"
        },
        documents_needed=[]
    ),
    
    on_complete=OnCompletePrompt(
        prompt="Once scheduled, please tell me the inspection date and confirmation number",
        expected_info=["scheduled_date", "confirmation_number", "time_window"]
    )
)
```

---

## LADWP MCP Server

**Purpose:** Los Angeles Department of Water and Power - Utility Services, Solar, Rebates

### Enums

```python
class RatePlan(str, Enum):
    STANDARD = "standard"
    TOU_D_A = "TOU-D-A"
    TOU_D_B = "TOU-D-B"
    TOU_D_PRIME = "TOU-D-PRIME"  # For solar customers

class MeterType(str, Enum):
    STANDARD = "standard"
    TOU = "tou"
    NET_METER = "net_meter"

class EquipmentType(str, Enum):
    HEAT_PUMP_HVAC = "heat_pump_hvac"
    HEAT_PUMP_WATER_HEATER = "heat_pump_water_heater"
    SMART_THERMOSTAT = "smart_thermostat"

class RebateStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"

class InterconnectionStatus(str, Enum):
    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    ENGINEERING_REVIEW = "engineering_review"
    APPROVED = "approved"
    PTO_ISSUED = "pto_issued"  # Permission to Operate
    DENIED = "denied"
```

### Models

```python
class Account(BaseModel):
    """LADWP utility account information."""
    account_number: str
    account_holder: str
    service_address: str
    current_rate_plan: RatePlan
    meter_type: MeterType
    pending_requests: List[str]     # e.g., ["TOU enrollment pending"]
    has_solar: bool
    has_battery: bool

class RatePlanInfo(BaseModel):
    """Rate plan details."""
    plan_code: RatePlan
    plan_name: str
    description: str
    rates: RateSchedule
    eligibility: str                # Who can enroll
    best_for: str                   # Who this plan suits

class RateSchedule(BaseModel):
    """Rate schedule details."""
    off_peak_rate: float            # $/kWh
    mid_peak_rate: Optional[float]  # $/kWh (TOU only)
    on_peak_rate: Optional[float]   # $/kWh (TOU only)
    off_peak_hours: Optional[str]   # e.g., "8pm-4pm weekdays"
    on_peak_hours: Optional[str]    # e.g., "4pm-9pm weekdays"

class TOUEnrollmentResult(BaseModel):
    """Result of TOU enrollment."""
    success: bool
    confirmation_number: str
    rate_plan: RatePlan
    effective_date: datetime
    meter_swap_required: bool
    meter_swap_date: Optional[datetime]
    next_steps: str

class Interconnection(BaseModel):
    """Solar interconnection application status."""
    application_id: Optional[str]
    address: str
    system_size_kw: float
    battery_size_kwh: Optional[float]
    status: InterconnectionStatus
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    pto_date: Optional[datetime]    # Permission to Operate date
    next_steps: Optional[str]

class RebateApplication(BaseModel):
    """Rebate application information."""
    application_id: str
    account_number: str
    equipment_type: EquipmentType
    status: RebateStatus
    submitted_at: datetime
    equipment_details: str
    estimated_rebate: float
    approved_amount: Optional[float]
    paid_at: Optional[datetime]
    denial_reason: Optional[str]
```

### Tools

---

#### `queryKB`

Search LADWP knowledge base for rate plans, rebates, solar programs.

**Type:** Query

**Signature:**
```python
async def queryKB(
    query: str,
    top: int = 5
) -> KnowledgeResult
```

---

#### `account.show`

Get current account information including rate plan and pending requests.

**Type:** Query

**Signature:**
```python
async def account_show(
    account_number: str
) -> Account
```

**Example:**
```python
# Input
account_show(account_number="1234567890")

# Output
Account(
    account_number="1234567890",
    account_holder="John Smith",
    service_address="123 Main St, Los Angeles, CA 90012",
    current_rate_plan=RatePlan.STANDARD,
    meter_type=MeterType.STANDARD,
    pending_requests=["TOU-D-PRIME enrollment - effective 2026-02-01"],
    has_solar=False,
    has_battery=False
)
```

---

#### `plans.list`

List available LADWP rate plans.

**Type:** Query

**Signature:**
```python
async def plans_list(
    account_number: str
) -> PlansListResult

class PlansListResult(BaseModel):
    current_plan: RatePlan
    available_plans: List[RatePlanInfo]
    recommended_plan: Optional[RatePlan]    # Based on usage/solar
    recommendation_reason: Optional[str]
```

**Example:**
```python
# Input
plans_list(account_number="1234567890")

# Output
PlansListResult(
    current_plan=RatePlan.STANDARD,
    available_plans=[
        RatePlanInfo(
            plan_code=RatePlan.STANDARD,
            plan_name="Standard Residential",
            description="Flat rate pricing",
            rates=RateSchedule(off_peak_rate=0.25, mid_peak_rate=None, on_peak_rate=None),
            eligibility="All residential customers",
            best_for="Customers with consistent usage throughout the day"
        ),
        RatePlanInfo(
            plan_code=RatePlan.TOU_D_PRIME,
            plan_name="TOU-D-PRIME",
            description="Time-of-Use rate optimized for solar customers",
            rates=RateSchedule(
                off_peak_rate=0.15,
                mid_peak_rate=0.28,
                on_peak_rate=0.45,
                off_peak_hours="8pm-4pm weekdays, all weekend",
                on_peak_hours="4pm-9pm weekdays"
            ),
            eligibility="Customers with solar PV systems",
            best_for="Solar customers with battery storage"
        )
    ],
    recommended_plan=RatePlan.TOU_D_PRIME,
    recommendation_reason="With your planned solar installation, TOU-D-PRIME could save 30-50% on electricity costs"
)
```

---

#### `tou.enroll`

Enroll in a Time-of-Use rate plan.

**Type:** Automated

**Signature:**
```python
async def tou_enroll(
    account_number: str,
    rate_plan: RatePlan
) -> TOUEnrollmentResult
```

**Example:**
```python
# Input
tou_enroll(account_number="1234567890", rate_plan=RatePlan.TOU_D_PRIME)

# Output
TOUEnrollmentResult(
    success=True,
    confirmation_number="TOU-2026-78901",
    rate_plan=RatePlan.TOU_D_PRIME,
    effective_date=datetime(2026, 2, 1),
    meter_swap_required=True,
    meter_swap_date=datetime(2026, 1, 28),
    next_steps="A technician will install your TOU meter on Jan 28. Your new rate takes effect Feb 1."
)
```

---

#### `interconnection.submit`

Prepare solar interconnection application (requires user action - email submission).

**Type:** User Action

**Signature:**
```python
async def interconnection_submit(
    address: str,
    system_size_kw: float,
    battery_size_kwh: Optional[float],
    equipment_specs: dict,           # Inverter model, panel specs, etc.
    applicant_name: str,
    applicant_email: str
) -> UserActionResponse
```

**Example:**
```python
# Input
interconnection_submit(
    address="123 Main St, Los Angeles, CA 90012",
    system_size_kw=8.5,
    battery_size_kwh=13.5,
    equipment_specs={
        "inverter": "SolarEdge SE7600H",
        "panels": "REC Alpha Pure 400W x 22",
        "battery": "Tesla Powerwall 2"
    },
    applicant_name="John Smith",
    applicant_email="john@example.com"
)

# Output
UserActionResponse(
    requires_user_action=True,
    action_type="email",
    target="SolarCoordinator@ladwp.com",
    reason="Interconnection agreements require signed documents and engineering review",
    
    prepared_materials=PreparedMaterials(
        email_draft="""Subject: Interconnection Application - 123 Main St, Los Angeles

Dear LADWP Solar Coordinator,

I am submitting an interconnection application for a solar PV system with battery storage at:

Address: 123 Main St, Los Angeles, CA 90012
System Size: 8.5 kW DC
Battery Storage: 13.5 kWh (Tesla Powerwall 2)
Inverter: SolarEdge SE7600H

Please find attached:
1. Completed Interconnection Application Form
2. Single-line electrical diagram
3. Equipment specification sheets
4. Site plan

Applicant: John Smith
Email: john@example.com
LADBS Electrical Permit: [Include permit number when approved]

Thank you,
John Smith""",
        checklist=[
            "Complete LADWP Interconnection Application Form (download from ladwp.com/nem)",
            "Attach single-line electrical diagram",
            "Attach equipment spec sheets (inverter, panels, battery)",
            "Attach site plan showing equipment locations",
            "Include LADBS electrical permit number"
        ],
        contact_info={
            "email": "SolarCoordinator@ladwp.com",
            "phone": "213-367-6163",
            "department": "PV/BESS Service Design Group"
        },
        documents_needed=[
            "Interconnection Application Form",
            "Single-line diagram",
            "Equipment specs",
            "Site plan",
            "LADBS permit (when approved)"
        ]
    ),
    
    on_complete=OnCompletePrompt(
        prompt="Once you've emailed the application, let me know and I'll help track the status",
        expected_info=["submission_date", "confirmation_email_received"]
    )
)
```

---

#### `interconnection.getStatus`

Check interconnection application status.

**Type:** Query

**Signature:**
```python
async def interconnection_getStatus(
    application_id: Optional[str] = None,
    address: Optional[str] = None
) -> Interconnection
```

**Example:**
```python
# Input
interconnection_getStatus(address="123 Main St, Los Angeles, CA 90012")

# Output
Interconnection(
    application_id="IA-2026-12345",
    address="123 Main St, Los Angeles, CA 90012",
    system_size_kw=8.5,
    battery_size_kwh=13.5,
    status=InterconnectionStatus.APPROVED,
    submitted_at=datetime(2026, 1, 20),
    approved_at=datetime(2026, 2, 15),
    pto_date=None,
    next_steps="Complete installation and pass LADBS final inspection, then request PTO inspection"
)
```

---

#### `rebates.filed`

List all rebate applications for an account.

**Type:** Query

**Signature:**
```python
async def rebates_filed(
    account_number: str
) -> RebatesFiledResult

class RebatesFiledResult(BaseModel):
    applications: List[RebateApplication]
    total_count: int
```

**Example:**
```python
# Input
rebates_filed(account_number="1234567890")

# Output
RebatesFiledResult(
    applications=[
        RebateApplication(
            application_id="CRP-2026-1234",
            account_number="1234567890",
            equipment_type=EquipmentType.HEAT_PUMP_HVAC,
            status=RebateStatus.UNDER_REVIEW,
            submitted_at=datetime(2026, 1, 15),
            equipment_details="Mitsubishi 3-zone ductless heat pump, 3 tons",
            estimated_rebate=7500.00,
            approved_amount=None,
            paid_at=None,
            denial_reason=None
        )
    ],
    total_count=1
)
```

---

#### `rebates.apply`

Submit a rebate application.

**Type:** Automated

**Signature:**
```python
async def rebates_apply(
    account_number: str,
    equipment_type: EquipmentType,
    equipment_details: str,         # Make, model, tonnage, etc.
    purchase_date: datetime,
    invoice_total: float,
    ahri_certificate: str,          # AHRI certificate number/reference
    ladbs_permit_number: str        # Required for HVAC rebates
) -> RebateApplyResult

class RebateApplyResult(BaseModel):
    success: bool
    application_id: str
    estimated_rebate: float
    processing_time: str            # e.g., "8-12 weeks"
    next_steps: str
```

**Example:**
```python
# Input
rebates_apply(
    account_number="1234567890",
    equipment_type=EquipmentType.HEAT_PUMP_HVAC,
    equipment_details="Mitsubishi MXZ-3C30NAHZ2 outdoor unit with 3 indoor heads, 3 tons, SEER2 20.0, HSPF2 10.0",
    purchase_date=datetime(2026, 1, 10),
    invoice_total=15000.00,
    ahri_certificate="AHRI-12345678",
    ladbs_permit_number="2026-001235"
)

# Output
RebateApplyResult(
    success=True,
    application_id="CRP-2026-1234",
    estimated_rebate=7500.00,  # $2,500/ton x 3 tons
    processing_time="8-12 weeks",
    next_steps="Your application is submitted. LADWP may schedule a verification inspection. Rebate check will be mailed upon approval."
)
```

---

#### `rebates.getStatus`

Get detailed status of a specific rebate application.

**Type:** Automated

**Signature:**
```python
async def rebates_getStatus(
    application_id: str
) -> RebateApplication
```

---

## LASAN MCP Server

**Purpose:** LA Sanitation & Environment - Waste Collection and Disposal

### Enums

```python
class PickupType(str, Enum):
    BULKY_ITEM = "bulky_item"
    EWASTE = "ewaste"
    HAZARDOUS = "hazardous"

class ItemCategory(str, Enum):
    APPLIANCES = "appliances"           # Refrigerators, washers, etc.
    FURNITURE = "furniture"             # Sofas, mattresses, etc.
    ELECTRONICS = "electronics"         # TVs, computers, etc.
    CONSTRUCTION_DEBRIS = "construction_debris"  # NOT accepted

class PickupStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

### Models

```python
class ScheduledPickup(BaseModel):
    """A scheduled pickup."""
    pickup_id: str
    pickup_type: PickupType
    address: str
    scheduled_date: datetime
    items: List[str]
    status: PickupStatus
    confirmation_number: Optional[str]
    notes: Optional[str]

class EligibilityResult(BaseModel):
    """Result of pickup eligibility check."""
    address: str
    eligible_items: List[EligibleItem]
    ineligible_items: List[IneligibleItem]
    annual_limit: int                   # e.g., 10 collections/year
    collections_used: int
    collections_remaining: int

class EligibleItem(BaseModel):
    """An item eligible for pickup."""
    item_type: str
    pickup_type: PickupType
    notes: Optional[str]

class IneligibleItem(BaseModel):
    """An item not eligible for pickup."""
    item_type: str
    reason: str
    alternatives: List[str]             # Alternative disposal options
```

### Tools

---

#### `queryKB`

Search LASAN knowledge base for disposal guidelines, recycling info.

**Type:** Query

**Signature:**
```python
async def queryKB(
    query: str,
    top: int = 5
) -> KnowledgeResult
```

---

#### `pickup.scheduled`

View scheduled pickups for an address.

**Type:** Query

**Signature:**
```python
async def pickup_scheduled(
    address: str
) -> PickupScheduledResult

class PickupScheduledResult(BaseModel):
    address: str
    pickups: List[ScheduledPickup]
    total_count: int
```

**Example:**
```python
# Input
pickup_scheduled(address="123 Main St, Los Angeles, CA 90012")

# Output
PickupScheduledResult(
    address="123 Main St, Los Angeles, CA 90012",
    pickups=[
        ScheduledPickup(
            pickup_id="BULKY-2026-5678",
            pickup_type=PickupType.BULKY_ITEM,
            address="123 Main St, Los Angeles, CA 90012",
            scheduled_date=datetime(2026, 2, 20),
            items=["old furnace", "air conditioning unit"],
            status=PickupStatus.CONFIRMED,
            confirmation_number="LASAN-789456",
            notes="Place items curbside by 6am"
        )
    ],
    total_count=1
)
```

---

#### `pickup.schedule`

Prepare pickup scheduling request (requires user action - 311 call or MyLA311 app).

**Type:** User Action

**Signature:**
```python
async def pickup_schedule(
    address: str,
    pickup_type: PickupType,
    items: List[str],
    contact_name: str,
    contact_phone: str
) -> UserActionResponse
```

**Example:**
```python
# Input
pickup_schedule(
    address="123 Main St, Los Angeles, CA 90012",
    pickup_type=PickupType.BULKY_ITEM,
    items=["old furnace", "air conditioning unit"],
    contact_name="John Smith",
    contact_phone="555-0123"
)

# Output
UserActionResponse(
    requires_user_action=True,
    action_type="phone_call",
    target="311",
    reason="LASAN bulky item pickup scheduling requires 311 call or MyLA311 app",
    
    prepared_materials=PreparedMaterials(
        phone_script="Call 311 and say: 'I need to schedule a bulky item pickup at 123 Main St, Los Angeles. I have an old furnace and air conditioning unit to dispose of. My name is John Smith, phone 555-0123.'",
        checklist=[
            "Items accepted: furnace, AC unit (appliances with Freon - LASAN handles refrigerant)",
            "Maximum 10 bulky pickups per year, up to 10 items each",
            "Place items curbside by 6am on collection day",
            "Do not block sidewalk or street"
        ],
        contact_info={
            "phone": "311",
            "hours": "24/7",
            "app": "MyLA311 (iOS/Android)",
            "website": "https://myla311.lacity.org"
        },
        documents_needed=[]
    ),
    
    on_complete=OnCompletePrompt(
        prompt="Once scheduled, please tell me the pickup date and confirmation number",
        expected_info=["scheduled_date", "confirmation_number"]
    )
)
```

---

#### `pickup.getEligibility`

Check what items are eligible for pickup at an address.

**Type:** Query

**Signature:**
```python
async def pickup_getEligibility(
    address: str,
    item_types: List[str]
) -> EligibilityResult
```

**Example:**
```python
# Input
pickup_getEligibility(
    address="123 Main St, Los Angeles, CA 90012",
    item_types=["old furnace", "concrete roof tiles", "electrical cables", "old electrical panel"]
)

# Output
EligibilityResult(
    address="123 Main St, Los Angeles, CA 90012",
    eligible_items=[
        EligibleItem(
            item_type="old furnace",
            pickup_type=PickupType.BULKY_ITEM,
            notes="Freon-containing appliances accepted; LASAN handles refrigerant disposal"
        ),
        EligibleItem(
            item_type="electrical cables",
            pickup_type=PickupType.EWASTE,
            notes="E-waste curbside pickup available"
        ),
        EligibleItem(
            item_type="old electrical panel",
            pickup_type=PickupType.EWASTE,
            notes="Contains recyclable metals; accepted as e-waste"
        )
    ],
    ineligible_items=[
        IneligibleItem(
            item_type="concrete roof tiles",
            reason="Construction debris is not accepted for city pickup",
            alternatives=[
                "Private hauling service (e.g., Junkluggers, 1-800-GOT-JUNK)",
                "Self-haul to landfill",
                "S.A.F.E. Centers (limited quantities, weekends 9am-3pm)"
            ]
        )
    ],
    annual_limit=10,
    collections_used=2,
    collections_remaining=8
)
```

---

## Implementation Notes

### Error Handling

All tools should return errors in a consistent format:

```python
class MCPError(BaseModel):
    """Error response from MCP tool."""
    error: bool = True
    code: str           # e.g., "NOT_FOUND", "INVALID_INPUT", "SERVICE_UNAVAILABLE"
    message: str        # Human-readable error message
    details: Optional[dict]
```

### Authentication

All tools require authentication via the MCP server's configured auth mechanism (managed identity for Azure services, API key for external backends).

### Mocking for Demo

For the demo, backend calls return mock data. The mock layer should:
1. Return realistic data matching real agency responses
2. Simulate realistic delays (permits: days, inspections: hours)
3. Store state in memory or CosmosDB for consistency within a session

### Tool Registration

Each MCP server registers its tools with the standard MCP protocol. Tool names use dot notation (e.g., `permits.submit`) for logical grouping.
