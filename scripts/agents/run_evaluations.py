#!/usr/bin/env python3
"""
DEPRECATED: This script has been replaced by the SDK-based evaluation suite.

Use the new evaluation runner instead:
    python -m evaluation.run_evaluation --data <data.jsonl> --output <output_dir>

See: scripts/agents/evaluation/run_evaluation.py
"""

import sys


def main():
    print("=" * 60)
    print("⚠️  DEPRECATED SCRIPT")
    print("=" * 60)
    print()
    print("This placeholder has been replaced by the SDK-based evaluation suite.")
    print()
    print("Please use the new evaluation runner:")
    print("  cd scripts/agents")
    print("  python -m evaluation.run_evaluation \\")
    print("    --data evaluation_data/collected_responses.jsonl \\")
    print("    --output evaluation_results/")
    print()
    print("See: scripts/agents/evaluation/run_evaluation.py")
    print("=" * 60)

    # Exit with error to fail CI if accidentally called
    return 1


if __name__ == "__main__":
    sys.exit(main())
