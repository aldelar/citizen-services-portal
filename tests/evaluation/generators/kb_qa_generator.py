"""
KB Q&A Generator

Generates question-answer pairs from knowledge base documents
using LLM-powered extraction.
"""

import json
from pathlib import Path
from typing import Any


class KBQAGenerator:
    """Generate Q&A pairs from knowledge base documents."""
    
    def __init__(self, kb_path: str = "./assets") -> None:
        """
        Initialize the KB Q&A generator.
        
        Args:
            kb_path: Path to knowledge base documents
        """
        self.kb_path = Path(kb_path)
        self.agency_docs: dict[str, list[dict[str, Any]]] = {}
        self._load_kb_documents()
    
    def _load_kb_documents(self) -> None:
        """Load knowledge base documents organized by agency."""
        for agency in ["ladbs", "ladwp", "lasan"]:
            agency_path = self.kb_path / agency
            if agency_path.exists():
                self.agency_docs[agency] = []
                for file_path in agency_path.glob("*.html"):
                    content = file_path.read_text(errors="ignore")
                    self.agency_docs[agency].append({
                        "filename": file_path.name,
                        "path": str(file_path),
                        "content": content,
                        "agency": agency.upper(),
                    })
    
    def get_document_inventory(self) -> dict[str, int]:
        """
        Get count of documents per agency.
        
        Returns:
            Dictionary mapping agency to document count
        """
        return {
            agency: len(docs) 
            for agency, docs in self.agency_docs.items()
        }
    
    def generate_manual_qa_pairs(self) -> list[dict[str, Any]]:
        """
        Generate manual Q&A pairs based on known KB content.
        
        These are hand-crafted pairs for critical functionality testing.
        
        Returns:
            List of Q&A test cases
        """
        qa_pairs: list[dict[str, Any]] = []
        
        # LADBS Q&A pairs
        ladbs_pairs = [
            {
                "query": "What permits are required for installing solar panels?",
                "expected_answer_keywords": ["electrical permit", "plan check", "LADBS"],
                "agency": "LADBS",
                "topic": "solar_permits",
            },
            {
                "query": "How much does an electrical permit cost?",
                "expected_answer_keywords": ["fee", "valuation", "permit"],
                "agency": "LADBS",
                "topic": "permit_fees",
            },
            {
                "query": "What is the Title 24 requirement?",
                "expected_answer_keywords": ["energy", "California", "compliance"],
                "agency": "LADBS",
                "topic": "title_24",
            },
            {
                "query": "How do I schedule an electrical inspection?",
                "expected_answer_keywords": ["311", "schedule", "inspection"],
                "agency": "LADBS",
                "topic": "inspections",
            },
            {
                "query": "What are the requirements for a panel upgrade permit?",
                "expected_answer_keywords": ["electrical", "panel", "permit", "load"],
                "agency": "LADBS",
                "topic": "panel_upgrade",
            },
        ]
        
        # LADWP Q&A pairs
        ladwp_pairs = [
            {
                "query": "What is the TOU-D-PRIME rate plan?",
                "expected_answer_keywords": ["time of use", "solar", "rate"],
                "agency": "LADWP",
                "topic": "tou_rates",
            },
            {
                "query": "How do I apply for solar interconnection?",
                "expected_answer_keywords": ["interconnection", "application", "solar"],
                "agency": "LADWP",
                "topic": "interconnection",
            },
            {
                "query": "What rebates are available for heat pumps?",
                "expected_answer_keywords": ["CRP", "rebate", "heat pump", "HVAC"],
                "agency": "LADWP",
                "topic": "rebates",
            },
            {
                "query": "What are the off-peak hours for TOU rates?",
                "expected_answer_keywords": ["off-peak", "hours", "rate"],
                "agency": "LADWP",
                "topic": "tou_schedule",
            },
            {
                "query": "How do I enroll in a Time of Use rate plan?",
                "expected_answer_keywords": ["enroll", "TOU", "account"],
                "agency": "LADWP",
                "topic": "tou_enrollment",
            },
        ]
        
        # LASAN Q&A pairs
        lasan_pairs = [
            {
                "query": "How do I schedule bulky item pickup?",
                "expected_answer_keywords": ["311", "bulky", "schedule", "pickup"],
                "agency": "LASAN",
                "topic": "bulky_pickup",
            },
            {
                "query": "What items are accepted for curbside pickup?",
                "expected_answer_keywords": ["appliances", "furniture", "curbside"],
                "agency": "LASAN",
                "topic": "accepted_items",
            },
            {
                "query": "Where can I dispose of hazardous waste?",
                "expected_answer_keywords": ["SAFE", "center", "hazardous"],
                "agency": "LASAN",
                "topic": "hazardous_waste",
            },
            {
                "query": "How do I dispose of old electrical panels?",
                "expected_answer_keywords": ["e-waste", "electronic", "recycle"],
                "agency": "LASAN",
                "topic": "ewaste",
            },
            {
                "query": "How many free pickups can I schedule per year?",
                "expected_answer_keywords": ["10", "collections", "year", "free"],
                "agency": "LASAN",
                "topic": "pickup_limits",
            },
        ]
        
        all_pairs = ladbs_pairs + ladwp_pairs + lasan_pairs
        
        for idx, pair in enumerate(all_pairs, start=1):
            qa_pairs.append({
                "id": f"KB-{idx:03d}",
                "category": "kb_qa",
                "query": pair["query"],
                "expected_answer_keywords": pair["expected_answer_keywords"],
                "expected_agencies": [pair["agency"]],
                "expected_tools": [f"{pair['agency']}_queryKB"],
                "topic": pair["topic"],
                "context": f"Testing {pair['agency']} knowledge base accuracy",
            })
        
        return qa_pairs
    
    def export_jsonl(
        self,
        qa_pairs: list[dict[str, Any]],
        output_path: str,
    ) -> None:
        """
        Export Q&A pairs to JSONL format.
        
        Args:
            qa_pairs: List of Q&A pairs to export
            output_path: Path to write JSONL file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with output.open("w") as f:
            for pair in qa_pairs:
                f.write(json.dumps(pair) + "\n")
