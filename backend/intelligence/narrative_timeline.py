"""
backend/intelligence/narrative_timeline.py

Converts raw per-chain transaction timelines into a cross-chain
"investigation narrative" — a small set of key milestones instead
of every single transaction.

Reuses timeline_builder.build_timeline() per chain (no duplication),
merges them chronologically, and detects milestone events:
  Wallet Created -> Exchange Deposit -> Bridge -> <next chain> -> ... -> Risk Level -> Final Score
"""

from intelligence.timeline import timeline_builder
from entity_labeling.label_database import lookup_known_address


def _detect_exchange_counterparty(event: dict) -> str | None:
    """Checks if either side of a transaction is a known exchange address."""
    for addr in (event.get("from_address"), event.get("to_address")):
        if not addr:
            continue
        match = lookup_known_address(addr)
        if match and match["label"] == "Exchange Wallet":
            return match["name"]
    return None


def build_investigation_narrative(chain_csv_paths: dict, wallet_address: str, risk_result: dict = None) -> list:
    """
    Args:
        chain_csv_paths: dict like {"ethereum": "datasets/ethereum/0x...csv",
                                     "polygon": "datasets/polygon/0x...csv",
                                     "arbitrum": "datasets/arbitrum/0x...csv"}
                          Only chains the wallet is actually active on need be included.
        wallet_address: the wallet being investigated
        risk_result: optional output of risk_engine.analyze() /
                     get_explainable_risk(), to append the risk/score milestones

    Returns:
        list[dict]: Ordered narrative milestones, each with a "milestone" label
                     and supporting detail.
    """
    merged_events = []

    # Step 1: Build each chain's timeline using the EXISTING builder, tag with chain
    for chain, csv_path in chain_csv_paths.items():
        chain_events = timeline_builder.build_timeline(csv_path, wallet_address, chain)
        for event in chain_events:
            event["chain"] = chain
        merged_events.extend(chain_events)

    # Step 2: Sort all events across all chains chronologically
    merged_events.sort(key=lambda e: e["timestamp"] if e["timestamp"] else 0)

    if not merged_events:
        return [{"milestone": "No transaction history found", "detail": ""}]

    narrative = []

    # Milestone: Wallet Created (first ever event, any chain)
    first_event = merged_events[0]
    narrative.append({
        "milestone": "Wallet Created",
        "detail": f"First activity on {first_event['chain']} at {first_event['datetime']}",
    })

    last_chain_seen = first_event["chain"]
    exchange_flagged = False

    for event in merged_events:
        # Milestone: Exchange Deposit (only report the first occurrence)
        if not exchange_flagged:
            exchange_name = _detect_exchange_counterparty(event)
            if exchange_name:
                narrative.append({
                    "milestone": "Exchange Deposit",
                    "detail": f"Interacted with {exchange_name} on {event['chain']} at {event['datetime']}",
                })
                exchange_flagged = True

        # Milestone: Bridge Transfer
        if event["event_type"] == "Bridge Transfer":
            narrative.append({
                "milestone": "Bridge",
                "detail": f"Bridge transfer detected on {event['chain']} at {event['datetime']}",
            })

        # Milestone: Chain switch (wallet's activity moves to a new chain)
        if event["chain"] != last_chain_seen:
            narrative.append({
                "milestone": event["chain"].capitalize(),
                "detail": f"Activity resumed on {event['chain']} at {event['datetime']}",
            })
            last_chain_seen = event["chain"]

    # Milestone: Risk Level + Final Score (if risk_result provided)
    if risk_result:
        narrative.append({
            "milestone": f"{risk_result.get('risk_level', 'Unknown')} Risk",
            "detail": f"Risk indicators: {', '.join(risk_result.get('explanation', [])) or 'None'}",
        })
        narrative.append({
            "milestone": "Final Score",
            "detail": f"{risk_result.get('risk_score', 'N/A')}/100",
        })

    return narrative