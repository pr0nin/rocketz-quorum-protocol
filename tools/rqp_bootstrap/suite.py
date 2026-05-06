"""Fixture-suite runner and generated negative conformance checks."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .errors import VerificationError
from .fixture import load_json
from .verify import verify, verify_objects


@dataclass(frozen=True)
class FixturePair:
    fixture: Path
    audit: Path


@dataclass(frozen=True)
class CheckResult:
    name: str
    fixture: str | None
    audit: str | None
    ok: bool
    error: str | None = None
    expected_error: str | None = None
    skipped: bool = False

    def as_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "fixture": self.fixture,
            "audit": self.audit,
            "ok": self.ok,
            "error": self.error,
            "expected_error": self.expected_error,
            "skipped": self.skipped,
        }


def default_fixture_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures" / "bootstrap"


def infer_audit_path(fixture_path: Path) -> Path:
    if fixture_path.name == "inertial-3-rounds.json":
        return fixture_path.with_name("post-game-audit.json")
    return fixture_path.with_name(f"{fixture_path.stem}-audit.json")


def discover_fixture_pairs(fixtures_dir: Path) -> list[FixturePair]:
    pairs: list[FixturePair] = []
    for fixture_path in sorted(fixtures_dir.glob("*.json")):
        if fixture_path.name.endswith("-audit.json") or fixture_path.name in ("post-game-audit.json", "rfc5-fixture-index.json"):
            continue
        pairs.append(FixturePair(fixture_path, infer_audit_path(fixture_path)))
    return pairs


def display_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def run_fixture_pair(pair: FixturePair) -> CheckResult:
    try:
        verify(pair.fixture, pair.audit)
    except VerificationError as error:
        return CheckResult(
            name="fixture",
            fixture=display_path(pair.fixture),
            audit=display_path(pair.audit),
            ok=False,
            error=str(error),
        )
    return CheckResult(name="fixture", fixture=display_path(pair.fixture), audit=display_path(pair.audit), ok=True)


def has_collision_fixture(pair: FixturePair) -> bool:
    try:
        fixture = load_json(pair.fixture)
    except VerificationError:
        return False
    objects = fixture.get("genesis", {}).get("world_state", {}).get("objects", [])
    return any(isinstance(obj, dict) and obj.get("collides") is True for obj in objects)


def has_weapon_fire_fixture(pair: FixturePair) -> bool:
    try:
        fixture = load_json(pair.fixture)
    except VerificationError:
        return False
    for round_fixture in fixture.get("rounds", []):
        for item in round_fixture.get("agent_inputs", []):
            weapons = item.get("commit_payload", {}).get("weapons", [])
            if weapons:
                return True
    return False


def expect_negative(
    name: str,
    pair: FixturePair | None,
    mutator: Callable[[dict[str, Any], dict[str, Any]], None] | None,
    expected_fragment: str,
) -> CheckResult:
    if pair is None or mutator is None:
        return CheckResult(name=name, fixture=None, audit=None, ok=True, skipped=True, expected_error=expected_fragment)

    fixture = load_json(pair.fixture)
    audit = load_json(pair.audit)
    fixture = copy.deepcopy(fixture)
    audit = copy.deepcopy(audit)
    mutator(fixture, audit)
    try:
        verify_objects(fixture, audit)
    except VerificationError as error:
        message = str(error)
        return CheckResult(
            name=name,
            fixture=display_path(pair.fixture),
            audit=display_path(pair.audit),
            ok=expected_fragment in message,
            error=message,
            expected_error=expected_fragment,
        )
    return CheckResult(
        name=name,
        fixture=display_path(pair.fixture),
        audit=display_path(pair.audit),
        ok=False,
        error="invalid case was accepted",
        expected_error=expected_fragment,
    )


def mutate_bad_world_hash(fixture: dict[str, Any], _audit: dict[str, Any]) -> None:
    fixture["rounds"][0]["world_state_hash"] = "0" * 64


def mutate_broken_ledger_chain(fixture: dict[str, Any], _audit: dict[str, Any]) -> None:
    fixture["rounds"][0]["agent_inputs"][0]["ledger_payload"]["previous_fuel_ledger_hash"] = "broken-chain"


def mutate_quorum_mismatch(fixture: dict[str, Any], _audit: dict[str, Any]) -> None:
    fixture["rounds"][0]["quorum"]["locked_hash"] = "0" * 64


def mutate_invalid_audit_salt(_fixture: dict[str, Any], audit: dict[str, Any]) -> None:
    disclosure = audit["agent_disclosures"][0]
    disclosure["ledger_salts"][0] = f"{disclosure['ledger_salts'][0]}-bad"


def mutate_collision_outcome(fixture: dict[str, Any], _audit: dict[str, Any]) -> None:
    previous_hp = {
        agent["agent_id"]: agent["hp"]
        for agent in fixture["genesis"]["world_state"]["agents"]
    }
    for round_fixture in fixture["rounds"]:
        for agent in round_fixture["world_state"]["agents"]:
            if agent["hp"] != previous_hp[agent["agent_id"]]:
                agent["hp"] += 1
                return
        previous_hp = {
            agent["agent_id"]: agent["hp"]
            for agent in round_fixture["world_state"]["agents"]
        }
    fixture["rounds"][0]["world_state"]["agents"][0]["hp"] += 1


def mutate_firing_outcome(fixture: dict[str, Any], _audit: dict[str, Any]) -> None:
    for round_fixture in fixture["rounds"]:
        if any(item.get("commit_payload", {}).get("weapons") for item in round_fixture.get("agent_inputs", [])):
            round_fixture["world_state"]["agents"][-1]["hp"] += 1
            return
    fixture["rounds"][0]["world_state"]["agents"][-1]["hp"] += 1


def run_negative_checks(pairs: list[FixturePair]) -> list[CheckResult]:
    base_pair = pairs[0] if pairs else None
    collision_pair = next((pair for pair in pairs if has_collision_fixture(pair)), None)
    firing_pair = next((pair for pair in pairs if has_weapon_fire_fixture(pair)), None)
    return [
        expect_negative("negative/bad-world-hash", base_pair, mutate_bad_world_hash, "world_state: expected hash"),
        expect_negative("negative/broken-ledger-chain", base_pair, mutate_broken_ledger_chain, "previous ledger"),
        expect_negative("negative/quorum-mismatch", base_pair, mutate_quorum_mismatch, "quorum locked_hash"),
        expect_negative("negative/invalid-audit-salt", base_pair, mutate_invalid_audit_salt, "rebuilt ledger payload"),
        expect_negative("negative/invalid-collision-outcome", collision_pair, mutate_collision_outcome, "produced world_state"),
        expect_negative("negative/invalid-firing-outcome", firing_pair, mutate_firing_outcome, "produced world_state"),
    ]


def run_suite(pairs: list[FixturePair], include_negative: bool) -> tuple[list[CheckResult], list[CheckResult]]:
    fixture_results = [run_fixture_pair(pair) for pair in pairs]
    negative_results = run_negative_checks(pairs) if include_negative else []
    return fixture_results, negative_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RQP bootstrap fixture conformance checks.")
    parser.add_argument("fixture", nargs="?", type=Path, help="optional fixture JSON to run")
    parser.add_argument("audit", nargs="?", type=Path, help="optional audit JSON; inferred when omitted")
    parser.add_argument("--fixtures-dir", type=Path, default=default_fixture_dir(), help="fixture directory for discovery")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON output")
    parser.add_argument("--no-negative", action="store_true", help="skip generated negative conformance checks")
    return parser.parse_args()


def selected_pairs(args: argparse.Namespace) -> list[FixturePair]:
    if args.fixture is not None:
        audit = args.audit if args.audit is not None else infer_audit_path(args.fixture)
        return [FixturePair(args.fixture, audit)]
    return discover_fixture_pairs(args.fixtures_dir)


def emit_text(fixture_results: list[CheckResult], negative_results: list[CheckResult]) -> None:
    for result in fixture_results:
        if result.ok:
            print(f"PASS fixture {result.fixture}")
        else:
            print(f"FAIL fixture {result.fixture}: {result.error}")

    for result in negative_results:
        if result.skipped:
            print(f"SKIP {result.name}: no matching fixture")
        elif result.ok:
            print(f"PASS {result.name}: failed as expected")
        else:
            print(f"FAIL {result.name}: {result.error}")

    failed = sum(not result.ok for result in fixture_results + negative_results)
    skipped = sum(result.skipped for result in negative_results)
    print(
        "SUMMARY "
        f"fixtures={sum(result.ok for result in fixture_results)}/{len(fixture_results)} "
        f"negative={sum(result.ok and not result.skipped for result in negative_results)}/"
        f"{sum(not result.skipped for result in negative_results)} "
        f"skipped={skipped} failed={failed}"
    )


def emit_json(fixture_results: list[CheckResult], negative_results: list[CheckResult]) -> None:
    failed = sum(not result.ok for result in fixture_results + negative_results)
    payload = {
        "ok": failed == 0,
        "summary": {
            "fixtures_total": len(fixture_results),
            "fixtures_passed": sum(result.ok for result in fixture_results),
            "negative_total": sum(not result.skipped for result in negative_results),
            "negative_passed": sum(result.ok and not result.skipped for result in negative_results),
            "negative_skipped": sum(result.skipped for result in negative_results),
            "failed": failed,
        },
        "fixtures": [result.as_json() for result in fixture_results],
        "negative": [result.as_json() for result in negative_results],
    }
    print(json.dumps(payload, sort_keys=True, indent=2))


def main() -> int:
    args = parse_args()
    try:
        pairs = selected_pairs(args)
        fixture_results, negative_results = run_suite(pairs, include_negative=not args.no_negative)
    except VerificationError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    if args.json:
        emit_json(fixture_results, negative_results)
    else:
        emit_text(fixture_results, negative_results)

    return 0 if all(result.ok for result in fixture_results + negative_results) else 1
