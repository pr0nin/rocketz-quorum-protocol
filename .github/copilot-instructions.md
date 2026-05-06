# Copilot instructions for Rocketz Quorum Protocol

This repository is a docs-first bootstrap specification and fixture suite for the first Rocketz Quorum Protocol (RQP) client. There is no package manifest, dependency manager, or general test framework yet; the executable baseline is the dependency-free Python verifier at `tools/rqp_verify_bootstrap.py`.

## Build, test, and lint commands

- Default bootstrap verifier:
  ```sh
  python3 tools/rqp_verify_bootstrap.py
  ```
- Run a single fixture/audit pair:
  ```sh
  python3 tools/rqp_verify_bootstrap.py fixtures/bootstrap/one-action-thrust.json fixtures/bootstrap/one-action-thrust-audit.json
  ```
- Run the full checked-in fixture suite and generated negative conformance checks:
  ```sh
  python3 tools/rqp_fixture_suite.py
  ```
- Run the fixture suite for a single fixture:
  ```sh
  python3 tools/rqp_fixture_suite.py fixtures/bootstrap/one-action-thrust.json
  ```
- Emit machine-readable fixture-suite output:
  ```sh
  python3 tools/rqp_fixture_suite.py --json
  ```
- Syntax/format checks used in this repo:
  ```sh
  python3 -m py_compile tools/rqp_verify_bootstrap.py tools/rqp_fixture_suite.py tools/rqp_bootstrap/*.py
  rm -rf tools/__pycache__ tools/rqp_bootstrap/__pycache__
  for f in fixtures/bootstrap/*.json; do python3 -m json.tool "$f" >/dev/null; done
  git --no-pager diff --check
  ```
- Validate `rfc5-fixture-index.json` references:
  ```sh
  python3 - <<'PY'
  import json
  from pathlib import Path
  root = Path("fixtures/bootstrap")
  index = json.loads((root / "rfc5-fixture-index.json").read_text())
  for section in index["sections"]:
      for fixture in section["fixtures"]:
          if not (root / fixture).exists():
              raise SystemExit(f"missing indexed fixture: {fixture}")
  print("rfc5 index valid")
  PY
  ```
- Serve the static browser visualizer:
  ```sh
  python3 -m http.server 8765 --bind 127.0.0.1
  ```
  Then open `http://127.0.0.1:8765/visualizer/`.
  The visualizer exposes `window.__rqpVisualRules.verifyObjectsContainedInHex()` so Playwright can assert all rendered ships/map objects fit inside their current hex.
- Run the visualizer browser harness:
  ```sh
  # Requires Node.js 18 or newer.
  npm ci
  npx playwright install chromium
  npm run test:visualizer
  ```
  This serves `/visualizer/`, loads every bundled fixture, sweeps all rounds, verifies `Hash OK`, checks containment, and exercises stepping/autoplay plus representative labels.

## High-level architecture

- `rfc.md` is the normative RQP 1.0 draft. It defines deterministic integer simulation, axial hex coordinates, map/condition profiles, movement, collision, bootstrap LOS weapons, canonical serialization, quorum, and audit.
- `fixtures/bootstrap/` is the implementation target. Each non-audit fixture contains genesis data, round inputs, expected ledger/commit/world-state hashes, votes, and quorum locks. Matching `*-audit.json` files disclose salts and final audit expectations. The inertial fixture uniquely pairs with `post-game-audit.json`.
- `tools/rqp_verify_bootstrap.py` is the backwards-compatible verifier CLI for one fixture/audit pair. Reusable implementation modules live under `tools/rqp_bootstrap/`, and `tools/rqp_fixture_suite.py` discovers fixture/audit pairs, runs the full suite, emits JSON output, and performs generated negative conformance checks.
- `visualizer/` is a static browser replay/debug studio. It loads bundled fixtures from `fixtures/bootstrap/`, supports replay JSON/folder uploads with optional audit sidecars, validates each displayed world-state hash in-browser, and supports previous/next/slider/timeline/manual stepping, reset, speed control, keyboard shortcuts, diff/debug panels, and Play/Pause automatic replay.
- `fixtures/bootstrap/README.md` explains fixture intent and expected hashes. `fixtures/bootstrap/rfc5-fixture-index.json` maps RFC section 5 deterministic simulation headings to executable fixture coverage.
- `README.md` is the developer entry point. `one-pager.md` is orientation. `canonical-test-vectors.md`, `ruleset-default.md`, `transport-profile-websocket.md`, and `tournament-profile.md` are support profiles/specs. `working.rfc.md`, `rfc-deviations.md`, `chatter.md`, and `Rocketz Quorum Protocol.md` are design rationale/source-history documents, not normative implementation targets.

## Key conventions

- Preserve `rqp/1.0-draft.1`, `sorted-key-json-v1`, and `sha-256` unless deliberately updating the protocol and every affected fixture/hash.
- Canonical JSON is `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`, hashed with SHA-256 hex.
- Canonical simulation uses integer math only. Do not introduce floating-point calculations into fixture-affecting protocol logic.
- Axial coordinates use `{ "q": int, "r": int }`; velocity/facing vectors use `{ "dq": int, "dr": int }`. Forward arc fixtures require facing to be one of the six axial unit directions.
- Fixture changes must update all derived hashes, the matching audit disclosure, `fixtures/bootstrap/README.md`, and `fixtures/bootstrap/rfc5-fixture-index.json` when coverage changes.
- Keep the verifier dependency-free and narrow. Unsupported protocol/ruleset combinations should fail explicitly via `VerificationError`/`FAIL:` diagnostics rather than silently falling back.
- Bootstrap fixtures currently support strict `2-of-2` quorum, unsigned local replay, `gravity_mode` values `none` and `constant_drift`, action levels 0/1, simple LOS weapons, stationary collision profiles, and post-game audit replay.
- For velocity-based stationary collisions, speed is based on the actual per-round position delta after action acceleration and gravity/drift, not only stored velocity.
- Out-of-range or out-of-arc weapon reveals are valid spent actions in bootstrap fixtures; they deal no damage and allow visualizers to show misses.
- After `py_compile`, remove `tools/__pycache__` before finishing.
- After Playwright runs, do not commit `test-results/`; it is ignored as a generated test artifact.
