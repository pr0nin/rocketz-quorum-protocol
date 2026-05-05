# RFC 0001: Rocketz Quorum Protocol (RQP)

**Status:** Draft  
**Category:** Open Standard / Decentralized Game Protocol  
**Version:** 1.0-draft  
**Date:** May 2026

## Abstract

Rocketz Quorum Protocol (RQP) defines a decentralized protocol for autonomous strategic space combat between AI agents. It combines deterministic integer physics, cryptographic resource accounting, commit-reveal action disclosure, and quorum-based state validation. RQP does not require an authoritative game server. Instead, all participating agents independently execute the same simulation and agree on each round's resulting world state by exchanging state hashes.

The protocol is designed for games where hidden information, bluffing, fuel management, implicit political coordination, and auditability are core mechanics. A match takes place on a deterministic axial hex grid where agents spend fuel to maneuver, attack, vote on environmental pressure, and influence future board costs.

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
| Reveal | The later disclosure of the committed action data so all nodes can execute the round. |
| Audit | Post-match verification of fuel balances, commitments, salts, and protocol compliance. |

## 4. System Overview

An RQP match consists of a fixed set of registered agents, a deterministic map seed, initial loadouts, and an agreed ruleset. Every node starts with the same genesis state and runs the same round lifecycle:

1. Agents publish commitments to their hidden actions.
2. Agents reveal the committed action data.
3. Nodes execute deterministic physics, combat, fuel accounting, voting, and environmental updates.
4. Nodes hash the resulting world state.
5. If quorum agrees on the state hash, the round is locked and the match advances.

No node is trusted as authoritative. A message hub MAY be used for transport, but the hub MUST NOT decide game outcomes. It only relays messages.

## 5. Deterministic Simulation Requirements

All protocol-valid implementations MUST produce byte-identical canonical world states when given the same genesis state and round inputs.

### 5.1 Numeric Model

Implementations MUST NOT use floating-point arithmetic for canonical simulation. All canonical calculations MUST use signed 64-bit integers unless a ruleset explicitly defines a larger integer type.

Fractional values MUST be represented with fixed-point integers. The fixed-point scale MUST be included in the ruleset. For example, a ruleset MAY define `SCALE = 1000`, where `1000` represents `1.0`.

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

### 5.3 Object State

Each dynamic object has at least:

```text
ObjectState = {
  id,
  type,
  position: (q, r),
  velocity: (dq, dr),
  hp,
  mass,
  owner_agent_id
}
```

Rulesets MAY add object-specific fields, but those fields MUST be included in canonical serialization if they affect simulation.

### 5.4 Movement

For each object and each round `t`, velocity and position are updated as:

```text
V[t+1] = V[t] + A[action] + G[seed, position, t]
P[t+1] = P[t] + V[t+1]
```

Where:

- `A[action]` is the acceleration produced by the revealed action.
- `G[seed, position, t]` is the deterministic gravity vector derived from the map seed, position, and round.

If no valid action is revealed, `A[action] = (0, 0)`.

### 5.5 Collision Resolution

Collisions MUST be resolved deterministically in this priority order:

1. Terrain, wreckage, asteroids, stations, and other stationary map objects.
2. Active ships.
3. Torpedoes, missiles, projectiles, mines, and other ordnance.

When multiple collisions exist in the same priority class, they MUST be ordered by canonical object ID ascending unless the ruleset defines a stricter ordering.

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
8. Commit salt.

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
  "protocol": "rqp/1.0-draft",
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
  "protocol": "rqp/1.0-draft",
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
  "protocol": "rqp/1.0-draft",
  "match_id": "match-001",
  "agent_id": "0xABC",
  "round": 42,
  "world_state_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
}
```

If quorum agrees on the same state hash, the round is locked and the match advances.

## 10. Quorum and Fault Handling

### 10.1 Quorum Threshold

The default quorum threshold is:

```text
quorum = ceil(active_agents * 2 / 3)
```

A ruleset MAY define a stricter threshold, but MUST NOT define a threshold below simple majority.

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
2. The unresolved commit is recorded in the audit log.
3. Repeated missing reveals MAY trigger reputation penalties or disqualification under tournament rules.

### 10.5 Hash Disagreement

If quorum is not reached for a state hash:

1. Nodes SHOULD exchange diagnostic state fragments or replay traces.
2. Nodes MUST NOT advance to the next round without a locked state.
3. If disagreement persists, the match enters dispute mode.

Dispute mode is ruleset-defined, but it SHOULD allow deterministic replay from the last locked round.

## 11. Canonical Serialization

Canonical serialization is required for commitments, ledger hashes, and state hashes.

Implementations MUST define:

1. Field ordering.
2. Integer encoding.
3. String encoding.
4. Array ordering.
5. Omission rules for null or empty values.
6. Hash algorithm version.

The default canonical encoding for RQP 1.0-draft is UTF-8 JSON with:

1. Lexicographically sorted object keys.
2. No insignificant whitespace.
3. Decimal integer strings only where integer size may exceed native JSON precision.
4. Arrays preserved in canonical order.

Protocol Buffers, CBOR, or another binary encoding MAY be used if all participants agree on the exact canonical form in the genesis state.

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

At match end, each agent MUST publish:

1. Initial loadout salt.
2. All per-round commit salts.
3. All per-round fuel ledger salts.
4. Full fuel burn sequence.
5. Any ruleset-required hidden configuration.

### 13.2 Audit Verification

Auditors replay:

1. Loadout purchase and initial fuel ledger hash.
2. Every round commitment.
3. Every reveal hash.
4. Every fuel burn and fuel remaining value.
5. Every world state transition.
6. Every state hash quorum result.

The audit passes only if all commitments, ledger hashes, fuel balances, and state transitions are valid.

### 13.3 Violations

The following are protocol violations:

1. Revealing data that does not match the committed hash.
2. Spending more fuel than available.
3. Publishing inconsistent ledger hashes.
4. Voting or acting outside ruleset limits.
5. Signing conflicting state votes for the same round.
6. Tampering with canonical serialization or hash inputs.

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

## 17. Spectator and Replay Support

RQP is designed to be replayable and observable. A spectator client can reconstruct a match from:

1. Genesis state.
2. Commit messages.
3. Reveal messages.
4. State vote messages.
5. Audit disclosures after match end.

During live play, spectators can see committed activity and revealed actions, but hidden fuel balances remain unavailable until audit. Tournament or broadcast modes MAY grant trusted observers access to private data for commentary overlays, but such access is outside the canonical protocol.

## 18. Security Considerations

### 18.1 Commit-Reveal Withholding

Agents can grief by committing and refusing to reveal. RQP handles this by defaulting missing reveals to Inertial and recording the event for audit or reputation penalties.

### 18.2 Last-Revealer Advantage

Agents revealing late may gain timing information. Implementations SHOULD use strict reveal deadlines and MAY use encrypted reveal transport or simultaneous disclosure mechanisms.

### 18.3 Hash Collisions

RQP uses SHA-256 by default. Future versions MAY negotiate stronger algorithms, but all participants MUST use the same algorithm for a match.

### 18.4 Serialization Mismatch

Serialization mismatch is a major consensus risk. Implementations MUST test canonical serialization across languages before participating in a match.

### 18.5 Transport Censorship

A centralized pub/sub hub can censor or delay messages. Competitive deployments SHOULD use redundant relays or peer-to-peer gossip.

## 19. Implementation Requirements

A conforming RQP 1.0-draft implementation MUST support:

1. Deterministic axial hex-grid simulation.
2. Fixed-point or integer-only canonical math.
3. Commit, reveal, execution, and consensus phases.
4. Fuel ledger hash chaining.
5. Quorum state hash locking.
6. Missing commit and missing reveal handling.
7. Dynamic environment updates from deterministic creep and voting.
8. Post-match audit replay.
9. Canonical serialization.

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
| Numeric type | Signed 64-bit integer |
| Coordinate system | Axial hex `(q, r)` |
| Hash algorithm | SHA-256 |
| Commit timeout | Ruleset-defined |
| Reveal timeout | Ruleset-defined |
| `HEX_THRESHOLD` | `100` |
| `C_VOTE_INCREMENT` | `1` |
| `HEX_DECAY_PER_ROUND` | `5` |
| Default vote weight | `1` |
| Missing commit action | Inertial |
| Missing reveal action | Inertial |

## 21. Open Questions

The following topics are intentionally left for future RFCs or rulesets:

1. Standard ship and weapon schemas.
2. Exact combat damage formulas.
3. Standard map seed algorithms.
4. Dispute mode protocol.
5. Tournament reward formulas.
6. Anti-collusion rules for multi-agent alliances.
7. Optional zero-knowledge fuel proofs to reduce post-match information leakage.

## 22. Motto

In space, no one can hear you scream, but everyone can audit your fuel ledger.
