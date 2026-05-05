# RQP Canonical Test Vectors

**Status:** Draft test suite  
**Encoding:** Sorted-key UTF-8 JSON with no insignificant whitespace  
**Hash:** SHA-256

These vectors are small interoperability fixtures. They are not balance examples.

## 1. Canonical JSON Rules

For these vectors:

1. Object keys are sorted lexicographically.
2. Strings are UTF-8.
3. Integers are encoded as JSON numbers when safe.
4. Arrays preserve order.
5. No extra whitespace is included in the hashed payload.

## 2. Genesis State Vector

Canonical JSON:

```json
{"agents":[{"agent_id":"0xA","fuel":1000,"hp":100,"position":{"q":0,"r":0},"velocity":{"dq":0,"dr":0}},{"agent_id":"0xB","fuel":1000,"hp":100,"position":{"q":2,"r":-2},"velocity":{"dq":0,"dr":0}}],"match_id":"vector-001","protocol":"rqp/1.0-draft","round":0,"seed":"seed-alpha"}
```

Expected SHA-256:

```text
c0a774e05765246845bd074f05b416dd122d9b27db846462d5e15943794e7b87
```

## 3. Commit Payload Vector

Canonical JSON:

```json
{"action_level":1,"agent_id":"0xA","fuel_burn":5,"fuel_ledger_hash":"ledger-round-1","match_id":"vector-001","movement":{"rotation":0,"thrust":[1,-1]},"round":1,"salt":"commit-salt-a1","vote":{"q":1,"r":-1},"weapons":[]}
```

Expected SHA-256:

```text
bf62789423427eec40eb75a019862151ad2744c9b6288f2b1d3435a6f8fd7dfb
```

## 4. Fuel Ledger Vector

Canonical JSON:

```json
{"agent_id":"0xA","fuel_burn":5,"fuel_remaining":995,"previous_fuel_ledger_hash":"ledger-round-0","round":1,"salt":"ledger-salt-a1"}
```

Expected SHA-256:

```text
62e013c078f817f332c14ce9bb209fe6205daaf3de1575983143a0dd2b75519c
```

## 5. One-Round World State Vector

Canonical JSON:

```json
{"agents":[{"agent_id":"0xA","fuel_committed_hash":"ledger-round-1","hp":100,"position":{"q":1,"r":-1},"velocity":{"dq":1,"dr":-1}},{"agent_id":"0xB","fuel_committed_hash":"ledger-b-round-1","hp":100,"position":{"q":2,"r":-2},"velocity":{"dq":0,"dr":0}}],"hex_potential":[{"potential":1,"q":1,"r":-1}],"match_id":"vector-001","round":1,"seed":"seed-alpha"}
```

Expected SHA-256:

```text
86039894d26035b5cdc880953f99be77e1d2946ad4c0a948a1562886571abf46
```

## 6. Implementation Note

These vectors are conformance fixtures for the exact canonical JSON strings shown above. Future suites should add generated fixtures from a reference encoder and include negative cases for key ordering, whitespace, and integer encoding mistakes.
