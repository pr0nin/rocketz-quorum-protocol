# RQP Bootstrap Fixture

This fixture is the first conformance target for a new RQP engine. It verifies canonical JSON hashing, fuel-ledger chaining, commit/reveal hashing, deterministic inertial execution, strict two-agent quorum, and post-game audit replay.

Files:

1. `inertial-3-rounds.json` - genesis data, three inertial rounds, expected ledger hashes, commit hashes, world-state hashes, state votes, and quorum locks.
2. `post-game-audit.json` - post-game disclosure and expected audit result for the same match.
3. `one-action-thrust.json` - genesis data and one active thrust round where `agent-a` spends fuel and changes velocity/position.
4. `one-action-thrust-audit.json` - post-game disclosure and expected audit result for the thrust fixture.
5. `gravity-7r-no-weapons.json` - seven visual rounds with constant downward drift and no equipped weapons.
6. `gravity-7r-no-weapons-audit.json` - post-game disclosure and expected audit result for the no-weapons gravity fixture.
7. `gravity-7r-one-armed.json` - seven visual rounds where only `agent-a` has a line-of-sight weapon.
8. `gravity-7r-one-armed-audit.json` - post-game disclosure and expected audit result for the one-armed gravity fixture.
9. `gravity-7r-both-armed.json` - seven visual rounds where both agents have line-of-sight weapons.
10. `gravity-7r-both-armed-audit.json` - post-game disclosure and expected audit result for the both-armed gravity fixture.
11. `gravity-7r-los-blocked.json` - seven visual rounds where both agents fire line-of-sight weapons, but two opaque objects block one firing round.
12. `gravity-7r-los-blocked-audit.json` - post-game disclosure and expected audit result for the blocked-LOS gravity fixture.
13. `gravity-4r-asteroid-collision.json` - four visual rounds where `agent-a` drifts into a stationary asteroid and takes collision damage.
14. `gravity-4r-asteroid-collision-audit.json` - post-game disclosure and expected audit result for the asteroid collision fixture.
15. `gravity-4r-asteroid-velocity-collision.json` - four visual rounds where the same asteroid impact uses velocity-based collision damage.
16. `gravity-4r-asteroid-velocity-collision-audit.json` - post-game disclosure and expected audit result for the velocity collision fixture.
17. `rfc5-fixture-index.json` - machine-readable index mapping RFC section 5 headings to executable fixtures.

## Fixture Scope

The match uses `rqp/1.0-draft.1` with the local replay bootstrap ruleset:

1. Two active agents: `agent-a` and `agent-b`.
2. Strict 2-of-2 quorum.
3. Unsigned local replay messages.
4. Gravity explicitly disabled by genesis ruleset.
5. Both agents choose Level 0 Inertial for rounds 1, 2, and 3.
6. No votes, weapons, collisions, fuel burn, creep, decay, damage, or eliminations.

This fixture does not test combat balance, advanced weapons, line-of-sight pruning, tournament rewards, signatures, networking, or zero-knowledge privacy.

The thrust fixture adds exactly one state-changing action:

1. `agent-a` uses Level 1 Active with thrust `[1, 0]`.
2. Fuel burn is `3`: active base `1` plus one thrust unit at cost `2`.
3. `agent-a` velocity changes from `(0, 0)` to `(1, 0)`.
4. `agent-a` position changes from `(0, 0)` to `(1, 0)`.
5. `agent-b` remains inertial.

The seven-round gravity fixtures are visual sanity scenarios on a 10-by-10 axial map:

1. Map bounds are `q = 0..9` and `r = 0..9`.
2. `agent-a` starts at `(3, 1)` and `agent-b` starts at `(6, 1)`.
3. Both agents are roughly three hexes from the horizontal map edges and close enough for the fixture weapon range `4`.
4. The visual "bottom" direction is `+r`.
5. `gravity_mode = constant_drift` applies `(dq = 0, dr = 1)` to position each round without changing velocity.
6. Both agents drift from `r = 1` to `r = 8` over seven rounds.
7. Weapon damage is `10`; initial HP is `60`; six unblocked firing rounds reduce a target to `0` HP.
8. Firing starts on round 2 so live-view engines can show one clean falling-only round before combat.

The blocked-LOS fixture adds two opaque asteroids:

1. `los-rock-1` at `(4, 4)`.
2. `los-rock-2` at `(5, 4)`.
3. During round 3, the agents drift to `r = 4`, so both blockers sit in the two intermediate hexes between `(3, 4)` and `(6, 4)`.
4. Round 3 shots are blocked and deal no damage.
5. Both agents end at `10` HP instead of `0` HP.

The asteroid collision fixture adds one stationary collision object:

1. `asteroid-impact-1` at `(3, 4)`.
2. `agent-a` starts at `(3, 1)` and drifts down the same `q = 3` column.
3. `agent-a` reaches the asteroid on round 3.
4. Bootstrap stationary collision damage is `40`, so `agent-a` drops from `60` HP to `20` HP.
5. `agent-b` drifts safely from `(6, 1)` to `(6, 5)` and remains at `60` HP.

The velocity collision fixture uses the same visual setup as the asteroid collision fixture, but the collision profile is `velocity_based`:

1. `agent-a` reaches `asteroid-impact-velocity-1` on round 3.
2. Impact speed is the actual round delta, `abs(0) + abs(1) = 1`.
3. Damage is `min(40, speed * 40) = 40`.
4. Final HP is therefore the same as the flat fixture, but it is produced by a different map/ruleset condition profile.

## Canonicalization

Every expected hash uses `sorted-key-json-v1`:

1. Serialize the target object as UTF-8 JSON.
2. Sort all object keys lexicographically.
3. Preserve array order.
4. Emit no insignificant whitespace.
5. Hash the resulting bytes with SHA-256.

For example, the genesis `world_state` hash is:

```text
6feaaa0dabfb86e478934491902eae204427ede07e4ca544af549f8cc1197ac9
```

## Engine Verification Procedure

The checked-in reference verifier runs this procedure:

```text
python3 tools/rqp_verify_bootstrap.py
```

It defaults to `fixtures/bootstrap/inertial-3-rounds.json` and `fixtures/bootstrap/post-game-audit.json`. It exits `0` and prints `PASS: RQP bootstrap fixture verified` when the fixture is valid. It exits non-zero and prints a `FAIL:` diagnostic when any check diverges.

Run the one-action thrust fixture with:

```text
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/one-action-thrust.json fixtures/bootstrap/one-action-thrust-audit.json
```

Run the seven-round gravity fixtures with:

```text
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/gravity-7r-no-weapons.json fixtures/bootstrap/gravity-7r-no-weapons-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/gravity-7r-one-armed.json fixtures/bootstrap/gravity-7r-one-armed-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/gravity-7r-both-armed.json fixtures/bootstrap/gravity-7r-both-armed-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/gravity-7r-los-blocked.json fixtures/bootstrap/gravity-7r-los-blocked-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/gravity-4r-asteroid-collision.json fixtures/bootstrap/gravity-4r-asteroid-collision-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/gravity-4r-asteroid-velocity-collision.json fixtures/bootstrap/gravity-4r-asteroid-velocity-collision-audit.json
```

1. Load `inertial-3-rounds.json`.
2. Canonicalize each `genesis.initial_ledger_payloads[*].payload` and verify its SHA-256 equals `expected_hash`.
3. Canonicalize `genesis.world_state` and verify it equals `genesis.world_state_hash`.
4. For each round in ascending order:
   - Canonicalize each `ledger_payload` and verify it equals `expected_ledger_hash`.
   - Verify each `ledger_payload.previous_fuel_ledger_hash` equals the previous ledger hash for that agent.
   - Canonicalize each `commit_payload` and verify it equals `expected_commit_hash`.
   - Execute the round from the previous locked world state using the fixture ruleset. Inertial fixtures keep positions and HP unchanged; thrust fixtures update velocity/position; gravity fixtures apply constant `+r` drift; weapon fixtures apply line-of-sight damage.
   - Canonicalize the produced `world_state` and verify it equals `world_state_hash`.
   - Verify both `state_votes` reference the same `world_state_hash`.
   - Verify quorum uses `threshold = 2`, `votes_for_hash = 2`, `locked = true`, and `locked_hash = world_state_hash`.
5. Load `post-game-audit.json`.
6. Rebuild each agent's initial ledger hash and per-round ledger hashes from the disclosed salts and fuel burns.
7. Rebuild each round's commit hashes from the disclosed commit salts.
8. Replay all three world-state transitions and quorum locks.
9. Accept the fixture only if the audit report is `result: "pass"` and both agents have no violations.

## Expected Round Hashes

### Inertial fixture

| Round | World-state hash |
| --- | --- |
| Genesis | `6feaaa0dabfb86e478934491902eae204427ede07e4ca544af549f8cc1197ac9` |
| 1 | `93075adb802d1b1ee1e54e0941eee06b759af55346973d6c8f41ec3dca5b89cf` |
| 2 | `efa840edf800f42bd812ac98402bd0fc458b76d8665c1aaaab999c97f26f5bee` |
| 3 | `813d70a3f4fdcf8d3a7304a551a6f0a8e69c86c123184405a58d057cb798a3fc` |

### One-action thrust fixture

| Round | World-state hash |
| --- | --- |
| Genesis | `f34a8f74f716fb7d7e2c308ce104aa95e80d13a9b4cb34321fa976b5438024d9` |
| 1 | `d8cf52c59055e7d45232785b638d066ce4311cdb90afb193658f9d14fe94cfb1` |

### Seven-round gravity fixtures

| Fixture | Genesis hash | Round 7 hash | Final HP |
| --- | --- | --- | --- |
| No weapons | `56863fc34a35ba514a02e723a83e7a5028bb1b12d045e7b8568ddb0c97493802` | `89d2e97f9f47e6370b565286f5f400d5523ca1e9ee139a919d82bff62a267ab0` | `agent-a: 60`, `agent-b: 60` |
| One armed | `0cbbabbb6d3051bf9bd02b91705d28cb10045f6e27f7acde1d087e45514d8b61` | `636ccb378c6aed897bea7faedc8d460eaebb9ba41338552cb16c5061d7976aa0` | `agent-a: 60`, `agent-b: 0` |
| Both armed | `09a28e7d5e65a46f446f554a6275ab2c42e357e4a5439589b8f4e84c4dc69eda` | `ce7de6cec7b82c548583f5616b0ae7635bd01ce0f21c7c55ebdb416e99f1cd6b` | `agent-a: 0`, `agent-b: 0` |
| Blocked LOS | `61709ef9f091fe6f5049863ee46ded38f79a76b34a28a4441c130ba14f46b780` | `e1437d46d3e5b920e6ba938e7273a774a4c263ba1349c04c817b5839868afee7` | `agent-a: 10`, `agent-b: 10` |
| Asteroid collision | `43cee0bb3a9a81789c3987724f015faf8ad7409f4e4c5ebf6c324bd255eb8361` | `48f025c11e366d413becf85cdaec49fc7e26c998fa1916cedaaf8127873bc984` | `agent-a: 20`, `agent-b: 60` |
| Velocity asteroid collision | `cd884a5a48d8797930c0037f8bc1dd465f46db50d72ded6e336a8211e7b0e28c` | `7b493f6b8a2fedbadb0a87a7a819f77beca07db045bf7328a53af172f68fe5d1` | `agent-a: 20`, `agent-b: 60` |

## RFC Section 5 Coverage

`rfc5-fixture-index.json` maps every RFC section 5 heading to executable fixtures. Headings with meaningful variation have at least two fixture examples:

| RFC heading | Fixture coverage |
| --- | --- |
| 5.1 Numeric Model | integer fuel/HP/position/costs in inertial and thrust fixtures |
| 5.2 Coordinate System | unblocked and blocked same-row axial LOS fixtures |
| 5.3 Map and Condition Profiles | flat and velocity-based asteroid map definitions |
| 5.3.1 Seed-Derived Map Generation | two `explicit-materialized-v1` seed/profile map fixtures |
| 5.3.2 Parameter Overrides | flat and velocity-based collision override fixtures |
| 5.4 Object State | opaque LOS blocker objects and colliding asteroid objects |
| 5.5 Movement | inertial, active thrust, and constant-drift gravity fixtures |
| 5.6 Collision Resolution | flat and velocity-based stationary collision fixtures |
| 5.7 Bootstrap Line-of-Sight Weapons | unblocked and blocked LOS weapon fixtures |
