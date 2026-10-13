from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from oncopilot_ai.ingestion.index_builder import build_and_save_index  # noqa: E402


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a workspace-scoped OncoPilot-AI index")
    parser.add_argument("--workspace", default="default")
    parser.add_argument("--sensitivity", choices=["public", "internal", "phi", "restricted"], default="internal")
    parser.add_argument("--roles", default="", help="Comma-separated roles allowed to retrieve the documents")
    parser.add_argument("--users", default="", help="Comma-separated user IDs allowed to retrieve the documents")
    args = parser.parse_args()
    result = build_and_save_index(
        workspace_id=args.workspace,
        sensitivity=args.sensitivity,
        allowed_roles=[x.strip() for x in args.roles.split(",") if x.strip()],
        allowed_users=[x.strip() for x in args.users.split(",") if x.strip()],
    )
    print(json.dumps(result, indent=2))
