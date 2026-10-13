"""Minimal evaluation harness skeleton.

Use this as a release gate after populating a representative, expert-curated workspace.
It intentionally avoids pretending that generic thresholds are clinically validated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="eval/golden_cases.jsonl")
    args = parser.parse_args()
    cases = [json.loads(line) for line in Path(args.cases).read_text().splitlines() if line.strip()]
    print(f"Loaded {len(cases)} evaluation cases.")
    print("Wire these cases to a staging workspace and score retrieval, grounding, citations, abstention, and ACL behavior before release.")


if __name__ == "__main__":
    main()
