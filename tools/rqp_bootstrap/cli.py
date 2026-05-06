"""Backwards-compatible CLI entry point for bootstrap fixture verification."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import VerificationError
from .verify import verify


def default_paths() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parents[2]
    default_fixture = repo_root / "fixtures" / "bootstrap" / "inertial-3-rounds.json"
    default_audit = repo_root / "fixtures" / "bootstrap" / "post-game-audit.json"
    return default_fixture, default_audit


def parse_args() -> argparse.Namespace:
    default_fixture, default_audit = default_paths()
    parser = argparse.ArgumentParser(description="Verify an RQP bootstrap replay fixture.")
    parser.add_argument("fixture", nargs="?", type=Path, default=default_fixture)
    parser.add_argument("audit", nargs="?", type=Path, default=default_audit)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        verify(args.fixture, args.audit)
    except VerificationError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("PASS: RQP bootstrap fixture verified")
    return 0
