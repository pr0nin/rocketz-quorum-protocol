"""Post-game audit replay for RQP bootstrap fixtures."""

from __future__ import annotations

import copy
from typing import Any

from .canonical import verify_hash
from .errors import require_equal
from .fixture import index_by_agent


def verify_audit(
    fixture: dict[str, Any],
    audit: dict[str, Any],
    agent_ids: list[str],
    round_numbers: list[int],
    round_inputs_by_round: dict[int, dict[str, dict[str, Any]]],
    final_fuel_remaining: dict[str, int],
    final_hp: dict[str, int],
) -> None:
    require_equal("audit type", audit.get("type"), "audit_report")
    require_equal("audit result", audit.get("result"), "pass")
    require_equal("audit verified_rounds", audit.get("verified_rounds"), round_numbers)

    missing_reveal_diagnostics = [
        {
            "agent_id": agent_id,
            "fallback": "inertial",
            "round": round_number,
            "type": "missing_reveal",
        }
        for round_number in round_numbers
        for agent_id in agent_ids
        if round_inputs_by_round[round_number][agent_id].get("missing_reveal") is True
    ]
    if missing_reveal_diagnostics:
        require_equal("audit missing reveal diagnostics", audit.get("diagnostics"), missing_reveal_diagnostics)

    dispute_diagnostics = [
        round_fixture["quorum_diagnostics"]
        for round_fixture in fixture["rounds"]
        if round_fixture.get("quorum", {}).get("locked") is False
    ]
    if dispute_diagnostics:
        require_equal("audit dispute diagnostics", audit.get("dispute_diagnostics"), dispute_diagnostics)

    disclosures = index_by_agent(audit.get("agent_disclosures", []), "audit disclosures")
    results = index_by_agent(audit.get("agent_results", []), "audit agent_results")
    require_equal("audit disclosure agents", sorted(disclosures), sorted(agent_ids))
    require_equal("audit result agents", sorted(results), sorted(agent_ids))

    genesis_payloads = index_by_agent(fixture["genesis"]["initial_ledger_payloads"], "genesis initial payloads")

    for agent_id in agent_ids:
        disclosure = disclosures[agent_id]
        result = results[agent_id]
        require_equal(f"audit {agent_id} result", result.get("audit"), "pass")
        require_equal(f"audit {agent_id} violations", result.get("violations"), [])

        initial_payload = {
            "agent_id": agent_id,
            "initial_fuel": disclosure.get("initial_fuel"),
            "loadout": disclosure.get("loadout"),
            "salt": disclosure.get("initial_ledger_salt"),
        }
        initial_hash = verify_hash(
            f"audit {agent_id} initial ledger disclosure",
            initial_payload,
            genesis_payloads[agent_id]["expected_hash"],
        )

        fuel_burns = disclosure.get("fuel_burns")
        ledger_salts = disclosure.get("ledger_salts")
        commit_salts = disclosure.get("commit_salts")
        require_equal(f"audit {agent_id} fuel_burn count", len(fuel_burns), len(round_numbers))
        require_equal(f"audit {agent_id} ledger salt count", len(ledger_salts), len(round_numbers))
        require_equal(f"audit {agent_id} commit salt count", len(commit_salts), len(round_numbers))

        previous_ledger_hash = initial_hash
        fuel_remaining = disclosure["initial_fuel"]
        total_burn = 0

        for index, round_number in enumerate(round_numbers):
            burn = fuel_burns[index]
            total_burn += burn
            fuel_remaining -= burn
            round_input = round_inputs_by_round[round_number][agent_id]
            expected_ledger_payload = round_input["ledger_payload"]
            rebuilt_ledger_payload = {
                "agent_id": agent_id,
                "fuel_burn": burn,
                "fuel_remaining": fuel_remaining,
                "previous_fuel_ledger_hash": previous_ledger_hash,
                "round": round_number,
                "salt": ledger_salts[index],
            }
            require_equal(
                f"audit {agent_id} round {round_number} rebuilt ledger payload",
                rebuilt_ledger_payload,
                expected_ledger_payload,
            )
            previous_ledger_hash = verify_hash(
                f"audit {agent_id} round {round_number} ledger disclosure",
                rebuilt_ledger_payload,
                round_input["expected_ledger_hash"],
            )

            rebuilt_commit_payload = copy.deepcopy(round_input["commit_payload"])
            rebuilt_commit_payload["salt"] = commit_salts[index]
            require_equal(
                f"audit {agent_id} round {round_number} rebuilt commit payload",
                rebuilt_commit_payload,
                round_input["commit_payload"],
            )
            verify_hash(
                f"audit {agent_id} round {round_number} commit disclosure",
                rebuilt_commit_payload,
                round_input["expected_commit_hash"],
            )

        require_equal(f"audit {agent_id} final fuel disclosure", disclosure.get("final_fuel"), fuel_remaining)
        require_equal(f"audit {agent_id} final fuel result", result.get("final_fuel"), fuel_remaining)
        require_equal(f"audit {agent_id} final fuel replay", fuel_remaining, final_fuel_remaining[agent_id])
        require_equal(f"audit {agent_id} total burn", result.get("fuel_burn_total"), total_burn)
        require_equal(f"audit {agent_id} initial fuel result", result.get("initial_fuel"), disclosure.get("initial_fuel"))
        if "final_hp" in result:
            require_equal(f"audit {agent_id} final hp result", result.get("final_hp"), final_hp[agent_id])
