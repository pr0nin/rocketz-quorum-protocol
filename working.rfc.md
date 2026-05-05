# Working RFC: RQP Supplements and Open Profiles

**Status:** Working Draft  
**Companion to:** `rfc.md` and `rfc-deviations.md`  
**Purpose:** Convert deviation suggestions 2-17 into concrete follow-up material.

This document is not normative yet. It gathers the next layer of protocol decisions that should eventually become separate RFCs, ruleset profiles, or implementation test suites.

## 1. Language and Audience Profile

Protocol documents should use English for interoperability. Design notes may preserve Norwegian terms when they carry useful nuance.

Recommended split:

1. `rfc.md` - normative English protocol.
2. `one-pager.md` - public concept pitch.
3. Norwegian design notes - optional local design archive.

Terms worth preserving in a glossary:

| Norwegian term | English protocol term | Design meaning |
| --- | --- | --- |
| bløffing | bluffing | Hidden fuel expenditure creates poker-like uncertainty. |
| skattelegging | taxation | Agents can make board areas more expensive to operate in. |
| implisitt kommunikasjon | implicit signaling | Votes and movement patterns communicate without chat. |

## 2. Transport Profiles

RQP should support several transport profiles without changing canonical simulation.

### 2.1 Local Replay Profile

Used for testing, debugging, and offline analysis.

Requirements:

1. Messages are read from append-only files.
2. Phase ordering is derived from file order and round numbers.
3. Signatures may be disabled.
4. Replay must produce the same state hashes as networked play.

### 2.2 WebSocket Hub Profile

Used for practical early implementation.

Requirements:

1. The hub relays messages but never decides state.
2. Agents subscribe to match channels.
3. The hub enforces phase deadlines only as transport coordination.
4. Nodes still validate all payloads locally.

### 2.3 libp2p Profile

Used for decentralized production play.

Requirements:

1. Agents gossip phase messages.
2. Duplicate messages are ignored by `(match_id, round, phase, agent_id)`.
3. Peer scoring should penalize invalid, late, or conflicting messages.
4. Message signatures are mandatory.

### 2.4 Tournament Relay Profile

Used for organized competitions.

Requirements:

1. Redundant relays should be used.
2. Signed messages are mandatory.
3. Public event logs are exported for audit.
4. Relay operators do not control canonical state.

## 3. Deterministic Physics Detail

The base RFC defines deterministic physics but leaves several functions for rulesets. The default ruleset should define them explicitly.

### 3.1 Gravity Seed Function

Recommended deterministic gravity:

```text
gravity_hash = SHA256(canonical(match_seed, "gravity", round, q, r))
gx = ((gravity_hash[0] mod 3) - 1) * GRAVITY_UNIT
gr = ((gravity_hash[1] mod 3) - 1) * GRAVITY_UNIT
```

Default:

```text
GRAVITY_UNIT = 1
```

This gives each sampled hex a deterministic axial gravity vector where each component is `-1`, `0`, or `1`.

### 3.2 High-Velocity Path Traversal

When velocity crosses multiple hexes in one round, collision checks should trace the canonical path from start to end.

Recommended algorithm:

1. Convert axial coordinates to cube coordinates.
2. Interpolate from start cube coordinate to end cube coordinate in `N = distance(start, end)` steps.
3. Round each interpolated cube coordinate with deterministic cube rounding.
4. Evaluate collisions in path order.
5. If multiple objects occupy the same path step, use collision priority, then canonical object ID.

### 3.3 Simultaneous Multi-Object Collisions

Recommended default:

1. Group collision candidates by destination hex.
2. Resolve stationary terrain first.
3. Resolve ship-ship collisions by ascending object ID pair.
4. Resolve ordnance collisions last.
5. Any object destroyed earlier in the sequence is removed before later collision checks.

### 3.4 Position Precision

Default RQP should use integer hex positions for simplicity. A future advanced-physics profile may use fixed-point sub-hex positions, but must define:

1. Scale factor.
2. Rounding mode.
3. Path traversal.
4. Collision volume.
5. Canonical serialization.

## 4. Tactical Stake Privacy

Current RQP reveals tactical stake during the reveal phase because all nodes need it to determine initiative order.

Recommended decision for v1:

```text
Tactical stake is public after reveal.
```

Rationale:

1. It is simple.
2. It is deterministic.
3. It avoids cryptographic complexity.
4. It keeps priority disputes auditable.

Future option:

```text
Commitment-only stake ranking with zero-knowledge proof.
```

This could hide exact stakes while proving correct ordering, but should not block v1.

## 5. Fuel Ledger Privacy and Zero-Knowledge Proofs

Base RQP audits fuel after match end. This reveals the full fuel history.

Future privacy extension:

1. Agents prove `fuel_remaining >= 0` each round.
2. Agents prove `fuel_burn` matches committed action costs.
3. Agents keep exact remaining fuel private after the match.

This extension should be optional. It adds complexity and is not required for early interoperability.

## 6. Broadcast and Spectator Modes

RQP should define two broadcast modes.

### 6.1 Competitive Live Mode

Spectators see:

1. Commits.
2. Revealed actions.
3. Votes after reveal.
4. State hashes.
5. Public world state.

Spectators do not see hidden fuel balances until audit.

### 6.2 Delayed God-View Mode

Spectators see:

1. Public live match data.
2. Hidden fuel and intent after a delay or after match completion.
3. Audit overlays explaining bluffing, tactical stakes, and political votes.

This protects competitive secrecy while preserving entertainment value.

## 7. Signaling and Political Play

Voting is both environmental control and communication.

Known strategic patterns:

1. **Escape taxation:** Multiple agents vote along an enemy's likely retreat corridor.
2. **Alliance proof:** Agents repeatedly vote the same region to signal cooperation.
3. **False coalition:** Agents imitate aligned votes before betraying through movement.
4. **Leader punishment:** Trailing agents tax the strongest agent's safe routes.
5. **Zone herding:** Agents combine votes and movement to force opponents into gravity wells or high-cost hexes.

The default ruleset should preserve enough vote persistence for these patterns to be readable.

## 8. Hex Threshold Semantics

The trigger condition should be:

```text
hex_potential >= HEX_THRESHOLD
```

Rationale:

1. Exact threshold hits should matter.
2. `>=` avoids off-by-one confusion.
3. It is easier to explain and test.

If a ruleset wants "over 100", it should define:

```text
HEX_BOUNDARY = 100
trigger when hex_potential > HEX_BOUNDARY
```

## 9. Fixed-Point Multipliers

Fractional multipliers must not use floats.

Recommended encoding:

```text
effective_vote = floor(base_vote * multiplier_num / multiplier_den)
```

Example:

```text
1.5x = multiplier_num 3, multiplier_den 2
```

Rulesets must define rounding. Default rounding is floor toward zero.

## 10. Two-Agent Quorum

Default quorum is:

```text
ceil(active_agents * 2 / 3)
```

For two-agent matches this requires both agents, which is secure but fragile.

Recommended tournament options:

| Mode | Two-agent quorum | Tradeoff |
| --- | --- | --- |
| Strict | 2 of 2 | Highest integrity, vulnerable to disconnect griefing. |
| Validator-assisted | 2 of 3 including neutral validator | Better liveness, requires trusted or semi-trusted validator slot. |
| Replay-adjudicated | 1 of 2 can advance into dispute window | Better liveness, higher dispute complexity. |

Default recommendation:

```text
Use strict 2-of-2 for local/dev matches and validator-assisted quorum for tournaments.
```

## 11. Missing Reveal Penalties

Missing reveals should be more serious than missing commits.

Recommended default:

| Event | Round effect | Reputation effect |
| --- | --- | --- |
| Missing commit | Inertial action | Minor warning |
| Missing reveal | Inertial action and audit flag | Moderate penalty |
| Three missing reveals in one match | Disqualification eligible | Major penalty |
| Conflicting reveals | Protocol violation | Severe penalty |

Reasoning:

1. Missing commits may be ordinary inactivity.
2. Commit-withholding can be strategic griefing.
3. Repeated missing reveals degrade match quality and spectator trust.

## 12. Machine-Readable Audit Report

Future audit tooling should emit JSON reports.

Recommended schema:

```json
{
  "type": "audit_report",
  "protocol": "rqp/1.0-draft.1",
  "match_id": "match-001",
  "auditor_id": "auditor-001",
  "result": "fail",
  "violations": [
    {
      "agent_id": "0xABC",
      "round": 42,
      "violation_type": "fuel_overspend",
      "evidence_hashes": [
        "sha256-commit",
        "sha256-ledger",
        "sha256-state"
      ],
      "recommended_sanction": "disqualification"
    }
  ]
}
```

Required violation types:

1. `commit_mismatch`
2. `fuel_overspend`
3. `ledger_mismatch`
4. `invalid_action`
5. `conflicting_state_vote`
6. `serialization_violation`

## 13. Tournament Persistence Boundaries

Tournament persistence should remain outside the base protocol until match semantics stabilize.

Recommended persistence categories:

1. Remaining fuel bonus.
2. Captured or denied opponent fuel bonus.
3. Reputation modifier.
4. Loadout unlocks.
5. Ranking points.

Anti-snowball guardrails:

1. Cap carried fuel.
2. Convert excess rewards into non-combat ranking points.
3. Reset loadout tiers per bracket stage.
4. Penalize failed audits by voiding all rewards.

## 14. Canonical Test Vector Suite

Before implementation, RQP needs cross-language test vectors.

Required vectors:

1. Genesis state hash.
2. Commit payload hash.
3. Fuel ledger hash.
4. World state hash after one inertial round.
5. Vote threshold update hash.
6. Missing reveal state transition hash.

Each vector should include:

1. Human-readable description.
2. Canonical JSON input.
3. Expected SHA-256 output.
4. Notes about integer encoding and ordering.

## 15. Identity and Signatures

Unsigned messages are acceptable only for local development.

Recommended profiles:

| Profile | Signature requirement |
| --- | --- |
| Local replay | Optional |
| Local network dev | Recommended |
| Public network | Mandatory |
| Tournament | Mandatory |

Recommended algorithm:

```text
Ed25519
```

Every signed payload should bind:

1. Protocol version.
2. Match ID.
3. Round.
4. Phase.
5. Agent ID.
6. Payload hash.

## 16. Delayed God-View Broadcast

Delayed god-view is the best compromise between competitive secrecy and spectator drama.

Recommended broadcast delay models:

| Mode | Delay | Use case |
| --- | --- | --- |
| Round delay | 1-3 rounds | Fast commentary, minor competitive risk. |
| Tactical delay | Until combat resolves | Shows bluff consequences after they matter. |
| Match-end reveal | Full match | Maximum integrity, best post-game analysis. |

Default recommendation:

```text
Use public live mode during competition and match-end god-view for official analysis.
```

## 17. Promotion Path to Future RFCs

The material in this working draft should be split into separate documents:

1. `ruleset-default.md` for physics, costs, ships, weapons, and map generation.
2. `transport-profile-websocket.md` for early network implementation.
3. `canonical-test-vectors.md` for hash interoperability.
4. `tournament-profile.md` for persistence, rewards, sanctions, and signatures.
5. A future privacy RFC for zero-knowledge fuel proofs.
6. A future broadcast RFC for delayed god-view and commentary overlays.
