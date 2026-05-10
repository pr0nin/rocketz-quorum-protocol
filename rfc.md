# RFC 0001: Rocketz Quorum Protocol (RQP)

**Status:** Draft  
**Category:** Open Standard / Decentralized Game Protocol  
**Version:** 1.0-draft.1
**Date:** May 2026

## Abstract

Rocketz Quorum Protocol (RQP) defines a decentralized protocol for autonomous strategic space combat between AI agents. It combines deterministic integer physics, cryptographic resource accounting, commit-reveal action disclosure, and quorum-based state validation. RQP does not require an authoritative game server. Instead, all participating agents independently execute the same simulation and agree on each round's resulting world state by exchanging state hashes.

The protocol is designed for games where hidden information, bluffing, fuel management, implicit political coordination, and auditability are core mechanics. A match takes place on a deterministic axial hex grid where agents spend fuel to maneuver, attack, vote on environmental pressure, and influence future board costs.

This draft also defines a minimal local-replay bootstrap path. A new implementation can prove basic conformance by loading a genesis fixture, replaying three inertial rounds between two agents, locking each round by quorum, and validating the post-game audit data.

## 1. Goals

RQP has the following goals:

1. Enable serverless AI-vs-AI strategic combat.
2. Guarantee deterministic simulation across machines and runtimes.
3. Keep in-match fuel balances hidden while preserving post-match auditability.
4. Support bluffing through commit-reveal fuel accounting.
5. Allow agents to influence the environment through accumulated voting.
6. Provide quorum-based agreement on canonical world state.
7. Support tournaments where audited performance and remaining resources can persist across matches.
8. Make the match observable and replayable for spectators, commentators, and auditors.

## 2. Non-Goals

RQP does not define:

1. A specific AI framework or agent implementation.
2. A mandatory transport implementation.
3. A visual client, spectator UI, or livestream overlay.
4. A token, blockchain, or economic settlement layer.
5. A complete game balance table for ships, weapons, maps, or tournament rewards.
6. Advanced long-range weapon pruning, fuel mining, zero-knowledge fuel proofs, or delayed god-view broadcast rules.

Implementations MAY define these layers independently as long as they preserve the canonical protocol semantics described here.

## 3. Terminology

| Term | Definition |
| --- | --- |
| Agent | An autonomous participant controlling one ship or faction. |
| Node | A process participating in message exchange and state validation. In most matches, each agent runs one node. |
| Quorum | The threshold of valid participants required to lock a round state. |
| Round | One discrete simulation tick consisting of commit, reveal, execution, and consensus phases. |
| World State | The full canonical state of the match at a given round. |
| State Hash | A SHA-256 hash of the canonical serialized world state. |
| Fuel | The universal resource used for loadout, movement, weapons, tactical priority, and operating in costly hexes. |
| Fuel Ledger | The cryptographic chain committing to an agent's hidden fuel balance over time. |
| Creep | Deterministic environmental pressure that increases operating costs on the map. |
| Hex Potential | Accumulated vote pressure on a hex coordinate before an environmental change is triggered. |
| Commit | A one-way hash of an agent's intended action, fuel burn, vote, and nonce. |
| Commit Nonce | The per-agent, per-round secret value included in a commit payload and disclosed during reveal. The base JSON profile calls this value `salt` for backwards compatibility. Competitive profiles require high entropy, while local fixtures may use deterministic test salts. |
| Reveal | The later disclosure of the committed action data so all nodes can execute the round. |
| Energy Flux | A ruleset-defined public aggregate of per-round energy expenditure that can hide detailed resource allocation until audit. |
| Simulated Deck | A ruleset-defined delayed deterministic randomness source derived from revealed commit nonces. |
| Thermal Debt | A ruleset-defined risk state accumulated when an agent exceeds declared structural or energy capacity. |
| Signal Flare | A ruleset-defined transparency state that forces some future Commit Nonces, deck entropy inputs, or intent commitments to become public. |
| Audit | Post-match verification of fuel balances, commitments, salts, and protocol compliance. |

## 4. System Overview

An RQP match consists of a fixed set of registered agents, a deterministic map seed, map definition or map series, initial loadouts, and an agreed ruleset. Every node starts with the same genesis state and runs the same round lifecycle:

1. Agents publish commitments to their hidden actions.
2. Agents reveal the committed action data.
3. Nodes execute deterministic physics, combat, fuel accounting, voting, and environmental updates.
4. Nodes hash the resulting world state.
5. If quorum agrees on the state hash, the round is locked and the match advances.

No node is trusted as authoritative. A message hub MAY be used for transport, but the hub MUST NOT decide game outcomes. It only relays messages.

### 4.1 Extension Negotiation and Layering

RQP extensions MUST be negotiated explicitly through the genesis state, ruleset profile, or tournament profile. Implementations MUST NOT infer advanced behavior from field presence alone when that behavior affects canonical simulation or audit validity.

Extensions are layered as follows:

1. Core protocol requirements cover commit/reveal, nonce entropy, canonical serialization, audit replay, quorum locking, signatures where required, and fault handling.
2. Ruleset-defined gameplay mechanics cover public energy aggregates, delayed deterministic randomness, thermal debt, signal flares, jump drives, mining, advanced weapons, or other balance-sensitive effects.
3. Tournament and broadcast profiles cover sanctions, slashing, persistence, reputation, bright/dark information policy, delayed spectator disclosure, and public reporting.

Bootstrap fixtures remain valid unless their genesis state deliberately opts into an extension profile and updates every affected canonical hash, audit disclosure, and fixture index entry.

## 5. Deterministic Simulation Requirements

All protocol-valid implementations MUST produce byte-identical canonical world states when given the same genesis state and round inputs.

### 5.1 Numeric Model

Implementations MUST NOT use floating-point arithmetic for canonical simulation. All canonical calculations MUST use signed 64-bit integers unless a ruleset explicitly defines a larger integer type.

Fractional values MUST be represented with fixed-point integers or rational integer pairs. The fixed-point scale or rational encoding MUST be included in the ruleset. For example, a ruleset MAY define `SCALE = 1000`, where `1000` represents `1.0`, or encode `1.5x` as `multiplier_num = 3` and `multiplier_den = 2`.

When rational multipliers are used, the default calculation is:

```text
effective_value = floor(base_value * multiplier_num / multiplier_den)
```

Rulesets MUST define rounding for every fractional multiplier. The default rounding mode is floor toward zero.

### 5.2 Coordinate System

The map uses axial hex coordinates:

```text
Hex = (q, r)
```

The derived cube coordinate is:

```text
s = -q - r
```

Distance between two hexes MUST be computed as:

```text
distance(a, b) = (abs(a.q - b.q) + abs(a.r - b.r) + abs(a.s - b.s)) / 2
```

### 5.3 Map and Condition Profiles

The genesis state MUST declare the map definition used by the match. A match MAY use one map for all rounds or an ordered map series where different maps or map conditions become active at deterministic round boundaries.

A map definition SHOULD include:

```text
MapDefinition = {
  map_id,
  bounds,
  seed,
  generation_profile,
  parameter_overrides,
  objects,
  conditions,
  active_rounds
}
```

Where:

1. `map_id` is a stable canonical identifier.
2. `bounds` defines the playable coordinate extent if the ruleset uses bounded maps.
3. `seed` MAY override or derive from the match seed for map-local generation.
4. `generation_profile` identifies the deterministic algorithm used to derive generated map data.
5. `parameter_overrides` contains explicit map-local changes to ruleset parameters.
6. `objects` lists stationary or dynamic map objects such as asteroids, stations, wreckage, blockers, hazards, or objectives.
7. `conditions` contains deterministic map-local rule parameters.
8. `active_rounds` defines the inclusive round range or transition rule for map-series play.

### 5.3.1 Seed-Derived Map Generation

A map MAY be fully or partially derived from a seed. Seed-derived generation is valid only when the genesis state names the exact `generation_profile` and all profile parameters needed to reproduce the map.

Generation profiles MAY derive:

1. Bounds, spawn zones, exits, and objectives.
2. Stationary objects such as asteroids, blockers, wreckage, stations, and hazards.
3. Object-local fields such as `opaque`, `collides`, mass, HP, or terrain type.
4. Map-local gravity profile and gravity constants.
5. Crash and collision parameters.
6. Static operating cost, environmental multipliers, and creep parameters.
7. Weapon, sensor, movement, or fuel modifiers.

Generation MUST be deterministic and integer-only. A profile MUST define:

1. Seed input string and domain separators.
2. Hash or PRNG algorithm.
3. Sampling order.
4. Rejection or collision handling for generated objects.
5. Bounds and coordinate selection.
6. Any caps, weights, lookup tables, and rounding rules.
7. Canonical ordering of generated objects and generated condition entries.

If generated data affects canonical simulation, implementations MUST either:

1. Materialize the generated data into the genesis state; or
2. Include the generation profile and all parameters in genesis so every node can regenerate byte-identical data before round 1.

The default recommendation for early clients is to materialize generated objects and conditions in genesis and also include the seed/profile as provenance.

The first playable support profile, `rqp-default-playable-v0`, follows this recommendation by using `explicit-materialized-v1`: the seed and generation profile are recorded for provenance, but every object that affects canonical play is listed in genesis/world state. A future RFC may standardize a seed-derived generator once its hash input, sampling order, rejection rules, and canonical object ordering are fixture-backed.

### 5.3.2 Parameter Overrides

Rulesets MAY expose adjustable parameters that maps or map series can override. Overrides are canonical only when declared in genesis or deterministically generated by the active map profile.

An override SHOULD identify:

```text
ParameterOverride = {
  path,
  value,
  scope,
  active_rounds
}
```

Where:

1. `path` is a stable parameter path, for example `gravity.mode`, `gravity.vector`, `collision.profile`, `collision.flat_damage`, `collision.velocity_factor`, `weapon.training_laser.damage`, or `movement.max_thrust`.
2. `value` is the canonical replacement value.
3. `scope` declares whether the value applies globally, to one map, to one object, to a hex region, or to a round/event window.
4. `active_rounds` is optional if the override applies for the full active map.

Rulesets MUST declare which parameters are overrideable. Non-declared parameters MUST NOT be overridden by maps.

For crash and collision behavior, map overrides MAY select among at least:

1. Baseline ruleset collision behavior.
2. Flat crash damage.
3. Velocity-based crash damage.
4. Hybrid flat plus velocity-based crash damage.
5. Object-specific collision damage.

The exact formula and constants MUST be explicit after condition resolution. For example, a map may define:

```text
collision.profile = velocity_based
collision.velocity_factor = 12
collision.max_damage = 75
```

or:

```text
collision.profile = flat
collision.flat_damage = 40
```

Map conditions MAY override or specialize ruleset behavior for:

1. Gravity profile and gravity constants.
2. Static operating costs and environmental multipliers.
3. Collision behavior and crash damage.
4. Terrain effects, hazards, blockers, and opacity.
5. Weapon, sensor, movement, or fuel modifiers.
6. Spawn zones, map exits, or transition triggers.

Condition resolution MUST be deterministic. Unless a ruleset defines a different precedence order, the default precedence is:

```text
base ruleset
  < active map conditions
  < active round/event conditions
  < object-local or hex-local modifiers
```

All condition values that affect canonical simulation MUST be present in the genesis state, derived deterministically from genesis data, or introduced by a prior locked state transition. Nodes MUST NOT use local configuration, wall-clock data, external map files, or non-canonical UI metadata to determine active conditions.

For map series, every map transition MUST be deterministic. Valid transition mechanisms include:

1. Fixed round ranges, for example `map-a` active for rounds `1..50`.
2. Locked state triggers, for example all active agents enter an exit zone.
3. Ruleset-defined deterministic tournament stage transitions.

If multiple maps or condition layers are active at once, the ruleset MUST define merge order and conflict resolution.

### 5.4 Object State

Each dynamic object has at least:

```text
ObjectState = {
  id,
  type,
  position: (q, r),
  velocity: (dq, dr),
  facing: (dq, dr),
  hp,
  mass,
  owner_agent_id
}
```

`facing` is optional for objects that cannot aim, rotate, or have directional effects. If a ruleset uses firing arcs, directional shields, thrust orientation, sensors, or any facing-dependent effect, every affected object MUST include canonical facing. Bootstrap fixtures encode facing as one of the six axial unit directions.

Rulesets MAY add object-specific fields, but those fields MUST be included in canonical serialization if they affect simulation. Stationary map objects MAY omit velocity, facing, and owner fields if the map profile defines them as immobile and unowned.

### 5.5 Movement

For each object and each round `t`, velocity and position are updated as:

```text
V[t+1] = V[t] + A[action] + G[seed, position, t]
P[t+1] = P[t] + V[t+1]
```

Where:

- `A[action]` is the acceleration produced by the revealed action.
- `G[seed, position, t]` is the deterministic gravity vector derived from the map seed, position, and round.

If no valid action is revealed, `A[action] = (0, 0)`.

The ruleset MUST define the gravity function. The recommended default gravity function is:

```text
gravity_hash = SHA256(canonical(match_seed, "gravity", round, q, r))
gx = ((gravity_hash[0] mod 3) - 1) * GRAVITY_UNIT
gr = ((gravity_hash[1] mod 3) - 1) * GRAVITY_UNIT
```

The default `GRAVITY_UNIT` is `1`. A bootstrap or test-vector ruleset MAY explicitly set gravity to `(0, 0)` for all hexes and rounds, but this MUST be declared in the genesis state.

Bootstrap visual fixtures MAY define a simplified constant-drift gravity profile:

```text
gravity_mode = constant_drift
D = (dq, dr)
V[t+1] = V[t] + A[action]
P[t+1] = P[t] + V[t+1] + D
```

This profile is intended for small visual conformance fixtures where the map should show a readable one-hex-per-round environmental pull. It MUST be declared in the genesis state or ruleset and MUST NOT be assumed by default physics implementations.

### 5.6 Collision Resolution

Collisions MUST be resolved deterministically in this priority order:

1. Terrain, wreckage, asteroids, stations, and other stationary map objects.
2. Active ships.
3. Torpedoes, missiles, projectiles, mines, and other ordnance.

When multiple collisions exist in the same priority class, they MUST be ordered by canonical object ID ascending unless the ruleset defines a stricter ordering.

For high-velocity movement that crosses multiple hexes in one round, implementations MUST trace the canonical path from start to end instead of checking only the destination. The default path traversal is:

1. Convert axial coordinates to cube coordinates.
2. Interpolate from start cube coordinate to end cube coordinate in `N = distance(start, end)` steps.
3. Round each interpolated cube coordinate with deterministic cube rounding.
4. Evaluate collisions in path order.
5. If multiple objects occupy the same path step, use collision priority, then canonical object ID.

If several dynamic objects collide simultaneously, the default ruleset resolves stationary terrain first, ship-ship collisions by ascending object ID pair second, and ordnance collisions last. Objects destroyed earlier in the sequence are removed before later collision checks.

Rulesets MUST define the crash-damage profile used for collisions that affect HP. The profile MAY be global or map-specific through active map conditions.

Recommended crash-damage profiles are:

| Profile | Formula | Use case |
| --- | --- | --- |
| `flat` | `damage = flat_damage` | Simple hazards, tutorial fixtures, predictable visual tests. |
| `velocity_based` | `damage = min(max_damage, speed * mass_or_factor)` | Physics-like asteroid, terrain, and ship impacts. |
| `hybrid` | `damage = flat_damage + min(max_damage, speed * mass_or_factor)` | Maps where hazards have baseline danger plus velocity scaling. |

For velocity-based profiles:

```text
speed = abs(delta.q) + abs(delta.r)
```

where `delta` is the object's actual position change during the round after action acceleration, gravity, map drift, and other movement effects. Rulesets MAY define another integer-only speed metric, but MUST declare it. All formula constants, caps, and rounding rules MUST be declared in the active ruleset or active map conditions.

Bootstrap visual fixtures MAY define a simple stationary-object collision profile. In this profile:

1. Stationary objects with `collides = true` are collision objects.
2. Collision is checked after movement for the round.
3. If an agent's post-movement position equals a collision object's position, the active collision profile is applied to that agent.
4. HP is clamped at `0`.
5. An agent with `hp = 0` is marked eliminated.
6. Unless the ruleset explicitly says otherwise, the collision does not alter velocity, remove the stationary object, or move the agent out of the collision hex.

For fixture simplicity, `stationary_damage` is an alias for a `flat` stationary collision profile:

```text
collision.profile = flat
collision.flat_damage = stationary_damage
```

### 5.7 Bootstrap Line-of-Sight Weapons

The base RFC leaves complete weapon schemas and balance to rulesets, but bootstrap fixtures MAY use a simple deterministic line-of-sight weapon profile.

For this profile:

1. The weapon target is an agent ID.
2. The weapon is instantaneous and range-limited by axial hex distance.
3. The shot is valid only when attacker and target lie on a straight axial line:
   - same `q`,
   - same `r`, or
   - same derived cube `s = -q - r`.
4. Line of sight is blocked by any stationary object in an intermediate hex with `opaque = true`.
5. The attacker and target hexes themselves are not considered intermediate blocker hexes.
6. All valid weapon damage in a round is accumulated from revealed actions and then applied simultaneously after movement for that round.
7. HP is reduced by integer damage and clamped at `0`.
8. An agent with `hp = 0` is marked eliminated.

Bootstrap line-of-sight weapons MAY define firing arcs:

| Arc | Semantics |
| --- | --- |
| `360` | Any straight axial line within range may hit. |
| `forward` | The target must lie exactly along the attacker's facing vector. |

An out-of-range or out-of-arc shot MAY still appear in a reveal payload as a spent action, but it deals no damage. This allows fixtures and clients to visualize misses without treating the reveal as invalid.

Rulesets that use line-of-sight weapons MUST define weapon range, damage, fuel cost, arc semantics, blocker semantics, and whether line-of-sight is checked before movement or after movement. The bootstrap profile checks line of sight after movement.

## 6. Fuel Economy

Fuel is the only canonical resource in RQP. It regulates pre-match loadout, in-match actions, tactical priority, weapon usage, and the cost of operating in dangerous hexes.

### 6.1 Initial Fuel and Loadout

Each agent starts with an initial fuel allocation defined by the match configuration or tournament profile. Before round 1, agents MAY spend fuel on loadout. Loadout purchases MUST be committed in the genesis state and included in the audit trail.

### 6.2 Action Levels

Each round, every agent chooses exactly one action level.

| Level | Name | Cost | Semantics |
| --- | --- | --- | --- |
| 0 | Inertial | `0` | No thrust, no rotation, no weapon activation. The ship drifts under velocity and gravity. |
| 1 | Active | `C_base(q,r,t)` plus action costs | Standard maneuvering, rotation, and weapon use. |
| 2 | Tactical | `C_base(q,r,t) + stake` plus action costs | Buys priority execution before Active agents. Stake MUST be a positive integer. |

`C_base(q,r,t)` is the operating cost of the agent's current hex at round `t`. It is derived from the map seed, environmental creep, and accumulated votes.

### 6.3 Tactical Priority

Tactical actions execute before Active actions. If multiple agents choose Tactical in the same round, they are ordered by:

1. Higher tactical stake.
2. Lower canonical agent ID if stakes are equal.

Active actions execute after Tactical actions and are ordered by canonical agent ID unless the ruleset defines an initiative modifier.

Inertial agents do not execute voluntary actions but still move under velocity and gravity.

### 6.4 Fuel Burn

For each round, an agent's fuel burn is:

```text
fuel_burn =
  action_level_cost
  + movement_cost
  + weapon_cost
  + environment_cost
  + ruleset_modifiers
```

An agent MUST NOT spend more fuel than it has available. During the match, this is hidden by the fuel ledger. At audit time, overspending is a protocol violation.

### 6.5 Optional Energy Flux Extension

Rulesets MAY enable an `energy_flux-v1` extension for competitive profiles that want to reveal aggregate energy expenditure while hiding detailed resource allocation during live play. When enabled, each agent commits to and reveals a single non-negative integer:

```text
energy_flux[n] = sum(all visible and hidden energy expenditures for agent in round n)
```

The ruleset MUST define which costs are included in `energy_flux`, including movement, weapons, mining, charging, thermal management, tactical priority, environmental costs, and any hidden or delayed actions. `energy_flux` is public during the round. The detailed resource log that decomposes the aggregate into individual costs MAY remain hidden until audit.

For profiles that enable `energy_flux-v1`, the live commit/reveal schema MUST be declared in the ruleset profile. The default `energy_flux-v1` schema replaces the base payload's live `fuel_burn` field with live `energy_flux`. Consensus peers verify the round commitment against that public reveal payload using the same `SHA256(canonical(revealed_payload)) == commit_hash[n]` rule. The detailed `fuel_burn` sequence remains hidden until audit, while `fuel_ledger_hash` continues to commit to the actual audited resource transition.

Auditors MUST perform strict integer-sum replay of the complete disclosed detailed action log, including entries that were visible during live play and entries that remained hidden until audit. If the sum of those cost entries does not equal the revealed `energy_flux`, audit fails with deterministic `energy_flux_mismatch`. The post-game disclosure MUST prove that:

1. The detailed action log sums exactly to the revealed `energy_flux`.
2. The committed ledger hash matches the audited fuel burn and remaining fuel.
3. The public world-state transition is consistent with all visible effects.
4. Any hidden effects that were deferred until audit are permitted by the ruleset.

Bootstrap and local replay profiles that do not enable `energy_flux-v1` continue to reveal `fuel_burn` as shown in the base examples.

### 6.6 Optional Thermal Debt Extension

Rulesets MAY define Thermal Debt for ships or objects that can exceed safe operating limits. A Thermal Debt profile MUST declare all capacity fields, thresholds, lookup tables, consequences, and integer rounding rules in the ruleset or genesis state.

If enabled, each affected object SHOULD materialize a structural capacity field, for example `structural_capacity`, and any active debt state in canonical world state. A simple profile can define:

```text
thermal_excess[n] = max(0, energy_flux[n] - effective_structural_capacity[n])
thermal_debt[n+1] = thermal_debt[n] + thermal_excess[n] - cooling[n]
```

The ruleset MUST define whether excess is caused by public `energy_flux`, detailed audited fuel burn, specific hidden actions, environmental hazards, jump-drive use, or a combination of these. It MUST also define deterministic consequences such as temporary capacity reduction, thrust or speed penalties, hull damage, subsystem damage, forced shutdown, elimination, or delayed recovery.

Thermal outcomes MAY use the Simulated Deck extension only if that extension is enabled. In that case, the ruleset MUST identify the deck round used for each risk check and MUST specify the sampling order, domain separator, rejection rules, and consequence table.

### 6.7 Optional Signal Flares and Pre-Locking

Rulesets MAY define Signal Flares as a transparency penalty for catastrophic heat, extreme spacetime effects, jump drives, repeated Thermal Debt, or other high-power mechanics. If enabled, the ruleset MUST define canonical visibility states such as `dark`, `flaring`, and `bright`, and MUST materialize any state that affects commitments, deck entropy, targeting, sensors, or spectator disclosure.

A pre-lock profile MUST declare:

1. The trigger conditions that enter `flaring` or `bright` state.
2. The number of future rounds affected.
3. Whether future nonces are revealed immediately, hash-locked and later revealed, or bound through another canonical commitment.
4. How pre-locked nonces interact with ordinary commit/reveal payloads and Simulated Deck entropy.
5. The fallback and sanction when an agent fails to use the required pre-locked sequence.

Breaking a pre-lock commitment is a protocol or tournament violation as declared by the active profile. A flaring agent's physical action can remain hidden until the normal reveal phase unless the ruleset explicitly makes action intent public.

## 7. Cryptographic Fuel Ledger

RQP uses a hash-chain ledger to hide fuel balances during the match while preserving post-match verifiability.

### 7.1 Ledger Hash

For each agent and round `n`:

```text
fuel_remaining[n] = fuel_remaining[n-1] - fuel_burn[n]
fuel_ledger_hash[n] = SHA256(
  canonical(agent_id, n, fuel_remaining[n], fuel_burn[n], fuel_ledger_hash[n-1], salt[n])
)
```

The initial `fuel_ledger_hash[0]` MUST be derived from the audited loadout state:

```text
fuel_ledger_hash[0] = SHA256(canonical(agent_id, initial_fuel, loadout, salt[0]))
```

During the match, agents publish only `fuel_ledger_hash[n]`, not `fuel_remaining[n]`.

### 7.2 Commit Payload

Each round commit MUST bind:

1. Agent ID.
2. Round number.
3. Action level.
4. Movement and weapon commands.
5. Vote coordinate, if any.
6. Fuel burn.
7. Fuel ledger hash.
8. Commit Nonce, represented by the `salt` field in the base JSON profile or by `commit_nonce` in a profile that explicitly negotiates that field name; see Section 7.4 for field name conventions.

The base schema binds `fuel_burn` as item 6. Profiles such as `energy_flux-v1` MAY replace item 6 only by declaring an explicit commit/reveal schema override and preserving deterministic commit verification.

The commitment is:

```text
commit_hash[n] = SHA256(canonical(commit_payload[n]))
```

### 7.3 Reveal

During reveal, the agent discloses the full payload and salt. Other nodes MUST verify that:

```text
SHA256(canonical(revealed_payload)) == commit_hash[n]
```

If verification fails, the reveal is invalid.

### 7.4 Commit Nonce Requirements

The commit nonce is the foundation of action privacy. Because many RQP action spaces are small enough to brute-force, a commit payload that omits strong local entropy can leak the committed move before reveal.

Competitive and public-network profiles MUST require every commit nonce to be:

1. Generated from a cryptographically secure random source or an equivalent high-entropy agent-local secret process.
2. Unique for the tuple `(match_id, agent_id, round)`.
3. Bound inside the canonical commit payload before hashing.
4. Revealed under the declared profile no later than the matching action payload.
5. Auditable after match end.

Profiles SHOULD require at least 128 bits of unpredictable entropy for each nonce.

Local replay fixtures MAY use human-readable deterministic salts because they are non-competitive conformance vectors with fixed expected hashes. Those salts are valid for canonical test replay, as documented in `fixtures/bootstrap/README.md`, but MUST NOT be used as examples for competitive profiles.

Implementations SHOULD keep fixture replay and competitive nonce generation on distinct code paths to avoid accidentally reusing deterministic test salts in production.

`Commit Nonce` is the conceptual security term. The base `rqp/1.0-draft.1` JSON examples use the field name `salt` for backwards compatibility with existing fixtures and test vectors. Competitive profiles MAY require the explicit field name `commit_nonce`, but only when they:

1. Use the extension negotiation process in Section 4.1.
2. Declare a new canonical schema version.
3. Update all affected test vectors and fixtures.

## 8. Dynamic Environment

The map is an active strategic surface. Hex operating costs change through deterministic creep and accumulated voting.

### 8.1 Base Cost

Every hex has a round-specific operating cost:

```text
C_base(q,r,t) = C_seed(q,r,t) + C_vote(q,r,t) + C_static(q,r)
```

Where:

- `C_seed` is deterministic creep from the map seed.
- `C_vote` is the cost added by accumulated agent votes.
- `C_static` is static terrain or object-based cost.

### 8.2 Deterministic Creep

The ruleset MUST define a creep algorithm. The algorithm MUST depend only on the genesis state, map seed, and round number.

Example creep mode:

```text
Concentric(seed):
  every 10 rounds, reduce safe_radius by 1
  all hexes outside safe_radius gain +1 C_seed
```

This creates environmental pressure that pushes agents toward conflict.

### 8.3 Accumulated Voting

Each round, an agent MAY vote for one hex coordinate. Votes are hidden during commit and revealed during reveal.

Each revealed valid vote adds potential:

```text
hex_potential[q,r] += vote_weight(agent, q, r, t) * environment_multiplier(q, r, t)
```

The default vote weight is `1`. Rulesets MAY define stronger vote weights based on ship type, loadout, or tournament modifiers.

### 8.4 Thresholds and Decay

At the end of each execution phase:

1. If `hex_potential[q,r] >= HEX_THRESHOLD`, increase `C_vote(q,r,t+1)` by `C_VOTE_INCREMENT`.
2. If a threshold is triggered, subtract `HEX_THRESHOLD` from the hex potential unless the ruleset defines full reset.
3. Apply deterministic decay to all hex potentials.

Default parameters:

```text
HEX_THRESHOLD = 100
C_VOTE_INCREMENT = 1
HEX_DECAY_PER_ROUND = 5
```

Rulesets MAY override these values.

### 8.5 Environmental Multipliers

Terrain, wreckage, asteroids, debris, or stations MAY modify vote potential. For example:

```text
environment_multiplier(q,r,t) = 1.5
```

Because canonical simulation uses integers, fractional multipliers MUST be encoded as fixed-point values.

## 9. Round Lifecycle

Each round has four phases.

### 9.1 Commit Phase

Each agent publishes a commitment before the commit deadline.

```json
{
  "type": "round_commit",
  "protocol": "rqp/1.0-draft.1",
  "match_id": "match-001",
  "agent_id": "0xABC",
  "round": 42,
  "commit_hash": "3a7bd3e2360a3d...",
  "fuel_ledger_hash": "e3b0c44298fc..."
}
```

Nodes MUST reject commits for the wrong match, wrong round, unknown agent, malformed hash, or duplicate agent-round pair.

### 9.2 Reveal Phase

After the commit phase closes, agents publish their reveal payloads.

```json
{
  "type": "round_reveal",
  "protocol": "rqp/1.0-draft.1",
  "match_id": "match-001",
  "agent_id": "0xABC",
  "round": 42,
  "action_level": 2,
  "movement": {
    "thrust": [1, -1],
    "rotation": 0
  },
  "weapons": [
    {
      "weapon_id": "torpedo-1",
      "target": [5, -2]
    }
  ],
  "vote": {
    "q": 5,
    "r": -2
  },
  "fuel_burn": 15,
  "fuel_ledger_hash": "e3b0c44298fc...",
  "salt": "random_nonce_123"
}
```

Nodes MUST verify that the reveal matches the prior commit. If an agent submitted no valid commit or no valid reveal, its round action defaults to Level 0 Inertial.

### 9.3 Execution Phase

Each node executes the canonical simulation using:

1. The locked previous world state.
2. All valid reveal payloads.
3. Inertial defaults for missing or invalid reveals.
4. The deterministic ruleset.

Execution MUST include fuel burn application, tactical ordering, movement, collision resolution, combat effects, vote accumulation, creep, decay, elimination checks, and any ruleset-defined effects.

### 9.4 Consensus Phase

After execution, every node computes:

```text
world_state_hash[n] = SHA256(canonical(world_state[n]))
```

Each node publishes:

```json
{
  "type": "state_vote",
  "protocol": "rqp/1.0-draft.1",
  "match_id": "match-001",
  "agent_id": "0xABC",
  "round": 42,
  "world_state_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
}
```

If quorum agrees on the same state hash, the round is locked and the match advances.

### 9.5 Optional Simulated Deck Entropy

Rulesets MAY enable a Simulated Deck extension to resolve probabilistic events without an external oracle. The deck is deterministic once the relevant reveal phase has closed and MUST be derived only from canonical data.

A profile that enables Simulated Deck MUST define:

1. The participant set whose revealed nonces contribute entropy.
2. The canonical ordering of those nonces.
3. The domain-separated hash input.
4. The first round in which a generated seed can be consumed.
5. The sampling order for every probabilistic event.
6. The behavior for missing commits, missing reveals, eliminated agents, and disqualified agents.

The default recommendation is:

```text
deck_seed[n+1] = SHA256(canonical(
  "rqp-simulated-deck-v1",
  match_id,
  n,
  locked_world_state_hash[n],
  ordered_revealed_commit_nonces[n]
))
```

The seed derived from round `n` MUST NOT resolve events in round `n`. It MAY resolve events in round `n+1` or later, as declared by the ruleset. This ensures all round `n` reveals and the round `n` state lock complete before any agent can observe outcomes resolved by the round `n` deck seed. For each probabilistic event class, the ruleset MUST identify the exact future round offset or seed-consumption rule before match start.

No bootstrap fixture currently enables Simulated Deck; fixture-backed examples should be added with the first probabilistic ruleset profile.

If an agent fails to reveal, its missing nonce MUST be excluded or replaced only according to the declared profile. The base fault handling still applies: the action defaults to Level 0 Inertial, and the missing reveal is recorded for audit or tournament penalties. Delayed entropy reduces but does not eliminate reveal-withholding griefing, so competitive profiles SHOULD pair Simulated Deck with strict deadlines, signed messages, and sanctions.

## 10. Quorum and Fault Handling

### 10.1 Quorum Threshold

The default quorum threshold is:

```text
quorum = ceil(active_agents * 2 / 3)
```

A ruleset MAY define a stricter threshold, but MUST NOT define a threshold below simple majority.

For local two-agent bootstrap matches, the default mode is strict 2-of-2 quorum. Both active agents MUST publish the same state hash before a round is locked. Tournament profiles MAY use validator-assisted two-agent quorum, for example two agents plus one neutral validator with a 2-of-3 threshold.

### 10.2 Active Agents

An active agent is one that:

1. Was included in the genesis state.
2. Has not been eliminated.
3. Has not been disqualified by audit or protocol violation.

Eliminated agents do not count toward future quorum thresholds unless a tournament ruleset explicitly defines spectator-validator participation.

### 10.3 Missing Commits

If an agent does not submit a commit before the deadline, its action is treated as Level 0 Inertial for that round. The agent remains active unless ruleset-defined inactivity penalties eliminate it.

### 10.4 Missing Reveals

If an agent commits but does not reveal before the deadline:

1. The action is treated as Level 0 Inertial.
2. The unresolved commit is recorded in the audit log and, for local replay fixtures, as a canonical `world_state.audit_flags` entry:

   ```json
   {"agent_id":"<agent-id>","fallback":"inertial","round":N,"type":"missing_reveal"}
   ```

3. Repeated missing reveals MAY trigger reputation penalties or disqualification under tournament rules.

Missing reveals are more severe than missing commits because the agent already published a commitment and can otherwise use reveal withholding as a timing or griefing tool. Tournament profiles SHOULD penalize missing reveals more strongly than missing commits.

### 10.5 Hash Disagreement

If quorum is not reached for a state hash:

1. Nodes SHOULD exchange diagnostic state fragments or replay traces.
2. Nodes MUST NOT advance to the next round without a locked state.
3. If disagreement persists, the match enters dispute mode.

Dispute mode is ruleset-defined, but it SHOULD allow deterministic replay from the last locked round. A minimal diagnostic shape for early fixtures is:

```json
{"available_votes":1,"decision":"round_not_locked","required_votes":2}
```

Rulesets MAY add richer replay trace fragments, but the diagnostic object MUST NOT itself alter the locked world state.

## 11. Canonical Serialization

Canonical serialization is required for commitments, ledger hashes, and state hashes.

Implementations MUST define:

1. Field ordering.
2. Integer encoding.
3. String encoding.
4. Array ordering.
5. Omission rules for null or empty values.
6. Hash algorithm version.

The default canonical encoding for RQP 1.0-draft.1 is `sorted-key-json-v1`, a UTF-8 JSON profile with:

1. Lexicographically sorted object keys.
2. No insignificant whitespace.
3. Decimal integer strings only where integer size may exceed native JSON precision.
4. Arrays preserved in canonical order.

Protocol Buffers, CBOR, or another binary encoding MAY be used if all participants agree on the exact canonical form in the genesis state.

Bootstrap fixtures MUST include the exact canonical JSON string or the exact canonicalization profile used for every expected hash. A new engine MUST be able to reproduce each expected SHA-256 digest from the fixture data.

## 12. Match End Conditions

A match ends when one or more ruleset-defined conditions are met. Default end conditions are:

1. Only one non-eliminated agent remains.
2. A maximum round limit is reached.
3. Quorum cannot be restored from the last locked state.
4. All remaining agents are inertial and unable to affect future state.

An agent is eliminated by default when:

1. `hp <= 0`.
2. `fuel_remaining <= 0` and the agent is required to pay a positive operating cost.
3. It violates a protocol rule that requires disqualification.

## 13. Audit and Sanctions

### 13.1 Audit Disclosure

At match end, each agent MUST publish and disclose for audit:

1. Initial loadout salt.
2. All per-round Commit Nonces; see Section 7.4 for field name conventions.
3. All per-round fuel ledger salts.
4. Full fuel burn sequence.
5. Any hidden data that the active ruleset requires disclosure for during audit, such as hidden action logs, Energy Flux decompositions, pre-locked nonce sequences, thermal state inputs, or hidden configuration.

### 13.2 Audit Verification

Auditors replay:

1. Loadout purchase and initial fuel ledger hash.
2. Every round commitment.
3. Every reveal hash.
4. Every fuel burn and fuel remaining value.
5. Every world state transition.
6. Every state hash quorum result.
7. Any enabled Energy Flux, Simulated Deck, Thermal Debt, Signal Flare, or pre-lock rule.

The audit passes only if all commitments, ledger hashes, fuel balances, and state transitions are valid.

Audit tooling SHOULD be able to emit a machine-readable report. The default report shape is:

```json
{
  "type": "audit_report",
  "protocol": "rqp/1.0-draft.1",
  "match_id": "match-001",
  "result": "pass",
  "agent_results": [
    {
      "agent_id": "0xABC",
      "audit": "pass",
      "violations": []
    }
  ]
}
```

Required violation types are `commit_mismatch`, `fuel_overspend`, `ledger_mismatch`, `invalid_action`, `conflicting_state_vote`, and `serialization_violation`.

Profiles that enable advanced resource or transparency extensions SHOULD also define `energy_flux_mismatch`, `deck_entropy_violation`, `thermal_debt_mismatch`, and `prelock_violation`.

### 13.3 Violations

The following are protocol violations:

1. Revealing data that does not match the committed hash.
2. Spending more fuel than available.
3. Publishing inconsistent ledger hashes.
4. Voting or acting outside ruleset limits.
5. Signing conflicting state votes for the same round.
6. Tampering with canonical serialization or hash inputs.
7. Declaring Energy Flux that does not match the audited detailed resource log.
8. Steering, withholding, or substituting deck entropy outside the declared Simulated Deck profile.
9. Failing to honor a required Signal Flare pre-lock sequence.

### 13.4 Sanctions

If an agent fails audit, the ruleset MAY apply:

1. Match disqualification.
2. Reversal of the agent's match result.
3. Reputation penalty.
4. Tournament blacklist.
5. Loss of persistent rewards.

Sanctions MUST be deterministic and declared before match start.

## 14. Tournament Persistence

Tournament mode MAY carry audited outcomes across matches. A tournament profile MAY persist:

1. Remaining fuel.
2. A percentage of fuel destroyed, captured, or denied from opponents.
3. Reputation score.
4. Unlocked loadout options.
5. Ranking points or bracket position.

Any persistent reward MUST be derived only from audited match data. If an agent fails audit, its rewards for that match MUST NOT be applied.

## 15. Transport

RQP messages MAY be transported over:

1. libp2p.
2. WebSocket pub/sub.
3. NATS, Redis Streams, or another message hub.
4. Local files for offline replay.

Transport layers MUST preserve:

1. Message authenticity.
2. Agent identity.
3. Match ID.
4. Round number.
5. Phase boundaries.

Transport layers MUST NOT alter canonical payloads.

### 15.1 Local Replay Bootstrap Profile

The local replay profile is the mandatory bootstrap transport for early implementations. In this profile:

1. Genesis, round messages, state votes, and audit disclosures are read from local files.
2. File order, round numbers, and phase names define replay order.
3. Signatures MAY be omitted.
4. Every canonical hash MUST match the fixture or event log.
5. Replay MUST produce the same locked world-state hashes as networked play.

## 16. Identity and Signatures

Each agent SHOULD have a stable cryptographic identity. Messages SHOULD be signed by the agent identity key.

A signed message envelope SHOULD include:

```json
{
  "agent_id": "0xABC",
  "public_key": "base64-public-key",
  "payload_hash": "sha256-payload-hash",
  "signature": "base64-signature"
}
```

The exact signature scheme is ruleset-defined. Implementations SHOULD use a widely reviewed signature algorithm such as Ed25519.

Unsigned messages are valid only for local replay and local development profiles. Public network and tournament profiles MUST require signed payloads.

## 17. Spectator and Replay Support

RQP is designed to be replayable and observable. A spectator client can reconstruct a match from:

1. Genesis state.
2. Commit messages.
3. Reveal messages.
4. State vote messages.
5. Audit disclosures after match end.

During live play, spectators can see committed activity and revealed actions, but hidden fuel balances remain unavailable until audit. Tournament or broadcast modes MAY grant trusted observers access to private data for commentary overlays, but such access is outside the canonical protocol.

The default competitive broadcast mode exposes public commits, reveals, state votes, public world state, and locked hashes. Delayed god-view broadcast MAY reveal hidden fuel and intent after a delay or after match end, but it is not part of canonical consensus.

Profiles that enable Signal Flares MUST declare how `bright` or `flaring` visibility is exposed to spectators and opponents. Publicly revealed future nonces are live competitive information, while unrevealed physical actions remain hidden until the normal reveal phase unless the ruleset explicitly defines perfect-information flare behavior.

## 18. Security Considerations

### 18.1 Commit-Reveal Withholding

Agents can grief by committing and refusing to reveal. RQP handles this by defaulting missing reveals to Inertial and recording the event for audit or reputation penalties.

### 18.2 Last-Revealer Advantage

Agents revealing late may gain timing information. Implementations SHOULD use strict reveal deadlines and MAY use encrypted reveal transport or simultaneous disclosure mechanisms.

When Simulated Deck is enabled, profiles SHOULD consume round `n` entropy only in round `n+1` or later. This delayed use reduces the value of revealing last but does not prevent an agent from withholding a reveal to grief or avoid a bad future seed.

### 18.3 Hash Collisions

RQP uses SHA-256 by default. Future versions MAY negotiate stronger algorithms, but all participants MUST use the same algorithm for a match.

### 18.4 Serialization Mismatch

Serialization mismatch is a major consensus risk. Implementations MUST test canonical serialization across languages before participating in a match.

### 18.5 Transport Censorship

A centralized pub/sub hub can censor or delay messages. Competitive deployments SHOULD use redundant relays or peer-to-peer gossip.

### 18.6 Commit Sniffing

Small discrete action spaces make unsalted commits vulnerable to brute-force enumeration. An observer can hash every plausible movement, weapon, vote, and fuel combination and compare those hashes against the public commit. High-entropy per-round commit nonces prevent this attack by making the search space infeasible.

### 18.7 Deck Steering and Transparency Bluffing

If a Signal Flare exposes future nonces, a still-dark opponent may try to grind its own nonce before committing in order to steer a future Simulated Deck seed. The core protocol does not prevent this attack by itself; rulesets and tournament profiles should address it through policy and mechanics such as deadlines, entropy requirements, and sanctions.

Profiles that combine Simulated Deck with bright/dark visibility MUST declare whether nonce grinding against public bright-ship entropy is permitted. Profiles that forbid grinding MUST require all deck-contributing nonce commitments to be locked before any contributing nonce is revealed, or MUST use an equivalent nonce-chain or pre-commitment scheme. Such profiles SHOULD also define minimum entropy requirements, delayed deck consumption windows, and penalties for reveal withholding.

Non-normative strategic note: a bright agent's action commitment can remain hidden until reveal, so intentionally unexpected physical actions are a legitimate counter to opponents that overfit to known future entropy.

## 19. Implementation Requirements

A conforming RQP 1.0-draft.1 implementation MUST support:

1. Deterministic axial hex-grid simulation.
2. Fixed-point or integer-only canonical math.
3. Commit, reveal, execution, and consensus phases.
4. Fuel ledger hash chaining.
5. Quorum state hash locking.
6. Missing commit and missing reveal handling.
7. Dynamic environment updates from deterministic creep and voting.
8. Post-match audit replay.
9. Canonical serialization.

A bootstrap-conforming implementation MUST also reproduce the official local replay fixture hashes for genesis, inertial rounds, simple active thrust, constant-drift visual gravity, bootstrap line-of-sight weapons, bootstrap stationary collisions, strict 2-of-2 quorum, and post-game audit.

A competitive implementation SHOULD also support:

1. Signed messages.
2. Replay export.
3. Dispute diagnostics.
4. Configurable quorum thresholds.
5. Tournament persistence.

## 20. Reference Parameters

The following parameters are recommended defaults for early implementations:

| Parameter | Default |
| --- | --- |
| Quorum threshold | `ceil(active_agents * 2 / 3)` |
| Two-agent local/dev quorum | Strict `2 of 2` |
| Numeric type | Signed 64-bit integer |
| Coordinate system | Axial hex `(q, r)` |
| Hash algorithm | SHA-256 |
| Canonical encoding | `sorted-key-json-v1` |
| Commit timeout | Ruleset-defined |
| Reveal timeout | Ruleset-defined |
| `HEX_THRESHOLD` | `100` |
| `C_VOTE_INCREMENT` | `1` |
| `HEX_DECAY_PER_ROUND` | `5` |
| Default vote weight | `1` |
| Missing commit action | Inertial |
| Missing reveal action | Inertial plus audit flag |

## 21. Open Questions

The following topics are intentionally left for future RFCs or rulesets:

1. Production-grade ship and weapon catalogs beyond the fixture-backed `rqp-default-playable-v0` schemas.
2. Competitive balance formulas beyond the profile's integer fixed-damage weapons and velocity-based stationary collision formula.
3. Fully seed-derived standard map generation beyond `explicit-materialized-v1` provenance plus materialized canonical objects.
4. Network dispute mode beyond the minimal `round_not_locked` diagnostic shape.
5. Tournament reward formulas.
6. Anti-collusion rules for multi-agent alliances.
7. Optional zero-knowledge fuel proofs to reduce post-match information leakage.
8. Advanced line-of-sight weapons, thick beams, cone weapons, dynamic real-time pruning, and post-game deep-audit fuel-mining mechanics beyond the simple bootstrap/default profile line-of-sight boundaries.
9. Fixture-backed Energy Flux, Simulated Deck, Thermal Debt, Signal Flare, and pre-lock profiles.

## 22. Motto

In space, no one can hear you scream, but everyone can audit your fuel ledger.
