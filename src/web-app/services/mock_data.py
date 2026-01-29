"""Mock data for the Citizen Services Portal."""

from datetime import datetime, timedelta
from models.user import User
from models.project import (
    Project, Plan, PlanStep, StepStatus, ProjectStatus,
    UserTask, UserTaskType
)
from models.message import Message, MessageType


# Mock User
MOCK_USER = User(
    id="user-001",
    email="john.smith@example.com",
    name="John Smith",
    phone="555-0123",
)

# Mock project constants
MOCK_ADDRESS = "123 Main St, Los Angeles"
MOCK_PERMIT_NUMBER = "2026-001234"


# Mock Plan Steps for Home Renovation project
MOCK_PLAN_STEPS = [
    PlanStep(
        id="P1",
        title="Electrical Permit",
        agency="LADBS",
        status=StepStatus.COMPLETED,
        depends_on=[],
        completed_at=datetime.now() - timedelta(days=7),
        result={"permitNumber": MOCK_PERMIT_NUMBER},
    ),
    PlanStep(
        id="P2",
        title="Mechanical Permit",
        agency="LADBS",
        status=StepStatus.COMPLETED,
        depends_on=[],
        completed_at=datetime.now() - timedelta(days=6),
        result={"permitNumber": "2026-001235"},
    ),
    PlanStep(
        id="P3",
        title="Building Permit",
        agency="LADBS",
        status=StepStatus.COMPLETED,
        depends_on=[],
        completed_at=datetime.now() - timedelta(days=5),
        result={"permitNumber": "2026-001236"},
    ),
    PlanStep(
        id="U1",
        title="TOU Rate Enrollment",
        agency="LADWP",
        status=StepStatus.COMPLETED,
        depends_on=[],
        completed_at=datetime.now() - timedelta(days=4),
    ),
    PlanStep(
        id="U2",
        title="Interconnection Agreement",
        agency="LADWP",
        status=StepStatus.IN_PROGRESS,
        depends_on=["P1"],
        started_at=datetime.now() - timedelta(days=2),
    ),
    PlanStep(
        id="I1",
        title="Schedule Inspection",
        agency="LADBS",
        status=StepStatus.SCHEDULED,
        depends_on=["P1", "P2", "P3"],
        user_task=UserTask(
            type=UserTaskType.PHONE_CALL,
            target="311",
            reason="LADBS inspection scheduling is only available via phone",
            phone_script=(
                f"I need to schedule a rough electrical inspection for "
                f"permit #{MOCK_PERMIT_NUMBER} at {MOCK_ADDRESS}. "
                f"My name is {MOCK_USER.name}, phone {MOCK_USER.phone}."
            ),
            checklist=[
                f"Have permit number ready: {MOCK_PERMIT_NUMBER}",
                "Confirm work is ready for inspection",
                "Request morning slot if preferred",
            ],
            contact_info={
                "phone": "311",
                "hours": "24/7",
            },
        ),
    ),
    PlanStep(
        id="F1",
        title="Final Inspection",
        agency="LADBS",
        status=StepStatus.DEFINED,
        depends_on=["I1"],
    ),
]


# Mock Projects
MOCK_PROJECTS = [
    Project(
        id="proj-001",
        user_id="user-001",
        title="Home Renovation",
        description=f"Solar panel installation at {MOCK_ADDRESS}",
        status=ProjectStatus.ACTIVE,
        progress=0.8,
        created_at=datetime.now() - timedelta(days=14),
        updated_at=datetime.now() - timedelta(hours=2),
        plan=Plan(
            id="plan-001",
            status="active",
            steps=MOCK_PLAN_STEPS,
        ),
    ),
    Project(
        id="proj-002",
        user_id="user-001",
        title="Bulk Pickup",
        description="456 Oak Ave",
        status=ProjectStatus.COMPLETED,
        progress=1.0,
        created_at=datetime.now() - timedelta(days=7),
        updated_at=datetime.now() - timedelta(days=1),
        plan=Plan(
            id="plan-002",
            status="completed",
            steps=[],
        ),
    ),
]


# Mock Messages for Home Renovation project
MOCK_MESSAGES = [
    Message(
        id="msg-001",
        project_id="proj-001",
        message_type=MessageType.AGENT,
        content=(
            f"Hi! I'm here to help you with your home renovation project. "
            f"I see you want to install solar panels at {MOCK_ADDRESS}. "
            f"Let me help you navigate the permit process."
        ),
        timestamp=datetime.now() - timedelta(days=14),
        sender_name="Agent",
    ),
    Message(
        id="msg-002",
        project_id="proj-001",
        message_type=MessageType.USER,
        content="Yes, I want to install solar panels and battery storage on my house.",
        timestamp=datetime.now() - timedelta(days=14) + timedelta(minutes=5),
        sender_name=MOCK_USER.name,
    ),
    Message(
        id="msg-003",
        project_id="proj-001",
        message_type=MessageType.AGENT,
        content=(
            "Great! Based on your project, you'll need:\n\n"
            "• Electrical permit from LADBS\n"
            "• Mechanical permit from LADBS\n"
            "• Building permit from LADBS\n"
            "• Interconnection agreement with LADWP\n\n"
            "I've started the permit applications for you. "
            "The electrical permit has been approved!"
        ),
        timestamp=datetime.now() - timedelta(days=7),
        sender_name="Agent",
    ),
    Message(
        id="msg-004",
        project_id="proj-001",
        message_type=MessageType.AGENT,
        content=(
            "Your electrical permit has been approved! 🎉\n\n"
            "Now you need to **schedule the rough inspection**. "
            "This requires a phone call to 311."
        ),
        timestamp=datetime.now() - timedelta(hours=2),
        sender_name="Agent",
    ),
]


def get_mock_projects(user_id: str) -> list[Project]:
    """Get mock projects for a user."""
    return [p for p in MOCK_PROJECTS if p.user_id == user_id or user_id == "local-dev-user"]


def get_mock_project(project_id: str) -> Project | None:
    """Get a specific mock project by ID."""
    for project in MOCK_PROJECTS:
        if project.id == project_id:
            return project
    return None


def get_mock_messages(project_id: str) -> list[Message]:
    """Get mock messages for a project."""
    return [m for m in MOCK_MESSAGES if m.project_id == project_id]
