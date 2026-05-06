"""Canonical JSON and hash utilities for RQP bootstrap verification."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .errors import fail

PROTOCOL = "rqp/1.0-draft.1"
CANONICAL_ENCODING = "sorted-key-json-v1"
HASH_ALGORITHM = "sha-256"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def verify_hash(label: str, value: Any, expected_hash: str) -> str:
    actual_hash = sha256_hex(value)
    if actual_hash != expected_hash:
        fail(f"{label}: expected hash {expected_hash}, got {actual_hash}")
    return actual_hash
