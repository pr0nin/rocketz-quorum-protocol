# RQP WebSocket Transport Profile

**Status:** Draft profile  
**Applies to:** `rqp/1.0-draft.1`
**Purpose:** Define a practical non-authoritative WebSocket relay for early RQP implementations.

## 1. Role of the Hub

The WebSocket hub is a relay, not a game server.

The hub MAY:

1. Accept client connections.
2. Authenticate agents.
3. Relay match messages.
4. Enforce message size limits.
5. Broadcast phase timers.
6. Store append-only event logs.

The hub MUST NOT:

1. Decide round outcomes.
2. Modify canonical payloads.
3. Resolve state hash disputes.
4. Spend fuel or validate hidden balances authoritatively.
5. Advance a match without node quorum.

## 2. Channels

Recommended channels:

```text
/matches/{match_id}/commits
/matches/{match_id}/reveals
/matches/{match_id}/state-votes
/matches/{match_id}/audit
/matches/{match_id}/events
```

## 3. Message Envelope

All messages should be sent in an envelope:

```json
{
  "envelope_type": "rqp_message",
  "protocol": "rqp/1.0-draft.1",
  "match_id": "match-001",
  "phase": "commit",
  "round": 42,
  "agent_id": "0xABC",
  "payload": {},
  "payload_hash": "sha256-payload",
  "signature": "base64-signature"
}
```

For local development, `signature` MAY be omitted. Public and tournament deployments MUST require it.

## 4. Phase Timing

The hub may publish phase timer events:

```json
{
  "type": "phase_timer",
  "match_id": "match-001",
  "round": 42,
  "phase": "commit",
  "deadline_unix_ms": 1777999999000
}
```

Timer events are coordination hints. Nodes still determine validity from protocol rules.

## 5. Deduplication

Nodes and hubs should deduplicate by:

```text
(match_id, round, phase, agent_id, message_type)
```

If two different signed payloads exist for the same key, the event is a conflict and should be included in audit evidence.

## 6. Ordering

The hub does not need to provide total ordering. Canonical ordering is derived from:

1. Round number.
2. Phase.
3. Agent ID.
4. Ruleset-defined action ordering.

## 7. Reconnect and Replay

The hub should retain all messages for the active match. On reconnect, an agent may request:

```json
{
  "type": "replay_request",
  "match_id": "match-001",
  "from_round": 40
}
```

The hub responds by replaying known messages from that round onward.

## 8. Error Messages

Transport errors should be explicit:

```json
{
  "type": "transport_error",
  "match_id": "match-001",
  "round": 42,
  "code": "duplicate_message",
  "detail": "commit already received for agent 0xABC"
}
```

Transport errors are not canonical protocol sanctions unless included in audit evidence.

## 9. Security Requirements

Public deployments should require:

1. TLS.
2. Signed payloads.
3. Message size limits.
4. Rate limits.
5. Append-only logs.
6. Replay export.

Tournament deployments should use at least two independent relays or a relay plus peer gossip fallback.
