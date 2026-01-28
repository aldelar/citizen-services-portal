#!/usr/bin/env python3
"""
Evaluation Results Analyzer

Analyze trends in evaluation results over time.

Usage:
    python analyze_results.py --results-dir results/ --compare previous_results/
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def load_results(results_path: Path) -> dict[str, Any] | None:
    """Load aggregated results from a directory."""
    results_file = results_path / "aggregated_results.json"
    
    if not results_file.exists():
        return None
    
    with open(results_file) as f:
        return json.load(f)


def compare_results(
    current: dict[str, Any],
    previous: dict[str, Any],
) -> dict[str, Any]:
    """Compare current and previous evaluation results."""
    comparison: dict[str, Any] = {
        "current_timestamp": current.get("timestamp"),
        "previous_timestamp": previous.get("timestamp"),
        "evaluator_comparisons": {},
    }
    
    current_evals = current.get("evaluator_results", {})
    previous_evals = previous.get("evaluator_results", {})
    
    all_evaluators = set(current_evals.keys()) | set(previous_evals.keys())
    
    for evaluator in all_evaluators:
        curr_data = current_evals.get(evaluator, {})
        prev_data = previous_evals.get(evaluator, {})
        
        curr_mean = curr_data.get("mean")
        prev_mean = prev_data.get("mean")
        
        if curr_mean is not None and prev_mean is not None:
            delta = curr_mean - prev_mean
            pct_change = (delta / prev_mean * 100) if prev_mean != 0 else 0
            
            comparison["evaluator_comparisons"][evaluator] = {
                "current": curr_mean,
                "previous": prev_mean,
                "delta": delta,
                "pct_change": pct_change,
                "improved": delta > 0,
                "regressed": delta < -0.1,  # Allow small fluctuation
            }
        elif curr_mean is not None:
            comparison["evaluator_comparisons"][evaluator] = {
                "current": curr_mean,
                "previous": None,
                "status": "new",
            }
        elif prev_mean is not None:
            comparison["evaluator_comparisons"][evaluator] = {
                "current": None,
                "previous": prev_mean,
                "status": "missing",
            }
    
    return comparison


def print_analysis(results: dict[str, Any]) -> None:
    """Print analysis of evaluation results."""
    print("\n📊 Evaluation Results Analysis")
    print("=" * 60)
    print(f"Timestamp: {results.get('timestamp', 'N/A')}")
    print(f"Total Test Cases: {results.get('total_test_cases', 0)}")
    print()
    
    evaluator_results = results.get("evaluator_results", {})
    
    if not evaluator_results:
        print("No evaluator results available.")
        return
    
    print("| Evaluator | Mean | Min | Max | Pass Rate |")
    print("|-----------|------|-----|-----|-----------|")
    
    for name, data in sorted(evaluator_results.items()):
        mean = data.get("mean")
        min_val = data.get("min")
        max_val = data.get("max")
        total = data.get("total", 0)
        passed = data.get("passed", 0)
        
        mean_str = f"{mean:.2f}" if mean is not None else "N/A"
        min_str = f"{min_val:.2f}" if min_val is not None else "N/A"
        max_str = f"{max_val:.2f}" if max_val is not None else "N/A"
        pass_rate = f"{passed/total*100:.1f}%" if total > 0 else "N/A"
        
        print(f"| {name:25} | {mean_str:>4} | {min_str:>3} | {max_str:>3} | {pass_rate:>9} |")


def print_comparison(comparison: dict[str, Any]) -> None:
    """Print comparison between current and previous results."""
    print("\n📈 Results Comparison")
    print("=" * 60)
    print(f"Current: {comparison.get('current_timestamp', 'N/A')}")
    print(f"Previous: {comparison.get('previous_timestamp', 'N/A')}")
    print()
    
    evals = comparison.get("evaluator_comparisons", {})
    
    if not evals:
        print("No comparisons available.")
        return
    
    improved_count = 0
    regressed_count = 0
    
    print("| Evaluator | Current | Previous | Delta | Status |")
    print("|-----------|---------|----------|-------|--------|")
    
    for name, data in sorted(evals.items()):
        current = data.get("current")
        previous = data.get("previous")
        delta = data.get("delta")
        
        current_str = f"{current:.2f}" if current is not None else "N/A"
        previous_str = f"{previous:.2f}" if previous is not None else "N/A"
        
        if delta is not None:
            delta_str = f"{delta:+.2f}"
            if data.get("improved"):
                status = "✅ ↑"
                improved_count += 1
            elif data.get("regressed"):
                status = "❌ ↓"
                regressed_count += 1
            else:
                status = "➡️"
        elif data.get("status") == "new":
            delta_str = "new"
            status = "🆕"
        else:
            delta_str = "N/A"
            status = "⚠️"
        
        print(f"| {name:25} | {current_str:>7} | {previous_str:>8} | {delta_str:>5} | {status:>6} |")
    
    print()
    print(f"Summary: {improved_count} improved, {regressed_count} regressed")


def main() -> int:
    """Main entry point for results analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze CSP Agent evaluation results"
    )
    parser.add_argument(
        "--results-dir",
        default="tests/evaluation/results",
        help="Path to current evaluation results",
    )
    parser.add_argument(
        "--compare",
        help="Path to previous results for comparison",
    )
    parser.add_argument(
        "--output",
        help="Path to save analysis output (JSON)",
    )
    
    args = parser.parse_args()
    
    results_path = Path(args.results_dir)
    
    if not results_path.exists():
        print(f"❌ Results directory not found: {results_path}")
        return 1
    
    results = load_results(results_path)
    
    if results is None:
        print(f"❌ No aggregated results found in {results_path}")
        return 1
    
    print_analysis(results)
    
    if args.compare:
        compare_path = Path(args.compare)
        previous = load_results(compare_path)
        
        if previous:
            comparison = compare_results(results, previous)
            print_comparison(comparison)
            
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(comparison, f, indent=2, default=str)
                print(f"\n✅ Comparison saved to {args.output}")
        else:
            print(f"\n⚠️ No previous results found at {compare_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
