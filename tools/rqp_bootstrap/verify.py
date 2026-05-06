"""High-level RQP bootstrap fixture verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .audit import verify_audit
from .engine import verify_rounds
from .errors import require
from .fixture import load_json, verify_genesis
from .schema import validate_bootstrap_schema


def verify_objects(fixture: dict[str, Any], audit: dict[str, Any]) -> None:
    require(isinstance(fixture, dict), "fixture root must be an object")
    require(isinstance(audit, dict), "audit root must be an object")

    validate_bootstrap_schema(fixture, audit)
    agent_ids, ledger_hashes, genesis_world = verify_genesis(fixture)
    round_numbers, round_inputs_by_round, final_fuel_remaining, final_hp = verify_rounds(
        fixture,
        agent_ids,
        ledger_hashes,
        genesis_world,
    )
    verify_audit(
        fixture,
        audit,
        agent_ids,
        round_numbers,
        round_inputs_by_round,
        final_fuel_remaining,
        final_hp,
    )


def verify(fixture_path: Path, audit_path: Path) -> None:
    fixture = load_json(fixture_path)
    audit = load_json(audit_path)
    verify_objects(fixture, audit)
