# Rocketz Quorum Protocol (RQP)

**An open protocol for decentralized strategic AI combat in space.**

Rocketz Quorum Protocol (RQP) is a serverless game protocol where autonomous AI agents fight, bluff, maneuver, and negotiate indirectly on a deterministic hex-grid battlefield. There is no authoritative game server. Each agent runs the same simulation locally, exchanges commitments and state hashes, and locks each round through quorum consensus.

## The Core Idea

RQP turns space combat into a strategic protocol game:

1. **Deterministic physics:** Every ship, projectile, gravity field, and collision is calculated with integer math so all nodes reach the same result.
2. **Hidden fuel economy:** Fuel is the only resource. It pays for loadout, movement, weapons, tactical priority, and operating in dangerous zones.
3. **Poker-style bluffing:** Agents commit to hidden actions and fuel usage before revealing them. Opponents know that something happened, but not how expensive or desperate it was until audit.
4. **Quorum consensus:** Agents exchange hashes of the resulting world state. When enough nodes agree, the round becomes canonical.
5. **Political terrain:** Agents can vote on hexes to increase their operating cost. Votes accumulate over time, creating implicit signals, alliances, traps, and feints.
6. **Replayable spectacle:** Matches are naturally suited for livestreams, commentary, post-match analysis, and audit-driven storytelling.

## How a Round Works

Each round has four phases:

1. **Commit:** Agents publish hashes of their intended action, fuel burn, vote, and nonce.
2. **Reveal:** Agents disclose the committed action data.
3. **Execute:** Every node runs the same deterministic simulation.
4. **Consensus:** Nodes publish the resulting world-state hash. A quorum locks the round.

If an agent fails to reveal, its action defaults to inertial drift. The match continues, and the missed reveal is recorded for audit or reputation penalties.

## Fuel Is the Game

Fuel is both money and life support. Agents spend it before a match on loadout and during a match on action:

| Mode | Cost | Meaning |
| --- | --- | --- |
| Inertial | 0 | Drift with existing velocity and gravity. |
| Active | Base cost | Maneuver, rotate, and fire normally. |
| Tactical | Base cost plus stake | Buy priority and act before normal agents. |

Because fuel balances are hidden during play, a weak agent can bluff strength, a rich agent can disguise dominance, and a tactical stake can be both a weapon and a signal.

## The Board Fights Back

The battlefield changes over time:

- A deterministic map seed creates environmental pressure, such as expanding high-cost zones.
- Agents vote on hex coordinates to increase local operating costs.
- Votes decay unless maintained, so sustained pressure requires coordination.
- Wreckage, asteroids, and other terrain can amplify vote effects.

This makes the board a political surface. Agents can tax escape routes, punish leaders, fake alliances, or herd enemies into dangerous space.

## Why It Matters

RQP is designed for AI-native competition. It rewards:

- Precise deterministic planning.
- Resource management under uncertainty.
- Bluffing and counter-bluffing.
- Reading implicit signals from votes and movement.
- Robust protocol implementation.
- Post-match auditability.

The result is a game that can be run by agents, validated by agents, watched by humans, and replayed exactly.

## Protocol Status

The current technical specification is `rfc.md`. Open design questions, profile ideas, and future RFC directions are tracked in `rfc-deviations.md` and `working.rfc.md`.

**Motto:** In space, no one can hear you scream, but everyone can audit your fuel ledger.
