# RQP RFC Deviations, Rationale, and Suggestions

This document compares the split versions in `Rocketz Quorum Protocol.md` and explains how `rfc.md` resolves their differences. It is intended as a companion decision log, not a replacement for the RFC.

## Source Variants

| Variant | Location in source | Character | Main value |
| --- | --- | --- | --- |
| One-pager | Lines 1-29 | Pitch / concept summary | Communicates the core fantasy quickly: decentralized AI combat, poker-fuel bluffing, political voting, livestream value. |
| RFC v1 sketch | Lines 33-81 | Compact technical outline | Gives a clean first structure: physics, fuel ledger, dynamic environment, quorum phases, audit, implementation notes. |
| "Rfc pro" draft | Lines 83-188 | Formal spec attempt | Adds terminology, concrete phase messages, default voting parameters, audit sanctions, and tournament persistence. |

## Key Deviations and Resolutions

### 1. Document purpose: pitch vs implementable standard

**Deviation:** The one-pager is written for sharing and persuasion, while the later drafts aim to be implementation-facing RFCs.

**Value of one-pager:** It captures the unique identity of RQP better than the technical drafts. It explains why the protocol is interesting: AI agents bluff, spend hidden fuel, shape the board politically, and create a spectator-friendly strategy game.

**Value of RFC drafts:** They are closer to what implementers need: deterministic physics, message phases, fuel hashes, quorum, and audit.

**Resolution in `rfc.md`:** The refined RFC uses the technical structure from the RFC drafts but preserves the one-pager's concepts as formal goals: hidden information, implicit cooperation, tournament persistence, and spectator/replay support.

**Suggestion:** Keep `rfc.md` as the normative document and create a separate short `one-pager.md` later for investors, players, streamers, or community onboarding.

### 2. Language and audience

**Deviation:** The source is mostly Norwegian, while the refined RFC is in English.

**Value of Norwegian source:** It is expressive and clear for the original design context. Terms like "bløffing", "skattelegging", and "implisitt kommunikasjon" carry strong design intent.

**Value of English RFC:** English is more suitable for an open technical standard and wider implementation by developers.

**Resolution in `rfc.md`:** English is used for standardization, but the concepts are preserved as "bluffing", "environmental pressure", "accumulated voting", and "implicit political coordination".

**Suggestion:** If the project is public, use English for protocol specs and optionally maintain Norwegian design notes separately.

### 3. Serverless architecture vs message hub

**Deviation:** The drafts say RQP is serverless but also mention a simple Pub/Sub hub, WebSockets, or libp2p.

**Potential conflict:** A hub can look like a server, which may weaken the "serverless" claim.

**Resolution in `rfc.md`:** The RFC distinguishes between an authoritative game server and a non-authoritative transport hub. The hub may relay messages but must not decide state.

**Value of this resolution:** It keeps the protocol practical. A relay can simplify implementation without compromising decentralized validation.

**Suggestion:** Future RFCs should define recommended transport profiles:

1. Local/offline replay profile.
2. WebSocket hub profile.
3. libp2p peer-to-peer profile.
4. Tournament relay profile with signatures and redundancy.

### 4. Deterministic physics detail

**Deviation:** The compact RFC says axial hex grid, fixed-point math, gravity, and collision priority. The "Rfc pro" draft adds 64-bit integers and movement formulas, but leaves the distance formula blank.

**Resolution in `rfc.md`:** The refined RFC fills the gap with axial-to-cube distance, explicit integer-only math, object state shape, movement update equations, and deterministic collision ordering.

**Value of source versions:** The compact version gives the right conceptual model. The formal version correctly identifies that no floats should be allowed.

**Suggestion:** The next spec pass should define:

1. Exact gravity seed function.
2. Exact line/path traversal across hexes for high velocity.
3. Collision behavior for simultaneous multi-object collisions.
4. Whether positions are always integer hexes or can use fixed-point sub-hex coordinates.

### 5. Tactical action priority

**Deviation:** The source says Tactical actions happen before others, but does not fully define ties or ordering between multiple Tactical agents.

**Resolution in `rfc.md`:** Tactical priority is ordered by higher stake first, then canonical agent ID. Active actions default to canonical agent ID order.

**Value of this addition:** Consensus requires deterministic tie-breaking. Without it, different nodes could resolve the same round differently.

**Suggestion:** Decide whether tactical stake should be fully revealed during the reveal phase or whether advanced cryptographic techniques should preserve partial stake secrecy until audit. The current RFC reveals it because execution priority requires shared knowledge.

### 6. Fuel ledger hash contents

**Deviation:** The compact draft defines `H_n = SHA256(Fuel_igjen + H_{n-1} + Salt_n)`. The formal draft says a new hash is calculated but leaves the formula blank.

**Issue:** Hashing only remaining fuel may not fully bind the action's claimed burn, round number, or agent identity.

**Resolution in `rfc.md`:** The ledger hash includes agent ID, round, remaining fuel, fuel burn, previous ledger hash, and salt.

**Value of this resolution:** It reduces ambiguity and prevents replay or cross-agent hash confusion.

**Suggestion:** Future versions could add zero-knowledge proofs so agents can prove non-negative balances without disclosing exact post-match fuel history, but that is beyond the current protocol.

### 7. Commit-reveal privacy claim

**Deviation:** The one-pager says a livestream client can decrypt all data in real time and show the "god perspective", while the protocol sections say fuel remains hidden until reveal/audit.

**Potential conflict:** If spectators can see hidden fuel in real time, then strategic secrecy is weakened unless spectators are trusted or delayed.

**Resolution in `rfc.md`:** Spectator support is formalized as replayable public data. Hidden fuel remains unavailable during canonical live play. Trusted broadcast overlays are allowed but explicitly outside the canonical protocol.

**Value of one-pager idea:** A god-view stream could be excellent entertainment if delayed, permissioned, or separated from competing agents.

**Suggestion:** Define two broadcast modes later:

1. Competitive live mode: spectators see only public data.
2. Delayed god-view mode: stream reveals hidden fuel after a delay or after match completion.

### 8. Voting, politics, and environmental control

**Deviation:** The one-pager emphasizes implicit communication and alliances. The later drafts define voting more mechanically with thresholds, persistence, decay, and environmental multipliers.

**Resolution in `rfc.md`:** Both are preserved. Voting is specified as a deterministic cost-map mechanic while its strategic purpose is described as implicit political coordination.

**Value of the one-pager:** It frames voting as more than terrain manipulation. It is also a signaling layer.

**Value of the formal draft:** It provides useful defaults: threshold 100, decay 5, cost increment +1, and environmental multipliers.

**Suggestion:** Add a future "signaling analysis" or game-design document describing known strategies:

1. Coordinated taxation of escape routes.
2. Feint votes to imply false alliances.
3. Long-term pressure around resource-rich or low-gravity zones.
4. Punishment votes against leading agents.

### 9. Hex-potential threshold comparison

**Deviation:** The formal draft uses `Hex_Potential > 100`, while a threshold system is generally clearer as `>= threshold`.

**Resolution in `rfc.md`:** The RFC uses `>= HEX_THRESHOLD`.

**Value of this change:** It avoids off-by-one ambiguity. If the threshold is 100, exactly 100 should trigger unless there is a strong design reason otherwise.

**Suggestion:** If designers want "over 100" specifically, rename the threshold to a boundary and define the exact trigger as part of balance rules.

### 10. Environmental multiplier and integer math

**Deviation:** The formal draft mentions a `1.5x` multiplier while also requiring integer-only physics.

**Potential conflict:** Fractional multipliers can reintroduce floating-point ambiguity if not encoded carefully.

**Resolution in `rfc.md`:** Fractional multipliers are allowed only as fixed-point values.

**Value of this resolution:** Designers keep expressive balance tools while implementers preserve deterministic consensus.

**Suggestion:** Define all fractional balance constants as rational pairs or fixed-point integers, for example `multiplier_num = 3`, `multiplier_den = 2`.

### 11. Quorum threshold

**Deviation:** The source only says a threshold or `>= 66%` quorum. It does not specify rounding or active-agent handling.

**Resolution in `rfc.md`:** Default quorum is `ceil(active_agents * 2 / 3)`, and active agents exclude eliminated or disqualified agents.

**Value of this addition:** It makes small matches and eliminations deterministic.

**Suggestion:** Future rulesets should define exact quorum behavior for two-agent matches. A strict two-thirds quorum with two agents requires both agents, which may be too fragile if one disconnects.

### 12. Missing reveal behavior

**Deviation:** The formal draft says missing reveals become Level 0 Inertial. Earlier sections imply all agents reveal after commit but do not say what happens if they do not.

**Resolution in `rfc.md`:** Missing commits and missing reveals both default to Inertial, but missing reveals are recorded for audit/reputation.

**Value of this resolution:** The match can continue without giving non-revealing agents arbitrary power.

**Suggestion:** Tournament mode should penalize repeated missing reveals more strongly than missing commits, because commit-withholding can be used as griefing or timing manipulation.

### 13. Audit and slashing

**Deviation:** The drafts mention blacklisting, reputation, result reversal, and tournament persistence but do not define a full violation set.

**Resolution in `rfc.md`:** The RFC lists concrete violations and possible sanctions, while leaving exact sanction severity to the ruleset.

**Value of source versions:** They correctly identify audit as essential because hidden fuel is central to bluffing.

**Suggestion:** Add a machine-readable audit report format in a future RFC. It should include violation type, round, evidence hashes, and recommended sanction.

### 14. Tournament persistence

**Deviation:** One version says remaining fuel or "metabolic capital" carries forward. Another says remaining fuel plus a percentage of enemy lost fuel goes to a wallet/profile.

**Resolution in `rfc.md`:** Tournament persistence is optional and may include remaining fuel, captured/destroyed/denied opponent fuel, reputation, unlocks, and ranking points.

**Value of each source idea:** Remaining fuel rewards conservation. Enemy fuel capture rewards aggression. Metabolic capital can smooth progression and avoid runaway snowballing.

**Suggestion:** Keep persistence outside the base protocol until the core match protocol is stable. Tournament persistence can strongly affect incentives and should be balanced separately.

### 15. Encoding and canonical serialization

**Deviation:** The compact RFC says JSON or Protocol Buffers. The source does not define canonical serialization.

**Issue:** Without canonical serialization, the same semantic state can hash differently across nodes.

**Resolution in `rfc.md`:** Canonical UTF-8 JSON is the default, with sorted keys and no insignificant whitespace. Alternative encodings are allowed only if agreed in genesis.

**Value of this addition:** This is one of the most important implementation requirements for consensus.

**Suggestion:** Create a small canonical test vector suite before implementation:

1. Genesis state hash vector.
2. Commit payload hash vector.
3. Fuel ledger hash vector.
4. World state hash vector after one simple round.

### 16. Identity and signatures

**Deviation:** The source mentions cryptographic reputation IDs but does not define signed messages.

**Resolution in `rfc.md`:** Stable cryptographic identity and signatures are recommended, not mandatory.

**Value of this resolution:** It keeps the base RFC implementable while acknowledging that real tournaments need authenticated messages.

**Suggestion:** Make signatures mandatory in any public network or tournament profile. Unsigned mode should be limited to local simulation and development.

### 17. "God perspective" and audit timing

**Deviation:** The one-pager's livestream section suggests a real-time god perspective, but the audit model reveals hidden fuel after match end.

**Resolution in `rfc.md`:** The canonical protocol favors competitive secrecy. God-view is treated as a non-canonical broadcast mode.

**Value comparison:** Competitive secrecy creates better agent strategy. God-view creates better spectator drama.

**Suggestion:** Use delayed disclosure for broadcasts: stream the public match live, then reveal hidden fuel and political intent during replay analysis.

## Decisions Made in `rfc.md`

| Decision | Reason |
| --- | --- |
| English RFC | Better fit for open implementation. |
| Added Goals and Non-Goals | Separates protocol scope from game/product ambitions. |
| Added canonical serialization | Required for state hash consensus. |
| Filled hex distance formula | The source left it incomplete. |
| Added deterministic tie-breakers | Required for tactical priority and collision consistency. |
| Expanded fuel ledger hash | Binds round, agent, burn, previous hash, and salt. |
| Preserved voting defaults | The formal draft had useful concrete values. |
| Made spectator god-view non-canonical | Avoids conflict with hidden fuel/bluffing. |
| Made tournament persistence optional | It is valuable but balance-sensitive. |
| Added security considerations | Commit-reveal protocols have predictable attack surfaces. |

## Suggested Future Files

1. `one-pager.md` - a polished short concept pitch based on the first source section.
2. `ruleset-default.md` - concrete default balance values for ships, weapons, fuel costs, gravity, and map generation.
3. `canonical-test-vectors.md` - hash examples for interoperability.
4. `transport-profile-websocket.md` - practical message relay profile.
5. `tournament-profile.md` - persistence, reputation, rewards, and sanctions.

## Summary

The source versions are complementary rather than contradictory. The one-pager gives RQP its identity and audience appeal. The compact RFC gives the core mechanic structure. The formal draft contributes useful implementation details and defaults. The refined `rfc.md` keeps the shared protocol spine, resolves missing deterministic details, and moves product-facing or balance-sensitive ideas into optional profiles or future RFCs.
