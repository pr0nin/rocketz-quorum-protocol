"""Fixture loading and genesis verification helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .canonical import verify_hash
from .errors import fail, require, require_equal, require_unique


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as error:
        fail(f"file not found: {path}")
        raise AssertionError from error
    except json.JSONDecodeError as error:
        fail(f"invalid JSON in {path}: {error}")
        raise AssertionError from error


def index_by_agent(items: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    agent_ids = [item.get("agent_id") for item in items]
    require(all(isinstance(agent_id, str) for agent_id in agent_ids), f"{label}: every item needs agent_id")
    require_unique(agent_ids, label)
    return {item["agent_id"]: item for item in items}


def verify_genesis(fixture: dict[str, Any]) -> tuple[list[str], dict[str, str], dict[str, Any]]:
    genesis = fixture.get("genesis")
    require(isinstance(genesis, dict), "genesis must be an object")

    initial_payloads = genesis.get("initial_ledger_payloads")
    require(isinstance(initial_payloads, list), "genesis.initial_ledger_payloads must be a list")

    ledger_hashes: dict[str, str] = {}
    for item in initial_payloads:
        agent_id = item.get("agent_id")
        payload = item.get("payload")
        expected_hash = item.get("expected_hash")
        require(isinstance(agent_id, str), "initial ledger payload missing agent_id")
        require(isinstance(payload, dict), f"initial ledger {agent_id}: payload must be an object")
        require(isinstance(expected_hash, str), f"initial ledger {agent_id}: expected_hash must be a string")
        require_equal(f"initial ledger {agent_id} payload agent", payload.get("agent_id"), agent_id)
        ledger_hashes[agent_id] = verify_hash(f"initial ledger {agent_id}", payload, expected_hash)

    world_state = genesis.get("world_state")
    require(isinstance(world_state, dict), "genesis.world_state must be an object")
    require_equal("genesis world protocol", world_state.get("protocol"), fixture["protocol"])
    require_equal("genesis world match_id", world_state.get("match_id"), fixture["match_id"])
    require_equal("genesis world round", world_state.get("round"), 0)
    verify_hash("genesis world_state", world_state, genesis.get("world_state_hash"))

    agents = world_state.get("agents")
    require(isinstance(agents, list), "genesis.world_state.agents must be a list")
    agent_ids = [agent.get("agent_id") for agent in agents]
    require(all(isinstance(agent_id, str) for agent_id in agent_ids), "genesis agents need agent_id")
    require_unique(agent_ids, "genesis agents")
    require_equal("genesis initial ledger agents", sorted(ledger_hashes), sorted(agent_ids))

    for agent in agents:
        agent_id = agent["agent_id"]
        require_equal(
            f"genesis agent {agent_id} fuel_ledger_hash",
            agent.get("fuel_ledger_hash"),
            ledger_hashes[agent_id],
        )

    return agent_ids, ledger_hashes, world_state
