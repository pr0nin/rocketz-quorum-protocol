"""State transition engine and round verification for RQP bootstrap fixtures."""

from __future__ import annotations

import copy
from typing import Any

from .canonical import verify_hash
from .combat import stationary_collision_damage, weapon_hits, weapon_rule_for
from .errors import fail, require, require_equal, require_unique
from .fixture import index_by_agent


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
