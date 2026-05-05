#!/usr/bin/env python3
"""Verify RQP bootstrap replay fixtures."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PROTOCOL = "rqp/1.0-draft.1"
CANONICAL_ENCODING = "sorted-key-json-v1"
HASH_ALGORITHM = "sha-256"


class VerificationError(Exception):
    """Raised when a bootstrap fixture check fails."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def fail(message: str) -> None:
    raise VerificationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def verify_hash(label: str, value: Any, expected_hash: str) -> str:
    actual_hash = sha256_hex(value)
    if actual_hash != expected_hash:
        fail(f"{label}: expected hash {expected_hash}, got {actual_hash}")
    return actual_hash


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as error:
        fail(f"file not found: {path}")
        raise AssertionError from error
    except json.JSONDecodeError as error:
        fail(f"invalid JSON in {path}: {error}")
        raise AssertionError from error


def require_unique(items: list[str], label: str) -> None:
    duplicates = sorted({item for item in items if items.count(item) > 1})
    require(not duplicates, f"{label}: duplicate values {duplicates}")


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
        gravity_mode in ("none", "constant_drift"),
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
    require_equal(
        "ruleset quorum",
        fixture.get("ruleset", {}).get("quorum"),
        "strict-2-of-2",
    )
    require_equal("audit quorum_mode", audit.get("quorum_mode"), "strict-2-of-2")


def index_by_agent(items: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    agent_ids = [item.get("agent_id") for item in items]
    require(all(isinstance(agent_id, str) for agent_id in agent_ids), f"{label}: every item needs agent_id")
    require_unique(agent_ids, label)
    return {item["agent_id"]: item for item in items}


def verify_genesis(fixture: dict[str, Any]) -> tuple[list[str], dict[str, str], dict[str, Any]]:
    genesis = fixture.get("genesis")
    require(isinstance(genesis, dict), "genesis must be an object")

    initial_payloads = genesis.get("initial_ledger_payloads")
    require(isinstance(initial_payloads, list), "genesis.initial_ledger_payloads must be a list")

    ledger_hashes: dict[str, str] = {}
    for item in initial_payloads:
        agent_id = item.get("agent_id")
        payload = item.get("payload")
        expected_hash = item.get("expected_hash")
        require(isinstance(agent_id, str), "initial ledger payload missing agent_id")
        require(isinstance(payload, dict), f"initial ledger {agent_id}: payload must be an object")
        require(isinstance(expected_hash, str), f"initial ledger {agent_id}: expected_hash must be a string")
        require_equal(f"initial ledger {agent_id} payload agent", payload.get("agent_id"), agent_id)
        ledger_hashes[agent_id] = verify_hash(f"initial ledger {agent_id}", payload, expected_hash)

    world_state = genesis.get("world_state")
    require(isinstance(world_state, dict), "genesis.world_state must be an object")
    require_equal("genesis world protocol", world_state.get("protocol"), fixture["protocol"])
    require_equal("genesis world match_id", world_state.get("match_id"), fixture["match_id"])
    require_equal("genesis world round", world_state.get("round"), 0)
    verify_hash("genesis world_state", world_state, genesis.get("world_state_hash"))

    agents = world_state.get("agents")
    require(isinstance(agents, list), "genesis.world_state.agents must be a list")
    agent_ids = [agent.get("agent_id") for agent in agents]
    require(all(isinstance(agent_id, str) for agent_id in agent_ids), "genesis agents need agent_id")
    require_unique(agent_ids, "genesis agents")
    require_equal("genesis initial ledger agents", sorted(ledger_hashes), sorted(agent_ids))

    for agent in agents:
        agent_id = agent["agent_id"]
        require_equal(
            f"genesis agent {agent_id} fuel_ledger_hash",
            agent.get("fuel_ledger_hash"),
            ledger_hashes[agent_id],
        )

    return agent_ids, ledger_hashes, world_state


def thrust_magnitude(thrust: list[int]) -> int:
    return abs(thrust[0]) + abs(thrust[1])


def expected_fuel_burn(fixture: dict[str, Any], action_level: int, thrust: list[int], weapons: list[Any]) -> int:
    if action_level == 0:
        require_equal("inertial weapon fire", weapons, [])
        return 0

    if action_level == 1:
        action_costs = fixture.get("ruleset", {}).get("action_costs", {})
        active_base = action_costs.get("active_base", 1)
        thrust_per_unit = action_costs.get("thrust_per_unit", 2)
        require(isinstance(active_base, int), "ruleset.action_costs.active_base must be an integer")
        require(isinstance(thrust_per_unit, int), "ruleset.action_costs.thrust_per_unit must be an integer")
        return active_base + thrust_magnitude(thrust) * thrust_per_unit + weapon_fire_cost(fixture, weapons)

    fail(f"unsupported action_level {action_level}; bootstrap verifier supports only 0 and 1")
    raise AssertionError


def weapon_fire_cost(fixture: dict[str, Any], weapons: list[Any]) -> int:
    weapon_definitions = fixture.get("ruleset", {}).get("weapons")
    if isinstance(weapon_definitions, dict):
        total = 0
        for weapon in weapons:
            require(isinstance(weapon, dict), "weapon entries must be objects")
            weapon_id = weapon.get("weapon_id")
            require(weapon_id in weapon_definitions, f"unknown weapon definition {weapon_id!r}")
            cost = weapon_definitions[weapon_id].get("fuel_cost", 0)
            require(isinstance(cost, int), f"ruleset.weapons.{weapon_id}.fuel_cost must be an integer")
            total += cost
        return total

    fire_weapon = fixture.get("ruleset", {}).get("action_costs", {}).get("fire_weapon", 0)
    require(isinstance(fire_weapon, int), "ruleset.action_costs.fire_weapon must be an integer")
    return len(weapons) * fire_weapon


def require_bootstrap_input(
    fixture: dict[str, Any],
    round_number: int,
    agent_id: str,
    item: dict[str, Any],
    previous_fuel_remaining: int,
) -> None:
    ledger_payload = item.get("ledger_payload")
    commit_payload = item.get("commit_payload")
    require(isinstance(ledger_payload, dict), f"round {round_number} {agent_id}: ledger_payload must be object")
    require(isinstance(commit_payload, dict), f"round {round_number} {agent_id}: commit_payload must be object")

    require_equal(f"round {round_number} {agent_id} ledger agent", ledger_payload.get("agent_id"), agent_id)
    require_equal(f"round {round_number} {agent_id} ledger round", ledger_payload.get("round"), round_number)
    require_equal(f"round {round_number} {agent_id} commit agent", commit_payload.get("agent_id"), agent_id)
    require_equal(f"round {round_number} {agent_id} commit round", commit_payload.get("round"), round_number)
    action_level = commit_payload.get("action_level")
    require(action_level in (0, 1), f"round {round_number} {agent_id}: unsupported action_level {action_level!r}")
    thrust = commit_payload.get("movement", {}).get("thrust")
    require(
        isinstance(thrust, list) and len(thrust) == 2 and all(isinstance(component, int) for component in thrust),
        f"round {round_number} {agent_id}: thrust must be two integers",
    )
    require_equal(f"round {round_number} {agent_id} rotation", commit_payload.get("movement", {}).get("rotation"), 0)
    weapons = commit_payload.get("weapons")
    require(isinstance(weapons, list), f"round {round_number} {agent_id}: weapons must be a list")
    require_equal(f"round {round_number} {agent_id} vote", commit_payload.get("vote"), None)
    if action_level == 0:
        require_equal(f"round {round_number} {agent_id} inertial thrust", thrust, [0, 0])

    fuel_burn = expected_fuel_burn(fixture, action_level, thrust, weapons)
    require_equal(f"round {round_number} {agent_id} ledger fuel_burn", ledger_payload.get("fuel_burn"), fuel_burn)
    require_equal(f"round {round_number} {agent_id} commit fuel_burn", commit_payload.get("fuel_burn"), fuel_burn)
    require_equal(
        f"round {round_number} {agent_id} fuel_remaining",
        ledger_payload.get("fuel_remaining"),
        previous_fuel_remaining - fuel_burn,
    )


def simulate_bootstrap_round(
    fixture: dict[str, Any],
    previous_world: dict[str, Any],
    round_number: int,
    agent_inputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    produced = copy.deepcopy(previous_world)
    produced["round"] = round_number
    agents = produced.get("agents", [])
    agents_by_id = {agent.get("agent_id"): agent for agent in agents}
    previous_agents_by_id = {agent.get("agent_id"): agent for agent in previous_world.get("agents", [])}
    damage_by_agent = {agent_id: 0 for agent_id in agents_by_id}
    impact_delta_by_agent: dict[str, dict[str, int]] = {}
    gravity = fixture.get("ruleset", {}).get("gravity_vector", {"dq": 0, "dr": 0})

    for agent in agents:
        agent_id = agent.get("agent_id")
        require(agent_id in agent_inputs, f"round {round_number}: missing input for {agent_id}")
        commit_payload = agent_inputs[agent_id]["commit_payload"]
        thrust = commit_payload["movement"]["thrust"]
        velocity = agent["velocity"]
        position = agent["position"]
        delta = {"dq": 0, "dr": 0}
        if not agent.get("eliminated", False):
            velocity["dq"] += thrust[0]
            velocity["dr"] += thrust[1]
            delta = {"dq": velocity["dq"] + gravity["dq"], "dr": velocity["dr"] + gravity["dr"]}
            position["q"] += delta["dq"]
            position["r"] += delta["dr"]
        impact_delta_by_agent[agent_id] = delta
        agent["fuel_ledger_hash"] = agent_inputs[agent_id]["expected_ledger_hash"]

    collision_rules = fixture.get("ruleset", {}).get("collision", {})
    collision_objects = [
        obj
        for obj in produced.get("objects", [])
        if obj.get("collides") is True and isinstance(obj.get("position"), dict)
    ]
    collision_positions = {
        (obj["position"]["q"], obj["position"]["r"])
        for obj in collision_objects
    }
    for agent in agents:
        if agent.get("eliminated", False):
            continue
        position = agent["position"]
        if (position["q"], position["r"]) in collision_positions:
            damage = stationary_collision_damage(collision_rules, impact_delta_by_agent[agent["agent_id"]])
            agent["hp"] = max(0, agent["hp"] - damage)
            if agent["hp"] == 0:
                agent["eliminated"] = True

    opaque_objects = [
        obj
        for obj in produced.get("objects", [])
        if obj.get("opaque") is True and isinstance(obj.get("position"), dict)
    ]

    for attacker_id, item in agent_inputs.items():
        previous_attacker = previous_agents_by_id[attacker_id]
        attacker = agents_by_id[attacker_id]
        if previous_attacker.get("eliminated", False) or attacker.get("eliminated", False):
            require_equal(f"round {round_number} eliminated {attacker_id} weapons", item["commit_payload"]["weapons"], [])
            continue

        equipped_weapons = previous_attacker.get("weapons", [])
        for weapon in item["commit_payload"]["weapons"]:
            require(isinstance(weapon, dict), f"round {round_number} {attacker_id}: weapon entry must be object")
            weapon_id = weapon.get("weapon_id")
            target_id = weapon.get("target_agent_id")
            require(weapon_id in equipped_weapons, f"round {round_number} {attacker_id}: weapon {weapon_id!r} not equipped")
            require(target_id in previous_agents_by_id, f"round {round_number} {attacker_id}: unknown target {target_id!r}")
            previous_target = previous_agents_by_id[target_id]
            target = agents_by_id[target_id]
            require(not previous_target.get("eliminated", False), f"round {round_number} {attacker_id}: target {target_id} already eliminated")
            weapon_rule = weapon_rule_for(fixture, weapon_id)
            if weapon_hits(attacker, target, weapon_rule, opaque_objects):
                damage_by_agent[target_id] += weapon_rule["damage"]

    for agent_id, damage in damage_by_agent.items():
        if damage == 0:
            continue
        agent = agents_by_id[agent_id]
        agent["hp"] = max(0, agent["hp"] - damage)
        if agent["hp"] == 0:
            agent["eliminated"] = True

    return produced


def axial_distance(a: dict[str, int], b: dict[str, int]) -> int:
    a_s = -a["q"] - a["r"]
    b_s = -b["q"] - b["r"]
    return (abs(a["q"] - b["q"]) + abs(a["r"] - b["r"]) + abs(a_s - b_s)) // 2


def weapon_rule_for(fixture: dict[str, Any], weapon_id: str) -> dict[str, Any]:
    weapon_definitions = fixture.get("ruleset", {}).get("weapons")
    if isinstance(weapon_definitions, dict):
        require(weapon_id in weapon_definitions, f"unknown weapon definition {weapon_id!r}")
        rule = weapon_definitions[weapon_id]
        require(isinstance(rule.get("damage"), int), f"ruleset.weapons.{weapon_id}.damage must be an integer")
        require(isinstance(rule.get("range"), int), f"ruleset.weapons.{weapon_id}.range must be an integer")
        require(rule.get("arc", "360") in ("360", "forward"), f"ruleset.weapons.{weapon_id}.arc is unsupported")
        return rule

    weapon_rules = fixture.get("ruleset", {}).get("weapon", {})
    damage = weapon_rules.get("damage", 0)
    range_ = weapon_rules.get("range", 0)
    require(isinstance(damage, int), "ruleset.weapon.damage must be an integer")
    require(isinstance(range_, int), "ruleset.weapon.range must be an integer")
    return {"damage": damage, "range": range_, "arc": "360"}


def weapon_hits(
    attacker: dict[str, Any],
    target: dict[str, Any],
    weapon_rule: dict[str, Any],
    opaque_objects: list[dict[str, Any]],
) -> bool:
    attacker_position = attacker["position"]
    target_position = target["position"]

    if axial_distance(attacker_position, target_position) > weapon_rule["range"]:
        return False

    if not is_axial_straight(attacker_position, target_position):
        return False

    if weapon_rule.get("arc", "360") == "forward" and not target_in_forward_arc(attacker, target):
        return False

    return not line_of_sight_blocked(attacker_position, target_position, opaque_objects)


def is_axial_straight(a: dict[str, int], b: dict[str, int]) -> bool:
    return a["q"] == b["q"] or a["r"] == b["r"] or (-a["q"] - a["r"]) == (-b["q"] - b["r"])


def target_in_forward_arc(attacker: dict[str, Any], target: dict[str, Any]) -> bool:
    facing = attacker.get("facing")
    require(
        isinstance(facing, dict) and isinstance(facing.get("dq"), int) and isinstance(facing.get("dr"), int),
        f"{attacker.get('agent_id')} must define integer facing for forward arc weapons",
    )
    attacker_position = attacker["position"]
    target_position = target["position"]
    distance = axial_distance(attacker_position, target_position)
    return (
        distance > 0
        and target_position["q"] - attacker_position["q"] == facing["dq"] * distance
        and target_position["r"] - attacker_position["r"] == facing["dr"] * distance
    )


def stationary_collision_damage(collision_rules: dict[str, Any], impact_delta: dict[str, int]) -> int:
    if "stationary_damage" in collision_rules:
        damage = collision_rules["stationary_damage"]
        require(isinstance(damage, int), "ruleset.collision.stationary_damage must be an integer")
        return damage

    profile = collision_rules.get("profile", "flat")
    speed = abs(impact_delta["dq"]) + abs(impact_delta["dr"])

    if profile == "flat":
        damage = collision_rules.get("flat_damage", 0)
        require(isinstance(damage, int), "ruleset.collision.flat_damage must be an integer")
        return damage

    if profile == "velocity_based":
        factor = collision_rules.get("velocity_factor", 1)
        max_damage = collision_rules.get("max_damage", 2**63 - 1)
        require(isinstance(factor, int), "ruleset.collision.velocity_factor must be an integer")
        require(isinstance(max_damage, int), "ruleset.collision.max_damage must be an integer")
        return min(max_damage, speed * factor)

    if profile == "hybrid":
        flat_damage = collision_rules.get("flat_damage", 0)
        factor = collision_rules.get("velocity_factor", 1)
        max_velocity_damage = collision_rules.get("max_velocity_damage", 2**63 - 1)
        require(isinstance(flat_damage, int), "ruleset.collision.flat_damage must be an integer")
        require(isinstance(factor, int), "ruleset.collision.velocity_factor must be an integer")
        require(isinstance(max_velocity_damage, int), "ruleset.collision.max_velocity_damage must be an integer")
        return flat_damage + min(max_velocity_damage, speed * factor)

    fail(f"unsupported collision profile {profile!r}")
    raise AssertionError


def line_of_sight_blocked(
    attacker_position: dict[str, int],
    target_position: dict[str, int],
    opaque_objects: list[dict[str, Any]],
) -> bool:
    blocker_positions = {
        (obj["position"]["q"], obj["position"]["r"])
        for obj in opaque_objects
    }
    return any(
        (position["q"], position["r"]) in blocker_positions
        for position in axial_intermediate_line(attacker_position, target_position)
    )


def axial_intermediate_line(a: dict[str, int], b: dict[str, int]) -> list[dict[str, int]]:
    if a["r"] == b["r"]:
        step = 1 if b["q"] > a["q"] else -1
        return [{"q": q, "r": a["r"]} for q in range(a["q"] + step, b["q"], step)]

    if a["q"] == b["q"]:
        step = 1 if b["r"] > a["r"] else -1
        return [{"q": a["q"], "r": r} for r in range(a["r"] + step, b["r"], step)]

    a_s = -a["q"] - a["r"]
    b_s = -b["q"] - b["r"]
    if a_s == b_s:
        q_step = 1 if b["q"] > a["q"] else -1
        r_step = -q_step
        distance = abs(b["q"] - a["q"])
        return [
            {"q": a["q"] + q_step * index, "r": a["r"] + r_step * index}
            for index in range(1, distance)
        ]

    fail(f"weapon line of sight is not axial-straight: {a!r} -> {b!r}")
    raise AssertionError


def verify_rounds(
    fixture: dict[str, Any],
    agent_ids: list[str],
    ledger_hashes: dict[str, str],
    genesis_world: dict[str, Any],
) -> tuple[list[int], dict[int, dict[str, dict[str, Any]]], dict[str, int], dict[str, int]]:
    rounds = fixture.get("rounds")
    require(isinstance(rounds, list), "rounds must be a list")
    require(rounds, "fixture must contain at least one round")

    previous_world = genesis_world
    round_inputs_by_round: dict[int, dict[str, dict[str, Any]]] = {}
    fuel_remaining: dict[str, int] = {}

    for item in fixture["genesis"]["initial_ledger_payloads"]:
        payload = item["payload"]
        fuel_remaining[item["agent_id"]] = payload["initial_fuel"]

    for expected_round, round_fixture in enumerate(rounds, start=1):
        round_number = round_fixture.get("round")
        require_equal("round sequence", round_number, expected_round)
        inputs = round_fixture.get("agent_inputs")
        require(isinstance(inputs, list), f"round {round_number}: agent_inputs must be a list")
        agent_inputs = index_by_agent(inputs, f"round {round_number} agent_inputs")
        require_equal(f"round {round_number} agents", sorted(agent_inputs), sorted(agent_ids))
        round_inputs_by_round[round_number] = agent_inputs

        for agent_id in agent_ids:
            item = agent_inputs[agent_id]
            require_bootstrap_input(fixture, round_number, agent_id, item, fuel_remaining[agent_id])
            ledger_payload = item["ledger_payload"]
            commit_payload = item["commit_payload"]

            require_equal(
                f"round {round_number} {agent_id} previous ledger",
                ledger_payload.get("previous_fuel_ledger_hash"),
                ledger_hashes[agent_id],
            )
            ledger_hash = verify_hash(
                f"round {round_number} {agent_id} ledger_payload",
                ledger_payload,
                item.get("expected_ledger_hash"),
            )
            ledger_hashes[agent_id] = ledger_hash
            fuel_remaining[agent_id] = ledger_payload["fuel_remaining"]

            require_equal(
                f"round {round_number} {agent_id} commit ledger hash",
                commit_payload.get("fuel_ledger_hash"),
                ledger_hash,
            )
            require_equal(
                f"round {round_number} {agent_id} commit match_id",
                commit_payload.get("match_id"),
                fixture["match_id"],
            )
            verify_hash(
                f"round {round_number} {agent_id} commit_payload",
                commit_payload,
                item.get("expected_commit_hash"),
            )

        produced_world = simulate_bootstrap_round(fixture, previous_world, round_number, agent_inputs)
        require_equal(f"round {round_number} produced world_state", produced_world, round_fixture.get("world_state"))
        world_hash = verify_hash(
            f"round {round_number} world_state",
            produced_world,
            round_fixture.get("world_state_hash"),
        )

        state_votes = round_fixture.get("state_votes")
        require(isinstance(state_votes, list), f"round {round_number}: state_votes must be a list")
        require_equal(f"round {round_number} state vote count", len(state_votes), len(agent_ids))
        vote_agents = [vote.get("agent_id") for vote in state_votes]
        require_unique(vote_agents, f"round {round_number} state_votes")
        require_equal(f"round {round_number} state vote agents", sorted(vote_agents), sorted(agent_ids))
        for vote in state_votes:
            agent_id = vote["agent_id"]
            require_equal(f"round {round_number} {agent_id} vote type", vote.get("type"), "state_vote")
            require_equal(f"round {round_number} {agent_id} vote protocol", vote.get("protocol"), fixture["protocol"])
            require_equal(f"round {round_number} {agent_id} vote match_id", vote.get("match_id"), fixture["match_id"])
            require_equal(f"round {round_number} {agent_id} vote round", vote.get("round"), round_number)
            require_equal(f"round {round_number} {agent_id} vote hash", vote.get("world_state_hash"), world_hash)

        quorum = round_fixture.get("quorum")
        require(isinstance(quorum, dict), f"round {round_number}: quorum must be an object")
        require_equal(f"round {round_number} quorum active_agents", quorum.get("active_agents"), len(agent_ids))
        require_equal(f"round {round_number} quorum threshold", quorum.get("threshold"), 2)
        require_equal(f"round {round_number} quorum votes_for_hash", quorum.get("votes_for_hash"), len(agent_ids))
        require_equal(f"round {round_number} quorum locked", quorum.get("locked"), True)
        require_equal(f"round {round_number} quorum locked_hash", quorum.get("locked_hash"), world_hash)

        previous_world = round_fixture["world_state"]

    final_hp = {
        agent["agent_id"]: agent["hp"]
        for agent in previous_world["agents"]
    }
    return [round_fixture["round"] for round_fixture in rounds], round_inputs_by_round, fuel_remaining, final_hp


def verify_audit(
    fixture: dict[str, Any],
    audit: dict[str, Any],
    agent_ids: list[str],
    round_numbers: list[int],
    round_inputs_by_round: dict[int, dict[str, dict[str, Any]]],
    final_fuel_remaining: dict[str, int],
    final_hp: dict[str, int],
) -> None:
    require_equal("audit type", audit.get("type"), "audit_report")
    require_equal("audit result", audit.get("result"), "pass")
    require_equal("audit verified_rounds", audit.get("verified_rounds"), round_numbers)

    disclosures = index_by_agent(audit.get("agent_disclosures", []), "audit disclosures")
    results = index_by_agent(audit.get("agent_results", []), "audit agent_results")
    require_equal("audit disclosure agents", sorted(disclosures), sorted(agent_ids))
    require_equal("audit result agents", sorted(results), sorted(agent_ids))

    genesis_payloads = index_by_agent(fixture["genesis"]["initial_ledger_payloads"], "genesis initial payloads")

    for agent_id in agent_ids:
        disclosure = disclosures[agent_id]
        result = results[agent_id]
        require_equal(f"audit {agent_id} result", result.get("audit"), "pass")
        require_equal(f"audit {agent_id} violations", result.get("violations"), [])

        initial_payload = {
            "agent_id": agent_id,
            "initial_fuel": disclosure.get("initial_fuel"),
            "loadout": disclosure.get("loadout"),
            "salt": disclosure.get("initial_ledger_salt"),
        }
        initial_hash = verify_hash(
            f"audit {agent_id} initial ledger disclosure",
            initial_payload,
            genesis_payloads[agent_id]["expected_hash"],
        )

        fuel_burns = disclosure.get("fuel_burns")
        ledger_salts = disclosure.get("ledger_salts")
        commit_salts = disclosure.get("commit_salts")
        require_equal(f"audit {agent_id} fuel_burn count", len(fuel_burns), len(round_numbers))
        require_equal(f"audit {agent_id} ledger salt count", len(ledger_salts), len(round_numbers))
        require_equal(f"audit {agent_id} commit salt count", len(commit_salts), len(round_numbers))

        previous_ledger_hash = initial_hash
        fuel_remaining = disclosure["initial_fuel"]
        total_burn = 0

        for index, round_number in enumerate(round_numbers):
            burn = fuel_burns[index]
            total_burn += burn
            fuel_remaining -= burn
            round_input = round_inputs_by_round[round_number][agent_id]
            expected_ledger_payload = round_input["ledger_payload"]
            rebuilt_ledger_payload = {
                "agent_id": agent_id,
                "fuel_burn": burn,
                "fuel_remaining": fuel_remaining,
                "previous_fuel_ledger_hash": previous_ledger_hash,
                "round": round_number,
                "salt": ledger_salts[index],
            }
            require_equal(
                f"audit {agent_id} round {round_number} rebuilt ledger payload",
                rebuilt_ledger_payload,
                expected_ledger_payload,
            )
            previous_ledger_hash = verify_hash(
                f"audit {agent_id} round {round_number} ledger disclosure",
                rebuilt_ledger_payload,
                round_input["expected_ledger_hash"],
            )

            rebuilt_commit_payload = copy.deepcopy(round_input["commit_payload"])
            rebuilt_commit_payload["salt"] = commit_salts[index]
            require_equal(
                f"audit {agent_id} round {round_number} rebuilt commit payload",
                rebuilt_commit_payload,
                round_input["commit_payload"],
            )
            verify_hash(
                f"audit {agent_id} round {round_number} commit disclosure",
                rebuilt_commit_payload,
                round_input["expected_commit_hash"],
            )

        require_equal(f"audit {agent_id} final fuel disclosure", disclosure.get("final_fuel"), fuel_remaining)
        require_equal(f"audit {agent_id} final fuel result", result.get("final_fuel"), fuel_remaining)
        require_equal(f"audit {agent_id} final fuel replay", fuel_remaining, final_fuel_remaining[agent_id])
        require_equal(f"audit {agent_id} total burn", result.get("fuel_burn_total"), total_burn)
        require_equal(f"audit {agent_id} initial fuel result", result.get("initial_fuel"), disclosure.get("initial_fuel"))
        if "final_hp" in result:
            require_equal(f"audit {agent_id} final hp result", result.get("final_hp"), final_hp[agent_id])


def verify(fixture_path: Path, audit_path: Path) -> None:
    fixture = load_json(fixture_path)
    audit = load_json(audit_path)
    require(isinstance(fixture, dict), "fixture root must be an object")
    require(isinstance(audit, dict), "audit root must be an object")

    require_profile(fixture, audit)
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


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_fixture = repo_root / "fixtures" / "bootstrap" / "inertial-3-rounds.json"
    default_audit = repo_root / "fixtures" / "bootstrap" / "post-game-audit.json"
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


if __name__ == "__main__":
    raise SystemExit(main())
