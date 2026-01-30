#!/usr/bin/env python3
"""
CSP Agent Evaluation Runner using Azure AI Evaluation SDK.

This script runs LOCAL evaluations using Microsoft's official SDK.
NO CUSTOM EVALUATION LOGIC - uses only built-in evaluators.

Reference: https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk

Usage:
    uv run python -m evaluation.run_evaluation \
        --data evaluation_data/collected_responses.jsonl \
        --output evaluation_results/

    # Check against custom thresholds
    uv run python -m evaluation.run_evaluation \
        --data evaluation_data/collected_responses.jsonl \
        --thresholds evaluation/thresholds.yaml
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from azure.ai.evaluation import (
    CoherenceEvaluator,
    F1ScoreEvaluator,
    FluencyEvaluator,
    GroundednessEvaluator,
    RelevanceEvaluator,
    SimilarityEvaluator,
    evaluate,
)

from .config import get_model_config


def run_evaluation(
    data_path: str,
    output_path: str,
    evaluators_to_use: list[str] | None = None,
) -> dict[str, Any]:
    """
    Run evaluation using Azure AI Evaluation SDK.

    Args:
        data_path: Path to JSONL data file with query, response, context, ground_truth
        output_path: Directory to write evaluation results
        evaluators_to_use: Optional list of evaluator names to use (default: all)

    Returns:
        Dictionary with evaluation results
    """
    print("=" * 60)
    print("CSP Agent Evaluation - Azure AI Evaluation SDK")
    print("=" * 60)

    print(f"\nData file: {data_path}")
    print(f"Output directory: {output_path}")

    # Get model configuration for AI-assisted evaluators
    print("\nInitializing model configuration...")
    try:
        model_config = get_model_config()
        print(f"  ✓ Using deployment: {model_config.azure_deployment}")
    except ValueError as e:
        print(f"  ⚠ {e}")
        print("  Falling back to non-AI evaluators only")
        model_config = None

    # Initialize SDK evaluators (NO CUSTOM CODE)
    print("\nInitializing evaluators...")
    evaluators: dict[str, Any] = {}

    # Define all available evaluators
    available_evaluators = {
        # Quality evaluators (require model_config)
        "coherence": lambda: CoherenceEvaluator(model_config=model_config),
        "fluency": lambda: FluencyEvaluator(model_config=model_config),
        "relevance": lambda: RelevanceEvaluator(model_config=model_config),
        "groundedness": lambda: GroundednessEvaluator(model_config=model_config),
        "similarity": lambda: SimilarityEvaluator(model_config=model_config),
        # Non-AI evaluators (no model_config needed)
        "f1_score": lambda: F1ScoreEvaluator(),
    }

    # AI-assisted evaluators that require model_config
    ai_evaluators = {"coherence", "fluency", "relevance", "groundedness", "similarity"}

    # Determine which evaluators to use
    if evaluators_to_use is None:
        evaluators_to_use = list(available_evaluators.keys())

    for name in evaluators_to_use:
        if name not in available_evaluators:
            print(f"  ⚠ Unknown evaluator: {name}")
            continue

        # Skip AI evaluators if no model config
        if model_config is None and name in ai_evaluators:
            print(f"  ⚠ Skipping {name} (requires model configuration)")
            continue

        try:
            evaluators[name] = available_evaluators[name]()
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ⚠ Failed to initialize {name}: {e}")

    if not evaluators:
        print("\n✗ No evaluators available. Cannot proceed.")
        sys.exit(1)

    # Create output directory
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # Run batch evaluation using SDK's evaluate() function
    print("\nRunning evaluation...")
    print("  This may take a few minutes depending on dataset size...")

    try:
        result = evaluate(
            data=data_path,
            evaluators=evaluators,
            evaluator_config={
                "default": {
                    "column_mapping": {
                        "query": "${data.query}",
                        "response": "${data.response}",
                        "context": "${data.context}",
                        "ground_truth": "${data.ground_truth}",
                    }
                }
            },
            output_path=output_path,
        )

        print("\n  ✓ Evaluation complete!")
        return result

    except Exception as e:
        print(f"\n  ✗ Evaluation failed: {e}")
        raise


def check_thresholds(results: dict[str, Any], thresholds_path: str) -> bool:
    """
    Check if evaluation results meet defined thresholds.

    Args:
        results: Evaluation results from run_evaluation
        thresholds_path: Path to YAML file with threshold definitions

    Returns:
        True if all thresholds are met, False otherwise
    """
    if not Path(thresholds_path).exists():
        print(f"\n⚠ Thresholds file not found: {thresholds_path}")
        print("  Skipping threshold check.")
        return True

    with open(thresholds_path, "r") as f:
        thresholds = yaml.safe_load(f)

    passed = True
    metrics = results.get("metrics", {})

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    # Check pass thresholds
    pass_thresholds = thresholds.get("pass_thresholds", {})
    for metric_name, threshold in pass_thresholds.items():
        # Try different metric name formats
        actual = None
        for key_format in [
            metric_name,
            metric_name.replace(".", "_"),
            metric_name.split(".")[-1],
        ]:
            if key_format in metrics:
                actual = metrics[key_format]
                break

        if actual is None:
            print(f"{metric_name}: N/A (not computed)")
            continue

        if isinstance(actual, (int, float)):
            status = "✅ PASS" if actual >= threshold else "❌ FAIL"
            print(f"{metric_name}: {actual:.3f} (threshold: {threshold}) {status}")
            if actual < threshold:
                passed = False
        else:
            print(f"{metric_name}: {actual} (threshold: {threshold})")

    # Check safety thresholds (zero tolerance)
    safety_thresholds = thresholds.get("safety_thresholds", {})
    if safety_thresholds:
        print("\n--- Safety Metrics ---")
        for metric_name, threshold in safety_thresholds.items():
            actual = metrics.get(metric_name, metrics.get(metric_name.replace(".", "_")))
            if actual is not None:
                status = "✅ PASS" if actual <= threshold else "❌ FAIL"
                print(f"{metric_name}: {actual} (max: {threshold}) {status}")
                if actual > threshold:
                    passed = False

    print("=" * 60)
    print(f"OVERALL: {'✅ PASSED' if passed else '❌ FAILED'}")
    print("=" * 60)

    return passed


def print_summary(results: dict[str, Any]) -> None:
    """Print a summary of evaluation results."""
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    metrics = results.get("metrics", {})
    if metrics:
        print("\nAggregate Metrics:")
        for name, value in sorted(metrics.items()):
            if isinstance(value, float):
                print(f"  {name}: {value:.3f}")
            else:
                print(f"  {name}: {value}")

    rows = results.get("rows", [])
    if rows:
        print(f"\nEvaluated {len(rows)} samples")

    studio_url = results.get("studio_url")
    if studio_url:
        print(f"\nView in Azure AI Foundry Studio: {studio_url}")


def main():
    parser = argparse.ArgumentParser(
        description="Run CSP Agent evaluation using Azure AI Evaluation SDK"
    )
    parser.add_argument(
        "--data",
        "-d",
        required=True,
        type=str,
        help="Path to JSONL data file with collected responses",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="./evaluation_results",
        type=str,
        help="Output directory for evaluation results",
    )
    parser.add_argument(
        "--thresholds",
        "-t",
        default="evaluation/thresholds.yaml",
        type=str,
        help="Path to thresholds YAML file",
    )
    parser.add_argument(
        "--evaluators",
        "-e",
        nargs="+",
        choices=["coherence", "fluency", "relevance", "groundedness", "similarity", "f1_score"],
        help="Specific evaluators to run (default: all available)",
    )
    parser.add_argument(
        "--no-threshold-check",
        action="store_true",
        help="Skip threshold checking",
    )

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.data).exists():
        print(f"✗ Data file not found: {args.data}")
        print("\nRun the data collector first:")
        print("  uv run python -m evaluation.data_collector")
        sys.exit(1)

    # Run evaluation
    try:
        result = run_evaluation(
            data_path=args.data,
            output_path=args.output,
            evaluators_to_use=args.evaluators,
        )
    except Exception as e:
        print(f"\n✗ Evaluation failed: {e}")
        sys.exit(1)

    # Print summary
    print_summary(result)

    # Check thresholds
    if args.no_threshold_check:
        print("\nThreshold check skipped (--no-threshold-check)")
        sys.exit(0)

    passed = check_thresholds(result, args.thresholds)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
