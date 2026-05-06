"""Combat, line-of-sight, and collision helpers for the bootstrap engine."""

from __future__ import annotations

from typing import Any

from .errors import fail, require


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
