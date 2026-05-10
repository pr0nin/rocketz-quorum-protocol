# RQP Tournament Profile

**Status:** Draft profile  
**Applies to:** `rqp/1.0-draft.1`
**Purpose:** Define persistence, reputation, rewards, and sanctions for organized RQP play.

## 1. Goals

Tournament mode should:

1. Reward audited performance.
2. Preserve competitive integrity.
3. Avoid runaway snowballing.
4. Penalize protocol abuse.
5. Produce clear public audit records.

## 2. Required Features

Tournament matches MUST use:

1. Signed messages.
2. Public match IDs.
3. Append-only event logs.
4. Post-match audit reports.
5. Deterministic sanctions.
6. Explicit persistence rules.

## 3. Quorum

Default tournament quorum:

```text
ceil(active_validators * 2 / 3)
```

For two-agent matches, use validator-assisted quorum:

```text
agent A + agent B + neutral validator = 2 of 3 required
```

The neutral validator must run the same simulation and publish state votes.

## 4. Persistence

Tournament profiles may persist:

1. Remaining fuel bonus.
2. Captured fuel bonus.
3. Denied fuel bonus.
4. Reputation score.
5. Loadout unlocks.
6. Ranking points.

Recommended formulas:

```text
carried_fuel = min(remaining_fuel, CARRY_FUEL_CAP)
captured_bonus = floor(opponent_destroyed_fuel * CAPTURE_RATE_NUM / CAPTURE_RATE_DEN)
metabolic_capital = floor((carried_fuel + captured_bonus) / 2)
```

Defaults:

| Parameter | Value |
| --- | --- |
| Carry fuel cap | `250` |
| Capture rate | `1/4` |
| Maximum loadout tier gain per match | `1` |

## 5. Anti-Snowball Rules

1. Carry fuel is capped.
2. Excess fuel converts to ranking points, not combat power.
3. Failed audits void all rewards.
4. Bracket stages may reset loadout tiers.
5. Matchmaking should consider persistent advantage.

## 6. Reputation

Recommended reputation events:

| Event | Reputation change |
| --- | --- |
| Clean audit | `+1` |
| Match win with clean audit | `+2` |
| Missing commit | `-1` |
| Missing reveal | `-3` |
| Three missing reveals | `-10` |
| Invalid reveal | `-15` |
| Fuel overspend | `-25` |
| Energy Flux mismatch | `-25` |
| Pre-lock violation | `-25` |
| Conflicting state vote | `-25` |

## 7. Sanctions

| Violation | Default sanction |
| --- | --- |
| Commit mismatch | Round action invalidated |
| Fuel overspend | Match disqualification |
| Ledger mismatch | Match disqualification |
| Energy Flux mismatch | Match disqualification or result reversal |
| Simulated Deck entropy violation | Match disqualification and evidence review |
| Thermal Debt mismatch | Match disqualification if it changes damage, elimination, or rewards |
| Signal Flare pre-lock violation | Round action invalidated and disqualification eligible |
| Conflicting state vote | Match disqualification and reputation penalty |
| Serialization violation | Client quarantine until fixed |
| Repeated missing reveals | Disqualification eligible |

## 8. Audit Report

Tournament audit reports should use:

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
      "reputation_delta": 3,
      "rewards": {
        "carried_fuel": 120,
        "metabolic_capital": 75,
        "ranking_points": 10
      }
    }
  ]
}
```

## 9. Broadcast

Tournament broadcasts should use:

1. Public live mode during active rounds.
2. Match-end god-view replay after audit.
3. Commentary overlays generated from audit data.

If a match enables Signal Flares, the broadcast profile should define:

1. Canonical `bright` or `flaring` status and publicly revealed future nonces that are exposed at the same time they become available to competitors.
2. Hidden actions, hidden fuel details, and Energy Flux decompositions that remain withheld until their normal reveal or audit disclosure.
3. Any delayed god-view exception that reveals additional hidden data to spectators after a tournament-defined delay.

## 10. Blacklisting

An agent may be blacklisted when:

1. It fails audit for severe fraud.
2. It signs conflicting canonical messages.
3. It repeatedly griefs reveal phases.
4. It uses an implementation known to produce invalid canonical serialization.

Blacklists should include evidence hashes and an appeal or revalidation process.
