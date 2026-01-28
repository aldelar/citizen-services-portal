#!/usr/bin/env python3
"""
CSP Agent Evaluation Threshold Checker

Validates evaluation results against defined thresholds.
Returns non-zero exit code if thresholds are not met (for CI/CD gating).

Usage:
    python check_thresholds.py --results results/ --thresholds thresholds.yaml
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


def load_thresholds(thresholds_path: str) -> dict[str, Any]:
    """Load threshold configuration from YAML file."""
    with open(thresholds_path) as f:
        return yaml.safe_load(f)


def load_results(results_path: str) -> dict[str, Any]:
    """Load aggregated evaluation results."""
    results_file = Path(results_path) / "aggregated_results.json"
    
    if not results_file.exists():
        raise FileNotFoundError(f"Results file not found: {results_file}")
    
    with open(results_file) as f:
        return json.load(f)


def check_thresholds(
    results: dict[str, Any],
    thresholds: dict[str, Any],
) -> tuple[bool, list[str], list[str]]:
    """
    Check if evaluation results meet threshold requirements.
    
    Args:
        results: Aggregated evaluation results
        thresholds: Threshold configuration
        
    Returns:
        Tuple of (all_passed, failures, warnings)
    """
    failures: list[str] = []
    warnings: list[str] = []
    
    evaluator_results = results.get("evaluator_results", {})
    
    # Check built-in evaluator thresholds (1-5 scale)
    pass_thresholds = thresholds.get("pass_thresholds", {})
    for evaluator_name, threshold in pass_thresholds.items():
        if evaluator_name in evaluator_results:
            data = evaluator_results[evaluator_name]
            mean = data.get("mean")
            
            if mean is None:
                warnings.append(f"{evaluator_name}: No data available")
            elif mean < threshold:
                failures.append(
                    f"{evaluator_name}: {mean:.2f} < {threshold:.2f} (threshold)"
                )
            else:
                print(f"  ✓ {evaluator_name}: {mean:.2f} >= {threshold:.2f}")
    
    # Check custom evaluator thresholds (0-1 scale)
    custom_thresholds = thresholds.get("custom_thresholds", {})
    for evaluator_name, threshold in custom_thresholds.items():
        # Map threshold names to evaluator names
        evaluator_key = evaluator_name.replace("_valid", "").replace("_correct", "")
        
        if evaluator_key in evaluator_results:
            data = evaluator_results[evaluator_key]
            mean = data.get("mean")
            
            if mean is None:
                warnings.append(f"{evaluator_name}: No data available")
            elif mean < threshold:
                failures.append(
                    f"{evaluator_name}: {mean:.2f} < {threshold:.2f} (threshold)"
                )
            else:
                print(f"  ✓ {evaluator_name}: {mean:.2f} >= {threshold:.2f}")
    
    # Check safety thresholds (zero tolerance)
    safety_thresholds = thresholds.get("safety_thresholds", {})
    unsafe_rate = safety_thresholds.get("unsafe_response_rate", 0.0)
    
    # Calculate unsafe response rate from safety evaluator results
    if "safety_boundary" in evaluator_results:
        data = evaluator_results["safety_boundary"]
        total = data.get("total", 0)
        failed = data.get("failed", 0)
        
        if total > 0:
            actual_unsafe_rate = failed / total
            if actual_unsafe_rate > unsafe_rate:
                failures.append(
                    f"unsafe_response_rate: {actual_unsafe_rate:.2%} > "
                    f"{unsafe_rate:.2%} (threshold)"
                )
            else:
                print(f"  ✓ unsafe_response_rate: {actual_unsafe_rate:.2%} <= {unsafe_rate:.2%}")
    
    # Check prompt-based evaluator thresholds
    prompt_thresholds = thresholds.get("prompt_thresholds", {})
    for evaluator_name, threshold in prompt_thresholds.items():
        if evaluator_name in evaluator_results:
            data = evaluator_results[evaluator_name]
            mean = data.get("mean")
            
            if mean is None:
                warnings.append(f"{evaluator_name}: No data available")
            elif mean < threshold:
                failures.append(
                    f"{evaluator_name}: {mean:.2f} < {threshold:.2f} (threshold)"
                )
            else:
                print(f"  ✓ {evaluator_name}: {mean:.2f} >= {threshold:.2f}")
    
    all_passed = len(failures) == 0
    
    return all_passed, failures, warnings


def generate_check_report(
    passed: bool,
    failures: list[str],
    warnings: list[str],
    output_path: Path,
) -> None:
    """Generate a threshold check report."""
    report_lines: list[str] = [
        "# Threshold Check Report",
        "",
        f"**Status:** {'✅ PASSED' if passed else '❌ FAILED'}",
        "",
    ]
    
    if failures:
        report_lines.extend([
            "## Failures",
            "",
        ])
        for failure in failures:
            report_lines.append(f"- ❌ {failure}")
        report_lines.append("")
    
    if warnings:
        report_lines.extend([
            "## Warnings",
            "",
        ])
        for warning in warnings:
            report_lines.append(f"- ⚠️ {warning}")
        report_lines.append("")
    
    if not failures and not warnings:
        report_lines.append("All thresholds met! 🎉")
        report_lines.append("")
    
    with open(output_path / "threshold_check.md", "w") as f:
        f.write("\n".join(report_lines))


def main() -> int:
    """Main entry point for threshold checker."""
    parser = argparse.ArgumentParser(
        description="Check evaluation results against thresholds"
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to evaluation results directory",
    )
    parser.add_argument(
        "--thresholds",
        required=True,
        help="Path to thresholds configuration",
    )
    
    args = parser.parse_args()
    
    print("🔍 CSP Agent Threshold Checker")
    print("=" * 50)
    
    # Load thresholds
    thresholds_path = Path(args.thresholds)
    if not thresholds_path.exists():
        print(f"❌ Thresholds file not found: {thresholds_path}")
        return 1
    
    thresholds = load_thresholds(str(thresholds_path))
    print(f"✓ Loaded thresholds from {thresholds_path}")
    
    # Load results
    results_path = Path(args.results)
    try:
        results = load_results(str(results_path))
        print(f"✓ Loaded results from {results_path}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1
    
    print("\n📊 Checking thresholds...")
    print("-" * 50)
    
    # Check thresholds
    passed, failures, warnings = check_thresholds(results, thresholds)
    
    print("-" * 50)
    
    # Generate report
    generate_check_report(passed, failures, warnings, results_path)
    
    # Print summary
    print("")
    if failures:
        print("❌ FAILURES:")
        for failure in failures:
            print(f"   - {failure}")
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
    
    print("")
    if passed:
        print("✅ All thresholds met!")
        return 0
    else:
        print("❌ Threshold check failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
