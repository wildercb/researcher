"""Eval harness — loads datasets, runs agents, scores outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger()

DATASETS_DIR = Path(__file__).parent / "datasets"


@dataclass
class EvalResult:
    agent_name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    details: list[dict] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / max(self.total, 1)

    @property
    def score(self) -> float:
        return round(self.pass_rate, 4)


def load_dataset(agent_name: str) -> list[dict]:
    """Load eval dataset for an agent."""
    path = DATASETS_DIR / f"{agent_name}.jsonl"
    if not path.exists():
        return []
    examples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def list_datasets() -> list[str]:
    """List available eval datasets."""
    return [
        p.stem for p in DATASETS_DIR.glob("*.jsonl")
    ]


def score_contains(output: str, expected_contains: list[str]) -> bool:
    """Check if output contains all expected strings (case-insensitive)."""
    output_lower = output.lower()
    return all(term.lower() in output_lower for term in expected_contains)


def score_sections(output: str, expected_sections: list[str]) -> bool:
    """Check if output contains expected markdown sections."""
    return all(f"## {section}" in output or section.lower() in output.lower() for section in expected_sections)


def run_eval_offline(agent_name: str) -> EvalResult:
    """Run eval dataset checks that don't require LLM calls.

    Validates dataset structure and basic expectations.
    """
    result = EvalResult(agent_name=agent_name)
    dataset = load_dataset(agent_name)
    result.total = len(dataset)

    for i, example in enumerate(dataset):
        try:
            # Validate structure
            if "input" not in example:
                result.failed += 1
                result.details.append({"index": i, "error": "missing 'input' field"})
                continue

            # Check that expectations are defined
            has_expectation = any(
                k in example
                for k in ("expected_contains", "expected_sections", "expected_min_score", "expected")
            )
            if has_expectation:
                result.passed += 1
            else:
                result.failed += 1
                result.details.append({"index": i, "error": "no expectation defined"})

        except Exception as e:
            result.errors += 1
            result.details.append({"index": i, "error": str(e)})

    return result
