# Project Plan Step Nomenclature

This document defines the standard step type codes used in project plans across all city agencies.

## Step Type Codes

| Code | Category | Description | Examples |
|------|----------|-------------|----------|
| **PRM** | Permit | Apply for/obtain official permits | Electrical permit, Building permit, Mechanical permit |
| **INS** | Inspection | City inspections (including final sign-off) | Rough electrical, Final inspection, Meter inspection |
| **TRD** | Trade | Hire professionals + physical work phases | Hire electrician, Install panel, Run conduit |
| **APP** | Application | Submit applications (non-permit) | Rebate application, Interconnection request, Service upgrade |
| **PCK** | Pickup | Schedule pickups and drop-offs | Bulky item pickup, Hazardous waste drop-off, E-waste collection |
| **ENR** | Enroll | Sign up for programs/plans | TOU rate plan, EV program, Recycling program |
| **DOC** | Document | Gather documents/materials | Load calculations, Site plans, Equipment specs |
| **PAY** | Payment | Pay fees/deposits | Permit fees, Service deposit, Plan check fees |

## Step ID Format

Step IDs follow the format: `{TYPE}-{NUMBER}`

Examples:
- `PRM-1` - First permit step
- `INS-2` - Second inspection step
- `TRD-1` - First trade/work step

## Step Type Details

### PRM - Permit
Permit steps involve applying for and obtaining official permits from city agencies.

**Agency Coverage:**
- **LADBS**: Electrical, Mechanical, Building, Plumbing permits
- **LADWP**: Generally no permits (uses APP instead)
- **LASAN**: Generally no permits (uses APP instead)

**Typical Flow:** `DOC → PRM → (wait for approval) → TRD`

### INS - Inspection
Inspection steps are city inspections required to verify work compliance. This includes final inspections and sign-offs.

**Agency Coverage:**
- **LADBS**: Rough inspections, Final inspections, Safety inspections
- **LADWP**: Meter inspections, Service verification
- **LASAN**: Generally no inspections

**Typical Flow:** `TRD → INS → (pass/fail)`

### TRD - Trade
Trade steps combine hiring licensed professionals and the physical work they perform.

**Agency Coverage:**
- **LADBS**: Licensed contractors (C-10 Electrician, General Contractor, Plumber)
- **LADWP**: Not typically used
- **LASAN**: Haulers for construction debris

**Typical Flow:** `PRM (approved) → TRD → INS`

### APP - Application
Application steps are non-permit applications to city programs and services.

**Agency Coverage:**
- **LADBS**: Not typically used (uses PRM instead)
- **LADWP**: Interconnection applications, Rebate applications, Service upgrades
- **LASAN**: Service change requests

**Typical Flow:** `DOC → APP → (processing) → ENR or PCK`

### PCK - Pickup
Pickup steps involve scheduling pickups and drop-offs with city services.

**Agency Coverage:**
- **LADBS**: Not typically used
- **LADWP**: Not typically used
- **LASAN**: Bulky item pickup, Hazardous waste drop-off, E-waste collection

**Typical Flow:** `APP → PCK`

### ENR - Enroll
Enrollment steps involve signing up for ongoing programs or rate plans.

**Agency Coverage:**
- **LADBS**: Not typically used
- **LADWP**: TOU rate plans, EV charging programs, Solar programs
- **LASAN**: Recycling programs, Composting programs

**Typical Flow:** `APP (approved) → ENR`

### DOC - Document
Document steps involve gathering required documents and materials before applications.

**Agency Coverage:**
- All agencies - preparation is universal

**Typical Flow:** `DOC → PRM or APP`

### PAY - Payment
Payment steps involve paying fees, deposits, or charges.

**Agency Coverage:**
- **LADBS**: Permit fees, Plan check fees
- **LADWP**: Service deposits, Connection fees
- **LASAN**: Generally no fees

**Typical Flow:** Usually parallel with `PRM` or `APP`

---

## Example Plan: 400A Electrical Panel Upgrade

```
DOC-1: Prepare electrical plans and load calculations      [LADBS]
PRM-1: Submit electrical permit application                [LADBS]
TRD-1: Hire licensed C-10 electrician                     [LADBS]
PAY-1: Pay permit and plan check fees                      [LADBS]
APP-1: Submit LADWP service upgrade request               [LADWP]
TRD-2: Install 400A panel and wiring                      [LADBS]
INS-1: Schedule and pass rough electrical inspection      [LADBS]
INS-2: Schedule and pass final electrical inspection      [LADBS]
```

**Dependency Graph:**
```
DOC-1 ──┬──► PRM-1 ──► APP-1 ──► TRD-2 ──► INS-1 ──► INS-2
        │                          ▲
        └──► TRD-1 ────────────────┘
        │
        └──► PAY-1
```

## Chat Reference Examples

Users and agents can reference steps by their short codes:

- "What's the status of TRD-1?"
- "Can we start INS-1 now?"
- "PRM-1 was approved, moving to TRD-2"
- "I need help with DOC-1"
