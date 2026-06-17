"""Offline case bundle helpers for LaunchFit AI."""

from __future__ import annotations

import datetime as _dt
from typing import Any

from launchfit.benchmarking import validate_benchmark_worksheet


ALLOWED_TIERS = {"T1", "T2", "T3", "T4", "T5"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_GO_TO_MARKET_MODELS = {
    "cross_border_ecommerce",
    "physical_trade",
    "hybrid",
    "unknown",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _valid_date(value: Any) -> bool:
    if not _text(value):
        return True
    try:
        _dt.date.fromisoformat(_text(value))
        return True
    except ValueError:
        return False


def normalize_destination_markets(case: dict[str, Any], allow_legacy: bool = True) -> list[str]:
    raw = case.get("destination_markets")
    values: list[Any]
    if isinstance(raw, list):
        values = raw
    elif raw in (None, "") and allow_legacy:
        values = [case.get("destination_market")]
    else:
        values = []
    destinations: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        destinations.append(text)
    return destinations


def normalize_go_to_market_model(case: dict[str, Any]) -> str:
    model = _text(case.get("go_to_market_model")).lower()
    if model in ALLOWED_GO_TO_MARKET_MODELS:
        return model
    business_model = _text(case.get("business_model")).lower()
    platform = _text(case.get("platform"))
    if platform or any(token in business_model for token in ("marketplace", "fba", "fbm", "seller", "shop")):
        return "cross_border_ecommerce"
    if any(token in business_model for token in ("export", "import", "distributor", "wholesale", "retail")):
        return "physical_trade"
    return "unknown"


def bundle_template(
    platform: str,
    market: str,
    category: str,
    product: str = "",
    origin_country: str = "",
    destination_markets: list[str] | None = None,
    go_to_market_model: str = "unknown",
) -> dict[str, Any]:
    destinations = destination_markets if destination_markets is not None else [market]
    return {
        "bundle_type": "launchfit_offline_case",
        "case": {
            "case_id": "",
            "applicant_name": "",
            "applicant_role": "",
            "origin_country": origin_country,
            "platform": platform,
            "marketplace_site": market,
            "destination_market": market,
            "destination_markets": destinations,
            "go_to_market_model": go_to_market_model,
            "business_model": "",
            "product_category": category,
            "subcategory": product,
            "product_name": product,
            "brand_name": "",
            "review_purpose": "launch readiness and qualification intake",
            "requested_decision_deadline": "",
            "review_date": "",
        },
        "documents": [],
        "packaging": {
            "front_label": "",
            "back_label": "",
            "claims": [],
            "ingredients_or_materials": [],
            "warnings": [],
            "languages": [],
            "units": [],
            "visible_certification_marks": [],
            "data_basis": "user_provided",
        },
        "benchmarks": [],
        "logistics": [],
        "user_search_channels": [],
        "sources": [],
        "external_checks": [],
    }


def bundle_benchmarks(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data.get("benchmarks")
    if not isinstance(rows, list):
        rows = data.get("competitors")
    return [row for row in rows or [] if isinstance(row, dict)]


def validate_case_bundle(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if data.get("bundle_type") != "launchfit_offline_case":
        errors.append("bundle_type must be launchfit_offline_case")
    case = data.get("case")
    if not isinstance(case, dict):
        errors.append("case must be an object")
        case = {}
    model = normalize_go_to_market_model(case)
    if _text(case.get("go_to_market_model")) and _text(case.get("go_to_market_model")).lower() not in ALLOWED_GO_TO_MARKET_MODELS:
        errors.append("case.go_to_market_model is invalid")
    if model == "unknown":
        warnings.append("case.go_to_market_model is unknown; ask whether this is cross-border ecommerce, physical trade, or hybrid")

    for field in ("origin_country", "product_category", "review_purpose"):
        if not _text(case.get(field)):
            errors.append(f"case.{field} is required")
    if model in {"cross_border_ecommerce", "hybrid"} and not _text(case.get("platform")):
        errors.append("case.platform is required")
    destination_markets = normalize_destination_markets(case, allow_legacy=False)
    if not destination_markets:
        errors.append("case.destination_markets must be a non-empty list")
    if not (_text(case.get("product_name")) or _text(case.get("subcategory"))):
        errors.append("case.product_name or case.subcategory is required")
    if not _valid_date(case.get("review_date")):
        errors.append("case.review_date must be YYYY-MM-DD when provided")

    documents = data.get("documents")
    if not isinstance(documents, list):
        errors.append("documents must be a list")
        documents = []
    for idx, document in enumerate(documents):
        if not isinstance(document, dict):
            errors.append(f"documents[{idx}] must be an object")
            continue
        if not _text(document.get("document_type")):
            errors.append(f"documents[{idx}].document_type is required")
        if not _text(document.get("file_reference")):
            errors.append(f"documents[{idx}].file_reference is required")
        if not _valid_date(document.get("issue_date")):
            errors.append(f"documents[{idx}].issue_date must be YYYY-MM-DD when provided")
        if not _valid_date(document.get("expiry_date")):
            errors.append(f"documents[{idx}].expiry_date must be YYYY-MM-DD when provided")
        confidence = _text(document.get("extraction_confidence")) or "medium"
        if confidence not in ALLOWED_CONFIDENCE:
            errors.append(f"documents[{idx}].extraction_confidence is invalid")

    packaging = data.get("packaging")
    if packaging not in (None, {}) and not isinstance(packaging, dict):
        errors.append("packaging must be an object when provided")
    if not packaging:
        warnings.append("packaging is empty; packaging and claim risks will be incomplete")

    benchmarks = bundle_benchmarks(data)
    if benchmarks:
        worksheet = {
            "worksheet_type": "launchfit_benchmark_worksheet",
            "scope": {
                "product": case.get("product_name") or case.get("subcategory", ""),
                "target_market": destination_markets[0] if destination_markets else case.get("destination_market", ""),
                "platform": case.get("platform", ""),
                "category": case.get("product_category", ""),
            },
            "benchmarks": benchmarks,
        }
        errors.extend(f"benchmarks: {error}" for error in validate_benchmark_worksheet(worksheet))
    else:
        warnings.append("benchmarks/competitors is empty; target-market benchmarking will be incomplete")

    logistics = data.get("logistics")
    if not isinstance(logistics, list):
        errors.append("logistics must be a list")
        logistics = []
    for idx, row in enumerate(logistics):
        if not isinstance(row, dict):
            errors.append(f"logistics[{idx}] must be an object")
            continue
        if not (_text(row.get("route")) or _text(row.get("mode"))):
            errors.append(f"logistics[{idx}].route or logistics[{idx}].mode is required")
        if not (_text(row.get("cost_basis")) or _text(row.get("data_basis"))):
            errors.append(f"logistics[{idx}].cost_basis or logistics[{idx}].data_basis is required")
    if not logistics:
        warnings.append("logistics is empty; logistics budget and route risks will be incomplete")

    user_search_channels = data.get("user_search_channels", [])
    if user_search_channels not in (None, []) and not isinstance(user_search_channels, list):
        errors.append("user_search_channels must be a list when provided")
    if isinstance(user_search_channels, list):
        for idx, channel in enumerate(user_search_channels):
            if not isinstance(channel, dict):
                errors.append(f"user_search_channels[{idx}] must be an object")
                continue
            if not _text(channel.get("title")):
                errors.append(f"user_search_channels[{idx}].title is required")
            applies_to = channel.get("applies_to_markets", [])
            if applies_to not in (None, []) and not isinstance(applies_to, list):
                errors.append(f"user_search_channels[{idx}].applies_to_markets must be a list when provided")

    sources = data.get("sources")
    if not isinstance(sources, list):
        errors.append("sources must be a list")
        sources = []
    for idx, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"sources[{idx}] must be an object")
            continue
        tier = _text(source.get("tier")) or "T4"
        if tier not in ALLOWED_TIERS:
            errors.append(f"sources[{idx}].tier is invalid")
        if not _valid_date(source.get("checked_at")):
            errors.append(f"sources[{idx}].checked_at must be YYYY-MM-DD when provided")

    external_checks = data.get("external_checks", [])
    if external_checks not in (None, []) and not isinstance(external_checks, list):
        errors.append("external_checks must be a list when provided")

    return errors, warnings
