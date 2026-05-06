"""Minimal schema and supported-profile checks for bootstrap fixtures."""

from __future__ import annotations

from typing import Any

from .canonical import CANONICAL_ENCODING, HASH_ALGORITHM, PROTOCOL
from .errors import require, require_equal


FIXTURE_REQUIRED_KEYS = (
    "protocol",
    "match_id",
    "canonicalization",
    "ruleset",
    "genesis",
    "rounds",
)
GENESIS_REQUIRED_KEYS = (
    "initial_ledger_payloads",
    "world_state",
    "world_state_hash",
)
ROUND_REQUIRED_KEYS = (
    "round",
    "agent_inputs",
    "world_state",
    "world_state_hash",
    "state_votes",
    "quorum",
)
AGENT_INPUT_REQUIRED_KEYS = (
    "agent_id",
    "ledger_payload",
    "expected_ledger_hash",
    "commit_payload",
    "expected_commit_hash",
)
AUDIT_REQUIRED_KEYS = (
    "protocol",
    "match_id",
    "type",
    "result",
    "quorum_mode",
    "verified_rounds",
    "agent_disclosures",
    "agent_results",
)
SUPPORTED_ACTION_LEVELS = (0, 1)
SUPPORTED_COLLISION_PROFILES = ("flat", "velocity_based", "hybrid")
SUPPORTED_GRAVITY_MODES = ("none", "constant_drift")
SUPPORTED_QUORUM = "strict-2-of-2"
SUPPORTED_WEAPON_ARCS = ("360", "forward")


def require_keys(container: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if key not in container]
    require(not missing, f"{label}: missing required keys {missing}")


def validate_bootstrap_schema(fixture: dict[str, Any], audit: dict[str, Any]) -> None:
    """Validate required top-level/round/audit keys and supported bootstrap values."""
    require_keys(fixture, FIXTURE_REQUIRED_KEYS, "fixture")
    require_keys(audit, AUDIT_REQUIRED_KEYS, "audit")

    genesis = fixture.get("genesis")
    require(isinstance(genesis, dict), "genesis must be an object")
    require_keys(genesis, GENESIS_REQUIRED_KEYS, "genesis")

    rounds = fixture.get("rounds")
    require(isinstance(rounds, list), "rounds must be a list")
    for index, round_fixture in enumerate(rounds, start=1):
        require(isinstance(round_fixture, dict), f"round {index}: must be an object")
        require_keys(round_fixture, ROUND_REQUIRED_KEYS, f"round {index}")
        inputs = round_fixture.get("agent_inputs")
        require(isinstance(inputs, list), f"round {index}: agent_inputs must be a list")
        for input_index, item in enumerate(inputs, start=1):
            require(isinstance(item, dict), f"round {index} agent_input {input_index}: must be an object")
            require_keys(item, AGENT_INPUT_REQUIRED_KEYS, f"round {index} agent_input {input_index}")
            commit_payload = item.get("commit_payload")
            require(isinstance(commit_payload, dict), f"round {index} agent_input {input_index}: commit_payload must be object")
            action_level = commit_payload.get("action_level")
            require(action_level in SUPPORTED_ACTION_LEVELS, f"round {index} agent_input {input_index}: unsupported action_level {action_level!r}")

    require_profile(fixture, audit)
    validate_ruleset_values(fixture)


def require_profile(fixture: dict[str, Any], audit: dict[str, Any]) -> None:
    require_equal("fixture protocol", fixture.get("protocol"), PROTOCOL)
    require_equal("audit protocol", audit.get("protocol"), PROTOCOL)
    require_equal("audit match_id", audit.get("match_id"), fixture.get("match_id"))
    require_equal(
        "canonical encoding",
        fixture.get("canonicalization", {}).get("encoding"),
        CANONICAL_ENCODING,
    )
    require_equal(
        "hash algorithm",
        fixture.get("canonicalization", {}).get("hash"),
        HASH_ALGORITHM,
    )
    gravity_mode = fixture.get("ruleset", {}).get("gravity_mode")
    require(
        gravity_mode in SUPPORTED_GRAVITY_MODES,
        f"ruleset gravity_mode: unsupported value {gravity_mode!r}",
    )
    if gravity_mode == "constant_drift":
        vector = fixture.get("ruleset", {}).get("gravity_vector")
        require(
            isinstance(vector, dict)
            and isinstance(vector.get("dq"), int)
            and isinstance(vector.get("dr"), int),
            "ruleset.gravity_vector must contain integer dq and dr for constant_drift",
        )
    require_equal("ruleset quorum", fixture.get("ruleset", {}).get("quorum"), SUPPORTED_QUORUM)
    require_equal("audit quorum_mode", audit.get("quorum_mode"), SUPPORTED_QUORUM)


def validate_ruleset_values(fixture: dict[str, Any]) -> None:
    ruleset = fixture.get("ruleset", {})
    collision_rules = ruleset.get("collision", {})
    if "stationary_damage" not in collision_rules:
        profile = collision_rules.get("profile", "flat")
        require(profile in SUPPORTED_COLLISION_PROFILES, f"unsupported collision profile {profile!r}")

    weapon_definitions = ruleset.get("weapons")
    if isinstance(weapon_definitions, dict):
        for weapon_id, rule in weapon_definitions.items():
            require(isinstance(rule, dict), f"ruleset.weapons.{weapon_id} must be an object")
            require(rule.get("arc", "360") in SUPPORTED_WEAPON_ARCS, f"ruleset.weapons.{weapon_id}.arc is unsupported")
