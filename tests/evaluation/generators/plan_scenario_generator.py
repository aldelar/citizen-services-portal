"""
Plan Scenario Generator

Generates test cases for multi-agency plan generation from demo storyline
and predefined scenarios.
"""

import json
from pathlib import Path
from typing import Any


class PlanScenarioGenerator:
    """Generate plan test scenarios from demo storyline and templates."""
    
    def __init__(self, demo_storyline_path: str = "./docs/3-demo-story-line.md") -> None:
        """
        Initialize the plan scenario generator.
        
        Args:
            demo_storyline_path: Path to demo storyline document
        """
        self.demo_storyline_path = Path(demo_storyline_path)
        self.demo_storyline = ""
        
        if self.demo_storyline_path.exists():
            self.demo_storyline = self.demo_storyline_path.read_text()
    
    def get_plan_scenarios(self) -> list[dict[str, Any]]:
        """
        Get predefined plan test scenarios.
        
        Returns:
            List of plan test cases
        """
        scenarios: list[dict[str, Any]] = []
        
        # John's Home Renovation (from demo storyline)
        scenarios.append({
            "id": "PLAN-001",
            "name": "Complete Home Solar Installation",
            "description": "Full solar panel installation with battery storage, TOU meter, and utility interconnection",
            "query": "I want to install 8.5kW solar panels with battery storage on my home. What's the complete process?",
            "expected_agencies": ["LADBS", "LADWP"],
            "expected_min_steps": 5,
            "expected_step_types": ["PRM", "INS", "ENR", "APP"],
            "expected_dependencies": True,
            "complexity": "multi_agency",
            "validation_rules": {
                "must_have_permit_step": True,
                "must_have_inspection_step": True,
                "must_have_interconnection_step": True,
                "must_have_tou_enrollment": True,
            },
        })
        
        scenarios.append({
            "id": "PLAN-002",
            "name": "Electrical Panel Upgrade",
            "description": "Upgrade from 200A to 400A panel for solar and EV readiness",
            "query": "I need to upgrade my electrical panel from 200A to 400A to support solar panels and an EV charger. What are all the steps?",
            "expected_agencies": ["LADBS", "LADWP"],
            "expected_min_steps": 4,
            "expected_step_types": ["PRM", "INS"],
            "expected_dependencies": True,
            "complexity": "multi_agency",
            "validation_rules": {
                "must_have_permit_step": True,
                "must_have_inspection_step": True,
                "panel_upgrade_mentioned": True,
            },
        })
        
        scenarios.append({
            "id": "PLAN-003",
            "name": "Heat Pump Installation with Rebate",
            "description": "Install ductless heat pumps and apply for LADWP CRP rebate",
            "query": "I want to replace my gas furnace with ductless heat pumps. How do I get the permits and apply for the LADWP rebate?",
            "expected_agencies": ["LADBS", "LADWP"],
            "expected_min_steps": 5,
            "expected_step_types": ["PRM", "INS", "REB", "APP"],
            "expected_dependencies": True,
            "complexity": "multi_agency",
            "validation_rules": {
                "must_have_permit_step": True,
                "must_have_inspection_step": True,
                "must_have_rebate_step": True,
            },
        })
        
        scenarios.append({
            "id": "PLAN-004",
            "name": "Complete Home Renovation",
            "description": "Full renovation: roof, rewiring, heat pumps, solar, and disposal",
            "query": "I'm doing a complete home renovation: new metal roof, full electrical rewiring, heat pump installation, solar panels, and I need to dispose of the old equipment. Create a complete plan.",
            "expected_agencies": ["LADBS", "LADWP", "LASAN"],
            "expected_min_steps": 8,
            "expected_step_types": ["PRM", "INS", "ENR", "APP", "DSP"],
            "expected_dependencies": True,
            "complexity": "full_renovation",
            "validation_rules": {
                "must_have_permit_step": True,
                "must_have_inspection_step": True,
                "must_have_disposal_step": True,
                "must_have_multiple_agencies": True,
            },
        })
        
        scenarios.append({
            "id": "PLAN-005",
            "name": "Simple Permit Application",
            "description": "Single agency permit for water heater replacement",
            "query": "I need to replace my water heater. What's the permit process?",
            "expected_agencies": ["LADBS"],
            "expected_min_steps": 2,
            "expected_step_types": ["PRM", "INS"],
            "expected_dependencies": True,
            "complexity": "single_agency",
            "validation_rules": {
                "must_have_permit_step": True,
                "must_have_inspection_step": True,
            },
        })
        
        scenarios.append({
            "id": "PLAN-006",
            "name": "TOU Rate Enrollment",
            "description": "Enroll in Time of Use rate plan for existing solar",
            "query": "I already have solar panels and want to switch to TOU-D-PRIME rate plan. What are the steps?",
            "expected_agencies": ["LADWP"],
            "expected_min_steps": 2,
            "expected_step_types": ["ENR"],
            "expected_dependencies": True,
            "complexity": "single_agency",
            "validation_rules": {
                "must_have_enrollment_step": True,
            },
        })
        
        scenarios.append({
            "id": "PLAN-007",
            "name": "Bulky Item Disposal",
            "description": "Schedule pickup for multiple bulky items",
            "query": "I need to dispose of an old refrigerator, washing machine, and some furniture. How do I schedule pickup?",
            "expected_agencies": ["LASAN"],
            "expected_min_steps": 1,
            "expected_step_types": ["DSP", "SCH"],
            "expected_dependencies": False,
            "complexity": "single_agency",
            "validation_rules": {
                "must_have_scheduling_step": True,
            },
        })
        
        return scenarios
    
    def export_jsonl(
        self,
        scenarios: list[dict[str, Any]],
        output_path: str,
    ) -> None:
        """
        Export plan scenarios to JSONL format.
        
        Args:
            scenarios: List of plan scenarios
            output_path: Path to write JSONL file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with output.open("w") as f:
            for scenario in scenarios:
                # Convert to evaluation format
                test_case = {
                    "id": scenario["id"],
                    "category": "plan_generation",
                    "subcategory": scenario["complexity"],
                    "query": scenario["query"],
                    "expected_agencies": scenario["expected_agencies"],
                    "expected_min_steps": scenario["expected_min_steps"],
                    "expected_step_types": scenario["expected_step_types"],
                    "expected_dependencies": scenario["expected_dependencies"],
                    "validation_rules": scenario["validation_rules"],
                    "description": scenario["description"],
                }
                f.write(json.dumps(test_case) + "\n")
