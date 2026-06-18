"""Benchmark worksheet helpers for LaunchFit AI.

The functions in this module are dependency-free and intentionally conservative:
they summarize supplied benchmark rows without inventing products, prices, or
source facts.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


ALLOWED_BENCHMARK_SOURCE_TYPES = {
    "direct_competitor",
    "substitute",
    "adjacent_reference",
    "category_leader",
    "local_niche_brand",
    "platform_best_seller",
    "offline_retail_shelf",
    "dtc_social_commerce",
}

ALLOWED_DATA_BASIS = {"current_checked", "user_provided", "assumption", "not_checked"}
ALLOWED_CHANNEL_ROLES = {
    "search_marketplace",
    "social_commerce",
    "mass_retail",
    "club_store",
    "specialty",
    "pharmacy",
    "dtc",
    "offline_shelf",
    "other",
}
ALLOWED_POSITIONING = {"mass", "mainstream", "premium", "specialty", "luxury", "unknown"}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _strings(value: Any) -> list[str]:
    return [_text(item) for item in _list(value) if _text(item)]


def benchmark_template(
    market: str,
    category: str,
    product: str = "",
    platform: str = "",
    count: int = 8,
) -> dict[str, Any]:
    source_types = [
        "direct_competitor",
        "substitute",
        "adjacent_reference",
        "category_leader",
        "local_niche_brand",
        "platform_best_seller",
        "offline_retail_shelf",
        "dtc_social_commerce",
    ]
    rows: list[dict[str, Any]] = []
    row_count = max(3, min(count, 12))
    for idx in range(row_count):
        source_type = source_types[idx] if idx < len(source_types) else "direct_competitor"
        rows.append(
            {
                "benchmark_id": f"BM-{idx + 1:03d}",
                "benchmark_source_type": source_type,
                "product_name": "",
                "brand": "",
                "channel": "",
                "channel_role": "other",
                "market": market,
                "source_url": "",
                "image_url": "",
                "image_alt": "",
                "checked_at": "",
                "pack_size": "",
                "price": "",
                "unit_price": "",
                "bundle_strategy": "",
                "positioning": "unknown",
                "product_type": "",
                "formula_or_material": "",
                "origin_story": "",
                "core_buyer_promise": "",
                "packaging_structure": [],
                "visual_hierarchy": [],
                "label_language": [],
                "warnings": [],
                "responsible_party_signal": "",
                "visible_claims": [],
                "proof_points": [],
                "certification_signals": [],
                "platform_trust_markers": [],
                "review_rating": "",
                "review_count": "",
                "review_praise": [],
                "review_objections": [],
                "purchase_triggers": [],
                "fulfillment_signals": [],
                "data_basis": "not_checked",
                "source_ids": [],
                "evidence_ids": [],
                "takeaway": "",
                "copy_action": "",
                "avoid_action": "",
                "improve_action": "",
            }
        )
    return {
        "worksheet_type": "launchfit_benchmark_worksheet",
        "generated_at": "",
        "scope": {
            "product": product,
            "target_market": market,
            "platform": platform,
            "category": category,
        },
        "benchmarks": rows,
    }


def validate_benchmark_worksheet(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("worksheet_type") != "launchfit_benchmark_worksheet":
        errors.append("worksheet_type must be launchfit_benchmark_worksheet")
    if not isinstance(data.get("scope"), dict):
        errors.append("scope must be an object")
    rows = data.get("benchmarks")
    if not isinstance(rows, list) or not rows:
        errors.append("benchmarks must be a non-empty list")
        return errors
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"benchmarks[{idx}] must be an object")
            continue
        if not _text(row.get("product_name")):
            errors.append(f"benchmarks[{idx}].product_name is required")
        if not _text(row.get("channel")):
            errors.append(f"benchmarks[{idx}].channel is required")
        source_type = _text(row.get("benchmark_source_type")) or "direct_competitor"
        if source_type not in ALLOWED_BENCHMARK_SOURCE_TYPES:
            errors.append(f"benchmarks[{idx}].benchmark_source_type is invalid")
        data_basis = _text(row.get("data_basis")) or "not_checked"
        if data_basis not in ALLOWED_DATA_BASIS:
            errors.append(f"benchmarks[{idx}].data_basis is invalid")
        if data_basis == "current_checked" and not _text(row.get("checked_at")):
            errors.append(f"benchmarks[{idx}].checked_at is required when data_basis is current_checked")
        channel_role = _text(row.get("channel_role")) or "other"
        if channel_role not in ALLOWED_CHANNEL_ROLES:
            errors.append(f"benchmarks[{idx}].channel_role is invalid")
        positioning = _text(row.get("positioning")) or "unknown"
        if positioning not in ALLOWED_POSITIONING:
            errors.append(f"benchmarks[{idx}].positioning is invalid")
        for list_key in (
            "packaging_structure",
            "visual_hierarchy",
            "label_language",
            "warnings",
            "visible_claims",
            "proof_points",
            "certification_signals",
            "platform_trust_markers",
            "review_praise",
            "review_objections",
            "purchase_triggers",
            "fulfillment_signals",
            "source_ids",
            "evidence_ids",
        ):
            if list_key in row and not isinstance(row.get(list_key), list):
                errors.append(f"benchmarks[{idx}].{list_key} must be a list")
    return errors


def summarize_benchmark_worksheet(data: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in data.get("benchmarks", []) if isinstance(row, dict)]
    source_types = sorted({_text(row.get("benchmark_source_type")) for row in rows if _text(row.get("benchmark_source_type"))})
    channels = sorted({_text(row.get("channel")) for row in rows if _text(row.get("channel"))})
    channel_roles = sorted({_text(row.get("channel_role")) for row in rows if _text(row.get("channel_role"))})
    positions = sorted({_text(row.get("positioning")) for row in rows if _text(row.get("positioning")) and row.get("positioning") != "unknown"})
    prices = [_text(row.get("unit_price") or row.get("price")) for row in rows if _text(row.get("unit_price") or row.get("price"))]
    claims = Counter(signal for row in rows for signal in _strings(row.get("visible_claims")))
    proof = Counter(signal for row in rows for signal in _strings(row.get("proof_points")))
    trust = Counter(signal for row in rows for signal in _strings(row.get("certification_signals")) + _strings(row.get("platform_trust_markers")))
    packaging = Counter(signal for row in rows for signal in _strings(row.get("packaging_structure")) + _strings(row.get("visual_hierarchy")))
    praise = Counter(signal for row in rows for signal in _strings(row.get("review_praise")))
    objections = Counter(signal for row in rows for signal in _strings(row.get("review_objections")))
    triggers = Counter(signal for row in rows for signal in _strings(row.get("purchase_triggers")))
    fulfill = Counter(signal for row in rows for signal in _strings(row.get("fulfillment_signals")))
    copy_actions = [_text(row.get("copy_action")) for row in rows if _text(row.get("copy_action"))]
    avoid_actions = [_text(row.get("avoid_action")) for row in rows if _text(row.get("avoid_action"))]
    improve_actions = [_text(row.get("improve_action")) for row in rows if _text(row.get("improve_action"))]
    unchecked_count = sum(1 for row in rows if row.get("data_basis") != "current_checked")
    return {
        "summary_type": "launchfit_benchmark_summary",
        "scope": data.get("scope", {}),
        "row_count": len(rows),
        "source_types_covered": source_types,
        "missing_source_types": sorted(ALLOWED_BENCHMARK_SOURCE_TYPES.difference(source_types)),
        "channel_map": {
            "channels": channels,
            "channel_roles": channel_roles,
        },
        "reference_price_band": {
            "observed_prices": prices,
            "basis": "current_checked" if rows and unchecked_count == 0 else "mixed_or_user_provided",
        },
        "positioning_map": positions,
        "packaging_conventions": [item for item, _ in packaging.most_common()],
        "claims_and_proof": {
            "visible_claims": [item for item, _ in claims.most_common()],
            "proof_points": [item for item, _ in proof.most_common()],
            "trust_signals": [item for item, _ in trust.most_common()],
        },
        "review_signal_map": {
            "praise": [item for item, _ in praise.most_common()],
            "objections": [item for item, _ in objections.most_common()],
            "purchase_triggers": [item for item, _ in triggers.most_common()],
        },
        "fulfillment_signal_map": [item for item, _ in fulfill.most_common()],
        "copy_avoid_improve": {
            "copy": copy_actions,
            "avoid": avoid_actions,
            "improve": improve_actions,
        },
        "verification_needed": [
            "Recheck all user_provided, assumption, and not_checked benchmark rows before pricing, ordering, printing, listing, or shipping."
        ]
        if unchecked_count
        else [],
    }
