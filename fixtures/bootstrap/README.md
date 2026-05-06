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
17. `firing-arc-both-away.json` - one round where both ships start 10 hexes apart, face away, and both weapons miss.
18. `firing-arc-both-away-audit.json` - post-game disclosure and expected audit result for the both-away arc fixture.
19. `firing-arc-agent-a-forward.json` - one round where only `agent-a` faces the target, so only `agent-a`'s fixed railgun hits.
20. `firing-arc-agent-a-forward-audit.json` - post-game disclosure and expected audit result for the one-forward arc fixture.
21. `firing-arc-both-forward.json` - one round where both ships face each other, so both fixed railguns hit.
22. `firing-arc-both-forward-audit.json` - post-game disclosure and expected audit result for the both-forward arc fixture.
23. `firing-arc-pass-by-7r.json` - seven rounds where two ships race past each other, railguns hit from the front, then only 360-degree mazers hit during side/backward pass windows.
24. `firing-arc-pass-by-7r-audit.json` - post-game disclosure and expected audit result for the pass-by arc fixture.
25. `playable-default-campaign.json` - five-round playable default-profile campaign with asymmetric loadouts, rotation plus thrust, blocked and unblocked weapons, collision aftermath, elimination, and missing reveal fallback.
26. `playable-default-campaign-audit.json` - post-game disclosure, missing-reveal diagnostic, and expected audit result for the playable campaign.
27. `playable-quorum-failure.json` - one-round strict `2-of-2` quorum diagnostic fixture where only one state vote is available, so the tentative state does not lock.
28. `playable-quorum-failure-audit.json` - post-game disclosure and expected audit/dispute diagnostics for the quorum failure fixture.
29. `rfc5-fixture-index.json` - machine-readable index mapping RFC section 5 headings to executable fixtures.

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

The firing arc fixtures add facing and two equipped weapons:

1. `agent-a` starts at `(0, 0)`, `agent-b` starts at `(10, 0)`.
2. Both ships equip `micro-micro-mazer` and `fixed-railgun`.
3. `micro-micro-mazer` has range `3`, damage `5`, and arc `360`; it is always out of range at distance `10`.
4. `fixed-railgun` has range `10`, damage `20`, and arc `forward`; it only hits when the target lies exactly along the attacker's facing vector.
5. In `firing-arc-both-away`, `agent-a` faces `(-1, 0)` and `agent-b` faces `(1, 0)`, so both railguns miss.
6. In `firing-arc-agent-a-forward`, `agent-a` faces `(1, 0)` and hits `agent-b`; `agent-b` still faces away.
7. In `firing-arc-both-forward`, both ships face each other and both railguns hit.

The pass-by firing arc fixture extends this into a 7-round visual sequence:

1. `agent-a` starts at `(0, 0)` facing `(1, 0)` with velocity `(1, 0)`.
2. `agent-b` starts at `(10, 0)` facing `(-1, 0)` with velocity `(-1, 0)`.
3. Rounds 1-3 are front-facing approach shots: fixed railguns hit and micro-micro mazers are out of range.
4. Round 4 offsets the pass; fixed arcs cannot hit.
5. Round 5 is a side close pass at distance `2`; only the 360-degree micro-micro mazers hit.
6. Round 6 is a behind close pass at distance `2`; fixed railguns still miss and only the 360-degree mazers hit.
7. Round 7 separates the ships again; no weapon hits.

The playable default campaign fixture is the first coherent mini-match for `rqp-default-playable-v0`:

1. `agent-a` uses a `striker-v1` with `training-laser` and `breach-rail`; `agent-b` uses a `guardian-v1` with `training-laser`.
2. Round 1 rotates `agent-a` from `(1, -1)` to `(1, 0)` and thrusts down the lane.
3. Round 2 has both lasers blocked by `screen-asteroid`.
4. Round 3 records `agent-b` as a missing reveal and applies the inertial fallback while `agent-a` lands an unblocked `breach-rail` shot.
5. Round 4 moves `agent-a` into `recovery-wreck`, applies velocity-based collision damage, then resolves simultaneous weapon damage; `agent-b` is eliminated.
6. Round 5 spends recovery thrust to arrest `agent-a`'s velocity after the collision aftermath.

The quorum failure fixture is a diagnostic-only local replay:

1. Both agents submit inertial inputs.
2. Only `agent-a` publishes a state vote.
3. Strict `2-of-2` quorum does not lock (`locked = false`, `locked_hash = null`).
4. `quorum_diagnostics` records `available_votes = 1`, `required_votes = 2`, and `decision = round_not_locked`.

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
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/firing-arc-both-away.json fixtures/bootstrap/firing-arc-both-away-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/firing-arc-agent-a-forward.json fixtures/bootstrap/firing-arc-agent-a-forward-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/firing-arc-both-forward.json fixtures/bootstrap/firing-arc-both-forward-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/firing-arc-pass-by-7r.json fixtures/bootstrap/firing-arc-pass-by-7r-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/playable-default-campaign.json fixtures/bootstrap/playable-default-campaign-audit.json
python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/playable-quorum-failure.json fixtures/bootstrap/playable-quorum-failure-audit.json
```

1. Load `inertial-3-rounds.json`.
2. Canonicalize each `genesis.initial_ledger_payloads[*].payload` and verify its SHA-256 equals `expected_hash`.
3. Canonicalize `genesis.world_state` and verify it equals `genesis.world_state_hash`.
4. For each round in ascending order:
   - Canonicalize each `ledger_payload` and verify it equals `expected_ledger_hash`.
   - Verify each `ledger_payload.previous_fuel_ledger_hash` equals the previous ledger hash for that agent.
   - Canonicalize each `commit_payload` and verify it equals `expected_commit_hash`.
   - Execute the round from the previous locked world state using the fixture ruleset. Inertial fixtures keep positions and HP unchanged; thrust fixtures update velocity/position; rotation fixtures update facing; gravity fixtures apply constant `+r` drift; weapon fixtures apply line-of-sight damage; playable fixtures can add missing-reveal audit flags.
   - Canonicalize the produced `world_state` and verify it equals `world_state_hash`.
   - Verify every present `state_vote` references the same `world_state_hash`.
   - Verify quorum uses `threshold = 2`; locked rounds require both votes and `locked_hash = world_state_hash`, while the quorum failure diagnostic requires too few votes and `locked_hash = null`.
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

### Firing arc fixtures

| Fixture | Genesis hash | Round 1 hash | Final HP |
| --- | --- | --- | --- |
| Both away | `b9f63cc1b7cc6e5629caca6daad8ab613e6d3d660a8971c3af2515971937594b` | `fcc111743e29a3937ddfcdf321a2cc8b67c27377a9b5be7d3f99651a02f589ba` | `agent-a: 60`, `agent-b: 60` |
| Agent A forward | `cad1601950daa802c6ca482e74a9d56687f8d5159b30e1e499113ebcc7be30d4` | `16d3402c0d1240c24f719724424c02ab2e97be81559107f0618beb1f93399d5b` | `agent-a: 60`, `agent-b: 40` |
| Both forward | `690563ad1895e0e1c45e2eeb17dc085da20904aa744905143bc04f5b524c26e9` | `f8f8610edc91e2f67048a562bbb097e88bc813fefa10af9138bcb77d6da55c9e` | `agent-a: 40`, `agent-b: 40` |
| Pass-by race | `df0ebd4d00e7625b44455ab967e3495b5ab758509ecfa64de74edd0a8fecb986` | `b3b178e4b21337e853d9cb748ba616977673cdfec9ff39ab26e99f346c880cf4` | `agent-a: 20`, `agent-b: 20` |

### Playable default profile fixtures

| Fixture | Genesis hash | Final/tentative round hash | Lock result | Final locked HP |
| --- | --- | --- | --- | --- |
| Playable campaign | `9287e860a81c6f0215c848255f9b672123b673859dc5120139f2ece4a9d03d3a` | `77428eb8d6bc2ece011138a971e9989d0fa12f66ae7982ab4d1a76c4f67f76ea` | locked round 5 | `agent-a: 35`, `agent-b: 0` |
| Quorum failure diagnostic | `66665526861997ac254edffe67e1e01d84f7df20ab6b1a010cb0857237c10c4b` | `3be20d019d251188739c08d88ec4459ff94b594eb2692b512abdffe17abfd874` | unlocked round 1 | `agent-a: 100`, `agent-b: 100` |

## RFC Section 5 Coverage

`rfc5-fixture-index.json` maps every RFC section 5 heading to executable fixtures. Headings with meaningful variation have at least two fixture examples:

| RFC heading | Fixture coverage |
| --- | --- |
| 5.1 Numeric Model | integer fuel/HP/position/costs in inertial and thrust fixtures |
| 5.2 Coordinate System | unblocked and blocked same-row axial LOS fixtures |
| 5.3 Map and Condition Profiles | flat and velocity-based asteroid map definitions |
| 5.3.1 Seed-Derived Map Generation | two `explicit-materialized-v1` seed/profile map fixtures |
| 5.3.2 Parameter Overrides | flat and velocity-based collision override fixtures |
| 5.4 Object State | opaque LOS blocker objects, colliding asteroid objects, ship facing, and playable ship/loadout state |
| 5.5 Movement | inertial, active thrust, constant-drift gravity, and playable rotation/recovery thrust fixtures |
| 5.6 Collision Resolution | flat, velocity-based stationary collision, and playable collision-aftermath fixtures |
| 5.7 Bootstrap Line-of-Sight Weapons | unblocked LOS, blocked LOS, out-of-range 360, fixed forward arc, and playable fixed-damage weapon fixtures |
