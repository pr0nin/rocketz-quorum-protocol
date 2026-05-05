# RQP Default Ruleset Profile

**Status:** Draft profile  
**Applies to:** `rqp/1.0-draft`  
**Purpose:** Provide concrete default values for early interoperable matches.

This profile is intentionally conservative. It favors deterministic behavior, simple implementation, and easy replay over deep balance.

## 1. Numeric Model

| Parameter | Value |
| --- | --- |
| Integer type | Signed 64-bit |
| Fixed-point scale | `1000` |
| Rounding | Floor toward zero |
| Hash algorithm | SHA-256 |
| Canonical encoding | Sorted-key UTF-8 JSON |

Fractional constants are encoded as rational pairs:

```text
value = floor(base * numerator / denominator)
```

## 2. Match Defaults

| Parameter | Value |
| --- | --- |
| Initial fuel | `1000` |
| Initial HP | `100` |
| Max rounds | `200` |
| Quorum | `ceil(active_agents * 2 / 3)` |
| Missing commit | Inertial |
| Missing reveal | Inertial plus audit flag |

## 3. Ship Defaults

```text
Ship = {
  hp: 100,
  mass: 10,
  max_thrust: 2,
  max_rotation: 1,
  cargo_slots: 3
}
```

## 4. Action Costs

| Action | Fuel cost |
| --- | --- |
| Inertial | `0` |
| Active base | `C_base(q,r,t)` |
| Tactical base | `C_base(q,r,t) + stake` |
| Thrust per unit | `2` |
| Rotation | `1` |
| Fire light weapon | `8` |
| Fire torpedo | `20` |

Tactical stake must be at least `1`.

## 5. Map Costs

```text
C_base(q,r,t) = C_seed(q,r,t) + C_vote(q,r,t) + C_static(q,r)
```

Defaults:

| Component | Value |
| --- | --- |
| Normal space static cost | `1` |
| Asteroid static cost | `3` |
| Wreckage static cost | `2` |
| Station static cost | `0` |
| Maximum base cost | `50` |

## 6. Gravity

Default gravity is sampled per hex and round:

```text
gravity_hash = SHA256(canonical(match_seed, "gravity", round, q, r))
gx = ((gravity_hash[0] mod 3) - 1)
gr = ((gravity_hash[1] mod 3) - 1)
```

The resulting vector is axial `(gx, gr)`.

## 7. Creep

Default creep mode is concentric pressure.

```text
safe_radius[round] = initial_safe_radius - floor(round / 10)
```

If `distance(hex, origin) > safe_radius`, then:

```text
C_seed(q,r,t) += 1
```

Defaults:

| Parameter | Value |
| --- | --- |
| Initial safe radius | `12` |
| Shrink interval | `10 rounds` |
| Creep increment | `1` |

## 8. Voting

| Parameter | Value |
| --- | --- |
| Default vote weight | `1` |
| Hex threshold | `100` |
| Trigger comparison | `>=` |
| Vote cost increment | `1` |
| Decay per round | `5` |

Environmental multipliers:

| Hex type | Multiplier |
| --- | --- |
| Normal | `1/1` |
| Asteroid | `3/2` |
| Wreckage | `3/2` |
| Station | `1/2` |

Effective vote:

```text
effective_vote = floor(vote_weight * multiplier_num / multiplier_den)
```

## 9. Weapons

### 9.1 Light Weapon

| Parameter | Value |
| --- | --- |
| Fuel cost | `8` |
| Damage | `10` |
| Range | `3` |
| Projectile speed | Instant line-of-sight |

### 9.2 Torpedo

| Parameter | Value |
| --- | --- |
| Fuel cost | `20` |
| Damage | `35` |
| Projectile speed | `2 hexes / round` |
| Lifetime | `5 rounds` |

## 10. Collision Damage

Default collision damage:

```text
damage = min(50, relative_speed * other_mass)
```

Terrain collision stops velocity and applies damage:

```text
damage = min(75, speed * ship_mass)
```

## 11. Elimination

An agent is eliminated when:

1. `hp <= 0`.
2. `fuel_remaining <= 0` and the agent owes positive operating cost.
3. It is disqualified by audit or tournament sanction.

## 12. Notes

These values are placeholders for interoperability and prototyping. They should be tuned through simulation before competitive use.
