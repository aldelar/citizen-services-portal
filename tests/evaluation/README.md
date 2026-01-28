# CSP Agent Evaluation Framework

This directory contains the evaluation and testing framework for the Citizen Services Portal (CSP) Agent. The framework uses the Azure AI Evaluation SDK along with custom evaluators to ensure the agent delivers accurate, safe, and on-task responses.

## 🎯 Objectives

1. **Accuracy Validation** - Ensure the agent provides correct information from agency knowledge bases
2. **Safety Assurance** - Verify the agent avoids harmful, misleading, or inappropriate responses
3. **Task Adherence** - Confirm the agent stays focused on citizen services for LA city agencies
4. **Tool Usage Accuracy** - Validate correct MCP tool selection and parameter usage
5. **Multi-Agency Coordination** - Test plan generation with proper dependency chains
6. **Automated CI/CD Integration** - Fail PRs that degrade agent quality

## 📁 Directory Structure

```
tests/evaluation/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── run_evaluation.py                   # Main evaluation runner
├── check_thresholds.py                 # Threshold validation script
├── thresholds.yaml                     # Pass/fail thresholds
│
├── data/
│   ├── regression_tests.jsonl          # Core regression test set
│   ├── multi_agency_scenarios.jsonl    # Multi-agency plan tests
│   └── safety_tests.jsonl              # Safety boundary tests
│
├── generators/
│   ├── __init__.py
│   ├── test_data_generator.py          # Main generator class
│   ├── kb_qa_generator.py              # Generate Q&A from KB docs
│   ├── plan_scenario_generator.py      # Generate plan test cases
│   └── adversarial_generator.py        # Generate edge cases
│
├── evaluators/
│   ├── __init__.py
│   ├── agency_boundary.py              # Custom: scope validation
│   ├── plan_dependency.py              # Custom: DAG validation
│   ├── step_type_convention.py         # Custom: naming validation
│   ├── citation_accuracy.py            # Custom: source validation
│   ├── action_type_classification.py   # Custom: action type validation
│   │
│   └── prompty/
│       ├── citizen_friendliness.prompty  # LLM judge: friendliness
│       ├── la_government_accuracy.prompty # LLM judge: LA accuracy
│       └── safety_boundary.prompty        # LLM judge: safety
│
├── results/                            # Evaluation results (gitignored)
│   └── .gitkeep
│
└── scripts/
    ├── generate_test_data.py           # CLI for test data generation
    └── analyze_results.py              # Analyze evaluation trends
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r tests/evaluation/requirements.txt

# Set environment variables (for Azure AI evaluators)
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
```

### Running Evaluations

```bash
# Run evaluation with custom evaluators only
python tests/evaluation/run_evaluation.py \
    --dataset tests/evaluation/data/regression_tests.jsonl \
    --output-path tests/evaluation/results

# Check thresholds
python tests/evaluation/check_thresholds.py \
    --results tests/evaluation/results \
    --thresholds tests/evaluation/thresholds.yaml
```

### Generating Test Data

```python
from tests.evaluation.generators import CSPTestDataGenerator

# Generate regression tests
generator = CSPTestDataGenerator()
test_cases = generator.generate_regression_tests()
generator.export_jsonl(test_cases, "data/regression_tests.jsonl")
```

## 📊 Evaluators

### Built-in Evaluators (Azure AI Evaluation SDK)

| Evaluator | Purpose | Required Data |
|-----------|---------|---------------|
| **CoherenceEvaluator** | Evaluate clarity and natural flow | `query`, `response` |
| **GroundednessEvaluator** | Ensure responses grounded in KB | `response`, `context` |
| **RelevanceEvaluator** | Assess response relevance | `query`, `response` |

### Custom Code-Based Evaluators

| Evaluator | Purpose | Threshold |
|-----------|---------|-----------|
| **AgencyBoundaryEvaluator** | Verify scope (LADBS/LADWP/LASAN only) | 0.95 |
| **PlanDependencyEvaluator** | Validate DAG dependencies | 1.0 |
| **StepTypeConventionEvaluator** | Check step ID naming (PRM-/INS-/etc.) | 1.0 |
| **CitationAccuracyEvaluator** | Validate source citations | 0.90 |
| **ActionTypeClassificationEvaluator** | Check automated vs user_action | 0.95 |

### Prompt-Based Evaluators (LLM as Judge)

| Evaluator | Purpose | Threshold |
|-----------|---------|-----------|
| **citizen_friendliness.prompty** | Empathy, clarity, helpfulness | 4.0/5.0 |
| **la_government_accuracy.prompty** | LA-specific accuracy | 4.0/5.0 |
| **safety_boundary.prompty** | Safety review | 4.5/5.0 |

## 📋 Test Categories

### Single-Agency Scenarios
- `ladbs_permits` - Building permits, inspections, fees
- `ladwp_utilities` - Rates, TOU plans, rebates, interconnection
- `lasan_disposal` - Waste pickup, recycling, hazardous materials

### Multi-Agency Scenarios
- `solar_installation` - Solar with permits and utility coordination
- `home_renovation` - Full renovation spanning all agencies
- `panel_upgrade` - Electrical panel upgrades

### Safety & Edge Cases
- `out_of_scope` - DMV, federal agencies, legal advice
- `safety_critical` - Unpermitted work, code violations

## 🔄 CI/CD Integration

The evaluation framework integrates with GitHub Actions via `.github/workflows/agent-evaluation.yml`.

### Triggering Evaluation

Evaluations run automatically on PRs that modify:
- `src/agents/**`
- `src/mcp-servers/**`
- `specs/4-spec-csp-agent.md`
- `specs/1-spec-mcp-servers.md`
- `tests/evaluation/**`

### Threshold Gating

PRs are blocked if evaluations fall below thresholds defined in `thresholds.yaml`.

## 📈 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Task Adherence Score | ≥ 4.0/5.0 | Built-in evaluator average |
| Tool Call Accuracy | ≥ 4.5/5.0 | Built-in evaluator average |
| Agency Boundary Compliance | ≥ 95% | Custom evaluator |
| Plan Validity Rate | 100% | Custom evaluator (DAG check) |
| Safety Violation Rate | 0% | Zero tolerance |

## 🔗 Related Documentation

- [CSP Agent Spec](/specs/4-spec-csp-agent.md) - Agent technical specification
- [MCP Server Spec](/specs/1-spec-mcp-servers.md) - Tool definitions
- [Demo Storyline](/docs/3-demo-story-line.md) - John's renovation journey
- [Use Cases](/docs/2-use-cases.md) - Service scenarios
