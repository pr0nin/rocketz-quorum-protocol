# Bootstrap Replay Visualizer

A static browser replay studio for stepping through RQP bootstrap fixtures visually.

![Visualizer — genesis round of the inertial fixture, showing two ships on a hex grid with Hash OK validation](https://github.com/user-attachments/assets/458544a5-87c2-4692-b90c-bd074b25ac0c)

![Visualizer — round 3 of the playable default campaign, showing a breach-rail hit for 35 damage and depleted HP/fuel bars](https://github.com/user-attachments/assets/46e3a706-f831-4367-a4a2-c31d9875164d)

## Running

Start a local static server from the repository root:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/visualizer/
```

## Features

- **Fixture picker** — choose any bundled bootstrap fixture from the dropdown, or load a custom replay JSON or fixture folder via the upload buttons.
- **Round stepping** — use Previous / Next buttons, the round slider, or round-number markers to jump to any round. Keyboard shortcuts: `←`/`→` step, `Space`/`K` play/pause, `R` reset to genesis.
- **Play/Pause autoplay** — automatic round-by-round replay with configurable speed (0.5×, 1×, 2×, 4×).
- **Hash validation** — each displayed world state is validated in-browser against the fixture's expected SHA-256 hash. A green **Hash OK** label confirms the simulation is consistent.
- **Agent panel** — live position, velocity, facing vector, HP bar, and fuel bar for every agent.
- **Weapon declarations** — per-round weapon outcomes (hit / miss / out-of-arc / out-of-range), including damage dealt and collision annotations.
- **Round diff** — per-round delta display for position, velocity, HP, and fuel so you can see exactly what changed each round.
- **Audit sidecar** — load a matching `*-audit.json` alongside a fixture to display salt disclosures and post-game audit state.
- **Raw world-state inspection** — expandable panel with the full canonical JSON for the current round.
- **Copyable hashes** — click any displayed hash to copy it to the clipboard.
- **Hex containment check** — `window.__rqpVisualRules.verifyObjectsContainedInHex()` is exposed for browser automation; returns `{ ok, checked, failures }`.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Entry point and layout |
| `app.js` | Replay engine, rendering, UI logic |
| `styles.css` | Dark-theme stylesheet |

## Browser smoke test

The Playwright harness in `tests/visualizer-smoke.spec.js` loads every bundled fixture, sweeps all rounds, verifies `Hash OK`, calls `verifyObjectsContainedInHex()`, and exercises stepping, autoplay, and representative labels. Run it from the repository root:

```sh
npm ci
npx playwright install chromium
npm run test:visualizer
```
