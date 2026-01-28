#!/usr/bin/env python3
"""
Test Data Generator CLI

Generate test datasets for CSP Agent evaluation.

Usage:
    python generate_test_data.py --type all --output-dir data/
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.evaluation.generators import (
    AdversarialGenerator,
    CSPTestDataGenerator,
    KBQAGenerator,
    PlanScenarioGenerator,
)


def main() -> int:
    """Main entry point for test data generator CLI."""
    parser = argparse.ArgumentParser(
        description="Generate test data for CSP Agent evaluation"
    )
    parser.add_argument(
        "--type",
        choices=["regression", "plan", "kb_qa", "adversarial", "all"],
        default="all",
        help="Type of test data to generate",
    )
    parser.add_argument(
        "--output-dir",
        default="tests/evaluation/data",
        help="Output directory for generated test data",
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🏛️  CSP Agent Test Data Generator")
    print("=" * 50)
    
    if args.type in ["regression", "all"]:
        print("\n📋 Generating regression tests...")
        generator = CSPTestDataGenerator()
        tests = generator.generate_regression_tests()
        generator.export_jsonl(tests, str(output_dir / "regression_tests.jsonl"))
        print(f"   Generated {len(tests)} regression test cases")
    
    if args.type in ["plan", "all"]:
        print("\n📋 Generating plan scenarios...")
        generator = PlanScenarioGenerator()
        scenarios = generator.get_plan_scenarios()
        generator.export_jsonl(scenarios, str(output_dir / "multi_agency_scenarios.jsonl"))
        print(f"   Generated {len(scenarios)} plan scenarios")
    
    if args.type in ["kb_qa", "all"]:
        print("\n📋 Generating KB Q&A pairs...")
        generator = KBQAGenerator()
        qa_pairs = generator.generate_manual_qa_pairs()
        generator.export_jsonl(qa_pairs, str(output_dir / "kb_qa_pairs.jsonl"))
        print(f"   Generated {len(qa_pairs)} Q&A pairs")
        
        inventory = generator.get_document_inventory()
        print(f"   KB document inventory: {inventory}")
    
    if args.type in ["adversarial", "all"]:
        print("\n📋 Generating adversarial tests...")
        generator = AdversarialGenerator()
        tests = generator.generate_all_adversarial_tests()
        generator.export_jsonl(tests, str(output_dir / "adversarial_tests.jsonl"))
        print(f"   Generated {len(tests)} adversarial test cases")
    
    print("\n" + "=" * 50)
    print("✅ Test data generation complete!")
    print(f"   Output directory: {output_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
