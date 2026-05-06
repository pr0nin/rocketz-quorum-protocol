# Rocketz Quorum Protocol

Rocketz Quorum Protocol (RQP) is a draft open protocol for decentralized, deterministic AI space combat. Agents run the same integer-only hex-grid simulation, commit to hidden actions and fuel usage, reveal actions, and lock each round by quorum over canonical world-state hashes.

This repository is currently the bootstrap specification and fixture suite for the first RQP client.

## Start here

1. Read `one-pager.md` for the product and gameplay idea.
2. Read `rfc.md` for the normative protocol draft.
3. Run the reference verifier:

```sh
python3 tools/rqp_verify_bootstrap.py
```

Expected output:

```text
PASS: RQP bootstrap fixture verified
```

That default command verifies `fixtures/bootstrap/inertial-3-rounds.json` against `fixtures/bootstrap/post-game-audit.json`.

## Verify every bootstrap fixture

Run the full checked-in fixture suite with:

```sh
for fixture in fixtures/bootstrap/*.json; do
  case "$fixture" in
    *-audit.json|*/post-game-audit.json|*/rfc5-fixture-index.json) continue ;;
  esac

  audit="${fixture%.json}-audit.json"
  if [ "$fixture" = "fixtures/bootstrap/inertial-3-rounds.json" ]; then
    audit="fixtures/bootstrap/post-game-audit.json"
  fi

  python3 tools/rqp_verify_bootstrap.py "$fixture" "$audit"
done
```

Every fixture/audit pair should print:

```text
PASS: RQP bootstrap fixture verified
```

## View fixture replays in a browser

Start a local static server from the repository root:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/visualizer/
```

The visualizer loads the checked-in bootstrap fixtures, validates each round's world-state hash in the browser, and supports manual previous/next/slider stepping plus automatic Play/Pause replay. It can also load replay JSON files or a fixture folder through the upload control.

The visualizer exposes `window.__rqpVisualRules.verifyObjectsContainedInHex()` for browser automation. It returns `{ ok, checked, failures }` and verifies that every rendered ship or map object stays within its assigned hex.

## Repository map

| Path | Purpose | Status |
| --- | --- | --- |
| `rfc.md` | Normative RQP 1.0 draft: deterministic simulation, canonicalization, quorum, audit, bootstrap requirements. | Primary spec |
| `fixtures/bootstrap/` | Machine-readable conformance fixtures and post-game audit disclosures. | Primary implementation target |
| `fixtures/bootstrap/README.md` | Fixture-by-fixture guide, expected hashes, and verifier commands. | Primary fixture documentation |
| `tools/rqp_verify_bootstrap.py` | Dependency-free Python reference verifier/engine harness. | Executable baseline |
| `visualizer/` | Static browser replay viewer for stepping through bootstrap fixtures visually. | Visual verification |
| `canonical-test-vectors.md` | Canonical JSON and SHA-256 examples for interoperability checks. | Support spec |
| `ruleset-default.md` | Early default ruleset profile for physics, costs, ships, weapons, and map generation. | Support profile |
| `transport-profile-websocket.md` | Practical non-authoritative WebSocket relay profile. | Support profile |
| `tournament-profile.md` | Tournament persistence, rewards, reputation, sanctions, and signatures. | Support profile |
| `one-pager.md` | Short concept explanation for developers and non-specialist readers. | Orientation |
| `working.rfc.md` | Non-normative working draft for future profile/spec material. | Design backlog |
| `rfc-deviations.md` | Decision log explaining how source drafts were reconciled into `rfc.md`. | Rationale |
| `chatter.md` | Design notes about advanced line-of-sight/infinite-range weapon reasoning. | Rationale |
| `Rocketz Quorum Protocol.md` | Original mixed-language source archive used to derive the refined docs. | Historical source |

## Fixture progression

The bootstrap fixtures intentionally progress from static replay to visual and ruleset variations:

1. `inertial-3-rounds.json` proves canonicalization, SHA-256 hashing, fuel-ledger chaining, commits, inertial execution, strict 2-of-2 quorum, and audit replay.
2. `one-action-thrust.json` proves the first active movement state transition.
3. `gravity-7r-*.json` fixtures prove constant-drift visual gravity, weapons, and line-of-sight blocking.
4. `gravity-4r-asteroid-*.json` fixtures prove flat and velocity-based collision profiles.
5. `firing-arc-*.json` fixtures prove facing, fixed forward arcs, 360-degree short-range weapons, and pass-by engagement windows.

`fixtures/bootstrap/rfc5-fixture-index.json` maps RFC section 5 simulation headings to executable fixture coverage.

## Building a new engine

A new engine should first pass the fixture verifier's behavior, not reimplement the full competitive protocol at once:

1. Implement `sorted-key-json-v1` canonicalization and SHA-256 hashing.
2. Load a fixture genesis state and verify its `world_state_hash`.
3. Replay fuel-ledger hashes and commit hashes for each round.
4. Execute the deterministic transition for the fixture profile.
5. Require strict 2-of-2 quorum over the produced state hash.
6. Replay the audit disclosure and fail on any mismatch.
7. Add fixtures one at a time until the full bootstrap suite passes.

The verifier intentionally fails loudly for unsupported profile combinations. Treat it as a narrow reference oracle for bootstrapping, not as a complete game engine.

## Current limits

RQP is still a draft. The bootstrap suite does not yet define a complete production ruleset, advanced weapon geometry, network dispute mode, tournament economics, zero-knowledge fuel proofs, or a visual client. Those topics are either in support profiles or listed as open questions in `rfc.md`.
