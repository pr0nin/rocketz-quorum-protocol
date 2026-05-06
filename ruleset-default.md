# RQP Default Ruleset Profile

**Status:** Playable draft profile (`rqp-default-playable-v0`)
**Applies to:** `rqp/1.0-draft.1`
**Purpose:** Provide the first small deterministic ruleset that an early engine can implement without guessing ship, weapon, movement, collision, or materialized-map semantics.

This profile is intentionally conservative. It favors integer-only replay, explicit genesis data, and executable fixture coverage over competitive balance depth.

## 1. Numeric Model

| Parameter | Value |
| --- | --- |
| Integer type | Signed 64-bit |
| Hash algorithm | SHA-256 |
| Canonical encoding | Sorted-key UTF-8 JSON (`sorted-key-json-v1`) |
| Rounding | Floor toward zero for every rational multiplier |

No canonical calculation in this profile uses floating-point arithmetic.

## 2. Match Defaults

| Parameter | Value |
| --- | --- |
| Initial fuel | `100` |
| Quorum | Strict `2-of-2` for two-agent local fixtures; otherwise `ceil(active_agents * 2 / 3)` |
| Missing commit | Level 0 Inertial |
| Missing reveal | Level 0 Inertial plus an audit flag |
| Signatures | Omitted only for local replay fixtures |

A missing reveal appends this canonical audit flag to `world_state.audit_flags`:

```json
{"agent_id":"<agent-id>","fallback":"inertial","round":N,"type":"missing_reveal"}
```

## 3. Ship and Loadout Schema

Genesis ledger payloads declare the purchased loadout:

```json
{"ship":"striker-v1","weapons":["training-laser","breach-rail"]}
```

World-state agents materialize the active ship stats so replay does not need an external catalog:

```json
{
  "ship": {"profile":"striker-v1","mass":10,"max_thrust":2,"max_rotation":1},
  "weapons": ["training-laser","breach-rail"]
}
```

The first two standard ships are:

| Ship profile | HP | Mass | Max thrust | Max rotation | Weapon slots | Fixture role |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `striker-v1` | `70` | `10` | `2` | `1` | `2` | Mobile attacker |
| `guardian-v1` | `80` | `14` | `1` | `1` | `1` | Durable defender |

## 4. Action Costs

| Action component | Fuel cost |
| --- | ---: |
| Level 0 Inertial | `0` |
| Level 1 Active base | `1` |
| Thrust per axial unit | `2` |
| Rotation per 60-degree step | `1` |
| Fire `training-laser` | `3` |
| Fire `breach-rail` | `8` |

For Level 1 Active actions:

```text
fuel_burn = active_base
          + (abs(thrust.dq) + abs(thrust.dr)) * thrust_per_unit
          + abs(rotation) * rotation_per_step
          + sum(fired_weapon.fuel_cost)
```

Level 0 Inertial requires zero thrust, zero rotation, and no weapon activation.

## 5. Rotation and Facing

Facing is one of the six axial unit directions, in positive rotation order:

```text
[(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)]
```

`movement.rotation` is a signed integer step count. A positive value advances through that list; a negative value moves backward. Rotation is applied before movement and before post-movement weapon arc checks. The default ships allow at most one step per Active action.

## 6. Weapons and Damage

Weapons are instant line-of-sight effects checked after movement. All valid damage in a round accumulates and applies simultaneously after movement and collision checks. HP is clamped at `0`; an agent at `0` HP is eliminated.

| Weapon | Schema | Range | Arc | Fuel | Damage formula |
| --- | --- | ---: | --- | ---: | --- |
| `training-laser` | `{"weapon_id":"training-laser","target_agent_id":"..."}` | `4` | `360` | `3` | `damage = 10` |
| `breach-rail` | `{"weapon_id":"breach-rail","target_agent_id":"..."}` | `5` | `forward` | `8` | `damage = 35` |

A shot that is out of range, out of arc, or blocked by an intermediate opaque object is still a valid spent action, but it deals `0` damage.

Advanced LOS weapons such as thick beams, cones, delayed projectiles, dynamic pruning, and post-game fuel-mining attacks are outside `rqp-default-playable-v0` and remain future-RFC material.

## 7. Collision Outcomes

The default playable collision profile is velocity-based stationary collision:

```text
speed = abs(actual_round_delta.dq) + abs(actual_round_delta.dr)
damage = min(max_damage, speed * velocity_factor)
```

Default fixture constants are `velocity_factor = 25` and `max_damage = 30`. Collision damage is applied before weapon damage. The bootstrap verifier does not yet model bounce or automatic velocity stop; ships may spend later thrust to recover after impact.

## 8. Map Profile

The playable profile uses `explicit-materialized-v1` maps for early interoperability. A map records `map_definition.seed` and `generation_profile` as provenance, but every object that affects canonical play is materialized in genesis/world state:

```json
{
  "generation_profile":"explicit-materialized-v1",
  "seed":"playable-lane-seed-001",
  "objects":["screen-asteroid","recovery-wreck"]
}
```

Seed-derived generation algorithms remain future-RFC work unless a fixture materializes the generated output and names the exact profile parameters.

## 9. Quorum and Dispute Diagnostics

Two-agent local fixtures require strict `2-of-2` state votes to lock. If fewer votes are available, the tentative world-state hash may be reported with:

```json
{"available_votes":1,"decision":"round_not_locked","required_votes":2}
```

Nodes MUST NOT advance the locked world state from an unlocked quorum diagnostic round.

## 10. Executable Coverage

The profile is covered by:

1. `fixtures/bootstrap/playable-default-campaign.json` for asymmetric loadouts, rotation plus thrust, blocked and unblocked weapons, collision aftermath, elimination, and missing reveal fallback.
2. `fixtures/bootstrap/playable-quorum-failure.json` for strict `2-of-2` quorum failure diagnostics.

These fixtures are intentionally small and are not final balance recommendations for competitive tournaments.
