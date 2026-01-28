#!/usr/bin/env python3
"""
CSP Agent Evaluation Runner

Main script for running evaluations on the CSP Agent using
Azure AI Evaluation SDK and custom evaluators.

Usage:
    python run_evaluation.py --dataset data/regression_tests.jsonl --output-path results
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def load_thresholds(thresholds_path: str) -> dict[str, Any]:
    """Load threshold configuration from YAML file."""
    with open(thresholds_path) as f:
        return yaml.safe_load(f)


def load_test_data(dataset_path: str) -> list[dict[str, Any]]:
    """Load test data from JSONL file."""
    test_cases: list[dict[str, Any]] = []
    with open(dataset_path) as f:
        for line in f:
            if line.strip():
                test_cases.append(json.loads(line))
    return test_cases


def setup_azure_evaluators(model_config: dict[str, Any]) -> dict[str, Any]:
    """
    Set up Azure AI Evaluation SDK built-in evaluators.
    
    Returns a dictionary of evaluator instances.
    """
    evaluators: dict[str, Any] = {}
    
    try:
        from azure.ai.evaluation import (
            CoherenceEvaluator,
            GroundednessEvaluator,
            RelevanceEvaluator,
        )
        
        # Initialize built-in evaluators with model config
        evaluators["coherence"] = CoherenceEvaluator(model_config=model_config)
        evaluators["groundedness"] = GroundednessEvaluator(model_config=model_config)
        evaluators["relevance"] = RelevanceEvaluator(model_config=model_config)
        
        print("✓ Azure AI Evaluation SDK evaluators initialized")
        
    except ImportError as e:
        print(f"⚠ Azure AI Evaluation SDK not available: {e}")
        print("  Running with custom evaluators only")
    except Exception as e:
        print(f"⚠ Error initializing Azure evaluators: {e}")
    
    return evaluators


def setup_custom_evaluators() -> dict[str, Any]:
    """
    Set up custom CSP evaluators.
    
    Returns a dictionary of custom evaluator instances.
    """
    evaluators: dict[str, Any] = {}
    
    try:
        from tests.evaluation.evaluators import (
            ActionTypeClassificationEvaluator,
            AgencyBoundaryEvaluator,
            CitationAccuracyEvaluator,
            PlanDependencyEvaluator,
            StepTypeConventionEvaluator,
        )
        
        evaluators["agency_boundary"] = AgencyBoundaryEvaluator()
        evaluators["plan_dependency"] = PlanDependencyEvaluator()
        evaluators["step_type_convention"] = StepTypeConventionEvaluator()
        evaluators["citation_accuracy"] = CitationAccuracyEvaluator()
        evaluators["action_type"] = ActionTypeClassificationEvaluator()
        
        print("✓ Custom CSP evaluators initialized")
        
    except ImportError as e:
        print(f"⚠ Error importing custom evaluators: {e}")
    
    return evaluators


def run_evaluation(
    test_cases: list[dict[str, Any]],
    azure_evaluators: dict[str, Any],
    custom_evaluators: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """
    Run evaluation on all test cases.
    
    Args:
        test_cases: List of test cases to evaluate
        azure_evaluators: Azure AI Evaluation SDK evaluators
        custom_evaluators: Custom CSP evaluators
        output_path: Path to store results
        
    Returns:
        Aggregated evaluation results
    """
    results: list[dict[str, Any]] = []
    
    print(f"\n📊 Running evaluation on {len(test_cases)} test cases...")
    
    for i, test_case in enumerate(test_cases):
        test_id = test_case.get("id", f"test-{i}")
        query = test_case.get("query", "")
        
        # For now, we'll use a placeholder response
        # In actual use, this would call the agent
        response = test_case.get("response", "")
        context = test_case.get("context", "")
        
        if not response:
            # Skip test cases without responses (they need agent execution)
            results.append({
                "id": test_id,
                "query": query,
                "status": "skipped",
                "reason": "No response provided - requires agent execution",
            })
            continue
        
        case_results: dict[str, Any] = {
            "id": test_id,
            "query": query,
            "category": test_case.get("category", "unknown"),
            "evaluations": {},
        }
        
        # Run custom evaluators
        for name, evaluator in custom_evaluators.items():
            try:
                result = evaluator(
                    query=query,
                    response=response,
                    context=context,
                )
                case_results["evaluations"][name] = result
            except Exception as e:
                case_results["evaluations"][name] = {
                    "score": None,
                    "error": str(e),
                }
        
        # Run Azure evaluators (if available and response exists)
        for name, evaluator in azure_evaluators.items():
            try:
                if name == "groundedness":
                    result = evaluator(
                        response=response,
                        context=context,
                    )
                else:
                    result = evaluator(
                        query=query,
                        response=response,
                    )
                case_results["evaluations"][name] = result
            except Exception as e:
                case_results["evaluations"][name] = {
                    "score": None,
                    "error": str(e),
                }
        
        results.append(case_results)
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(test_cases)} test cases")
    
    # Calculate aggregated metrics
    aggregated = aggregate_results(results)
    
    # Save detailed results
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / "detailed_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    with open(output_path / "aggregated_results.json", "w") as f:
        json.dump(aggregated, f, indent=2, default=str)
    
    # Generate summary report
    generate_summary_report(aggregated, results, output_path)
    
    return aggregated


def aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate evaluation results across all test cases."""
    aggregated: dict[str, dict[str, Any]] = {}
    
    for result in results:
        if result.get("status") == "skipped":
            continue
            
        evaluations = result.get("evaluations", {})
        
        for eval_name, eval_result in evaluations.items():
            if eval_name not in aggregated:
                aggregated[eval_name] = {
                    "scores": [],
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "errors": 0,
                }
            
            if isinstance(eval_result, dict):
                score = eval_result.get("score")
                if score is not None:
                    aggregated[eval_name]["scores"].append(score)
                    aggregated[eval_name]["total"] += 1
                    # Consider score >= 0.8 (or 4.0 for 1-5 scale) as passed
                    threshold = 0.8 if score <= 1.0 else 4.0
                    if score >= threshold:
                        aggregated[eval_name]["passed"] += 1
                    else:
                        aggregated[eval_name]["failed"] += 1
                elif eval_result.get("error"):
                    aggregated[eval_name]["errors"] += 1
    
    # Calculate means
    for eval_name, data in aggregated.items():
        scores = data["scores"]
        if scores:
            data["mean"] = sum(scores) / len(scores)
            data["min"] = min(scores)
            data["max"] = max(scores)
        else:
            data["mean"] = None
            data["min"] = None
            data["max"] = None
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_test_cases": len(results),
        "evaluator_results": aggregated,
    }


def generate_summary_report(
    aggregated: dict[str, Any],
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    """Generate a markdown summary report."""
    report_lines: list[str] = [
        "# CSP Agent Evaluation Report",
        "",
        f"**Generated:** {aggregated['timestamp']}",
        f"**Total Test Cases:** {aggregated['total_test_cases']}",
        "",
        "## Summary",
        "",
        "| Evaluator | Mean Score | Pass Rate | Status |",
        "|-----------|------------|-----------|--------|",
    ]
    
    evaluator_results = aggregated.get("evaluator_results", {})
    
    for eval_name, data in evaluator_results.items():
        mean = data.get("mean")
        total = data.get("total", 0)
        passed = data.get("passed", 0)
        
        if mean is not None:
            # Determine if score is 0-1 scale or 1-5 scale
            is_5_scale = mean > 1.0
            threshold = 4.0 if is_5_scale else 0.8
            
            pass_rate = (passed / total * 100) if total > 0 else 0
            status = "✅ PASS" if mean >= threshold else "❌ FAIL"
            
            mean_str = f"{mean:.2f}"
            pass_rate_str = f"{pass_rate:.1f}%"
        else:
            mean_str = "N/A"
            pass_rate_str = "N/A"
            status = "⚠️ No data"
        
        report_lines.append(
            f"| {eval_name} | {mean_str} | {pass_rate_str} | {status} |"
        )
    
    report_lines.extend([
        "",
        "## Details",
        "",
        "### Category Breakdown",
        "",
    ])
    
    # Group by category
    categories: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        category = result.get("category", "unknown")
        if category not in categories:
            categories[category] = []
        categories[category].append(result)
    
    for category, cat_results in categories.items():
        skipped = sum(1 for r in cat_results if r.get("status") == "skipped")
        evaluated = len(cat_results) - skipped
        report_lines.append(f"- **{category}**: {evaluated} evaluated, {skipped} skipped")
    
    report_lines.extend([
        "",
        "---",
        "",
        "*Report generated by CSP Agent Evaluation Framework*",
    ])
    
    with open(output_path / "summary.md", "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"✓ Summary report saved to {output_path / 'summary.md'}")


def main() -> int:
    """Main entry point for evaluation runner."""
    parser = argparse.ArgumentParser(
        description="Run CSP Agent evaluation"
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to test dataset (JSONL format)",
    )
    parser.add_argument(
        "--output-path",
        default="tests/evaluation/results",
        help="Path to store evaluation results",
    )
    parser.add_argument(
        "--thresholds",
        default="tests/evaluation/thresholds.yaml",
        help="Path to thresholds configuration",
    )
    
    args = parser.parse_args()
    
    print("🏛️  CSP Agent Evaluation Framework")
    print("=" * 50)
    
    # Validate paths
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        return 1
    
    output_path = Path(args.output_path)
    thresholds_path = Path(args.thresholds)
    
    # Load thresholds
    thresholds: dict[str, Any] = {}
    if thresholds_path.exists():
        thresholds = load_thresholds(str(thresholds_path))
        print(f"✓ Loaded thresholds from {thresholds_path}")
    
    # Load test data
    test_cases = load_test_data(str(dataset_path))
    print(f"✓ Loaded {len(test_cases)} test cases from {dataset_path}")
    
    # Set up model config for Azure evaluators
    model_config = {
        "azure_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        "api_key": os.environ.get("AZURE_OPENAI_API_KEY", ""),
        "azure_deployment": os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        "api_version": "2024-02-15-preview",
    }
    
    # Set up evaluators
    azure_evaluators = setup_azure_evaluators(model_config)
    custom_evaluators = setup_custom_evaluators()
    
    # Run evaluation
    results = run_evaluation(
        test_cases,
        azure_evaluators,
        custom_evaluators,
        output_path,
    )
    
    print("\n" + "=" * 50)
    print("✅ Evaluation complete!")
    print(f"   Results saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
