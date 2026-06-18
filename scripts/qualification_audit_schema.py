#!/usr/bin/env python3
"""Dependency-free helpers for cross-border qualification review outputs.

Commands:
  sample
  validate <json-file>
  case-check <case-file> <review-json-file>
  golden-replay [--cases-dir CASES_DIR] [--reviews-dir REVIEWS_DIR]
  quality-gate
  checklist --platform PLATFORM --market MARKET --category CATEGORY
  review-skeleton --platform PLATFORM --market MARKET --category CATEGORY
  benchmark-template --market MARKET --category CATEGORY
  benchmark-validate <worksheet-json-file>
  benchmark-summarize <worksheet-json-file>
  bundle-template --platform PLATFORM --market MARKET --category CATEGORY
  bundle-validate <bundle-json-file>
  batch-launch-report <input-dir> <output-dir>
  coverage-report
  launch-report <bundle-json-file>
  launch-report-markdown <review-json-file>
  launch-report-card <review-json-file> <output-file>
  launch-report-detail <review-json-file> <output-file>
  rulepack-new --country-code CODE --country-name NAME
  rulepack-validate <json-file>
  rulepack-index-validate
  source-freshness [json-file ...]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent.parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from launchfit.benchmarking import (
    benchmark_template as benchmark_worksheet_template,
    summarize_benchmark_worksheet,
    validate_benchmark_worksheet,
)
from launchfit.bundles import bundle_template as offline_bundle_template
from launchfit.bundles import normalize_go_to_market_model
from launchfit.bundles import normalize_destination_markets
from launchfit.bundles import validate_case_bundle
from launchfit.coverage import coverage_report


ALLOWED_DECISIONS = {
    "approve",
    "conditional_approve",
    "request_more_info",
    "reject",
    "escalate_human",
    "not_applicable",
}

ALLOWED_REQUIREMENT_STATUS = {
    "satisfied",
    "partial",
    "missing",
    "invalid",
    "not_applicable",
    "needs_external_verification",
}

ALLOWED_SEVERITY = {"critical", "high", "medium", "low"}
ALLOWED_TIERS = {"T1", "T2", "T3", "T4", "T5"}
ALLOWED_PACK_TYPES = {"global", "country", "region", "platform", "category"}
ALLOWED_PACK_MATURITY = {"seed", "validated", "production", "stale"}
ALLOWED_SURFACES = {
    "seller",
    "brand_ip",
    "product_category",
    "market_import",
    "certificate",
    "platform_listing",
    "service_provider",
}


ALLOWED_RISK_LEVELS = {"low", "medium", "high", "critical"}
ALLOWED_BENCHMARK_BASIS = {
    "current_checked",
    "user_provided",
    "assumption",
    "not_checked",
}
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
ALLOWED_GO_TO_MARKET_MODELS = {"cross_border_ecommerce", "physical_trade", "hybrid", "unknown"}

DEFINITIVE_STATUSES = {"approve", "conditional_approve", "reject"}
MATURE_PACKS = {"validated", "production"}
AUTHORITATIVE_TIERS = {"T1", "T2"}

REQUIRED_CASE_FIELDS = (
    "applicant_name",
    "origin_country",
    "destination_market",
    "destination_markets",
    "go_to_market_model",
    "product_category",
    "review_purpose",
)

SKILL_ROOT = Path(__file__).resolve().parent.parent

# Process-level checklist items that are not qualification requirements.
PROCESS_CHECKLIST = [
    "Sensitive personal or business data is redacted in user-facing output.",
]

# Pack type -> which checklist input its match keywords apply to.
PACK_MATCH_INPUT = {
    "platform": "platform",
    "category": "category",
    "country": "market",
    "region": "market",
}

PACK_COMPOSITION_ORDER = {
    "global": 0,
    "platform": 1,
    "region": 2,
    "country": 3,
    "category": 4,
}


def today() -> str:
    return _dt.date.today().isoformat()


def _unique_texts(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value).strip() if value is not None else ""
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def _split_generation_methods(value: str) -> list[str]:
    return _unique_texts(re.split(r"[,;；，、\n]+", value) if value else [])


def build_generation_metadata(report: dict[str, Any], source_bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    """Record who generated the report and which information routes fed it."""
    methods: list[Any] = _split_generation_methods(os.environ.get("LAUNCHFIT_SEARCH_METHODS", ""))
    bundle = source_bundle if isinstance(source_bundle, dict) else {}
    sources = [item for item in report.get("sources") or [] if isinstance(item, dict)]
    benchmarks = [item for item in report.get("market_benchmarks") or [] if isinstance(item, dict)]

    if report.get("documents") or any(str(source.get("source_id", "")).startswith("src-user-") for source in sources):
        methods.append("用户材料/输入包")
    if bundle.get("user_search_channels"):
        methods.append("用户指定搜索渠道")
    if bundle.get("external_checks"):
        methods.append("外部核验记录")
    if report.get("source_candidates") or report.get("research_tasks"):
        methods.append("规则包与待核验渠道规划")
    if any(str(source.get("tier")) in AUTHORITATIVE_TIERS for source in sources):
        methods.append("规则包官方来源候选")
    if any(str(source.get("source_id", "")).startswith("src-agent-") for source in sources):
        methods.append("agent 主动检索")
    if any(item.get("data_basis") == "current_checked" for item in benchmarks) or any(
        source_id.startswith("src-agent-")
        for item in benchmarks
        for source_id in [str(value) for value in item.get("source_ids") or []]
    ):
        methods.append("公开商业搜索/对标检索")
    if not methods:
        methods.append("用户材料/输入包")

    return {
        "agent": os.environ.get("LAUNCHFIT_AGENT_NAME", "Codex").strip() or "Codex",
        "model": os.environ.get("LAUNCHFIT_MODEL_NAME", "").strip() or "未声明",
        "search_methods": _unique_texts(methods),
        "generated_at": today(),
    }


def _generation_metadata(report: dict[str, Any]) -> dict[str, Any]:
    metadata = report.get("generation_metadata") if isinstance(report.get("generation_metadata"), dict) else {}
    normalized = {
        "agent": str(metadata.get("agent") or os.environ.get("LAUNCHFIT_AGENT_NAME", "Codex")).strip() or "Codex",
        "model": str(metadata.get("model") or os.environ.get("LAUNCHFIT_MODEL_NAME", "") or "未声明").strip() or "未声明",
        "search_methods": _unique_texts(metadata.get("search_methods") if isinstance(metadata.get("search_methods"), list) else []),
        "generated_at": str(metadata.get("generated_at") or today()).strip() or today(),
    }
    if not normalized["search_methods"]:
        normalized["search_methods"] = build_generation_metadata(report)["search_methods"]
    return normalized


def _generation_provenance_html(report: dict[str, Any], limit: int = 120) -> str:
    metadata = _generation_metadata(report)
    methods = "、".join(str(item) for item in metadata.get("search_methods") or [])
    return (
        f"生成说明：Agent {_html(metadata.get('agent'))} · "
        f"模型 {_html(metadata.get('model'))} · "
        f"搜索途径 {_html(_short_text(methods, limit))} · "
        f"生成日期 {_html(metadata.get('generated_at'))}"
    )


def parse_date(value: Any) -> _dt.date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return _dt.date.fromisoformat(value)
    except ValueError:
        return None


def age_days(value: Any, as_of: _dt.date | None = None) -> int | None:
    checked = parse_date(value)
    if checked is None:
        return None
    return ((as_of or _dt.date.today()) - checked).days


def load_rulepack_index() -> dict[str, Any]:
    path = SKILL_ROOT / "data" / "rulepacks" / "index.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_rulepack(rel_path: str) -> dict[str, Any]:
    return json.loads((SKILL_ROOT / rel_path).read_text(encoding="utf-8"))


def matches_pack(pack: dict[str, Any], inputs: dict[str, str]) -> bool:
    pack_type = pack.get("type")
    if pack_type == "global":
        return True
    input_key = PACK_MATCH_INPUT.get(str(pack_type))
    if input_key is None:
        return False
    keywords = (pack.get("match") or {}).get("keywords", [])
    target = inputs.get(input_key, "")
    return bool(target and any(str(keyword).lower() in target for keyword in keywords))


def matching_rulepacks(platform: str, market: str, category: str) -> list[dict[str, Any]]:
    inputs = {
        "platform": platform.strip().lower(),
        "market": market.strip().lower(),
        "category": category.strip().lower(),
    }
    packs: list[dict[str, Any]] = []
    for entry in load_rulepack_index().get("packs", []):
        pack = load_rulepack(entry["path"])
        if matches_pack(pack, inputs):
            pack["_index_entry"] = entry
            packs.append(pack)
    packs.sort(key=lambda pack: PACK_COMPOSITION_ORDER.get(str(pack.get("type")), 99))
    return packs


def sample() -> dict[str, Any]:
    payload = {
        "review_type": "cross_border_ecommerce_qualification",
        "case": {
            "case_id": "case-demo-001",
            "applicant_name": "Example Trading Co., Ltd.",
            "applicant_role": "distributor",
            "origin_country": "China",
            "platform": "Amazon",
            "marketplace_site": "US",
            "destination_market": "United States",
            "destination_markets": ["United States"],
            "go_to_market_model": "cross_border_ecommerce",
            "business_model": "marketplace seller",
            "product_category": "food",
            "subcategory": "sauce",
            "brand_name": "Example Brand",
            "review_purpose": "category qualification review",
            "requested_decision_deadline": "",
            "review_date": today(),
        },
        "decision": {
            "status": "request_more_info",
            "risk_level": "high",
            "risk_score": 35,
            "summary": "Cannot decide until brand authorization and current food facility/import documentation are verified.",
            "rationale": ["Required brand and food compliance evidence is incomplete."],
        },
        "documents": [],
        "market_benchmarks": [],
        "market_benchmark_summary": empty_benchmark_summary(),
        "requirements": [],
        "findings": [],
        "missing_materials": [],
        "evidence": [],
        "sources": [],
        "remediation": {
            "applicant_message": "",
            "internal_next_steps": [],
        },
        "privacy": {
            "redactions_applied": [],
            "sensitive_data_notes": [],
        },
        "audit_log": [
            {
                "timestamp": today(),
                "actor": "AI reviewer",
                "action": "created_sample",
                "details": "Template sample generated.",
            }
        ],
        "disclaimer": "Operational qualification review only; not legal advice.",
    }
    payload["generation_metadata"] = build_generation_metadata(payload)
    return payload


def checklist(platform: str, market: str, category: str) -> dict[str, Any]:
    index = load_rulepack_index()
    inputs = {
        "platform": platform.strip().lower(),
        "market": market.strip().lower(),
        "category": category.strip().lower(),
    }

    base_items: list[str] = []
    pack_items: list[str] = []
    matched_packs: list[str] = []
    matched_types: set[str] = set()
    matched_combinations: list[dict[str, Any]] = []

    for pack in matching_rulepacks(platform, market, category):
        pack_type = pack.get("type")
        if pack_type == "global":
            base_items = [req["requirement"] for req in pack.get("requirements", [])]
            matched_packs.append(pack["pack_id"])
            continue
        matched_packs.append(pack["pack_id"])
        matched_types.add(str(pack_type))
        pack_items.extend(pack.get("checklist_hints", []))
        pack_items.extend(req["requirement"] for req in pack.get("requirements", []))

    for combo in index.get("priority_combinations", []):
        if not isinstance(combo, dict):
            continue
        criteria = combo.get("criteria") if isinstance(combo.get("criteria"), dict) else {}
        platform_hit = _keyword_hit(criteria.get("platform_keywords"), inputs["platform"])
        market_hit = _keyword_hit(criteria.get("market_keywords"), inputs["market"])
        category_hit = _keyword_hit(criteria.get("category_keywords"), inputs["category"])
        if platform_hit and market_hit and category_hit:
            matched_combinations.append(
                {
                    "combo_id": combo.get("combo_id"),
                    "name": combo.get("name"),
                    "maturity": combo.get("maturity", "seed"),
                    "verification_tasks": combo.get("verification_tasks", []),
                    "expected_packs": combo.get("expected_packs", []),
                }
            )

    warnings: list[str] = []
    if "platform" not in matched_types:
        warnings.append(
            f"No platform pack matched '{platform}'. Verify official platform policy manually."
        )
    if "category" not in matched_types:
        warnings.append(
            f"No category pack matched '{category}'. Verify category-specific requirements manually."
        )
    if not matched_types.intersection({"country", "region"}):
        warnings.append(
            f"No country/region pack matched '{market}'. Using global baseline; verify official sources for this market."
        )

    return {
        "platform": platform,
        "market": market,
        "category": category,
        "generated_at": today(),
        "matched_packs": matched_packs,
        "matched_priority_combinations": matched_combinations,
        "warnings": warnings,
        "note": "Routing checklist only. Verify current official platform and regulator sources before final decision.",
        "items": base_items + PROCESS_CHECKLIST + pack_items,
    }


def review_skeleton(
    platform: str,
    market: str,
    category: str,
    applicant_name: str = "",
    applicant_role: str = "",
    business_model: str = "",
    brand_name: str = "",
    purpose: str = "launch readiness and qualification intake",
    case_id: str = "",
    marketplace_site: str = "",
) -> dict[str, Any]:
    packs = matching_rulepacks(platform, market, category)
    today_text = today()
    case_id = case_id.strip() or f"intake-{platform.strip().lower() or 'platform'}-{market.strip().lower() or 'market'}-{category.strip().lower() or 'category'}"
    marketplace_site = marketplace_site.strip() or market.strip()

    sources_by_id: dict[str, dict[str, Any]] = {}
    requirements_by_id: dict[str, dict[str, Any]] = {}
    source_pack_by_id: dict[str, str] = {}

    for pack in packs:
        for source in pack.get("sources", []):
            if not isinstance(source, dict) or not source.get("source_id"):
                continue
            source_id = str(source["source_id"])
            sources_by_id[source_id] = {
                "source_id": source_id,
                "title": str(source.get("title", "")),
                "url": str(source.get("url", "")),
                "tier": str(source.get("tier", "T3")),
                "checked_at": str(source.get("checked_at", today_text)),
                "confirms": str(source.get("confirms", "")),
            }
            source_pack_by_id[source_id] = str(pack.get("pack_id", ""))
        for req in pack.get("requirements", []):
            if not isinstance(req, dict) or not req.get("requirement_id"):
                continue
            requirements_by_id[str(req["requirement_id"])] = req

    requirements: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    missing_materials: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    audit_log: list[dict[str, str]] = []

    for source_id, source in sources_by_id.items():
        evidence.append(
            {
                "evidence_id": f"ev-{source_id}",
                "kind": "official_source" if source.get("tier") in AUTHORITATIVE_TIERS else "other",
                "reference": source.get("url", ""),
                "tier": source.get("tier", "T3"),
                "checked_at": source.get("checked_at", today_text),
                "extracted_fact": source.get("confirms", ""),
                "confidence": "high" if source.get("tier") in AUTHORITATIVE_TIERS else "medium",
            }
        )
        audit_log.append(
            {
                "timestamp": source.get("checked_at", today_text),
                "actor": "AI reviewer",
                "action": "loaded_rule_source",
                "details": f"{source_id} from {source_pack_by_id.get(source_id, '')}",
            }
        )

    missing_scope_fields = []
    if not platform.strip():
        missing_scope_fields.append("platform")
    if not market.strip():
        missing_scope_fields.append("destination_market")
    if not category.strip():
        missing_scope_fields.append("product_category")

    for idx, req in enumerate(requirements_by_id.values(), start=1):
        source_ids = [str(item) for item in req.get("source_ids", [])]
        if missing_scope_fields:
            status = "missing"
            notes = f"Missing scope fields: {', '.join(missing_scope_fields)}."
            severity = "high"
        elif source_ids:
            status = "missing"
            notes = "Official source is attached; applicant/product evidence still needs to be matched."
            severity = "high" if req.get("mandatory") is True else "medium"
        else:
            status = "needs_external_verification"
            notes = "No official source is attached to this rule pack requirement yet."
            severity = "medium"

        requirements.append(
            {
                "requirement_id": str(req.get("requirement_id")),
                "surface": str(req.get("surface", "platform_listing")),
                "requirement": str(req.get("requirement", "")),
                "status": status,
                "matched_evidence_ids": [],
                "source_ids": source_ids,
                "notes": notes,
            }
        )

        expected = [str(item) for item in req.get("evidence_expected", [])]
        if expected:
            missing_materials.append(
                {
                    "material": "; ".join(expected),
                    "why_required": str(req.get("decision_effect", "Required before final decision.")),
                    "acceptable_replacement": "Official registry/source confirmation or applicant document matching the exact platform, market, product, holder, scope, and validity period.",
                    "owner": "applicant / reviewer",
                    "priority": "P0" if req.get("mandatory") is True else "P1",
                }
            )

        findings.append(
            {
                "finding_id": f"F-{idx:03d}",
                "severity": severity,
                "surface": str(req.get("surface", "")),
                "requirement": str(req.get("requirement", "")),
                "submitted_evidence": "No applicant evidence supplied in this generated intake skeleton.",
                "observed_issue": "Requirement is not yet matched to submitted applicant/product evidence.",
                "business_impact": str(req.get("decision_effect", "Cannot issue a final qualification decision yet.")),
                "decision_effect": "request_more_info",
                "required_action": "Collect matching applicant evidence and verify current official sources before approval.",
                "acceptable_evidence": "; ".join(expected) if expected else "Verified official source and matching applicant evidence.",
                "source_ids": source_ids,
                "confidence": "medium" if source_ids else "low",
            }
        )

    if missing_scope_fields:
        risk_level = "high"
        risk_score = 35
        summary = f"Cannot start a final review until {', '.join(missing_scope_fields)} is provided."
    elif not requirements:
        risk_level = "high"
        risk_score = 35
        summary = "No matching rule pack requirements were found; use global intake and verify official sources manually."
    else:
        unresolved_high = any(item["severity"] == "high" for item in findings)
        risk_level = "high" if unresolved_high else "medium"
        risk_score = 35 if unresolved_high else 25
        summary = "Intake skeleton generated. Final decision requires submitted documents, evidence matching, and source verification."

    audit_log.append(
        {
            "timestamp": today_text,
            "actor": "AI reviewer",
            "action": "generated_review_skeleton",
            "details": f"Matched packs: {', '.join(str(pack.get('pack_id')) for pack in packs) or 'none'}",
        }
    )

    payload = {
        "review_type": "cross_border_ecommerce_qualification",
        "case": {
            "case_id": case_id,
            "applicant_name": applicant_name,
            "applicant_role": applicant_role,
            "platform": platform,
            "marketplace_site": marketplace_site,
            "destination_market": market,
            "business_model": business_model,
            "product_category": category,
            "subcategory": "",
            "brand_name": brand_name,
            "review_purpose": purpose,
            "requested_decision_deadline": "",
            "review_date": today_text,
        },
        "decision": {
            "status": "request_more_info",
            "risk_level": risk_level,
            "risk_score": risk_score,
            "summary": summary,
            "rationale": [
                "Generated skeleton is an intake artifact, not a final pass/fail decision.",
                "T4 applicant documents and current T1/T2 source checks must be matched before approval.",
            ],
        },
        "documents": [],
        "market_benchmarks": [],
        "market_benchmark_summary": empty_benchmark_summary(),
        "requirements": requirements,
        "findings": findings,
        "missing_materials": missing_materials,
        "evidence": evidence,
        "sources": list(sources_by_id.values()),
        "remediation": {
            "applicant_message": build_supplement_message(missing_materials),
            "internal_next_steps": [
                "Upload and classify applicant documents.",
                "Extract holder, issuer, number, issue date, expiry date, product scope, territory, and platform/channel coverage.",
                "Match every mandatory requirement to evidence and current official sources.",
                "Escalate suspected fraud, conflicting official sources, sanctions/export-control, or legal ambiguity.",
            ],
        },
        "privacy": {
            "redactions_applied": [],
            "sensitive_data_notes": [
                "Generated skeleton contains no applicant document numbers. Redact PII and confidential identifiers after document upload."
            ],
        },
        "audit_log": audit_log,
        "disclaimer": "Operational qualification review only; not legal advice.",
    }
    payload["generation_metadata"] = build_generation_metadata(payload)
    return payload


def benchmark_template(
    market: str,
    category: str,
    product: str = "",
    platform: str = "",
    count: int = 8,
) -> dict[str, Any]:
    """Create a target-market benchmark worksheet for seller-facing launch review."""
    row_count = max(3, min(count, 10))
    rows: list[dict[str, Any]] = []
    for idx in range(1, row_count + 1):
        rows.append(
            {
                "benchmark_id": f"BM-{idx:03d}",
                "product_name": "",
                "channel": "",
                "channel_role": "other",
                "market": market,
                "pack_size": "",
                "price": "",
                "unit_price": "",
                "positioning": "unknown",
                "visible_claims": [],
                "packaging_signals": [],
                "certification_signals": [],
                "review_signals": [],
                "data_basis": "not_checked",
                "source_ids": [],
                "evidence_ids": [],
                "takeaway": "",
            }
        )
    return {
        "template_type": "target_market_benchmark",
        "generated_at": today(),
        "scope": {
            "product": product,
            "target_market": market,
            "platform": platform,
            "category": category,
        },
        "purpose": "Find how similar products in the target market price, package, claim, certify, merchandise, and win buyer trust.",
        "collection_rules": [
            "Use 5-10 target-market products, not only global famous brands.",
            "Include direct substitutes and adjacent products that shape buyer expectations.",
            "Normalize pack size and unit price when price is available.",
            "Separate data_basis: current_checked, user_provided, assumption, or not_checked.",
            "Record visible compliance signals and claims instead of treating competitor copy as proof.",
        ],
        "market_benchmarks": rows,
        "summary_fields": {
            "reference_price_band": "",
            "channel_map": "",
            "packaging_conventions": "",
            "claims_and_proof": "",
            "visible_trust_signals": "",
            "review_themes": "",
            "gap_opportunity": "",
            "copy_avoid_improve": "",
            "listing_preparation": "",
            "verification_needed": "",
        },
    }


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _joined_text(values: list[Any]) -> str:
    return ", ".join(_text(value) for value in values if _text(value))


def _confidence(value: Any, default: str = "medium") -> str:
    text = _text(value).lower()
    return text if text in {"high", "medium", "low"} else default


def _risk_source_ids(sources: list[dict[str, Any]]) -> list[str]:
    return [str(source["source_id"]) for source in sources if source.get("source_id")]


def source_candidates_for_market(
    platform: str,
    origin_country: str,
    destination_market: str,
    category: str,
    user_search_channels: list[dict[str, Any]] | None = None,
    go_to_market_model: str = "unknown",
) -> list[dict[str, Any]]:
    pack_sources: list[dict[str, Any]] = []
    for pack in matching_rulepacks(platform, destination_market, category):
        pack_sources.extend(source for source in pack.get("sources", []) if isinstance(source, dict))

    def source_urls(*needles: str) -> list[str]:
        urls: list[str] = []
        lowered = [needle.lower() for needle in needles]
        for source in pack_sources:
            blob = " ".join(
                [
                    _text(source.get("source_id")),
                    _text(source.get("title")),
                    _text(source.get("confirms")),
                ]
            ).lower()
            if any(needle in blob for needle in lowered) and _text(source.get("url")):
                url = _text(source.get("url"))
                if url not in urls:
                    urls.append(url)
        return urls[:4]

    base = [
        {
            "channel_type": "platform_policy",
            "title": f"{platform or 'Marketplace'} official seller and category policy",
            "why": "Marketplace rules decide seller eligibility, restricted products, category gating, listing copy, and document submission.",
            "source_tier": "T1",
            "access_method": "official policy page, seller center, or authenticated seller workflow",
            "suggested_queries": [
                f"{platform} {destination_market} {category} seller requirements official",
                f"{platform} restricted products {category} official policy",
            ],
            "candidate_urls": source_urls("amazon", "tiktok", "temu", "shopee", "lazada", "aliexpress", "tmall"),
            "expected_facts": ["seller route", "category approval", "restricted products", "document requirements"],
            "freshness_days": 90,
        },
        {
            "channel_type": "destination_regulator",
            "title": f"{destination_market} product regulator for {category}",
            "why": "Destination regulators define admissibility, product safety, labeling, claims, notification, registration, and responsible entity duties.",
            "source_tier": "T1",
            "access_method": "official regulator site or registry",
            "suggested_queries": [
                f"{destination_market} {category} import registration labeling official regulator",
                f"{destination_market} {category} product safety claims official",
            ],
            "candidate_urls": source_urls("fda", "cpsc", "fcc", "commission", "hsa", "npra", "mhlw", "meti", "nmpa", "samr"),
            "expected_facts": ["classification", "required registrations", "label rules", "claims limits"],
            "freshness_days": 180,
        },
        {
            "channel_type": "customs_import",
            "title": f"{destination_market} customs and import route",
            "why": "Customs sources clarify importer of record, entry documents, admissibility, taxes, and import controls.",
            "source_tier": "T1",
            "access_method": "customs authority or government trade portal",
            "suggested_queries": [
                f"{destination_market} customs import {category} official",
                f"{destination_market} importer of record {category} official",
            ],
            "candidate_urls": source_urls("customs", "cbp", "gacc", "import"),
            "expected_facts": ["importer obligations", "customs documents", "admissibility", "tax/VAT route"],
            "freshness_days": 180,
        },
        {
            "channel_type": "brand_ip",
            "title": f"{destination_market} trademark and brand authorization route",
            "why": "Brand rights must cover territory, class, product scope, grantee, platform/channel, and validity period.",
            "source_tier": "T1",
            "access_method": "official trademark registry plus authorization chain review",
            "suggested_queries": [
                f"{destination_market} trademark search official",
                f"{platform} brand authorization {destination_market} official",
            ],
            "candidate_urls": source_urls("trademark", "wipo", "uspto", "euipo", "brand"),
            "expected_facts": ["owner", "class", "territory", "status", "expiry", "authorization scope"],
            "freshness_days": 365,
        },
        {
            "channel_type": "business_registry",
            "title": "Applicant, manufacturer, importer, and responsible-party registry checks",
            "why": "Entity names and roles must match documents, platform account, importer, rights holder, and certification holder.",
            "source_tier": "T1",
            "access_method": "official company registry, tax registry, or recognized LEI/company lookup",
            "suggested_queries": [
                f"{origin_country} company registry official",
                f"{destination_market} company registry importer official",
            ],
            "candidate_urls": source_urls("registry", "gleif", "company", "business"),
            "expected_facts": ["legal name", "status", "registered address", "business scope", "role relationship"],
            "freshness_days": 365,
        },
        {
            "channel_type": "certification_lab",
            "title": f"Certificate, issuer, lab, and accreditation checks for {category}",
            "why": "Certificates and reports need issuer validity, lab accreditation, product/model scope, site scope, standard, and expiry checks.",
            "source_tier": "T2",
            "access_method": "issuer lookup, accreditation body, certification body registry, or lab scope search",
            "suggested_queries": [
                f"{category} certificate verify issuer accreditation",
                f"{origin_country} lab accreditation scope {category}",
            ],
            "candidate_urls": source_urls("accreditation", "certificate", "lab", "standard", "iso", "haccp", "halal", "organic"),
            "expected_facts": ["issuer status", "accreditation scope", "standard", "product match", "expiry"],
            "freshness_days": 365,
        },
        {
            "channel_type": "standards_body",
            "title": f"Applicable standards and conformity route for {category}",
            "why": "Standards identify the correct test basis and conformity documents for regulated product families.",
            "source_tier": "T2",
            "access_method": "official standards body or regulator-referenced standards page",
            "suggested_queries": [
                f"{destination_market} {category} standard conformity official",
                f"{destination_market} {category} labeling standard official",
            ],
            "candidate_urls": source_urls("standard", "ce", "fcc", "ukca", "safety"),
            "expected_facts": ["applicable standard", "test basis", "technical file route", "label mark rules"],
            "freshness_days": 365,
        },
        {
            "channel_type": "logistics_warehouse",
            "title": f"{origin_country} to {destination_market} logistics, warehouse, and platform prep route",
            "why": "Freight, dangerous goods, warehouse acceptance, packaging tests, shelf-life, and local delivery affect launch viability.",
            "source_tier": "T3",
            "access_method": "forwarder quote, 3PL/warehouse rules, carrier dangerous-goods rules, platform fulfillment policy",
            "suggested_queries": [
                f"{platform} fulfillment prep {category} {destination_market} official",
                f"{origin_country} to {destination_market} freight {category} dangerous goods requirements",
            ],
            "candidate_urls": source_urls("fulfillment", "fba", "warehouse", "dangerous", "logistics"),
            "expected_facts": ["route constraints", "cost basis", "prep rules", "warehouse acceptance", "transit risk"],
            "freshness_days": 30,
        },
        {
            "channel_type": "origin_export_controls",
            "title": f"{origin_country} export, origin, and COO route",
            "why": "Origin-side checks clarify export controls, certificate of origin, manufacturer/exporter documents, and origin labeling consistency.",
            "source_tier": "T1",
            "access_method": "origin customs/export authority, trade portal, chamber of commerce, or exporter registry",
            "suggested_queries": [
                f"{origin_country} export {category} certificate of origin official",
                f"{origin_country} export controls {category} official",
            ],
            "candidate_urls": source_urls("export", "origin", "customs", "certificate of origin"),
            "expected_facts": ["export permissions", "COO route", "manufacturer/exporter identity", "origin label consistency"],
            "freshness_days": 180,
        },
    ]
    if go_to_market_model == "physical_trade":
        base = [item for item in base if item["channel_type"] != "platform_policy"]
    if go_to_market_model in {"physical_trade", "hybrid", "unknown"}:
        base.append(
            {
                "channel_type": "offline_channel",
                "title": f"{destination_market} importer, distributor, wholesale, retail, and offline shelf route",
                "why": "Physical trade needs a buyer/channel route, local responsibility split, shelf expectations, and offline admission constraints beyond marketplace rules.",
                "source_tier": "T3",
                "access_method": "importer/distributor brief, retail buyer checklist, trade association, wholesale marketplace, shelf audit, or user-provided channel",
                "suggested_queries": [
                    f"{destination_market} {category} importer distributor requirements",
                    f"{destination_market} {category} retail shelf imported product requirements",
                ],
                "candidate_urls": source_urls("retail", "distributor", "wholesale", "importer", "trade"),
                "expected_facts": ["offline channel requirements", "buyer documentation", "local responsibility", "shelf/packaging expectations"],
                "freshness_days": 90,
            }
        )
    candidates: list[dict[str, Any]] = []
    for idx, item in enumerate(base, start=1):
        candidates.append(
            {
                "source_candidate_id": f"SC-{destination_market.upper().replace(' ', '-')}-{idx:03d}",
                "origin_country": origin_country,
                "destination_market": destination_market,
                **item,
            }
        )
    for idx, raw in enumerate(user_search_channels or [], start=1):
        if not isinstance(raw, dict):
            continue
        applies_to = [_text(item).lower() for item in _as_list(raw.get("applies_to_markets")) if _text(item)]
        if applies_to and destination_market.lower() not in applies_to:
            continue
        channel_id = _text(raw.get("channel_id")) or f"USER-SC-{destination_market.upper().replace(' ', '-')}-{idx:03d}"
        candidates.append(
            {
                "source_candidate_id": channel_id,
                "origin_country": origin_country,
                "destination_market": destination_market,
                "channel_type": _text(raw.get("channel_type")) or "user_search_channel",
                "title": _text(raw.get("title")) or f"User-provided search channel {idx}",
                "why": _text(raw.get("why")) or "User-provided channel can add current market, platform, competitor, supplier, logistics, or registry signals.",
                "source_tier": _text(raw.get("source_tier")) or "T4",
                "access_method": _text(raw.get("access_method")) or "user-provided search channel",
                "suggested_queries": [_text(item) for item in _as_list(raw.get("suggested_queries")) if _text(item)],
                "candidate_urls": [_text(raw.get("url"))] if _text(raw.get("url")) else [_text(item) for item in _as_list(raw.get("candidate_urls")) if _text(item)],
                "expected_facts": [_text(item) for item in _as_list(raw.get("expected_facts")) if _text(item)] or ["current market signal", "source URL", "checked date"],
                "freshness_days": raw.get("freshness_days") if isinstance(raw.get("freshness_days"), int) else 30,
            }
        )
    return candidates


def research_tasks_for_market(
    platform: str,
    origin_country: str,
    destination_market: str,
    category: str,
    source_candidates: list[dict[str, Any]],
    go_to_market_model: str = "unknown",
) -> list[dict[str, Any]]:
    task_specs = []
    if go_to_market_model != "physical_trade":
        task_specs.append(("verify-platform-category-policy", "platform_policy", "Verify platform seller route, restricted product status, category approval, listing-copy limits, and required documents.", "P0"))
    task_specs.extend([
        ("verify-destination-regulator-route", "destination_regulator", "Verify product classification, regulator, registration/notification, label language, warnings, and claim limits.", "P0"),
        ("verify-destination-import-route", "customs_import", "Verify importer of record, customs documents, admissibility, tax/VAT route, and import controls.", "P0"),
        ("verify-brand-ip-territory", "brand_ip", "Verify trademark owner, class, territory, status, expiry, and authorization coverage for platform/channel/product.", "P0"),
        ("verify-entity-chain", "business_registry", "Verify applicant, manufacturer, importer, responsible party, rights holder, and certificate holder identity chain.", "P1"),
        ("verify-certificate-issuer-scope", "certification_lab", "Verify issuer/lab/accreditation status, standard, model/SKU/product scope, site scope, and expiry.", "P0"),
        ("verify-standards-route", "standards_body", "Verify applicable standards, conformity route, technical-file basis, and allowed marks.", "P1"),
        ("verify-logistics-route", "logistics_warehouse", "Verify freight constraints, dangerous goods, warehouse acceptance, platform prep, cost basis, and route timing.", "P1"),
        ("verify-origin-export-route", "origin_export_controls", "Verify export permissions, certificate of origin, manufacturer/exporter documents, and origin label consistency.", "P0"),
    ])
    if go_to_market_model in {"physical_trade", "hybrid", "unknown"}:
        task_specs.append(("verify-offline-channel-route", "offline_channel", "Verify importer/distributor/retail channel requirements, buyer documents, local responsibility split, and offline shelf expectations.", "P0" if go_to_market_model == "physical_trade" else "P1"))
    candidate_by_type = {candidate["channel_type"]: candidate for candidate in source_candidates}
    tasks: list[dict[str, Any]] = []
    for idx, (task_key, channel_type, instruction, priority) in enumerate(task_specs, start=1):
        candidate = candidate_by_type.get(channel_type, {})
        tasks.append(
            {
                "research_task_id": f"RT-{destination_market.upper().replace(' ', '-')}-{idx:03d}",
                "task_key": task_key,
                "priority": priority,
                "channel_type": channel_type,
                "source_candidate_ids": [candidate["source_candidate_id"]] if candidate else [],
                "origin_country": origin_country,
                "destination_market": destination_market,
                "platform": platform,
                "category": category,
                "instruction": instruction,
                "recommended_tier": candidate.get("source_tier", "T1"),
                "freshness_days": candidate.get("freshness_days", 180),
                "evidence_fields": candidate.get("expected_facts", []),
                "status": "needs_external_verification",
            }
        )
    standard_types = {channel_type for _, channel_type, _, _ in task_specs}
    for candidate in source_candidates:
        if candidate.get("channel_type") in standard_types:
            continue
        tasks.append(
            {
                "research_task_id": f"RT-{destination_market.upper().replace(' ', '-')}-{len(tasks) + 1:03d}",
                "task_key": "verify-user-search-channel",
                "priority": "P1",
                "channel_type": candidate.get("channel_type", "user_search_channel"),
                "source_candidate_ids": [candidate.get("source_candidate_id")],
                "origin_country": origin_country,
                "destination_market": destination_market,
                "platform": platform,
                "category": category,
                "instruction": f"Use user-provided channel '{candidate.get('title')}' to collect current signals, then record URL, checked date, extracted facts, confidence, and whether the source directly confirms the claim.",
                "recommended_tier": candidate.get("source_tier", "T4"),
                "freshness_days": candidate.get("freshness_days", 30),
                "evidence_fields": candidate.get("expected_facts", []),
                "status": "needs_external_verification",
            }
        )
    return tasks


def build_market_review(
    platform: str,
    origin_country: str,
    destination_market: str,
    category: str,
    case: dict[str, Any],
    user_search_channels: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    skeleton = review_skeleton(
        platform=platform,
        market=destination_market,
        category=category,
        applicant_name=_text(case.get("applicant_name")),
        applicant_role=_text(case.get("applicant_role")),
        business_model=_text(case.get("business_model")),
        brand_name=_text(case.get("brand_name")),
        purpose=_text(case.get("review_purpose")) or "launch readiness and qualification intake",
        case_id=f"{_text(case.get('case_id')) or 'case'}-{destination_market.lower().replace(' ', '-')}",
        marketplace_site=destination_market,
    )
    go_to_market_model = normalize_go_to_market_model(case)
    candidates = source_candidates_for_market(platform, origin_country, destination_market, category, user_search_channels, go_to_market_model)
    tasks = research_tasks_for_market(platform, origin_country, destination_market, category, candidates, go_to_market_model)
    return {
        "destination_market": destination_market,
        "origin_country": origin_country,
        "matched_packs": [
            str(pack.get("pack_id"))
            for pack in matching_rulepacks(platform, destination_market, category)
        ],
        "decision": skeleton.get("decision", {}),
        "requirements": skeleton.get("requirements", []),
        "findings": skeleton.get("findings", []),
        "missing_materials": skeleton.get("missing_materials", []),
        "source_candidates": candidates,
        "research_tasks": tasks,
    }


def normalize_bundle_source(raw: dict[str, Any], idx: int) -> dict[str, Any]:
    source_id = _text(raw.get("source_id")) or f"src-offline-{idx:03d}"
    tier = _text(raw.get("tier")) or "T4"
    if tier not in ALLOWED_TIERS:
        tier = "T4"
    return {
        "source_id": source_id,
        "title": _text(raw.get("title")) or f"Offline user-provided source {idx}",
        "url": _text(raw.get("url")),
        "tier": tier,
        "checked_at": _text(raw.get("checked_at")) or today(),
        "confirms": _text(raw.get("confirms")) or "User-provided offline source; external verification not completed.",
    }


def normalize_bundle_document(raw: dict[str, Any], idx: int) -> dict[str, Any]:
    doc_id = _text(raw.get("document_id")) or f"doc-offline-{idx:03d}"
    return {
        "document_id": doc_id,
        "document_type": _text(raw.get("document_type")) or "offline document",
        "file_reference": _text(raw.get("file_reference")) or doc_id,
        "holder": _text(raw.get("holder")),
        "issuer": _text(raw.get("issuer")),
        "number_redacted": _text(raw.get("number_redacted")),
        "issue_date": _text(raw.get("issue_date")),
        "expiry_date": _text(raw.get("expiry_date")),
        "scope": _text(raw.get("scope")),
        "extraction_confidence": _confidence(raw.get("extraction_confidence")),
        "privacy_level": _text(raw.get("privacy_level")) or "business_confidential",
    }


def _document_evidence(document: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    parts = [
        f"type={document.get('document_type', '')}",
        f"holder={document.get('holder', '')}",
        f"issuer={document.get('issuer', '')}",
        f"scope={document.get('scope', '')}",
        f"expiry={document.get('expiry_date', '')}",
    ]
    return {
        "evidence_id": f"ev-{document['document_id']}",
        "kind": "submitted_document",
        "reference": document.get("file_reference", ""),
        "tier": "T4",
        "checked_at": _text(raw.get("checked_at")) or today(),
        "extracted_fact": "; ".join(part for part in parts if not part.endswith("=")),
        "confidence": document.get("extraction_confidence", "medium"),
    }


def build_document_findings(
    bundle: dict[str, Any],
    documents: list[dict[str, Any]],
    source_ids: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    case = bundle.get("case") if isinstance(bundle.get("case"), dict) else {}
    raw_docs = [item for item in bundle.get("documents") or [] if isinstance(item, dict)]
    findings: list[dict[str, Any]] = []
    missing_materials: list[dict[str, Any]] = []
    applicant_name = _text(case.get("applicant_name")).lower()
    destination = _text(case.get("destination_market")).lower()
    platform = _text(case.get("platform")).lower()
    category = _text(case.get("product_category")).lower()
    brand_name = _text(case.get("brand_name")).lower()

    def add_finding(
        severity: str,
        requirement: str,
        submitted: str,
        issue: str,
        action: str,
        acceptable: str,
        material: str,
        priority: str,
    ) -> None:
        findings.append(
            {
                "finding_id": f"OFF-DOC-{len(findings) + 1:03d}",
                "severity": severity,
                "surface": "certificate",
                "requirement": requirement,
                "submitted_evidence": submitted,
                "observed_issue": issue,
                "business_impact": "Platform/category review can be delayed or rejected until the evidence is corrected or externally verified.",
                "decision_effect": "escalate_human" if severity == "critical" else "request_more_info",
                "required_action": action,
                "acceptable_evidence": acceptable,
                "source_ids": source_ids,
                "confidence": "high" if severity in {"critical", "high"} else "medium",
            }
        )
        missing_materials.append(
            {
                "material": material,
                "why_required": issue,
                "acceptable_replacement": acceptable,
                "owner": "applicant / reviewer",
                "priority": priority,
            }
        )

    for idx, document in enumerate(documents):
        raw = raw_docs[idx] if idx < len(raw_docs) else {}
        submitted = f"{document.get('document_type', '')}: {document.get('file_reference', '')}"
        expiry = parse_date(document.get("expiry_date"))
        if expiry is not None and expiry < _dt.date.today():
            add_finding(
                "high",
                "Submitted qualification documents must be valid on the review date.",
                submitted,
                f"{document.get('document_type')} expired on {document.get('expiry_date')}.",
                "Provide a renewed certificate/report or official issuer confirmation showing current validity.",
                "Current certificate/report with holder, issuer, scope, and validity matching this product and market.",
                f"Renewed {document.get('document_type')}",
                "P0",
            )
        holder = _text(document.get("holder")).lower()
        if applicant_name and holder and applicant_name not in holder and holder not in applicant_name:
            add_finding(
                "high",
                "Document holder must match the applicant or an explainable authorization chain.",
                submitted,
                f"Holder '{document.get('holder')}' does not match applicant '{case.get('applicant_name')}'.",
                "Provide entity relationship evidence or a corrected document naming the applicant.",
                "Business registration, authorization chain, or corrected certificate naming the applicant.",
                "Entity relationship evidence",
                "P0",
            )
        if document.get("extraction_confidence") == "low":
            add_finding(
                "medium",
                "Low-confidence extracted document fields must be rechecked before decision.",
                submitted,
                "Document extraction confidence is low.",
                "Re-upload a clearer document or manually confirm holder, issuer, dates, and scope.",
                "Clear source file or manual extraction record with reviewer confirmation.",
                "Clearer document image or confirmed extraction",
                "P1",
            )
        if raw.get("suspected_forgery") is True:
            add_finding(
                "critical",
                "Suspected forged materials require human escalation.",
                submitted,
                "The submitted document is marked as suspected forgery in the offline bundle.",
                "Escalate to human review and verify directly with issuer or registry.",
                "Issuer or registry confirmation and internal human review notes.",
                "Issuer verification for suspected forged document",
                "P0",
            )
        document_type = _text(document.get("document_type")).lower()
        scope_blob = " ".join(
            _text(raw.get(key)).lower()
            for key in ("scope", "territory", "platform_scope", "brand_scope", "product_scope")
        )
        if "brand authorization" in document_type:
            if destination and destination not in scope_blob and "us" in destination and "united states" not in scope_blob:
                add_finding(
                    "high",
                    "Brand authorization must cover the target territory.",
                    submitted,
                    "Brand authorization does not cover the US target territory.",
                    "Provide authorization covering the destination market.",
                    "Brand authorization letter naming the grantee, territory, product scope, validity, and grantor authority.",
                    "US territory brand authorization",
                    "P0",
                )
            if platform and platform not in scope_blob:
                add_finding(
                    "high",
                    "Brand authorization must cover the target platform or channel.",
                    submitted,
                    f"Brand authorization does not mention {case.get('platform')}.",
                    "Provide authorization covering the marketplace or online channel used for launch.",
                    "Brand authorization covering the named marketplace or sufficiently broad online sales channel.",
                    "Platform/channel brand authorization",
                    "P0",
                )
            if brand_name and brand_name not in scope_blob:
                add_finding(
                    "medium",
                    "Brand authorization should identify the reviewed brand.",
                    submitted,
                    f"Brand authorization scope does not clearly identify brand '{case.get('brand_name')}'.",
                    "Provide corrected authorization that identifies the brand and product family.",
                    "Corrected brand authorization naming the brand and product scope.",
                    "Brand-specific authorization",
                    "P1",
                )
        if category and document.get("scope") and category not in _text(document.get("scope")).lower():
            add_finding(
                "medium",
                "Document scope should match the reviewed product category.",
                submitted,
                f"Document scope does not clearly mention category '{case.get('product_category')}'.",
                "Confirm the document covers the reviewed product category and SKU.",
                "Scope page, product annex, model/SKU list, or issuer confirmation.",
                "Product/category scope evidence",
                "P1",
            )

    return findings, missing_materials


def build_market_benchmarks(
    bundle: dict[str, Any],
    source_ids: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    case = bundle.get("case") if isinstance(bundle.get("case"), dict) else {}
    rows: list[dict[str, Any]] = []
    assumptions: list[dict[str, Any]] = []
    benchmark_inputs = bundle.get("benchmarks")
    if not isinstance(benchmark_inputs, list):
        benchmark_inputs = bundle.get("competitors") or []
    for idx, raw in enumerate(benchmark_inputs, start=1):
        if not isinstance(raw, dict):
            continue
        data_basis = _text(raw.get("data_basis")) or "user_provided"
        if data_basis not in ALLOWED_BENCHMARK_BASIS:
            data_basis = "user_provided"
        channel_role = _text(raw.get("channel_role")) or "other"
        if channel_role not in ALLOWED_CHANNEL_ROLES:
            channel_role = "other"
        positioning = _text(raw.get("positioning")) or "unknown"
        if positioning not in ALLOWED_POSITIONING:
            positioning = "unknown"
        rows.append(
            {
                "benchmark_id": _text(raw.get("benchmark_id")) or f"BM-{idx:03d}",
                "product_name": _text(raw.get("product_name")) or f"Unnamed benchmark {idx}",
                "channel": _text(raw.get("channel")) or "user-provided channel",
                "channel_role": channel_role,
                "market": _text(raw.get("market")) or _text(case.get("destination_market")),
                "pack_size": _text(raw.get("pack_size")),
                "price": _text(raw.get("price")),
                "unit_price": _text(raw.get("unit_price")),
                "positioning": positioning,
                "visible_claims": [_text(item) for item in _as_list(raw.get("visible_claims")) if _text(item)],
                "packaging_signals": [_text(item) for item in _as_list(raw.get("packaging_signals")) if _text(item)],
                "certification_signals": [_text(item) for item in _as_list(raw.get("certification_signals")) if _text(item)],
                "review_signals": [_text(item) for item in _as_list(raw.get("review_signals")) if _text(item)],
                "data_basis": data_basis,
                "source_ids": [sid for sid in _as_list(raw.get("source_ids")) if _text(sid)] or source_ids,
                "evidence_ids": [],
                "takeaway": _text(raw.get("takeaway")) or "Use as a directional offline benchmark; verify current price and listing details before final action.",
            }
        )
    if not rows:
        assumptions.append(
            {
                "material": "Target-market benchmark products",
                "why_required": "Launch readiness needs local price, packaging, channel, and trust-signal references.",
                "acceptable_replacement": "5-10 current marketplace, retail, DTC, or user-provided benchmark rows with source basis.",
                "owner": "reviewer / user",
                "priority": "P1",
            }
        )
    prices = [_text(row.get("unit_price") or row.get("price")) for row in rows if _text(row.get("unit_price") or row.get("price"))]
    channels = sorted({_text(row.get("channel")) for row in rows if _text(row.get("channel"))})
    claims = sorted({claim for row in rows for claim in row.get("visible_claims", [])})
    packaging = sorted({signal for row in rows for signal in row.get("packaging_signals", [])})
    trust = sorted({signal for row in rows for signal in row.get("certification_signals", [])})
    reviews = sorted({signal for row in rows for signal in row.get("review_signals", [])})
    positions = sorted({_text(row.get("positioning")) for row in rows if _text(row.get("positioning")) and row.get("positioning") != "unknown"})
    summary = {
        "reference_price_band": "; ".join(prices) if prices else "No price basis supplied; verify current target-market prices.",
        "channel_map": ", ".join(channels) if channels else "No channel basis supplied.",
        "packaging_conventions": ", ".join(packaging) if packaging else "No packaging benchmark signals supplied.",
        "claims_and_proof": ", ".join(claims) if claims else "No competitor claim signals supplied.",
        "visible_trust_signals": ", ".join(trust) if trust else "No visible certification or trust signals supplied.",
        "review_themes": ", ".join(reviews) if reviews else "No review signals supplied.",
        "gap_opportunity": f"Position against observed tiers: {', '.join(positions)}." if positions else "Positioning cannot be assessed until benchmarks are verified.",
        "copy_avoid_improve": "Copy clear local pack-size and channel cues; avoid unverified regulated claims; improve proof for premium pricing.",
        "listing_preparation": "Verify current prices, source URLs, label requirements, brand authorization, and food/category documents before ordering, printing, or listing.",
        "verification_needed": "Competitor rows are offline/user-provided unless marked current_checked; recheck current prices, claims, review counts, and certifications.",
    }
    return rows, summary, assumptions


REGULATED_CLAIM_TERMS = {
    "cure",
    "treat",
    "treatment",
    "prevent",
    "disease",
    "immune",
    "medical",
    "fda approved",
    "spf",
    "organic",
    "antimicrobial",
    "hypoallergenic",
    "child safe",
    "ce",
    "fcc",
}


def regulated_claim_terms_in_text(text: str) -> list[str]:
    lowered = text.lower()
    matches: list[str] = []
    for term in sorted(REGULATED_CLAIM_TERMS):
        pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            matches.append(term)
    return matches


def build_packaging_findings(
    bundle: dict[str, Any],
    source_ids: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    packaging = bundle.get("packaging") if isinstance(bundle.get("packaging"), dict) else {}
    case = bundle.get("case") if isinstance(bundle.get("case"), dict) else {}
    findings: list[dict[str, Any]] = []
    missing_materials: list[dict[str, Any]] = []
    text_blob = " ".join(
        [
            _text(packaging.get("front_label")),
            _text(packaging.get("back_label")),
            _joined_text(_as_list(packaging.get("claims"))),
            _joined_text(_as_list(packaging.get("visible_certification_marks"))),
        ]
    ).lower()
    claims = [_text(item) for item in _as_list(packaging.get("claims")) if _text(item)]
    marks = [_text(item) for item in _as_list(packaging.get("visible_certification_marks")) if _text(item)]
    warnings = [_text(item) for item in _as_list(packaging.get("warnings")) if _text(item)]

    def add_packaging_finding(severity: str, issue: str, action: str, material: str, priority: str) -> None:
        findings.append(
            {
                "finding_id": f"OFF-PACK-{len(findings) + 1:03d}",
                "severity": severity,
                "surface": "product_category",
                "requirement": "Packaging labels and listing claims must be supportable for the target market and category.",
                "submitted_evidence": "Offline packaging text supplied by user.",
                "observed_issue": issue,
                "business_impact": "Packaging may need revision before printing or platform listing submission.",
                "decision_effect": "request_more_info",
                "required_action": action,
                "acceptable_evidence": "Revised label/listing copy plus substantiation or official confirmation for regulated claims and marks.",
                "source_ids": source_ids,
                "confidence": "medium",
            }
        )
        missing_materials.append(
            {
                "material": material,
                "why_required": issue,
                "acceptable_replacement": "Revised packaging text or substantiation evidence reviewed against current official requirements.",
                "owner": "applicant / packaging reviewer",
                "priority": priority,
            }
        )

    matched_terms = regulated_claim_terms_in_text(text_blob)
    if matched_terms:
        add_packaging_finding(
            "high" if any(term in {"fda approved", "immune", "cure", "treat", "disease"} for term in matched_terms) else "medium",
            f"Packaging or listing text includes regulated claim/mark terms: {', '.join(matched_terms)}.",
            "Remove, revise, or substantiate regulated claims before printing or listing.",
            "Claim substantiation and revised label/listing copy",
            "P0",
        )
    if marks:
        add_packaging_finding(
            "medium",
            f"Visible certification/regulator marks need evidence: {', '.join(marks)}.",
            "Match every visible mark to a valid certificate, registration, or allowed-use basis.",
            "Certification mark support evidence",
            "P1",
        )
    category = _text(case.get("product_category")).lower()
    ingredient_text = _joined_text(_as_list(packaging.get("ingredients_or_materials"))).lower()
    if category == "food":
        allergens = [item for item in ("peanut", "sesame", "soy", "milk", "egg", "wheat", "fish", "shellfish", "tree nut") if item in ingredient_text]
        if allergens and not warnings:
            add_packaging_finding(
                "medium",
                f"Food ingredients include allergen signals ({', '.join(allergens)}) but warning/allergen statement is missing from the bundle.",
                "Confirm required allergen declaration and warning language for the target market.",
                "Allergen declaration review",
                "P1",
            )
    language_list = [_text(item).lower() for item in _as_list(packaging.get("languages"))]
    if _text(case.get("destination_market")).lower() in {"us", "usa", "united states"} and "english" not in language_list:
        add_packaging_finding(
            "medium",
            "US launch bundle does not show English label language.",
            "Provide English packaging and listing copy for review.",
            "English label/listing copy",
            "P1",
        )
    if not claims and not packaging:
        add_packaging_finding(
            "medium",
            "No packaging or claim text was supplied.",
            "Provide front label, back label, claims, ingredients/materials, warnings, languages, and visible marks.",
            "Packaging transcription or images",
            "P1",
        )

    return findings, missing_materials


def build_logistics_findings(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rows = [item for item in bundle.get("logistics") or [] if isinstance(item, dict)]
    findings: list[dict[str, Any]] = []
    missing_materials: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    risk_terms = {"battery", "liquid", "aerosol", "food", "cold chain", "dangerous goods", "fragile", "glass", "high value", "leakage"}
    for idx, row in enumerate(rows, start=1):
        constraints = [_text(item) for item in _as_list(row.get("constraints")) if _text(item)]
        risks = [_text(item) for item in _as_list(row.get("risks")) if _text(item)]
        prep = [_text(item) for item in _as_list(row.get("preparation")) if _text(item)]
        normalized.append(
            {
                "route_id": _text(row.get("route_id")) or f"LOG-{idx:03d}",
                "route": _text(row.get("route")) or _text(row.get("mode")) or "offline logistics route",
                "mode": _text(row.get("mode")),
                "time": _text(row.get("time")),
                "cost_basis": _text(row.get("cost_basis")) or "not_checked",
                "best_for": _text(row.get("best_for")),
                "constraints": constraints,
                "risks": risks,
                "preparation": prep,
                "data_basis": _text(row.get("data_basis")) or "user_provided",
            }
        )
        blob = " ".join(constraints + risks).lower()
        matched = sorted(term for term in risk_terms if term in blob)
        if matched:
            findings.append(
                {
                    "finding_id": f"OFF-LOG-{len(findings) + 1:03d}",
                    "severity": "medium",
                    "surface": "market_import",
                    "requirement": "Logistics route must match product constraints, cost basis, and import/warehouse requirements.",
                    "submitted_evidence": _text(row.get("route")) or f"logistics row {idx}",
                    "observed_issue": f"Route has category/logistics risk signals: {', '.join(matched)}.",
                    "business_impact": "Freight, customs, warehouse, damage, or margin assumptions may fail without route confirmation.",
                    "decision_effect": "request_more_info",
                    "required_action": "Confirm route constraints with freight forwarder, warehouse, platform prep rules, and import route before inventory commitment.",
                    "acceptable_evidence": "Current logistics quotation, route constraints, packaging test, warehouse acceptance, and import/customs preparation notes.",
                    "source_ids": [],
                    "confidence": "medium",
                }
            )
    if not rows:
        missing_materials.append(
            {
                "material": "Logistics route and budget basis",
                "why_required": "Launch readiness cannot assess margin and inventory risk without route, cost driver, time, and constraints.",
                "acceptable_replacement": "Forwarder quotation, 3PL estimate, or user-provided route comparison clearly marked as not externally verified.",
                "owner": "applicant / logistics reviewer",
                "priority": "P1",
            }
        )
    return normalized, findings, missing_materials


def build_go_to_market_findings(
    bundle: dict[str, Any],
    source_ids: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    case = bundle.get("case") if isinstance(bundle.get("case"), dict) else {}
    packaging = bundle.get("packaging") if isinstance(bundle.get("packaging"), dict) else {}
    model = normalize_go_to_market_model(case)
    destination_markets = [item.lower() for item in normalize_destination_markets(case, allow_legacy=True)]
    category = _text(case.get("product_category")).lower()
    if model not in {"physical_trade", "hybrid"}:
        return [], []

    findings: list[dict[str, Any]] = []
    missing_materials: list[dict[str, Any]] = []

    def add_route_finding(issue: str, action: str, material: str, priority: str = "P0", severity: str = "high") -> None:
        findings.append(
            {
                "finding_id": f"OFF-GTM-{len(findings) + 1:03d}",
                "severity": severity,
                "surface": "market_import",
                "requirement": "Physical trade route must satisfy destination import, label, responsible-party, and customs requirements before shipment.",
                "submitted_evidence": "User-provided physical trade case bundle.",
                "observed_issue": issue,
                "business_impact": "Inventory can be delayed, relabeled, rejected, or held at customs if import route evidence is incomplete.",
                "decision_effect": "request_more_info",
                "required_action": action,
                "acceptable_evidence": "Current official import requirements, importer/responsible-party records, compliant local label artwork, customs document set, and logistics route confirmation.",
                "source_ids": source_ids,
                "confidence": "medium",
            }
        )
        missing_materials.append(
            {
                "material": material,
                "why_required": issue,
                "acceptable_replacement": "Official/current import route confirmation plus matching product, label, and shipment documents.",
                "owner": "importer / distributor / reviewer",
                "priority": priority,
            }
        )

    if "china" in destination_markets and category == "food":
        languages = {_text(item).lower() for item in _as_list(packaging.get("languages"))}
        if not {"chinese", "simplified chinese", "zh", "中文"}.intersection(languages):
            add_route_finding(
                "Chinese label basis is missing for China food import; visible packaging languages are not enough for local sale.",
                "Prepare or verify compliant Chinese label artwork before shipment, including product name, ingredients, net content, origin, importer/distributor, nutrition, date/lot, storage, and required standard markings.",
                "China-compliant Chinese label artwork and label review",
            )
        add_route_finding(
            "China food import route is not evidenced yet; importer, customs, inspection, label filing/review, and product document set are not confirmed.",
            "Confirm the China food import route with importer/customs broker and collect the required customs, inspection, invoice/packing, contract, origin, health/sanitary, and label materials before booking shipment.",
            "China food import document set and importer/customs route confirmation",
        )
        label_blob = " ".join(
            [
                _text(packaging.get("front_label")),
                _text(packaging.get("back_label")),
                _joined_text(_as_list(packaging.get("claims"))),
            ]
        ).lower()
        if "european union origin and not of european union origin" in label_blob or "eu and non-eu" in label_blob:
            add_route_finding(
                "EU and non-EU olive oil origin wording may not be sufficient for China import origin, COO, and Chinese label claims without supporting documents.",
                "Verify certificate of origin, manufacturer/exporter documents, ingredient/origin statement, and Chinese label origin wording before using Italy/EU origin cues in import materials.",
                "Certificate of origin and origin-claim support documents",
                priority="P1",
                severity="medium",
            )

    return findings, missing_materials


def choose_launch_decision(
    findings: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
    market_benchmarks: list[dict[str, Any]],
    logistics_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    severities = {finding.get("severity") for finding in findings if isinstance(finding, dict)}
    requirement_statuses = {req.get("status") for req in requirements if isinstance(req, dict)}
    if "critical" in severities:
        status = "escalate_human"
        risk_level = "critical"
        risk_score = 90
        summary = "Human escalation required because a critical blocker was detected in the offline bundle."
    elif "high" in severities or {"missing", "invalid", "needs_external_verification"}.intersection(requirement_statuses):
        status = "request_more_info"
        risk_level = "high"
        risk_score = 60
        summary = "Launch readiness is blocked until missing, expired, mismatched, or externally unverified evidence is resolved."
    elif "medium" in severities or not market_benchmarks or not logistics_rows:
        status = "conditional_approve"
        risk_level = "medium"
        risk_score = 35
        summary = "Launch may continue only after bounded packaging, benchmark, logistics, and verification actions are completed."
    else:
        status = "approve"
        risk_level = "low"
        risk_score = 10
        summary = "Offline bundle shows no material blocker, but current official sources should still be checked before final enforcement."
    return {
        "status": status,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary,
        "rationale": [
            "Offline launch report generated from user-provided bundle data.",
            "User-provided documents and screenshots are T4 evidence until independently verified.",
            "Current platform, regulator, registry, competitor price, and logistics facts require source checks before final action.",
        ],
    }


def go_to_market_route_profile(model: str) -> dict[str, Any]:
    profiles = {
        "cross_border_ecommerce": {
            "model": "cross_border_ecommerce",
            "label": "cross border ecommerce",
            "primary_checks": [
                "marketplace listing and category gating",
                "platform restricted-products policy",
                "brand authorization and IP coverage",
                "listing claims, packaging, and label readiness",
                "fulfillment, warehouse, and return route",
            ],
            "benchmark_focus": [
                "marketplace search results",
                "platform best sellers",
                "listing copy and claims",
                "visible trust signals",
                "review themes and price bands",
            ],
        },
        "physical_trade": {
            "model": "physical_trade",
            "label": "physical trade",
            "primary_checks": [
                "destination import and customs",
                "origin export controls and certificate of origin",
                "importer or responsible-party obligations",
                "local label, registration, and retail/distributor channel requirements",
                "Incoterms, freight, tax, warehouse, and insurance route",
            ],
            "benchmark_focus": [
                "local retail shelf and distributor channels",
                "imported substitute products",
                "wholesale and landed-cost references",
                "packaging language and responsibility marks",
                "certification signals visible in offline channels",
            ],
        },
        "hybrid": {
            "model": "hybrid",
            "label": "hybrid ecommerce and physical trade",
            "primary_checks": [
                "marketplace listing and category gating",
                "destination import and customs",
                "brand authorization and IP coverage",
                "local importer, responsible party, warehouse, and fulfillment obligations",
                "listing, packaging, label, and offline channel readiness",
            ],
            "benchmark_focus": [
                "marketplace best sellers",
                "offline retail shelf references",
                "DTC/social commerce examples",
                "landed cost and unit price bands",
                "online and offline packaging conventions",
            ],
        },
        "unknown": {
            "model": "unknown",
            "label": "unknown route",
            "primary_checks": [
                "confirm whether the route is cross-border ecommerce, physical trade, or hybrid",
                "destination import and customs",
                "marketplace or offline channel admission",
                "brand authorization and product qualification",
                "packaging, claims, logistics, and landed-cost basis",
            ],
            "benchmark_focus": [
                "candidate online channels",
                "candidate offline channels",
                "local substitute products",
                "price and packaging references",
                "signals that clarify the actual sales route",
            ],
        },
    }
    return profiles.get(model, profiles["unknown"])


def launch_report_from_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    case = bundle.get("case") if isinstance(bundle.get("case"), dict) else {}
    platform = _text(case.get("platform"))
    origin_country = _text(case.get("origin_country"))
    go_to_market_model = normalize_go_to_market_model(case)
    destination_markets = normalize_destination_markets(case, allow_legacy=True)
    market = destination_markets[0] if destination_markets else _text(case.get("destination_market"))
    category = _text(case.get("product_category"))
    report = review_skeleton(
        platform=platform,
        market=market,
        category=category,
        applicant_name=_text(case.get("applicant_name")),
        applicant_role=_text(case.get("applicant_role")),
        business_model=_text(case.get("business_model")),
        brand_name=_text(case.get("brand_name")),
        purpose=_text(case.get("review_purpose")) or "launch readiness and qualification intake",
        case_id=_text(case.get("case_id")),
        marketplace_site=_text(case.get("marketplace_site")),
    )
    report["case"].update(
        {
            "case_id": _text(case.get("case_id")) or report["case"]["case_id"],
            "applicant_name": _text(case.get("applicant_name")),
            "applicant_role": _text(case.get("applicant_role")),
            "origin_country": origin_country,
            "platform": platform,
            "marketplace_site": _text(case.get("marketplace_site")) or market,
            "destination_market": market,
            "destination_markets": destination_markets or ([market] if market else []),
            "go_to_market_model": go_to_market_model,
            "business_model": _text(case.get("business_model")),
            "product_category": category,
            "subcategory": _text(case.get("subcategory")),
            "product_name": _text(case.get("product_name")),
            "brand_name": _text(case.get("brand_name")),
            "review_purpose": _text(case.get("review_purpose")) or "launch readiness and qualification intake",
            "requested_decision_deadline": _text(case.get("requested_decision_deadline")),
            "review_date": _text(case.get("review_date")) or today(),
        }
    )

    bundle_sources = [
        normalize_bundle_source(raw, idx)
        for idx, raw in enumerate(bundle.get("sources") or [], start=1)
        if isinstance(raw, dict)
    ]
    declared_source_ids = {source.get("source_id") for source in report.get("sources", []) if isinstance(source, dict)}
    for source in bundle_sources:
        if source["source_id"] not in declared_source_ids:
            report["sources"].append(source)
            declared_source_ids.add(source["source_id"])
    offline_source_ids = _risk_source_ids(bundle_sources)

    raw_docs = [item for item in bundle.get("documents") or [] if isinstance(item, dict)]
    documents = [normalize_bundle_document(raw, idx) for idx, raw in enumerate(raw_docs, start=1)]
    report["documents"] = documents
    for raw, document in zip(raw_docs, documents):
        report["evidence"].append(_document_evidence(document, raw))

    benchmark_rows, benchmark_summary, benchmark_missing = build_market_benchmarks(bundle, offline_source_ids)
    report["market_benchmarks"] = benchmark_rows
    report["market_benchmark_summary"] = benchmark_summary

    document_findings, document_missing = build_document_findings(bundle, documents, offline_source_ids)
    packaging_findings, packaging_missing = build_packaging_findings(bundle, offline_source_ids)
    logistics_rows, logistics_findings, logistics_missing = build_logistics_findings(bundle)
    route_findings, route_missing = build_go_to_market_findings(bundle, offline_source_ids)

    external_requirement = {
        "requirement_id": "offline-current-source-verification",
        "surface": "platform_listing",
        "requirement": "Current platform, regulator, registry, competitor price, logistics, origin/export, and destination/import facts must be externally verified before final launch action.",
        "status": "needs_external_verification",
        "matched_evidence_ids": [],
        "source_ids": offline_source_ids,
        "notes": "Offline bundle facts are useful for intake and routing but do not replace current T1/T2 source checks.",
    }
    report["requirements"].append(external_requirement)
    market_reviews = [
        build_market_review(
            platform,
            origin_country,
            destination,
            category,
            report["case"],
            [item for item in bundle.get("user_search_channels") or [] if isinstance(item, dict)],
        )
        for destination in (destination_markets or ([market] if market else []))
    ]
    report["market_reviews"] = market_reviews
    report["source_candidates"] = [
        candidate
        for market_review in market_reviews
        for candidate in market_review.get("source_candidates", [])
    ]
    report["research_tasks"] = [
        task
        for market_review in market_reviews
        for task in market_review.get("research_tasks", [])
    ]

    existing_count = len(report["findings"])
    for idx, finding in enumerate(route_findings + document_findings + packaging_findings + logistics_findings, start=existing_count + 1):
        finding["finding_id"] = finding.get("finding_id") or f"OFF-{idx:03d}"
        report["findings"].append(finding)
    report["missing_materials"].extend(benchmark_missing + route_missing + document_missing + packaging_missing + logistics_missing)
    report["decision"] = choose_launch_decision(
        report["findings"],
        report["requirements"],
        report["market_benchmarks"],
        logistics_rows,
    )
    report["remediation"] = {
        "applicant_message": build_supplement_message(report["missing_materials"]),
        "internal_next_steps": [
            "Verify current official platform and regulator sources before final decision.",
            "Complete origin/export and destination/import research tasks for every destination market.",
            "Match submitted documents to holder, brand, product, territory, platform, scope, and validity.",
            "Recheck competitor prices and logistics quotations from current sources.",
            "Revise packaging/listing claims before printing or marketplace submission.",
        ],
    }
    report["audit_log"].append(
        {
            "timestamp": today(),
            "actor": "AI reviewer",
            "action": "generated_offline_launch_report",
            "details": f"Origin={origin_country or 'missing'}, destinations={len(market_reviews)}, documents={len(documents)}, benchmarks={len(benchmark_rows)}, logistics_routes={len(logistics_rows)}.",
        }
    )
    report["go_to_market_route"] = go_to_market_route_profile(go_to_market_model)
    report["offline_logistics"] = logistics_rows
    report["generation_metadata"] = build_generation_metadata(report, bundle)
    return report


def _md_cell(value: Any) -> str:
    text = _text(value)
    return text.replace("\n", "<br>").replace("|", "\\|")


def _md_list(values: Any) -> str:
    items = [_text(item) for item in _as_list(values) if _text(item)]
    return ", ".join(items)


def _html(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _display_label(value: Any) -> str:
    return _html(_text(value).replace("_", " "))


def _plain_label(value: Any) -> str:
    return _text(value).replace("_", " ")


def _short_text(value: Any, limit: int = 96) -> str:
    text = _plain_label(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _zh_status(value: Any) -> str:
    status = _text(value)
    labels = {
        "approve": "可推进",
        "conditional_approve": "谨慎推进",
        "request_more_info": "暂缓，需补件",
        "reject": "停止",
        "escalate_human": "人工复核",
        "not_applicable": "不适用",
    }
    return labels.get(status, _plain_label(status) or "待判断")


def _zh_risk(value: Any) -> str:
    risk = _text(value)
    labels = {"low": "低", "medium": "中", "high": "高", "critical": "严重"}
    return labels.get(risk, _plain_label(risk) or "未知")


def _zh_country(value: Any) -> str:
    labels = {
        "Italy": "意大利",
        "China": "中国",
        "US": "美国",
        "United States": "美国",
        "EU": "欧盟",
        "Japan": "日本",
    }
    text = _text(value)
    return labels.get(text, text)


def _zh_owner(value: Any) -> str:
    labels = {
        "applicant / reviewer": "申请人 / 审核人",
        "importer / distributor / reviewer": "进口商 / 经销商 / 审核人",
        "applicant / logistics reviewer": "申请人 / 物流审核人",
    }
    text = _text(value)
    return labels.get(text, text or "申请人 / 审核人")


def _zh_route_label(value: Any) -> str:
    labels = {
        "cross border ecommerce": "跨境电商",
        "physical trade": "实体贸易",
        "hybrid ecommerce and physical trade": "混合路径",
        "unknown route": "路径待确认",
    }
    return labels.get(_plain_label(value), _plain_label(value) or "路径待确认")


def _zh_channel(value: Any) -> str:
    labels = {
        "platform policy": "平台政策",
        "destination regulator": "目标国监管",
        "customs import": "海关进口",
        "brand ip": "品牌/IP",
        "business registry": "主体注册",
        "certification lab": "证书/实验室",
        "standards body": "标准依据",
        "logistics warehouse": "物流/仓储",
        "origin export controls": "原产地出口",
        "offline channel": "线下渠道",
        "marketplace search": "平台搜索",
    }
    key = _plain_label(value)
    return labels.get(key, key or "待补渠道")


def _zh_case_text(value: Any) -> str:
    text = _plain_label(value)
    if text.startswith("Holder '") and "does not match applicant" in text:
        return "文件持有人与待确认进口商/经销商不一致，需要确认进口主体和授权链。"
    replacements = {
        "Requirement is not yet matched to submitted applicant/product evidence.": "规则要求尚未匹配到申请人或商品证据。",
        "Collect matching applicant evidence and verify current official sources before approval.": "补充匹配的申请人/商品证据，并在批准前核验最新官方来源。",
        "Chinese label basis is missing for China food import; visible packaging languages are not enough for local sale.": "缺少中国进口食品中文标签依据；现有包装语言不足以直接用于境内销售。",
        "China food import route is not evidenced yet; importer, customs, inspection, label filing/review, and product document set are not confirmed.": "中国食品进口路径未核验；进口商、海关、商检、标签审核和产品文件集未确认。",
        "EU and non-EU olive oil origin wording may not be sufficient for China import origin, COO, and Chinese label claims without supporting documents.": "欧盟与非欧盟橄榄油来源表述需原产地证和中文标签口径支持。",
        "Document scope does not clearly mention category 'food'.": "文件范围没有清楚覆盖食品类目，需要确认品类、SKU 和用途范围。",
        "Confirm the document covers the reviewed product category and SKU.": "确认文件明确覆盖本次审核的产品类目和 SKU。",
        "Prepare or verify compliant Chinese label artwork before shipment, including product name, ingredients, net content, origin, importer/distributor, nutrition, date/lot, storage, and required standard markings.": "出货前准备并核验中文标签：品名、配料、净含量、原产地、进口商/经销商、营养、日期批号、贮存条件和标准标识。",
        "Confirm the China food import route with importer/customs broker and collect the required customs, inspection, invoice/packing, contract, origin, health/sanitary, and label materials before booking shipment.": "订舱前与进口商/报关行确认进口路径，并收集清关、商检、发票箱单、合同、原产地、卫生/检疫和标签材料。",
        "Verify certificate of origin, manufacturer/exporter documents, ingredient/origin statement, and Chinese label origin wording before using Italy/EU origin cues in import materials.": "使用意大利/EU来源表述前，核验证书、制造商/出口商文件、配料来源声明和中文标签原产地口径。",
        "China-compliant Chinese label artwork and label review": "中国合规中文标签稿与标签审核",
        "China food import document set and importer/customs route confirmation": "中国食品进口文件集与进口商/清关路径确认",
        "Certificate of origin and origin-claim support documents": "原产地证与来源宣称支持文件",
        "Product/category scope evidence": "产品/类目范围证明",
        "Entity relationship evidence": "主体关系与授权链证明",
        "Logistics route and budget basis": "物流路径与成本依据",
        "Holder 'Fratelli Mantova / Compagnia Alimentare Italiana S.p.A.' does not match applicant 'Importer / distributor to be confirmed'.": "文件持有人与待确认进口商/经销商不一致，需要确认进口主体和授权链。",
        "Provide entity relationship evidence or a corrected document naming the applicant.": "补充主体关系证明、授权链，或提供载明进口主体的文件。",
        "Provide product/category scope evidence or a corrected document naming the covered product/category.": "补充产品/类目范围证明，或提供明确覆盖该产品/类目的修正文件。",
        "Launch readiness is blocked until missing, expired, mismatched, or externally unverified evidence is resolved.": "存在缺失、过期、主体不匹配或未外部核验的材料，暂不建议推进。",
        "Launch readiness cannot assess margin and inventory risk without route, cost driver, time, and constraints.": "缺少路线、成本驱动、时效和限制条件时，无法评估利润和库存风险。",
        "business license or registration certificate; authorization document if applicant differs from rights holder": "主体注册/营业执照；申请人与权利人不一致时需授权文件",
        "Major mismatch is high severity and normally requires more information or rejection.": "主体或授权链不清会直接影响进口/销售准入。",
        "platform route source; customs/import source; warehouse or logistics route evidence": "平台/进口/物流路径依据",
        "Cannot approve China import/cross-border cases until the route and applicable official obligations are verified.": "未核验中国进口路径和适用官方义务前，不能给出通过结论。",
        "No price basis supplied; verify current target-market prices.": "尚未提供价格依据，需要核验目标市场现价。",
        "No channel basis supplied.": "尚未提供渠道依据。",
        "No packaging benchmark signals supplied.": "尚未提供包装对标信号。",
        "No competitor claim signals supplied.": "尚未提供竞品宣称信号。",
        "No visible certification or trust signals supplied.": "尚未提供可见认证或信任背书信号。",
        "No review signals supplied.": "尚未提供评论和用户反馈信号。",
        "Positioning cannot be assessed until benchmarks are verified.": "未核验对标样本前，暂不能判断定位。",
        "Competitor rows are offline/user-provided unless marked current_checked; recheck current prices, claims, review counts, and certifications.": "竞品信息若非实时核验，需重新确认现价、宣称、评论数和认证。",
        "Competitor rows are offline/user-provided unless marked current checked; recheck current prices, claims, review counts, and certifications.": "竞品信息若非实时核验，需重新确认现价、宣称、评论数和认证。",
        "Competitor rows are offline/user provided unless marked current checked; recheck current prices, claims, review counts, and certifications.": "竞品信息若非实时核验，需重新确认现价、宣称、评论数和认证。",
        "Operational qualification review only; not legal advice.": "本报告仅用于经营和资质审核，不构成法律意见。",
    }
    return replacements.get(text, text)


def _zh_route_checks(value: Any) -> str:
    labels = {
        "marketplace listing and category gating": "平台上架与类目准入",
        "platform restricted-products policy": "平台禁限售政策",
        "brand authorization and IP coverage": "品牌授权与知识产权覆盖",
        "listing claims, packaging, and label readiness": "Listing 宣称、包装与标签准备",
        "fulfillment, warehouse, and return route": "履约、仓储与退货路径",
        "destination import and customs": "目的国进口与清关",
        "origin export controls and certificate of origin": "原产地出口管制与原产地证",
        "importer or responsible-party obligations": "进口商或责任主体义务",
        "local label, registration, and retail/distributor channel requirements": "本地标签、注册与零售/经销渠道要求",
        "Incoterms, freight, tax, warehouse, and insurance route": "贸易术语、运费、税费、仓储与保险路径",
    }
    values = [labels.get(_plain_label(item), _plain_label(item)) for item in _as_list(value) if _text(item)]
    return "、".join(values)


def _zh_source_title(value: Any) -> str:
    text = _text(value)
    replacements = {
        "China product regulator for food": "中国食品监管分类、注册/备案与标签规则",
        "China customs and import route": "中国海关进口路径与清关文件",
        "China trademark and brand authorization route": "中国商标与品牌授权路径",
        "Applicant, manufacturer, importer, and responsible-party registry checks": "申请人、制造商、进口商和责任主体注册核验",
        "Certificate, issuer, lab, and accreditation checks for food": "食品证书、签发方、实验室和认可范围核验",
        "Applicable standards and conformity route for food": "食品适用标准与符合性路径",
        "Italy to China logistics, warehouse, and platform prep route": "意大利至中国物流、仓储和入境准备路径",
        "Italy export, origin, and COO route": "意大利出口、原产地与原产地证路径",
        "China importer, distributor, wholesale, retail, and offline shelf route": "中国进口商、经销、批发、零售与线下上架路径",
    }
    return replacements.get(text, text)


def _zh_expected_facts(value: Any) -> str:
    text = _joined_text(value)
    replacements = {
        "classification, required registrations, label rules, claims limits": "分类、注册/备案、标签规则、宣称限制",
        "importer obligations, customs documents, admissibility, tax/VAT route": "进口商义务、清关文件、准入、税费路径",
        "owner, class, territory, status, expiry, authorization scope": "权利人、类别、地区、状态、有效期、授权范围",
        "legal name, status, registered address, business scope, role relationship": "法定名称、状态、注册地址、经营范围、角色关系",
        "issuer status, accreditation scope, standard, product match, expiry": "签发方状态、认可范围、标准、产品匹配、有效期",
        "applicable standard, test basis, technical file route, label mark rules": "适用标准、测试依据、技术文件路径、标识规则",
        "route constraints, cost basis, prep rules, warehouse acceptance, transit risk": "路线限制、成本依据、准备规则、仓库接收、运输风险",
        "export permissions, COO route, manufacturer/exporter identity, origin label consistency": "出口许可、原产地证路径、制造商/出口商身份、原产地标签一致性",
        "offline channel requirements, buyer documentation, local responsibility, shelf/packaging expectations": "线下渠道要求、买方文件、本地责任、货架/包装要求",
    }
    return replacements.get(text, text)


def _zh_research_instruction(value: Any) -> str:
    text = _text(value)
    replacements = {
        "Verify product classification, regulator, registration/notification, label language, warnings, and claim limits.": "核验产品分类、主管机构、注册/备案、标签语言、警示语和宣称限制。",
        "Verify importer of record, customs documents, admissibility, tax/VAT route, and import controls.": "核验进口商、清关文件、准入条件、税费路径和进口管制。",
        "Verify trademark owner, class, territory, status, expiry, and authorization coverage for platform/channel/product.": "核验商标权利人、类别、地区、状态、有效期，以及平台/渠道/产品授权覆盖。",
        "Verify applicant, manufacturer, importer, responsible party, rights holder, and certificate holder identity chain.": "核验申请人、制造商、进口商、责任方、权利人和证书持有人的主体链路。",
        "Verify issuer/lab/accreditation status, standard, model/SKU/product scope, site scope, and expiry.": "核验证书签发方、实验室/认可状态、标准、型号/SKU/产品范围、场地范围和有效期。",
        "Verify applicable standards, conformity route, technical-file basis, and allowed marks.": "核验适用标准、符合性路径、技术文件依据和允许使用的标识。",
        "Verify freight constraints, dangerous goods, warehouse acceptance, platform prep, cost basis, and route timing.": "核验运输限制、危险品属性、仓库接收、备货要求、成本依据和路线时效。",
        "Verify export permissions, certificate of origin, manufacturer/exporter documents, and origin label consistency.": "核验出口许可、原产地证、制造商/出口商文件和原产地标签一致性。",
        "Verify importer/distributor/retail channel requirements, buyer documents, local responsibility split, and offline shelf expectations.": "核验进口商/经销商/零售渠道要求、买方文件、本地责任分工和线下上架要求。",
    }
    return replacements.get(text, text)


def _dedupe_rows(items: list[dict[str, Any]], key_fn) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        key = _plain_label(key_fn(item))
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _html_bullets(items: list[str], empty: str = "待补充") -> str:
    values = [_short_text(_zh_case_text(item), 118) for item in items if _text(item)]
    if not values:
        values = [empty]
    return "".join(f"<li>{_html(item)}</li>" for item in values)


def _top_findings(report: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    finding_order = {"OFF-GTM": 0, "OFF-PACK": 1, "OFF-DOC": 2, "OFF-LOG": 3}

    def source_priority(item: dict[str, Any]) -> int:
        finding_id = _text(item.get("finding_id"))
        for prefix, priority in finding_order.items():
            if finding_id.startswith(prefix):
                return priority
        return 9

    findings = [item for item in report.get("findings") or [] if isinstance(item, dict)]
    findings.sort(key=lambda item: (severity_order.get(str(item.get("severity")), 9), source_priority(item)))
    specific_findings = [
        item
        for item in findings
        if _plain_label(item.get("observed_issue")) != "Requirement is not yet matched to submitted applicant/product evidence."
    ]
    return _dedupe_rows(specific_findings or findings, lambda item: _zh_case_text(item.get("observed_issue")))[:limit]


def _top_missing(report: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    priority_order = {"P0": 0, "P1": 1, "P2": 2}

    def route_priority(item: dict[str, Any]) -> int:
        blob = " ".join([_text(item.get("material")), _text(item.get("why_required"))]).lower()
        priority_terms = (
            ("chinese label", 0),
            ("china-compliant", 0),
            ("china food import document", 1),
            ("importer/customs route", 1),
            ("certificate of origin", 2),
            ("origin-claim", 2),
            ("entity relationship", 3),
            ("product/category scope", 4),
            ("logistics route", 5),
            ("platform route source", 8),
        )
        for term, priority in priority_terms:
            if term in blob:
                return priority
        if any(term in blob for term in ("china", "import document", "customs route")):
            return 0
        return 9

    items = [item for item in report.get("missing_materials") or [] if isinstance(item, dict)]
    generic_materials = {
        "business registration; tax/payee information where required; platform seller eligibility source",
        "trademark certificate; brand authorization letter; distribution agreement",
        "official platform restricted-products source; official regulator/customs source where relevant",
        "test report; certificate; declaration of conformity; COA/SDS/label where relevant",
        "label artwork; claim substantiation; official label/claim requirements",
        "document inventory with issue/expiry dates",
        "platform route source; customs/import source; warehouse or logistics route evidence",
        "Chinese label artwork; official regulator source; platform category source",
        "official food regulator source; ingredient list; facility/importer evidence where required",
        "label artwork; claim substantiation; official labeling/claims source",
        "Target-market benchmark products",
    }
    specific_items = [
        item
        for item in items
        if _plain_label(item.get("material")) not in generic_materials
    ]
    items = specific_items or items
    items.sort(key=lambda item: (route_priority(item), priority_order.get(str(item.get("priority")), 9)))
    return _dedupe_rows(items, lambda item: f"{_zh_case_text(item.get('material'))}:{_zh_case_text(item.get('why_required'))}")[:limit]


def _channel_types(report: dict[str, Any], limit: int = 8) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for candidate in report.get("source_candidates") or []:
        if not isinstance(candidate, dict):
            continue
        channel = _text(candidate.get("channel_type"))
        if not channel or channel in seen:
            continue
        seen.add(channel)
        values.append(channel)
    return values[:limit]


def _evidence_status(report: dict[str, Any]) -> dict[str, int]:
    counts = {"authoritative": 0, "user_provided": 0, "needs_external_verification": 0}
    for evidence in report.get("evidence") or []:
        if not isinstance(evidence, dict):
            continue
        tier = _text(evidence.get("tier"))
        if tier in {"T1", "T2"}:
            counts["authoritative"] += 1
        elif tier == "T4":
            counts["user_provided"] += 1
    for requirement in report.get("requirements") or []:
        if isinstance(requirement, dict) and requirement.get("status") == "needs_external_verification":
            counts["needs_external_verification"] += 1
    for task in report.get("research_tasks") or []:
        if isinstance(task, dict) and task.get("status") == "needs_external_verification":
            counts["needs_external_verification"] += 1
    return counts


def _table_or_empty(rows: str, columns: int, message: str) -> str:
    return rows or f"<tr><td colspan='{columns}' class='muted'>{_html(message)}</td></tr>"


def _priority_badge(value: Any) -> str:
    text = _text(value)
    return text if text in {"P0", "P1", "P2"} else "P1"


def _zh_benchmark_role(value: Any) -> str:
    labels = {
        "search_marketplace": "平台搜索",
        "social_commerce": "社交电商",
        "mass_retail": "大众零售",
        "club_store": "会员店/仓储",
        "specialty": "垂直专门店",
        "pharmacy": "药妆/药房",
        "dtc": "品牌 DTC",
        "offline_shelf": "线下零售",
        "other": "其他渠道",
    }
    key = _plain_label(value).replace(" ", "_")
    return labels.get(key, _plain_label(value) or "待补渠道")


def _zh_data_basis(value: Any) -> str:
    labels = {
        "current_checked": "已实时核验",
        "user_provided": "用户提供",
        "assumption": "假设/待核验",
        "not_checked": "未核验",
    }
    key = _plain_label(value).replace(" ", "_")
    return labels.get(key, _plain_label(value) or "未核验")


def _zh_positioning(value: Any) -> str:
    labels = {
        "mass": "大众价位",
        "mainstream": "主流价位",
        "premium": "高端价位",
        "specialty": "特色/专业",
        "luxury": "奢侈/礼品",
        "unknown": "待判断",
    }
    return labels.get(_plain_label(value), _plain_label(value) or "待判断")


def _benchmark_research_plan_rows(route: dict[str, Any], destinations: list[Any], case: dict[str, Any]) -> str:
    destination_label = "、".join(_zh_country(item) for item in destinations if _text(item)) or _zh_country(case.get("destination_market"))
    route_label = _plain_label(route.get("label"))
    if "physical trade" in route_label:
        rows = [
            ("直接竞品", "线下零售 / 进口商 / 电商搜索", "同品类、同规格或同原产地的进口商品", "价格/规格/单位价、包装/标签信号、进口商/责任方、认证/中文标签、陈列渠道"),
            ("进口替代品", "商超 / 经销 / 批发", "目标市场已流通的进口替代商品", "到岸后零售价、渠道层级、原产地表达、中文背标、买方文件要求"),
            ("本地替代品", "本地零售 / 垂直渠道", "本地品牌或主流替代品", "本地价格锚点、包装容量、卖点表述、消费者预期"),
            ("线下零售", "商超 / 精品店 / 批发市场", "货架上实际出现的同类商品", "货架价、促销、包装尺寸、标签语言、认证标识、陈列位置"),
            ("平台搜索", "天猫/京东/抖音/小红书等用户指定渠道", "线上同类 Listing 和内容种草样本", "成交/评论信号、标题卖点、价格带、信任背书、差评主题"),
        ]
    else:
        rows = [
            ("直接竞品", "平台搜索", "同平台、同关键词、同价格带的直接竞品", "价格/规格/单位价、标题卖点、主图包装、认证标识、评论/口碑信号"),
            ("平台热销", "平台榜单 / 搜索结果", "类目热销或高评论商品", "转化型卖点、价格锚点、评论主题、物流/退货信号"),
            ("DTC/社交电商", "品牌站 / TikTok / 小红书 / Reddit", "品牌自营和内容驱动样本", "人群定位、内容钩子、购买触发点、争议点"),
            ("线下零售", "商超 / 药妆 / 专门店", "线下货架参照", "包装尺寸、货架价、标签语言、认证标识、使用场景"),
            ("进口替代品", "跨境平台 / 本地零售", "同产地或相邻产地的进口替代品", "进口溢价、原产地叙事、清关/责任方可见信号"),
        ]
    return "".join(
        f"<tr><td>{_html(kind)}</td><td>{_html(destination_label)}</td><td>{_html(channel)}</td><td>{_html(scope)}</td><td>{_html(fields)}</td></tr>"
        for kind, channel, scope, fields in rows
    )


def _benchmark_analysis_matrix_rows(report: dict[str, Any]) -> str:
    rows: list[str] = []
    for item in (report.get("market_benchmarks") or [])[:10]:
        if not isinstance(item, dict):
            continue
        price_parts = [
            _text(item.get("pack_size")),
            _text(item.get("price")),
            _text(item.get("unit_price")),
        ]
        sample_meta = " · ".join(
            [
                _zh_benchmark_role(item.get("channel_role")),
                _zh_positioning(item.get("positioning")),
                _zh_data_basis(item.get("data_basis")),
            ]
        )
        rows.append(
            "<tr>"
            f"<td>{_html(_short_text(item.get('product_name'), 54))}<br><span class='muted'>{_html(sample_meta)}</span></td>"
            f"<td>{_html(item.get('channel'))}</td>"
            f"<td>{_html(_short_text(' / '.join(part for part in price_parts if part), 64) or '待补')}</td>"
            f"<td>{_html(_short_text(_joined_text(item.get('packaging_signals')), 86) or '待补')}</td>"
            f"<td>{_html(_short_text(_joined_text(item.get('visible_claims')), 86) or '待补')}</td>"
            f"<td>{_html(_short_text(_joined_text(item.get('certification_signals')), 72) or '待补')}</td>"
            f"<td>{_html(_short_text(_joined_text(item.get('review_signals')), 72) or '待补')}</td>"
            f"<td>{_html(_short_text(_zh_case_text(item.get('takeaway')), 100))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _benchmark_source_rows(report: dict[str, Any]) -> str:
    benchmark_source_ids = {
        _text(source_id)
        for item in (report.get("market_benchmarks") or [])
        if isinstance(item, dict)
        for source_id in _as_list(item.get("source_ids"))
        if _text(source_id)
    }
    rows: list[str] = []
    for source in report.get("sources") or []:
        if not isinstance(source, dict):
            continue
        source_id = _text(source.get("source_id"))
        if source_id not in benchmark_source_ids and not source_id.startswith("src-agent-"):
            continue
        rows.append(
            "<tr>"
            f"<td>{_html(_short_text(_zh_source_title(source.get('title')), 70))}</td>"
            f"<td>{_html(_short_text(source.get('url'), 96))}</td>"
            f"<td>{_html(source.get('tier'))}</td>"
            f"<td>{_html(source.get('checked_at'))}</td>"
            f"<td>{_html(_short_text(_zh_case_text(source.get('confirms')), 110))}<br><span class='muted'>商业市场信号；不能替代官方、进口、标签或平台最终核验。</span></td>"
            "</tr>"
        )
    return "".join(rows)


def render_overview_card_html(report: dict[str, Any]) -> str:
    case = report.get("case") if isinstance(report.get("case"), dict) else {}
    decision = report.get("decision") if isinstance(report.get("decision"), dict) else {}
    route = report.get("go_to_market_route") if isinstance(report.get("go_to_market_route"), dict) else go_to_market_route_profile(_text(case.get("go_to_market_model")) or "unknown")
    destinations = _as_list(case.get("destination_markets")) or _as_list(case.get("destination_market"))
    findings = _top_findings(report)
    missing = _top_missing(report)
    channels = _channel_types(report)
    evidence = _evidence_status(report)
    product = _text(case.get("product_name") or case.get("subcategory") or case.get("product_category") or "商品")
    blocker_items = [_text(item.get("observed_issue")) for item in findings]
    action_items = [
        f"{_zh_case_text(item.get('material'))}: {_zh_case_text(item.get('why_required'))}"
        for item in missing
    ]
    channel_items = [_zh_channel(channel) for channel in channels[:8]]
    destination_text = "、".join(_zh_country(item) for item in destinations if _text(item))
    provenance = _generation_provenance_html(report, limit=92)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>出海体检核心卡 / Core Overview Card</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; width: 1200px; background: #f3f0e8; color: #172033; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif; letter-spacing: 0; }}
    .card {{ margin: 44px 52px; background: #fffdf8; border: 1px solid #1b2430; border-radius: 4px; box-shadow: 0 18px 44px rgba(20, 31, 43, .15); overflow: hidden; }}
    .top {{ display: grid; grid-template-columns: 1.25fr .75fr; gap: 0; border-bottom: 2px solid #1b2430; }}
    .title {{ padding: 38px 46px 30px; }}
    .eyebrow {{ color: #1769aa; font-weight: 850; font-size: 22px; margin-bottom: 16px; }}
    h1 {{ font-size: 52px; line-height: 1.06; margin: 0 0 16px; max-width: 760px; }}
    .subtitle {{ color: #5e6a78; font-size: 23px; line-height: 1.35; max-width: 760px; }}
    .verdict {{ background: #142033; color: #fffdf8; padding: 38px 36px; display: flex; flex-direction: column; justify-content: space-between; }}
    .verdict .small {{ color: #aebfcd; font-size: 18px; font-weight: 750; margin-bottom: 8px; }}
    .verdict .big {{ font-size: 42px; line-height: 1.1; font-weight: 900; }}
    .risk {{ display: inline-block; margin-top: 18px; padding: 8px 12px; background: #b93a32; color: white; font-size: 20px; font-weight: 850; }}
    .meta {{ display: grid; grid-template-columns: repeat(4, 1fr); border-bottom: 1px solid #1b2430; }}
    .meta > div {{ padding: 20px 24px; border-right: 1px solid #1b2430; min-height: 108px; }}
    .meta > div:last-child {{ border-right: 0; }}
    .label {{ color: #687381; font-size: 17px; font-weight: 850; margin-bottom: 10px; }}
    .value {{ font-size: 26px; font-weight: 900; line-height: 1.18; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
    .section {{ padding: 28px 34px; min-height: 294px; border-right: 1px solid #1b2430; border-bottom: 1px solid #1b2430; }}
    .section:nth-child(even) {{ border-right: 0; }}
    .section h2 {{ font-size: 30px; margin: 0 0 18px; display: flex; align-items: center; gap: 12px; }}
    .mark {{ width: 12px; height: 30px; display: inline-block; }}
    .blocker .mark {{ background: #b93a32; }}
    .verify .mark {{ background: #1c6f9e; }}
    .action .mark {{ background: #2f7d5b; }}
    .evidence .mark {{ background: #7b6b47; }}
    ul {{ margin: 0; padding-left: 25px; }}
    li {{ font-size: 22px; line-height: 1.38; margin: 0 0 12px; }}
    .section.blocker {{ background: #fff3f1; }}
    .section.verify {{ background: #eef7fb; }}
    .section.action {{ background: #eff8f2; }}
    .section.evidence {{ background: #f7f4eb; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .chip {{ font-size: 20px; padding: 8px 11px; border-radius: 2px; background: #fffdf8; color: #173c55; border: 1px solid #8ab4cc; font-weight: 850; }}
    .evidence-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 8px; }}
    .metric {{ background: #fffdf8; border: 1px solid #c6bda5; padding: 14px; }}
    .metric b {{ display: block; font-size: 28px; margin-bottom: 4px; }}
    .metric span {{ color: #687381; font-size: 16px; font-weight: 750; }}
    .footer {{ padding: 20px 34px; color: #5e6a78; font-size: 19px; line-height: 1.35; }}
    .verdict .provenance {{ color: #aebfcd; font-size: 12px; line-height: 1.35; margin-top: 12px; font-weight: 650; }}
    .compat {{ display: none; }}
  </style>
</head>
<body>
  <main class="card">
    <span class="compat">Core Overview Card Top blockers Must-check channels Next actions Evidence status Origin Destinations Go-to-market path Chinese label {_html(_plain_label(route.get("label")))}</span>
    <section class="top">
      <div class="title">
        <div class="eyebrow">LaunchFit AI · 出海体检核心卡</div>
        <h1>{_html(product)}</h1>
        <div class="subtitle">先判准入，再看对标。当前结论基于已提交材料，未完成官方外部核验前不建议推进。</div>
      </div>
      <div class="verdict">
        <div>
          <div class="small">体检结论</div>
          <div class="big">{_html(_zh_status(decision.get("status")))}</div>
          <div class="risk">风险：{_html(_zh_risk(decision.get("risk_level")))}</div>
        </div>
        <div>
          <div class="small">{_html(_short_text(_zh_case_text(decision.get("summary")), 88))}</div>
          <div class="provenance">{provenance}</div>
        </div>
      </div>
    </section>
    <section class="meta">
      <div><div class="label">销售路径</div><div class="value">{_html(_zh_route_label(route.get("label")))}</div></div>
      <div><div class="label">原产地</div><div class="value">{_html(_zh_country(case.get("origin_country")))}</div></div>
      <div><div class="label">目标市场</div><div class="value">{_html(destination_text)}</div></div>
      <div><div class="label">证据基础</div><div class="value">T4 用户材料</div></div>
    </section>
    <section class="grid">
      <div class="section blocker"><h2><span class="mark"></span>关键阻断</h2><ul>{_html_bullets(blocker_items)}</ul></div>
      <div class="section verify"><h2><span class="mark"></span>必须核验</h2><div class="chips">{"".join(f"<span class='chip'>{_html(channel)}</span>" for channel in channel_items) or "<span class='chip'>待补渠道</span>"}</div></div>
      <div class="section action"><h2><span class="mark"></span>下一步</h2><ul>{_html_bullets(action_items, "完成 P0/P1 核验任务")}</ul></div>
      <div class="section evidence"><h2><span class="mark"></span>证据状态</h2><div class="evidence-grid"><div class="metric"><b>{evidence['authoritative']}</b><span>T1/T2 权威来源</span></div><div class="metric"><b>{evidence['user_provided']}</b><span>T4 用户材料</span></div><div class="metric"><b>{evidence['needs_external_verification']}</b><span>需外部核验</span></div></div></div>
    </section>
    <div class="footer">说明：本卡用于快速决策，不替代官方监管、海关、平台或专业法律意见。详细依据见 PDF。</div>
  </main>
</body>
</html>
"""


def render_detailed_pdf_html(report: dict[str, Any]) -> str:
    case = report.get("case") if isinstance(report.get("case"), dict) else {}
    decision = report.get("decision") if isinstance(report.get("decision"), dict) else {}
    route = report.get("go_to_market_route") if isinstance(report.get("go_to_market_route"), dict) else go_to_market_route_profile(_text(case.get("go_to_market_model")) or "unknown")
    benchmark_summary = report.get("market_benchmark_summary") if isinstance(report.get("market_benchmark_summary"), dict) else {}
    destinations = _as_list(case.get("destination_markets")) or _as_list(case.get("destination_market"))
    evidence = _evidence_status(report)
    findings = _top_findings(report, limit=6)
    missing = _top_missing(report, limit=8)
    channels = _channel_types(report, limit=10)
    product = _text(case.get("product_name") or case.get("subcategory") or case.get("product_category") or "商品")
    destination_label = "、".join(_zh_country(item) for item in destinations if _text(item))
    market_rows = "".join(
        f"<tr><td>{_html(_zh_country(item.get('destination_market')))}</td><td>{_html(_joined_text(item.get('matched_packs')))}</td><td>{len(item.get('research_tasks') or [])}</td><td>{len(item.get('source_candidates') or [])}</td></tr>"
        for item in report.get("market_reviews") or []
        if isinstance(item, dict)
    )
    candidate_rows = "".join(
        f"<tr><td>{_html(_zh_country(item.get('destination_market')))}</td><td>{_html(_zh_channel(item.get('channel_type')))}</td><td>{_html(_short_text(_zh_source_title(item.get('title')), 74))}</td><td>{_html(item.get('source_tier'))}</td><td>{_html(_short_text(_zh_expected_facts(item.get('expected_facts')), 90))}</td></tr>"
        for item in (report.get("source_candidates") or [])[:14]
        if isinstance(item, dict)
    )
    task_rows = "".join(
        f"<tr><td>{_html(item.get('priority'))}</td><td>{_html(_zh_country(item.get('destination_market')))}</td><td>{_html(_zh_channel(item.get('channel_type')))}</td><td>{_html(_short_text(_zh_research_instruction(item.get('instruction')), 110))}</td></tr>"
        for item in (report.get("research_tasks") or [])[:12]
        if isinstance(item, dict)
    )
    finding_rows = "".join(
        f"<tr><td>{_html(_zh_risk(item.get('severity')))}</td><td>{_html(_short_text(_zh_case_text(item.get('observed_issue')), 120))}</td><td>{_html(_short_text(_zh_case_text(item.get('required_action')), 120))}</td></tr>"
        for item in findings
    )
    missing_rows = "".join(
        f"<tr><td>{_html(item.get('priority'))}</td><td>{_html(_short_text(_zh_case_text(item.get('material')), 82))}</td><td>{_html(_short_text(_zh_case_text(item.get('why_required')), 110))}</td><td>{_html(_zh_owner(item.get('owner')))}</td></tr>"
        for item in missing
    )
    evidence_rows = (
        f"<tr><td>T1/T2 权威入口</td><td>{evidence['authoritative']}</td><td>已收录为候选来源</td><td>按“必须核验渠道”逐项打开最新官方页面复核。</td></tr>"
        f"<tr><td>T4 用户材料</td><td>{evidence['user_provided']}</td><td>仅证明用户已提交</td><td>不能直接当作官方事实；需要与主体、SKU、有效期和目标市场匹配。</td></tr>"
        f"<tr><td>待外部核验</td><td>{evidence['needs_external_verification']}</td><td>不能自动通过</td><td>完成 P0 核验任务后再更新结论。</td></tr>"
    )
    document_rows = "".join(
        f"<tr><td>{_html(item.get('document_type'))}</td><td>{_html(_short_text(item.get('holder'), 48))}</td><td>{_html(_short_text(item.get('scope'), 60))}</td><td>{_html(item.get('expiry_date') or '待确认')}</td><td>T4</td></tr>"
        for item in (report.get("documents") or [])[:10]
        if isinstance(item, dict)
    )
    benchmark_rows = "".join(
        f"<tr><td>{_html(item.get('product_name'))}</td><td>{_html(item.get('channel'))}</td><td>{_html(item.get('price') or item.get('unit_price'))}</td><td>{_html(_short_text(_joined_text(item.get('visible_claims')), 74))}</td><td>{_html(_zh_data_basis(item.get('data_basis')))}</td></tr>"
        for item in (report.get("market_benchmarks") or [])[:10]
        if isinstance(item, dict)
    )
    benchmark_matrix_rows = _benchmark_analysis_matrix_rows(report)
    benchmark_plan_rows = _benchmark_research_plan_rows(route, destinations, case)
    benchmark_source_rows = _benchmark_source_rows(report)
    logistics_rows = "".join(
        f"<tr><td>{_html(item.get('route'))}</td><td>{_html(item.get('mode'))}</td><td>{_html(item.get('time') or '待报价')}</td><td>{_html(_short_text(item.get('cost_basis') or '待报价', 60))}</td><td>{_html(_short_text(_joined_text(item.get('risks') or item.get('constraints')), 74))}</td></tr>"
        for item in (report.get("offline_logistics") or [])[:8]
        if isinstance(item, dict)
    )
    pending_rows = "".join(
        f"<tr><td>{_html(_priority_badge(item.get('priority')))}</td><td>{_html(_zh_country(item.get('destination_market')))}</td><td>{_html(_zh_channel(item.get('channel_type')))}</td><td>{_html(_short_text(_zh_research_instruction(item.get('instruction')), 120))}</td><td>{_html(item.get('recommended_tier') or 'T1')}</td></tr>"
        for item in (report.get("research_tasks") or [])[:18]
        if isinstance(item, dict) and item.get("status") == "needs_external_verification"
    )
    source_rows = "".join(
        f"<tr><td>{_html(_zh_country(item.get('destination_market')))}</td><td>{_html(_zh_channel(item.get('channel_type')))}</td><td>{_html(_short_text(_zh_source_title(item.get('title')), 82))}</td><td>{_html(item.get('source_tier'))}</td></tr>"
        for item in (report.get("source_candidates") or [])[:18]
        if isinstance(item, dict)
    )
    localization_rows = "".join(
        [
            f"<tr><td>包装本地化</td><td>{_html(_zh_case_text(benchmark_summary.get('packaging_conventions')))}</td><td>目标市场语言、强制标签、营养/成分、责任方、日期批号和允许标识需逐项核验。</td></tr>",
            f"<tr><td>宣称与证明</td><td>{_html(_zh_case_text(benchmark_summary.get('claims_and_proof')))}</td><td>避免使用未证实的健康、监管、认证、天然、有机、免疫等高风险宣称。</td></tr>",
            f"<tr><td>价格与定位</td><td>{_html(_zh_case_text(benchmark_summary.get('reference_price_band')))}</td><td>用当前竞品价格、规格和渠道重新计算单位价格与进口后毛利。</td></tr>",
            f"<tr><td>渠道对标</td><td>{_html(_zh_case_text(benchmark_summary.get('channel_map')))}</td><td>区分平台电商、DTC、进口商、经销、批发和线下零售，不混用准入要求。</td></tr>",
        ]
    )
    implementation_rows = "".join(
        [
            f"<tr><td>渠道与落地路径</td><td>{_html(_zh_route_label(route.get('label')))}</td><td>{_html(_short_text(_zh_route_checks(route.get('primary_checks')), 150))}</td></tr>",
            "<tr><td>供应链与物流</td><td>待用报价和路线补齐</td><td>确认 Incoterms、订舱、清关、商检、仓储、保险、破损/泄漏、保质期和库存周转。</td></tr>",
            "<tr><td>服务商与责任方</td><td>待指定进口商/经销商/报关行</td><td>核验进口商、境内责任方、品牌授权链、清关行、实验室、物流服务商和零售买方要求。</td></tr>",
            "<tr><td>成本与时间线</td><td>待外部核验</td><td>补齐合规/标签/检测/物流/清关/仓储/渠道费用，并按出货前、到港前、上架前、试单后拆里程碑。</td></tr>",
        ]
    )
    audit_rows = "".join(
        f"<tr><td>{_html(item.get('timestamp'))}</td><td>{_html(item.get('action'))}</td><td>{_html(_short_text(item.get('details'), 120))}</td></tr>"
        for item in (report.get("audit_log") or [])[-10:]
        if isinstance(item, dict)
    )
    channel_list = "".join(f"<span>{_html(_zh_channel(channel))}</span>" for channel in channels)
    primary_checks = _html_bullets([_zh_channel(item) if "_" in _text(item) else _text(item) for item in route.get("primary_checks") or []], "确认销售路径")
    compat_route_checks = _joined_text(route.get("primary_checks")) if "cross border" in _plain_label(route.get("label")) else ""
    provenance = _generation_provenance_html(report, limit=180)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>LaunchFit 结构化审核简报 / Detailed LaunchFit Review</title>
  <style>
    @page {{ size: A4; margin: 13mm; }}
    * {{ box-sizing: border-box; }}
    body {{ color: #172033; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif; line-height: 1.42; letter-spacing: 0; font-size: 12px; }}
    h1 {{ font-size: 26px; margin: 0 0 5px; }}
    h2 {{ font-size: 16px; margin: 18px 0 8px; padding-bottom: 5px; border-bottom: 2px solid #172033; }}
    p {{ margin: 0 0 8px; }}
    .muted {{ color: #657181; }}
    .summary {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 10px; margin: 12px 0; }}
    .box {{ border: 1px solid #172033; padding: 10px; background: #fffdf8; }}
    .verdict {{ background: #142033; color: #fff; }}
    .verdict b {{ display: block; font-size: 24px; margin: 3px 0; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 10px 0; }}
    .metric {{ border: 1px solid #c8d0d8; padding: 7px; background: #f6f8fa; }}
    .metric b {{ display: block; font-size: 18px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 6px 0 14px; font-size: 10.5px; }}
    th, td {{ border: 1px solid #d6dde5; padding: 5px 6px; vertical-align: top; text-align: left; }}
    th {{ background: #eef3f7; color: #173c55; }}
    .risk th {{ background: #fff0ed; color: #8c241c; }}
    .todo th {{ background: #eef8f1; color: #2f6b4f; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 5px; margin: 5px 0 8px; }}
    .chips span {{ border: 1px solid #8ab4cc; background: #eef7fb; padding: 4px 7px; font-weight: 700; }}
    .engine {{ border-left: 5px solid #1769aa; padding-left: 9px; }}
    .engine2 {{ border-color: #2f7d5b; }}
    .engine3 {{ border-color: #7b6b47; }}
    .note {{ border: 1px solid #d6dde5; background: #fbfcfd; padding: 8px 10px; margin: 6px 0 10px; }}
    .provenance {{ border: 1px solid #d6dde5; background: #f7f4eb; color: #5e6a78; padding: 6px 8px; margin: 7px 0 10px; font-size: 10.5px; text-align: right; }}
    .compat {{ display: none; }}
    ul {{ margin: 4px 0 0; padding-left: 18px; }}
    li {{ margin-bottom: 4px; }}
  </style>
</head>
<body>
  <h1>LaunchFit 结构化审核简报</h1>
  <p class="muted">结论只基于已提交材料和规则路由；未完成官方外部核验前，不作为最终准入意见。<span class="compat">Detailed LaunchFit Review Go-to-market path {_html(_plain_label(route.get("label")))} {_html(compat_route_checks)}</span></p>
  <div class="provenance">{provenance}</div>

  <h2>一页摘要</h2>
  <div class="summary">
    <div class="box verdict"><span>当前结论</span><b>{_html(_zh_status(decision.get('status')))}</b><span>风险：{_html(_zh_risk(decision.get('risk_level')))} · {_html(_short_text(_zh_case_text(decision.get('summary')), 120))}</span></div>
    <div class="box"><b>范围</b><br>商品：{_html(product)}<br>路径：{_html(_zh_route_label(route.get('label')))}<br>原产地：{_html(_zh_country(case.get('origin_country')))}<br>目标市场：{_html(destination_label)}</div>
  </div>
  <div class="metrics">
    <div class="metric"><b>{len(findings)}</b>关键阻断</div>
    <div class="metric"><b>{len(missing)}</b>补件项</div>
    <div class="metric"><b>{evidence['user_provided']}</b>T4 用户材料</div>
    <div class="metric"><b>{evidence['needs_external_verification']}</b>需外部核验</div>
  </div>

  <h2>产品档案</h2>
  <table><tr><th>字段</th><th>内容</th><th>审核含义</th></tr>
    <tr><td>商品</td><td>{_html(product)}</td><td>所有标签、证书、授权、竞品和物流核验都必须回到同一 SKU/规格。</td></tr>
    <tr><td>品类</td><td>{_html(case.get('product_category'))} / {_html(case.get('subcategory'))}</td><td>品类决定监管、平台准入、标签和检测路径。</td></tr>
    <tr><td>原产地 → 目标市场</td><td>{_html(_zh_country(case.get('origin_country')))} → {_html(destination_label)}</td><td>支持多个目标市场逐一拆分，不能混成一个通用清单。</td></tr>
    <tr><td>销售路径</td><td>{_html(_zh_route_label(route.get('label')))}</td><td>跨境电商、实体贸易和混合路径的评估顺序不同。</td></tr>
  </table>

  <h2>三引擎综合建议</h2>
  <div class="note">先解决 P0 阻断，再做对标和落地预算。当前报告不伪造实时事实；未完成官方、平台、海关、进口商、物流和竞品渠道核验前，所有商业建议只作为工作清单。</div>

  <h2 class="engine">Engine 1：准入与合规审核</h2>
  <h2>市场准入概览</h2>
  <table><tr><th>目标市场</th><th>匹配规则包</th><th>核验任务</th><th>来源候选</th></tr>{_table_or_empty(market_rows, 4, '暂无目标市场拆解')}</table>

  <h2>关键阻断</h2>
  <table class="risk"><tr><th>等级</th><th>问题</th><th>动作</th></tr>{_table_or_empty(finding_rows, 3, '暂无关键阻断')}</table>

  <h2>补件清单</h2>
  <table class="todo"><tr><th>优先级</th><th>材料</th><th>为什么要</th><th>负责人</th></tr>{_table_or_empty(missing_rows, 4, '暂无补件项')}</table>

  <h2>已提交材料与资质状态</h2>
  <table><tr><th>材料</th><th>持有人</th><th>范围</th><th>有效期</th><th>证据层级</th></tr>{_table_or_empty(document_rows, 5, '未提交证书、授权或检测报告；用户图片/截图仍按 T4 处理')}</table>

  <h2>必须核验渠道</h2>
  <div class="chips">{channel_list or '<span>待补渠道</span>'}</div>
  <table><tr><th>目的地</th><th>渠道</th><th>来源候选</th><th>层级</th><th>要提取的事实</th></tr>{_table_or_empty(candidate_rows, 5, '暂无来源候选')}</table>

  <h2 class="engine engine2">Engine 2：本地化适配</h2>
  <h2>包装本地化</h2>
  <table><tr><th>维度</th><th>当前信号</th><th>建议动作</th></tr>{localization_rows}</table>

  <h2>目标市场对标</h2>
  <table><tr><th>竞品/参照</th><th>渠道</th><th>价格</th><th>宣称/卖点</th><th>数据基础</th></tr>{_table_or_empty(benchmark_rows, 5, '未提供目标市场竞品；需补 5-10 个当前平台、零售、DTC 或用户搜索渠道样本')}</table>

  <h2>对标调研设计</h2>
  <div class="note">当前不生成虚构竞品结论；没有实时或用户提供样本时，本节只定义最合适的采集渠道、样本类型和字段。采集完成后再更新价格带、包装惯例、评论主题和 Copy / Avoid / Improve。</div>
  <table><tr><th>样本类型</th><th>目标市场</th><th>优先渠道</th><th>样本边界</th><th>必须采集字段</th></tr>{benchmark_plan_rows}</table>

  <h2>对标分析矩阵</h2>
  <table><tr><th>样本</th><th>渠道</th><th>价格/规格/单位价</th><th>包装/标签信号</th><th>宣称/卖点</th><th>信任/认证信号</th><th>评论/口碑信号</th><th>启发</th></tr>{_table_or_empty(benchmark_matrix_rows, 8, '暂无可分析竞品样本；请按上方“对标调研设计”补齐当前样本')}</table>

  <h2>对标来源与核验边界</h2>
  <table><tr><th>来源</th><th>URL</th><th>层级</th><th>检查日期</th><th>可用边界</th></tr>{_table_or_empty(benchmark_source_rows, 5, '暂无 agent 主动检索的对标来源')}</table>

  <h2>对标摘要</h2>
  <table><tr><th>价格带</th><th>渠道图谱</th><th>包装惯例</th><th>宣称/证据</th><th>信任/认证</th><th>评论主题</th><th>Copy / Avoid / Improve</th><th>仍需核验</th></tr><tr><td>{_html(_zh_case_text(benchmark_summary.get('reference_price_band')))}</td><td>{_html(_zh_case_text(benchmark_summary.get('channel_map')))}</td><td>{_html(_zh_case_text(benchmark_summary.get('packaging_conventions')))}</td><td>{_html(_zh_case_text(benchmark_summary.get('claims_and_proof')))}</td><td>{_html(_zh_case_text(benchmark_summary.get('visible_trust_signals')))}</td><td>{_html(_zh_case_text(benchmark_summary.get('review_themes')))}</td><td>{_html(_zh_case_text(benchmark_summary.get('copy_avoid_improve')))}</td><td>{_html(_zh_case_text(benchmark_summary.get('verification_needed')))}</td></tr></table>

  <h2 class="engine engine3">Engine 3：全链路落地</h2>
  <h2>渠道与落地路径</h2>
  <table><tr><th>模块</th><th>当前状态</th><th>下一步</th></tr>{implementation_rows}</table>

  <h2>供应链与物流</h2>
  <table><tr><th>路线</th><th>模式</th><th>时效</th><th>成本依据</th><th>风险/限制</th></tr>{_table_or_empty(logistics_rows, 5, '未提供物流报价；需补货代/报关行/仓储路线、成本驱动、时效和约束')}</table>

  <h2>服务商与责任方</h2>
  <table><tr><th>角色</th><th>为什么重要</th><th>当前处理</th></tr>
    <tr><td>进口商/责任方</td><td>实体贸易和进口食品通常需要明确本地责任主体。</td><td>核验主体注册、授权链、进口文件和标签责任。</td></tr>
    <tr><td>报关行/清关服务商</td><td>决定申报、商检、税费、单证和到港处理路径。</td><td>取得当前清关文件清单、报价和异常处理说明。</td></tr>
    <tr><td>检测/认证/标签服务商</td><td>支撑标签、成分、标准、证书有效性和允许标识。</td><td>核验资质范围、样品/SKU、标准依据和有效期。</td></tr>
  </table>

  <h2>成本与时间线</h2>
  <table><tr><th>阶段</th><th>关键动作</th><th>依赖</th></tr>
    <tr><td>出货前</td><td>补齐 P0 材料、标签稿、主体/授权链、原产地和进口文件。</td><td>Engine 1 通过或人工复核。</td></tr>
    <tr><td>订舱/到港前</td><td>确认物流报价、报关资料、商检/抽检风险、保险和仓储。</td><td>进口商、报关行、货代确认。</td></tr>
    <tr><td>上架/铺货前</td><td>完成本地标签、渠道买方要求、竞品价格和销售文案核验。</td><td>Engine 2 对标和标签核验。</td></tr>
    <tr><td>试单后</td><td>复盘清关、破损、时效、毛利、渠道反馈和复购信号。</td><td>实际物流和销售数据。</td></tr>
  </table>

  <h2>核验任务</h2>
  <table><tr><th>优先级</th><th>目的地</th><th>渠道</th><th>任务</th></tr>{_table_or_empty(task_rows, 4, '暂无核验任务')}</table>

  <h2>目的地拆解 <span class="compat">Per-destination market reviews</span></h2>
  <table><tr><th>目标市场</th><th>匹配规则包</th><th>核验任务</th><th>来源候选</th></tr>{_table_or_empty(market_rows, 4, '暂无目标市场拆解')}</table>

  <h2>来源候选</h2>
  <table><tr><th>目的地</th><th>渠道</th><th>来源</th><th>层级</th></tr>{_table_or_empty(source_rows, 4, '暂无来源候选')}</table>

  <h2>待查证项</h2>
  <table><tr><th>优先级</th><th>目的地</th><th>渠道</th><th>待查事项</th><th>建议层级</th></tr>{_table_or_empty(pending_rows, 5, '暂无待外部核验项')}</table>

  <h2>证据等级 <span class="compat">Evidence and source status</span></h2>
  <table><tr><th>证据组</th><th>数量</th><th>当前状态</th><th>处理方式</th></tr>{evidence_rows}</table>

  <h2>审计摘要 <span class="compat">Audit log</span></h2>
  <table><tr><th>时间</th><th>动作</th><th>说明</th></tr>{audit_rows}</table>

  <h2>Source candidates</h2>
  <p class="muted">上方“必须核验渠道”已列出来源候选；本标题保留用于机器读取和版本兼容。</p>
  <h2>Research tasks</h2>
  <p class="muted">上方“核验任务”已列出 P0/P1 任务；本标题保留用于机器读取和版本兼容。</p>

  <h2>说明</h2>
  <p>{_html(_zh_case_text(report.get('disclaimer') or 'Operational qualification review only; not legal advice.'))} 用户图片、截图和自填信息默认属于 T4，只证明“用户提交了这些材料”，不等于官方事实已成立。</p>
</body>
</html>
"""


def _chrome_path() -> str | None:
    for candidate in (
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ):
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def _write_html_or_export(output_file: str, html_text: str, mode: str) -> int:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    if suffix in {"", ".html", ".htm"}:
        output_path.write_text(html_text, encoding="utf-8")
        return 0

    chrome = _chrome_path()
    if chrome is None:
        print(
            f"ERROR: Chrome/Chromium is required to export {suffix}; write .html instead or install Chrome.",
            file=sys.stderr,
        )
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / f"{mode}.html"
        html_path.write_text(html_text, encoding="utf-8")
        if mode == "card" and suffix == ".png":
            command = [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--window-size=1200,1280",
                f"--screenshot={output_path}",
                html_path.resolve().as_uri(),
            ]
        elif mode == "detail" and suffix == ".pdf":
            command = [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                f"--print-to-pdf={output_path}",
                html_path.resolve().as_uri(),
            ]
        else:
            expected = ".png" if mode == "card" else ".pdf"
            print(
                f"ERROR: unsupported {mode} output suffix '{suffix}'. Use .html or {expected}.",
                file=sys.stderr,
            )
            return 2
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as exc:
            print(f"ERROR: failed to export {output_path}: {exc.stderr.strip()}", file=sys.stderr)
            return 1
    return 0


def render_launch_markdown(report: dict[str, Any]) -> str:
    case = report.get("case") if isinstance(report.get("case"), dict) else {}
    decision = report.get("decision") if isinstance(report.get("decision"), dict) else {}
    route = report.get("go_to_market_route") if isinstance(report.get("go_to_market_route"), dict) else go_to_market_route_profile(_text(case.get("go_to_market_model")) or "unknown")
    summary = report.get("market_benchmark_summary") if isinstance(report.get("market_benchmark_summary"), dict) else {}
    metadata = _generation_metadata(report)
    method_text = _md_list(metadata.get("search_methods"))
    lines: list[str] = [
        "# Cross-Border Product Launch Review",
        "",
        "## Snapshot",
        f"- Product: {_md_cell(case.get('subcategory') or case.get('product_category'))}",
        f"- Origin: {_md_cell(case.get('origin_country'))}",
        f"- Go-to-market path: {_md_cell(route.get('label'))}",
        f"- Target markets/platform: {_md_cell(_md_list(case.get('destination_markets')) or case.get('destination_market'))} / {_md_cell(case.get('platform'))}",
        f"- Launch view: {_md_cell(decision.get('status'))}",
        f"- Biggest risk: {_md_cell(decision.get('summary'))}",
        "- Next action: Complete P0/P1 research tasks, resolve missing materials, and verify current official/source data before ordering, printing, or listing.",
        f"- Generation note: Agent {_md_cell(metadata.get('agent'))}; model {_md_cell(metadata.get('model'))}; search routes {_md_cell(method_text)}; generated {_md_cell(metadata.get('generated_at'))}.",
        "",
        "## Top Risks Before Listing",
        "| Risk | Impact | Owner | Fix |",
        "|---|---|---|---|",
    ]
    for finding in (report.get("findings") or [])[:8]:
        if not isinstance(finding, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(finding.get("observed_issue")),
                    _md_cell(finding.get("business_impact")),
                    "applicant / reviewer",
                    _md_cell(finding.get("required_action")),
                ]
            )
            + " |"
        )
    if len(lines) >= 8 and lines[-1] == "|---|---|---|---|":
        lines.append("| No material risk rows |  |  |  |")

    lines.extend(
        [
            "",
            "## Target-Market Benchmarks",
            "| Benchmark product | Channel role | Pack/unit price | Positioning | Visible trust signals | What it teaches us |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in report.get("market_benchmarks") or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("product_name")),
                    _md_cell(row.get("channel_role")),
                    _md_cell(row.get("unit_price") or row.get("price") or row.get("pack_size")),
                    _md_cell(row.get("positioning")),
                    _md_cell(_md_list(row.get("certification_signals")) or _md_list(row.get("visible_claims"))),
                    _md_cell(row.get("takeaway")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## What The Benchmarks Mean",
            "| Question | Conclusion | Action |",
            "|---|---|---|",
            f"| Reference price band | {_md_cell(summary.get('reference_price_band'))} | Verify current prices and unit economics. |",
            f"| Channel map | {_md_cell(summary.get('channel_map'))} | Decide which channel sets the launch reference. |",
            f"| Packaging conventions | {_md_cell(summary.get('packaging_conventions'))} | Match local expectations before printing. |",
            f"| Claims and proof | {_md_cell(summary.get('claims_and_proof'))} | Remove or substantiate regulated claims. |",
            f"| Review themes | {_md_cell(summary.get('review_themes'))} | Turn repeated objections into listing proof. |",
            f"| Gap opportunity | {_md_cell(summary.get('gap_opportunity'))} | Pick copy / avoid / improve actions. |",
            "",
            "## Packaging / Label",
            "| Area | Risk | Suggested change |",
            "|---|---|---|",
        ]
    )
    packaging_findings = [
        finding
        for finding in report.get("findings") or []
        if isinstance(finding, dict) and finding.get("finding_id", "").startswith("OFF-PACK")
    ]
    for finding in packaging_findings:
        lines.append(
            f"| Packaging / claims | {_md_cell(finding.get('observed_issue'))} | {_md_cell(finding.get('required_action'))} |"
        )
    if not packaging_findings:
        lines.append("| Packaging / claims | No offline packaging finding generated | Verify current market label rules. |")

    lines.extend(
        [
            "",
            "## Platform Admission",
            "| Requirement | Status | Evidence/action |",
            "|---|---|---|",
        ]
    )
    for req in (report.get("requirements") or [])[:10]:
        if not isinstance(req, dict):
            continue
        lines.append(
            f"| {_md_cell(req.get('requirement'))} | {_md_cell(req.get('status'))} | {_md_cell(req.get('notes'))} |"
        )

    lines.extend(
        [
            "",
            "## Logistics / Budget",
            "| Route | Fit | Risk | Preparation |",
            "|---|---|---|---|",
        ]
    )
    for row in report.get("offline_logistics") or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("route")),
                    _md_cell(row.get("best_for")),
                    _md_cell(_md_list(row.get("risks")) or row.get("cost_basis")),
                    _md_cell(_md_list(row.get("preparation"))),
                ]
            )
            + " |"
        )
    if not report.get("offline_logistics"):
        lines.append("| No logistics route supplied | Unknown | Missing budget basis | Add route, time, cost driver, constraints. |")

    lines.extend(
        [
            "",
            "## Research Routing",
            "| Destination | Channel | Why it matters | What to verify |",
            "|---|---|---|---|",
        ]
    )
    candidate_count = 0
    for market_review in report.get("market_reviews") or []:
        if not isinstance(market_review, dict):
            continue
        destination = market_review.get("destination_market")
        for candidate in (market_review.get("source_candidates") or [])[:5]:
            if not isinstance(candidate, dict):
                continue
            candidate_count += 1
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(destination),
                        _md_cell(candidate.get("channel_type")),
                        _md_cell(candidate.get("why")),
                        _md_cell(_md_list(candidate.get("expected_facts"))),
                    ]
                )
                + " |"
            )
    if candidate_count == 0:
        lines.append("| No destination routing generated | Unknown | Missing origin/destination scope | Add origin_country and destination_markets. |")

    lines.extend(
        [
            "",
            "## Research Tasks",
            "| Priority | Destination | Task | Evidence fields |",
            "|---|---|---|---|",
        ]
    )
    task_count = 0
    for task in (report.get("research_tasks") or [])[:12]:
        if not isinstance(task, dict):
            continue
        task_count += 1
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(task.get("priority")),
                    _md_cell(task.get("destination_market")),
                    _md_cell(task.get("instruction")),
                    _md_cell(_md_list(task.get("evidence_fields"))),
                ]
            )
            + " |"
        )
    if task_count == 0:
        lines.append("| P0 | Unknown | Generate market research tasks from origin and destination scope. | origin_country, destination_markets |")

    lines.extend(
        [
            "",
            "## Missing Materials",
            "| Material | Why needed | Who provides it |",
            "|---|---|---|",
        ]
    )
    for item in report.get("missing_materials") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| {_md_cell(item.get('material'))} | {_md_cell(item.get('why_required'))} | {_md_cell(item.get('owner'))} |"
        )

    lines.extend(
        [
            "",
            "## Assumptions And Verification Needed",
            "| Item | Current basis | How to verify |",
            "|---|---|---|",
            f"| Benchmark data | {_md_cell(summary.get('verification_needed'))} | Recheck live marketplace, retail, DTC, or screenshot source URLs. |",
            "| Applicant documents | T4 submitted evidence only | Verify issuer, registry, holder, scope, territory, platform, and validity. |",
            "| Platform/regulator rules | Rulepack routing plus source freshness | Check current official platform and regulator pages before final action. |",
            "| Origin and destination routes | Generated research tasks | Check official origin/export, destination/import, regulator, customs, and platform channels for every destination. |",
            "| Logistics costs | User-provided or rough offline quotations | Confirm with forwarder, 3PL, warehouse, and import/customs route. |",
            "",
            "## Disclaimer",
            _md_cell(report.get("disclaimer") or "Operational launch-readiness review only; not legal advice."),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def empty_benchmark_summary() -> dict[str, Any]:
    return {
        "reference_price_band": "",
        "channel_map": "",
        "packaging_conventions": "",
        "claims_and_proof": "",
        "visible_trust_signals": "",
        "review_themes": "",
        "gap_opportunity": "",
        "copy_avoid_improve": "",
        "listing_preparation": "",
        "verification_needed": "",
    }

def build_supplement_message(missing_materials: list[dict[str, Any]]) -> str:
    if not missing_materials:
        return "您好，请先补充平台、目标市场、商品类目和审核目的，以便启动资质审核。"
    lines = ["您好，当前申请暂无法完成审核。请补充以下材料：", ""]
    for idx, item in enumerate(missing_materials[:8], start=1):
        lines.extend(
            [
                f"{idx}. {item.get('material', '')}",
                f"   - 原因：{item.get('why_required', '')}",
                f"   - 要求：材料需覆盖本次平台、目标市场、产品范围、主体名称和有效期。",
                f"   - 可接受替代：{item.get('acceptable_replacement', '')}",
                "",
            ]
        )
    lines.append("请确保材料中的主体名称、品牌、产品范围、销售地区和平台授权范围与本次申请一致。")
    return "\n".join(lines)


def _keyword_hit(keywords: Any, target: str) -> bool:
    if not isinstance(keywords, list):
        return False
    return any(isinstance(keyword, str) and keyword.lower() in target for keyword in keywords)


def rulepack_template(country_code: str, country_name: str, region: str = "") -> dict[str, Any]:
    code = country_code.strip().upper()
    name = country_name.strip()
    pack_id = f"country-{code}"
    return {
        "schema_version": "1.0",
        "pack_id": pack_id,
        "type": "country",
        "name": f"{name} qualification review pack",
        "jurisdiction": {
            "country_code": code,
            "country_name": name,
            "region": region.strip(),
        },
        "maturity": "seed",
        "version": "0.1.0",
        "updated_at": today(),
        "updated_by": "",
        "change_note": "Initial scaffold. Fill with verified official sources before use for final decisions.",
        "match": {
            "keywords": [code.lower(), name.lower()],
        },
        "freshness_policy": {
            "platform_policy_days": 90,
            "regulator_source_days": 365,
            "customs_tax_days": 180,
            "high_risk_category_days": 30,
        },
        "golden_case_ids": [],
        "regulator_map": [
            {
                "category_family": "food|cosmetics|supplements|electronics|household|toys|medical|other",
                "authority": "",
                "official_url": "",
                "notes": "Add official regulator for this category family.",
            }
        ],
        "requirements": [
            {
                "requirement_id": f"{pack_id}-seller-eligibility",
                "surface": "seller",
                "category_scope": "*",
                "applicant_role_scope": "*",
                "business_model_scope": "*",
                "requirement": f"Confirm seller/entity eligibility for {name} marketplace or import route.",
                "mandatory": "conditional",
                "evidence_expected": [
                    "business registration",
                    "tax/payee evidence where required",
                    "official platform or regulator source",
                ],
                "decision_effect": "Cannot approve until the applicable official route is verified.",
                "source_ids": [],
                "freshness_days": 90,
                "notes": "Replace this scaffold with country-specific official requirements.",
            }
        ],
        "sources": [],
        "gaps": [
            "Add official company registry source if available.",
            "Add official trademark/IP registry source if available.",
            "Add official customs/import authority source.",
            "Add product regulator sources by category family.",
        ],
    }


def check_case(case: dict[str, Any], review: dict[str, Any]) -> list[str]:
    """Check a produced review JSON against a golden case expectation."""
    errors = validate_payload(review)
    expected = case.get("expected") if isinstance(case.get("expected"), dict) else {}

    status = (review.get("decision") or {}).get("status")
    allowed = expected.get("status_any_of") or []
    if allowed and status not in allowed:
        errors.append(f"decision.status is '{status}'; expected one of {allowed}")

    findings = [item for item in review.get("findings") or [] if isinstance(item, dict)]
    for need in expected.get("min_findings") or []:
        severity = need.get("severity") if isinstance(need, dict) else None
        if severity and not any(f.get("severity") == severity for f in findings):
            errors.append(f"expected at least one finding with severity '{severity}'")

    requirements = [item for item in review.get("requirements") or [] if isinstance(item, dict)]
    for required_status in expected.get("require_requirement_status") or []:
        if not any(r.get("status") == required_status for r in requirements):
            errors.append(f"expected at least one requirement with status '{required_status}'")

    return errors


def check_benchmark_case(case: dict[str, Any], worksheet: dict[str, Any]) -> list[str]:
    errors = validate_benchmark_worksheet(worksheet)
    if errors:
        return errors
    expected = case.get("expected") if isinstance(case.get("expected"), dict) else {}
    summary = summarize_benchmark_worksheet(worksheet)
    source_types = set(summary.get("source_types_covered", []))
    for source_type in expected.get("source_types") or []:
        if source_type not in source_types:
            errors.append(f"expected benchmark source type '{source_type}'")
    min_rows = expected.get("min_rows")
    if isinstance(min_rows, int) and summary.get("row_count", 0) < min_rows:
        errors.append(f"expected at least {min_rows} benchmark rows")
    if expected.get("requires_verification_warning") and not summary.get("verification_needed"):
        errors.append("expected verification warning for non-current benchmark rows")
    return errors


def replay_golden_cases(cases_dir: Path, reviews_dir: Path) -> tuple[list[str], list[str]]:
    passes: list[str] = []
    errors: list[str] = []
    case_paths = sorted(cases_dir.glob("*.json"))
    if not case_paths:
        errors.append(f"no case files found in {cases_dir}")
        return passes, errors
    for case_path in case_paths:
        try:
            case = json.loads(case_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{case_path}: failed to read case JSON: {exc}")
            continue
        if not isinstance(case, dict):
            errors.append(f"{case_path}: top-level case JSON must be an object")
            continue
        case_id = str(case.get("case_id") or case_path.stem)
        benchmark_fixture = case.get("benchmark_fixture")
        if isinstance(benchmark_fixture, str) and benchmark_fixture.strip():
            benchmark_path = SKILL_ROOT / benchmark_fixture.strip()
            if not benchmark_path.exists():
                errors.append(f"{case_id}: missing benchmark fixture {benchmark_path}")
                continue
            try:
                worksheet = json.loads(benchmark_path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"{case_id}: failed to read benchmark fixture JSON: {exc}")
                continue
            if not isinstance(worksheet, dict):
                errors.append(f"{case_id}: benchmark fixture JSON must be an object")
                continue
            case_errors = check_benchmark_case(case, worksheet)
            if case_errors:
                errors.extend(f"{case_id}: {error}" for error in case_errors)
            else:
                passes.append(case_id)
            continue
        review_fixture = case.get("review_fixture")
        if isinstance(review_fixture, str) and review_fixture.strip():
            review_path = SKILL_ROOT / review_fixture.strip()
        else:
            review_path = reviews_dir / f"{case_id}.json"
        if not review_path.exists():
            errors.append(f"{case_id}: missing produced review fixture {review_path}")
            continue
        try:
            review = json.loads(review_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{case_id}: failed to read review JSON: {exc}")
            continue
        if not isinstance(review, dict):
            errors.append(f"{case_id}: top-level review JSON must be an object")
            continue
        case_errors = check_case(case, review)
        if case_errors:
            errors.extend(f"{case_id}: {error}" for error in case_errors)
        else:
            passes.append(case_id)
    return passes, errors


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_payload(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _require(data.get("review_type") == "cross_border_ecommerce_qualification", "review_type must be cross_border_ecommerce_qualification", errors)
    _require(isinstance(data.get("case"), dict), "case must be an object", errors)
    _require(isinstance(data.get("decision"), dict), "decision must be an object", errors)
    _require(isinstance(data.get("market_benchmark_summary"), dict), "market_benchmark_summary must be an object", errors)
    if "generation_metadata" in data:
        metadata = data.get("generation_metadata")
        if not isinstance(metadata, dict):
            errors.append("generation_metadata must be an object")
        else:
            _require(bool(metadata.get("agent")), "generation_metadata.agent is required", errors)
            _require(bool(metadata.get("model")), "generation_metadata.model is required", errors)
            _require(isinstance(metadata.get("search_methods"), list), "generation_metadata.search_methods must be a list", errors)
            _require(bool(metadata.get("generated_at")), "generation_metadata.generated_at is required", errors)

    decision = data.get("decision") if isinstance(data.get("decision"), dict) else {}
    status = decision.get("status")
    _require(status in ALLOWED_DECISIONS, f"decision.status must be one of {sorted(ALLOWED_DECISIONS)}", errors)
    _require(decision.get("risk_level") in ALLOWED_RISK_LEVELS, f"decision.risk_level must be one of {sorted(ALLOWED_RISK_LEVELS)}", errors)

    case = data.get("case") if isinstance(data.get("case"), dict) else {}
    if case.get("go_to_market_model") and case.get("go_to_market_model") not in ALLOWED_GO_TO_MARKET_MODELS:
        errors.append(f"case.go_to_market_model must be one of {sorted(ALLOWED_GO_TO_MARKET_MODELS)}")
    if status in DEFINITIVE_STATUSES:
        for field in REQUIRED_CASE_FIELDS:
            _require(bool(case.get(field)), f"case.{field} is required for a definitive '{status}' decision", errors)
        if case.get("go_to_market_model") in {"cross_border_ecommerce", "hybrid"}:
            _require(bool(case.get("platform")), f"case.platform is required for a definitive '{status}' decision", errors)

    for key in ("documents", "market_benchmarks", "requirements", "findings", "missing_materials", "evidence", "sources", "audit_log"):
        _require(isinstance(data.get(key), list), f"{key} must be a list", errors)

    evidence_ids = {
        str(item.get("evidence_id"))
        for item in data.get("evidence") or []
        if isinstance(item, dict) and item.get("evidence_id")
    }
    declared_source_ids = {
        str(item.get("source_id"))
        for item in data.get("sources") or []
        if isinstance(item, dict) and item.get("source_id")
    }

    for idx, req in enumerate(data.get("requirements") or []):
        if not isinstance(req, dict):
            errors.append(f"requirements[{idx}] must be an object")
            continue
        _require(req.get("status") in ALLOWED_REQUIREMENT_STATUS, f"requirements[{idx}].status is invalid", errors)
        _require(bool(req.get("requirement")), f"requirements[{idx}].requirement is required", errors)
        for eid in req.get("matched_evidence_ids") or []:
            _require(str(eid) in evidence_ids, f"requirements[{idx}] references missing evidence_id {eid}", errors)
        for sid in req.get("source_ids") or []:
            _require(str(sid) in declared_source_ids, f"requirements[{idx}] references missing source_id {sid}", errors)

    for idx, benchmark in enumerate(data.get("market_benchmarks") or []):
        if not isinstance(benchmark, dict):
            errors.append(f"market_benchmarks[{idx}] must be an object")
            continue
        _require(bool(benchmark.get("product_name")), f"market_benchmarks[{idx}].product_name is required", errors)
        _require(bool(benchmark.get("channel")), f"market_benchmarks[{idx}].channel is required", errors)
        _require(benchmark.get("channel_role") in ALLOWED_CHANNEL_ROLES, f"market_benchmarks[{idx}].channel_role is invalid", errors)
        _require(benchmark.get("positioning") in ALLOWED_POSITIONING, f"market_benchmarks[{idx}].positioning is invalid", errors)
        _require(benchmark.get("data_basis") in ALLOWED_BENCHMARK_BASIS, f"market_benchmarks[{idx}].data_basis is invalid", errors)
        for list_key in ("visible_claims", "packaging_signals", "certification_signals", "review_signals", "source_ids", "evidence_ids"):
            _require(isinstance(benchmark.get(list_key), list), f"market_benchmarks[{idx}].{list_key} must be a list", errors)
        for sid in benchmark.get("source_ids") or []:
            _require(str(sid) in declared_source_ids, f"market_benchmarks[{idx}] references missing source_id {sid}", errors)
        for eid in benchmark.get("evidence_ids") or []:
            _require(str(eid) in evidence_ids, f"market_benchmarks[{idx}] references missing evidence_id {eid}", errors)

    benchmark_summary = data.get("market_benchmark_summary") if isinstance(data.get("market_benchmark_summary"), dict) else {}
    for key in (
        "reference_price_band",
        "channel_map",
        "packaging_conventions",
        "claims_and_proof",
        "visible_trust_signals",
        "review_themes",
        "gap_opportunity",
        "copy_avoid_improve",
        "listing_preparation",
        "verification_needed",
    ):
        _require(key in benchmark_summary, f"market_benchmark_summary.{key} is required", errors)

    finding_severities: set[str] = set()
    for idx, finding in enumerate(data.get("findings") or []):
        if not isinstance(finding, dict):
            errors.append(f"findings[{idx}] must be an object")
            continue
        _require(finding.get("severity") in ALLOWED_SEVERITY, f"findings[{idx}].severity is invalid", errors)
        _require(bool(finding.get("observed_issue")), f"findings[{idx}].observed_issue is required", errors)
        _require(bool(finding.get("required_action")), f"findings[{idx}].required_action is required", errors)
        if finding.get("severity") in ALLOWED_SEVERITY:
            finding_severities.add(finding["severity"])
        for sid in finding.get("source_ids") or []:
            _require(str(sid) in declared_source_ids, f"findings[{idx}] references missing source_id {sid}", errors)

    if status == "approve":
        _require(
            not finding_severities.intersection({"critical", "high"}),
            "approve is not allowed while critical/high findings remain",
            errors,
        )
    if status == "conditional_approve":
        _require(
            "critical" not in finding_severities,
            "conditional_approve is not allowed while critical findings remain",
            errors,
        )

    for idx, evidence in enumerate(data.get("evidence") or []):
        if not isinstance(evidence, dict):
            errors.append(f"evidence[{idx}] must be an object")
            continue
        _require(evidence.get("tier") in ALLOWED_TIERS, f"evidence[{idx}].tier is invalid", errors)
        _require(bool(evidence.get("checked_at")), f"evidence[{idx}].checked_at is required", errors)

    return errors


def validate_rulepack(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _require(data.get("schema_version") == "1.0", "schema_version must be 1.0", errors)
    _require(bool(data.get("pack_id")), "pack_id is required", errors)
    _require(data.get("type") in ALLOWED_PACK_TYPES, f"type must be one of {sorted(ALLOWED_PACK_TYPES)}", errors)
    _require(data.get("maturity") in ALLOWED_PACK_MATURITY, f"maturity must be one of {sorted(ALLOWED_PACK_MATURITY)}", errors)
    _require(isinstance(data.get("jurisdiction"), dict), "jurisdiction must be an object", errors)
    _require(isinstance(data.get("requirements"), list), "requirements must be a list", errors)
    _require(isinstance(data.get("sources"), list), "sources must be a list", errors)
    if data.get("type") != "global":
        match = data.get("match") if isinstance(data.get("match"), dict) else {}
        _require(isinstance(match.get("keywords"), list) and bool(match.get("keywords")), "non-global packs need match.keywords", errors)

    source_ids = set()
    source_by_id: dict[str, dict[str, Any]] = {}
    for idx, source in enumerate(data.get("sources") or []):
        if not isinstance(source, dict):
            errors.append(f"sources[{idx}] must be an object")
            continue
        sid = source.get("source_id")
        _require(bool(sid), f"sources[{idx}].source_id is required", errors)
        if sid:
            sid_text = str(sid)
            _require(sid_text not in source_ids, f"sources[{idx}].source_id is duplicated: {sid_text}", errors)
            source_ids.add(sid_text)
            source_by_id[sid_text] = source
        _require(bool(source.get("title")), f"sources[{idx}].title is required", errors)
        _require(source.get("tier") in ALLOWED_TIERS, f"sources[{idx}].tier is invalid", errors)
        _require(bool(source.get("checked_at")), f"sources[{idx}].checked_at is required", errors)
        _require(parse_date(source.get("checked_at")) is not None, f"sources[{idx}].checked_at must be YYYY-MM-DD", errors)
        _require(bool(source.get("url")), f"sources[{idx}].url is required", errors)
        if source.get("tier") in AUTHORITATIVE_TIERS:
            _require(bool(source.get("language")), f"sources[{idx}].language is required for T1/T2 sources", errors)
            _require(bool(source.get("confirms")), f"sources[{idx}].confirms is required for T1/T2 sources", errors)

    requirement_ids: set[str] = set()
    mandatory_count = 0
    mandatory_with_authoritative_source = 0
    for idx, req in enumerate(data.get("requirements") or []):
        if not isinstance(req, dict):
            errors.append(f"requirements[{idx}] must be an object")
            continue
        rid = req.get("requirement_id")
        _require(bool(rid), f"requirements[{idx}].requirement_id is required", errors)
        if rid:
            rid_text = str(rid)
            _require(rid_text not in requirement_ids, f"requirements[{idx}].requirement_id is duplicated: {rid_text}", errors)
            requirement_ids.add(rid_text)
        _require(req.get("surface") in ALLOWED_SURFACES, f"requirements[{idx}].surface is invalid", errors)
        _require(bool(req.get("requirement")), f"requirements[{idx}].requirement is required", errors)
        _require("mandatory" in req, f"requirements[{idx}].mandatory is required", errors)
        _require(isinstance(req.get("evidence_expected"), list), f"requirements[{idx}].evidence_expected must be a list", errors)
        _require(bool(req.get("decision_effect")), f"requirements[{idx}].decision_effect is required", errors)
        _require(isinstance(req.get("source_ids"), list), f"requirements[{idx}].source_ids must be a list", errors)
        if "freshness_days" in req:
            _require(isinstance(req.get("freshness_days"), int) and req.get("freshness_days") > 0, f"requirements[{idx}].freshness_days must be a positive integer", errors)
        has_authoritative_source = False
        for sid in req.get("source_ids") or []:
            _require(str(sid) in source_ids, f"requirements[{idx}] references missing source_id {sid}", errors)
            if (source_by_id.get(str(sid)) or {}).get("tier") in AUTHORITATIVE_TIERS:
                has_authoritative_source = True
        if req.get("mandatory") is True:
            mandatory_count += 1
            if has_authoritative_source:
                mandatory_with_authoritative_source += 1

    if data.get("maturity") in MATURE_PACKS:
        for idx, req in enumerate(data.get("requirements") or []):
            if isinstance(req, dict) and req.get("mandatory") is True:
                _require(bool(req.get("source_ids")), f"validated/production mandatory requirements[{idx}] need source_ids", errors)
        cases = data.get("golden_case_ids")
        _require(isinstance(cases, list) and len(cases) >= 3, "validated/production packs need at least 3 golden_case_ids", errors)
        for case_id in cases or []:
            case_path = SKILL_ROOT / "cases" / f"{case_id}.json"
            _require(case_path.exists(), f"golden case not found: cases/{case_id}.json", errors)

    if data.get("maturity") == "production" and mandatory_count:
        ratio = mandatory_with_authoritative_source / mandatory_count
        _require(ratio >= 0.8, "production packs need at least 80% of mandatory requirements backed by T1/T2 sources", errors)

    return errors


def validate_rulepack_index() -> list[str]:
    errors: list[str] = []
    index = load_rulepack_index()
    seen: set[str] = set()
    _require(isinstance(index.get("packs"), list), "index.packs must be a list", errors)
    for idx, entry in enumerate(index.get("packs") or []):
        if not isinstance(entry, dict):
            errors.append(f"packs[{idx}] must be an object")
            continue
        pack_id = entry.get("pack_id")
        path_text = entry.get("path")
        _require(bool(pack_id), f"packs[{idx}].pack_id is required", errors)
        if pack_id:
            _require(str(pack_id) not in seen, f"packs[{idx}].pack_id is duplicated: {pack_id}", errors)
            seen.add(str(pack_id))
        _require(bool(path_text), f"packs[{idx}].path is required", errors)
        pack_path = SKILL_ROOT / str(path_text)
        _require(pack_path.exists(), f"packs[{idx}] path not found: {path_text}", errors)
        if not pack_path.exists():
            continue
        try:
            pack = json.loads(pack_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"packs[{idx}] failed to read {path_text}: {exc}")
            continue
        if not isinstance(pack, dict):
            errors.append(f"packs[{idx}] file must contain a JSON object: {path_text}")
            continue
        _require(pack.get("pack_id") == pack_id, f"packs[{idx}] pack_id mismatch with {path_text}", errors)
        _require(pack.get("type") == entry.get("type"), f"packs[{idx}] type mismatch with {path_text}", errors)
        _require(pack.get("maturity") == entry.get("maturity"), f"packs[{idx}] maturity mismatch with {path_text}", errors)
        errors.extend(f"{path_text}: {error}" for error in validate_rulepack(pack))
    for idx, combo in enumerate(index.get("priority_combinations") or []):
        if not isinstance(combo, dict):
            errors.append(f"priority_combinations[{idx}] must be an object")
            continue
        _require(bool(combo.get("combo_id")), f"priority_combinations[{idx}].combo_id is required", errors)
        _require(isinstance(combo.get("criteria"), dict), f"priority_combinations[{idx}].criteria must be an object", errors)
        _require(isinstance(combo.get("expected_packs"), list), f"priority_combinations[{idx}].expected_packs must be a list", errors)
        for expected_pack in combo.get("expected_packs") or []:
            _require(str(expected_pack) in seen, f"priority_combinations[{idx}] references missing pack {expected_pack}", errors)
        _require(isinstance(combo.get("verification_tasks"), list) and bool(combo.get("verification_tasks")), f"priority_combinations[{idx}].verification_tasks must be a non-empty list", errors)
    return errors


def source_freshness(paths: list[str] | None = None) -> dict[str, Any]:
    if paths:
        pack_paths = [Path(path) for path in paths]
    else:
        pack_paths = [SKILL_ROOT / entry["path"] for entry in load_rulepack_index().get("packs", [])]

    as_of = _dt.date.today()
    stale: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []
    checked_count = 0
    for pack_path in pack_paths:
        data = json.loads(pack_path.read_text(encoding="utf-8"))
        sources = {
            str(source.get("source_id")): source
            for source in data.get("sources", [])
            if isinstance(source, dict) and source.get("source_id")
        }
        for req in data.get("requirements", []):
            if not isinstance(req, dict):
                continue
            freshness_days = req.get("freshness_days") if isinstance(req.get("freshness_days"), int) else 365
            source_ids = req.get("source_ids") or []
            if not source_ids:
                unverified.append(
                    {
                        "pack": data.get("pack_id"),
                        "maturity": data.get("maturity"),
                        "requirement_id": req.get("requirement_id"),
                        "issue": "requirement has no official source_ids; verify before final decision",
                    }
                )
            if data.get("maturity") in MATURE_PACKS and req.get("mandatory") is True and not source_ids:
                missing.append(
                    {
                        "pack": data.get("pack_id"),
                        "requirement_id": req.get("requirement_id"),
                        "issue": "mandatory mature requirement has no source_ids",
                    }
                )
            for source_id in source_ids:
                source = sources.get(str(source_id))
                if source is None:
                    missing.append(
                        {
                            "pack": data.get("pack_id"),
                            "requirement_id": req.get("requirement_id"),
                            "source_id": source_id,
                            "issue": "referenced source is missing",
                        }
                    )
                    continue
                checked_count += 1
                source_age = age_days(source.get("checked_at"), as_of)
                if source_age is None or source_age > freshness_days:
                    stale.append(
                        {
                            "pack": data.get("pack_id"),
                            "requirement_id": req.get("requirement_id"),
                            "source_id": source_id,
                            "checked_at": source.get("checked_at"),
                            "age_days": source_age,
                            "freshness_days": freshness_days,
                        }
                    )
    return {
        "as_of": as_of.isoformat(),
        "checked_source_links": checked_count,
        "unverified_requirements": unverified,
        "stale": stale,
        "missing": missing,
    }


def cmd_sample(_: argparse.Namespace) -> int:
    print(json.dumps(sample(), ensure_ascii=False, indent=2))
    return 0


def cmd_checklist(args: argparse.Namespace) -> int:
    print(json.dumps(checklist(args.platform, args.market, args.category), ensure_ascii=False, indent=2))
    return 0


def cmd_review_skeleton(args: argparse.Namespace) -> int:
    payload = review_skeleton(
        platform=args.platform,
        market=args.market,
        category=args.category,
        applicant_name=args.applicant_name or "",
        applicant_role=args.applicant_role or "",
        business_model=args.business_model or "",
        brand_name=args.brand_name or "",
        purpose=args.purpose or "launch readiness and qualification intake",
        case_id=args.case_id or "",
        marketplace_site=args.marketplace_site or "",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_benchmark_template(args: argparse.Namespace) -> int:
    payload = benchmark_worksheet_template(
        market=args.market,
        category=args.category,
        product=args.product or "",
        platform=args.platform or "",
        count=args.count,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_benchmark_validate(args: argparse.Namespace) -> int:
    data = _load_json_object(args.file, "benchmark worksheet")
    if data is None:
        return 2
    errors = validate_benchmark_worksheet(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def cmd_benchmark_summarize(args: argparse.Namespace) -> int:
    data = _load_json_object(args.file, "benchmark worksheet")
    if data is None:
        return 2
    errors = validate_benchmark_worksheet(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summarize_benchmark_worksheet(data), ensure_ascii=False, indent=2))
    return 0


def cmd_bundle_template(args: argparse.Namespace) -> int:
    payload = offline_bundle_template(
        platform=args.platform,
        market=args.market,
        category=args.category,
        product=args.product or "",
        origin_country=args.origin_country or "",
        destination_markets=args.destination_market or [args.market],
        go_to_market_model=args.go_to_market_model,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_bundle_validate(args: argparse.Namespace) -> int:
    data = _load_json_object(args.file, "case bundle")
    if data is None:
        return 2
    errors, warnings = validate_case_bundle(data)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def cmd_batch_launch_report(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    if not input_dir.is_dir():
        print(f"ERROR: input directory not found: {input_dir}", file=sys.stderr)
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    errors: list[str] = []
    for bundle_path in sorted(input_dir.glob("*.json")):
        data = _load_json_object(str(bundle_path), "case bundle")
        if data is None:
            errors.append(f"{bundle_path}: failed to load bundle")
            continue
        bundle_errors, bundle_warnings = validate_case_bundle(data)
        for warning in bundle_warnings:
            print(f"WARNING: {bundle_path.name}: {warning}", file=sys.stderr)
        if bundle_errors:
            errors.extend(f"{bundle_path}: {error}" for error in bundle_errors)
            continue
        report = launch_report_from_bundle(data)
        case_id = str((report.get("case") or {}).get("case_id") or bundle_path.stem)
        json_path = output_dir / f"{case_id}.json"
        md_path = output_dir / f"{case_id}.md"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_launch_markdown(report), encoding="utf-8")
        generated.extend([str(json_path), str(md_path)])
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"generated": generated}, ensure_ascii=False, indent=2))
    return 0


def cmd_coverage_report(_: argparse.Namespace) -> int:
    print(json.dumps(coverage_report(SKILL_ROOT), ensure_ascii=False, indent=2))
    return 0


def cmd_launch_report(args: argparse.Namespace) -> int:
    bundle = _load_json_object(args.bundle_file, "offline launch bundle")
    if bundle is None:
        return 2
    bundle_errors, bundle_warnings = validate_case_bundle(bundle)
    for warning in bundle_warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if bundle_errors:
        for error in bundle_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    payload = launch_report_from_bundle(bundle)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_launch_report_markdown(args: argparse.Namespace) -> int:
    report = _load_json_object(args.review_file, "review")
    if report is None:
        return 2
    errors = validate_payload(report)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(render_launch_markdown(report), end="")
    return 0


def cmd_launch_report_card(args: argparse.Namespace) -> int:
    report = _load_json_object(args.review_file, "review")
    if report is None:
        return 2
    errors = validate_payload(report)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return _write_html_or_export(args.output_file, render_overview_card_html(report), "card")


def cmd_launch_report_detail(args: argparse.Namespace) -> int:
    report = _load_json_object(args.review_file, "review")
    if report is None:
        return 2
    errors = validate_payload(report)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return _write_html_or_export(args.output_file, render_detailed_pdf_html(report), "detail")


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: failed to read JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("ERROR: top-level JSON must be an object", file=sys.stderr)
        return 2
    errors = validate_payload(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def _load_json_object(file_path: str, label: str) -> dict[str, Any] | None:
    path = Path(file_path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: failed to read {label} JSON: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print(f"ERROR: top-level {label} JSON must be an object", file=sys.stderr)
        return None
    return data


def cmd_case_check(args: argparse.Namespace) -> int:
    case = _load_json_object(args.case_file, "case")
    review = _load_json_object(args.review_file, "review")
    if case is None or review is None:
        return 2
    errors = check_case(case, review)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {case.get('case_id', args.case_file)}")
    return 0


def cmd_golden_replay(args: argparse.Namespace) -> int:
    cases_dir = Path(args.cases_dir)
    reviews_dir = Path(args.reviews_dir)
    passes, errors = replay_golden_cases(cases_dir, reviews_dir)
    for case_id in passes:
        print(f"PASS: {case_id}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"OK: {len(passes)} golden cases replayed")
    return 0


def cmd_quality_gate(_: argparse.Namespace) -> int:
    errors: list[str] = []

    index_errors = validate_rulepack_index()
    errors.extend(f"rulepack-index: {error}" for error in index_errors)

    try:
        freshness = source_freshness()
    except Exception as exc:
        errors.append(f"source-freshness: {exc}")
        freshness = None
    if freshness:
        for item in freshness.get("missing", []):
            errors.append(f"source-freshness missing: {item}")
        for item in freshness.get("stale", []):
            errors.append(f"source-freshness stale: {item}")
        for item in freshness.get("unverified_requirements", []):
            errors.append(f"source-freshness unverified: {item}")

    passes, replay_errors = replay_golden_cases(SKILL_ROOT / "cases", SKILL_ROOT / "reviews" / "golden")
    errors.extend(f"golden-replay: {error}" for error in replay_errors)

    benchmark_paths = sorted((SKILL_ROOT / "examples").glob("*benchmark*.json"))
    for benchmark_path in benchmark_paths:
        try:
            benchmark_data = json.loads(benchmark_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"benchmark-validate {benchmark_path}: {exc}")
            continue
        if isinstance(benchmark_data, dict):
            errors.extend(f"benchmark-validate {benchmark_path}: {error}" for error in validate_benchmark_worksheet(benchmark_data))
        else:
            errors.append(f"benchmark-validate {benchmark_path}: top-level JSON must be an object")

    bundle_paths = [SKILL_ROOT / "examples" / "offline-launch-case.json"]
    bundle_paths.extend(sorted((SKILL_ROOT / "examples" / "batch").glob("*.json")))
    for bundle_path in bundle_paths:
        if not bundle_path.exists():
            errors.append(f"bundle-validate missing fixture: {bundle_path}")
            continue
        try:
            bundle_data = json.loads(bundle_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"bundle-validate {bundle_path}: {exc}")
            continue
        if isinstance(bundle_data, dict):
            bundle_errors, _ = validate_case_bundle(bundle_data)
            errors.extend(f"bundle-validate {bundle_path}: {error}" for error in bundle_errors)
        else:
            errors.append(f"bundle-validate {bundle_path}: top-level JSON must be an object")

    try:
        coverage_report(SKILL_ROOT)
    except Exception as exc:
        errors.append(f"coverage-report: {exc}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    checked_links = freshness.get("checked_source_links", 0) if freshness else 0
    print("OK: rulepack index valid")
    print(f"OK: source freshness clean ({checked_links} checked source links)")
    print(f"OK: {len(passes)} golden cases replayed")
    print(f"OK: {len(benchmark_paths)} benchmark worksheet fixtures valid")
    print(f"OK: {len(bundle_paths)} bundle fixtures valid")
    print("OK: coverage report generated")
    return 0


def cmd_rulepack_new(args: argparse.Namespace) -> int:
    print(json.dumps(rulepack_template(args.country_code, args.country_name, args.region or ""), ensure_ascii=False, indent=2))
    return 0


def cmd_rulepack_validate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: failed to read JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("ERROR: top-level JSON must be an object", file=sys.stderr)
        return 2
    errors = validate_rulepack(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def cmd_rulepack_index_validate(_: argparse.Namespace) -> int:
    errors = validate_rulepack_index()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def cmd_source_freshness(args: argparse.Namespace) -> int:
    try:
        report = source_freshness(args.files)
    except Exception as exc:
        print(f"ERROR: failed to scan sources: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["stale"] or report["missing"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Qualification audit schema helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sample = sub.add_parser("sample", help="print sample review JSON")
    p_sample.set_defaults(func=cmd_sample)

    p_checklist = sub.add_parser("checklist", help="print routing checklist")
    p_checklist.add_argument("--platform", required=True)
    p_checklist.add_argument("--market", required=True)
    p_checklist.add_argument("--category", required=True)
    p_checklist.set_defaults(func=cmd_checklist)

    p_review_skeleton = sub.add_parser("review-skeleton", help="print a structured intake review JSON")
    p_review_skeleton.add_argument("--platform", required=True)
    p_review_skeleton.add_argument("--market", required=True)
    p_review_skeleton.add_argument("--category", required=True)
    p_review_skeleton.add_argument("--applicant-name", default="")
    p_review_skeleton.add_argument("--applicant-role", default="")
    p_review_skeleton.add_argument("--business-model", default="")
    p_review_skeleton.add_argument("--brand-name", default="")
    p_review_skeleton.add_argument("--purpose", default="launch readiness and qualification intake")
    p_review_skeleton.add_argument("--case-id", default="")
    p_review_skeleton.add_argument("--marketplace-site", default="")
    p_review_skeleton.set_defaults(func=cmd_review_skeleton)

    p_benchmark_template = sub.add_parser("benchmark-template", help="print a target-market benchmark worksheet JSON")
    p_benchmark_template.add_argument("--market", required=True)
    p_benchmark_template.add_argument("--category", required=True)
    p_benchmark_template.add_argument("--product", default="")
    p_benchmark_template.add_argument("--platform", default="")
    p_benchmark_template.add_argument("--count", type=int, default=8)
    p_benchmark_template.set_defaults(func=cmd_benchmark_template)

    p_benchmark_validate = sub.add_parser("benchmark-validate", help="validate a benchmark worksheet JSON file")
    p_benchmark_validate.add_argument("file")
    p_benchmark_validate.set_defaults(func=cmd_benchmark_validate)

    p_benchmark_summarize = sub.add_parser("benchmark-summarize", help="summarize a benchmark worksheet JSON file")
    p_benchmark_summarize.add_argument("file")
    p_benchmark_summarize.set_defaults(func=cmd_benchmark_summarize)

    p_bundle_template = sub.add_parser("bundle-template", help="print an offline launch case bundle template")
    p_bundle_template.add_argument("--platform", default="")
    p_bundle_template.add_argument("--market", required=True)
    p_bundle_template.add_argument("--category", required=True)
    p_bundle_template.add_argument("--product", default="")
    p_bundle_template.add_argument("--origin-country", default="")
    p_bundle_template.add_argument("--destination-market", action="append")
    p_bundle_template.add_argument(
        "--go-to-market-model",
        choices=sorted(ALLOWED_GO_TO_MARKET_MODELS),
        default="unknown",
    )
    p_bundle_template.set_defaults(func=cmd_bundle_template)

    p_bundle_validate = sub.add_parser("bundle-validate", help="validate an offline launch case bundle JSON file")
    p_bundle_validate.add_argument("file")
    p_bundle_validate.set_defaults(func=cmd_bundle_validate)

    p_batch_launch_report = sub.add_parser("batch-launch-report", help="generate launch reports for all bundle JSON files in a directory")
    p_batch_launch_report.add_argument("input_dir")
    p_batch_launch_report.add_argument("output_dir")
    p_batch_launch_report.set_defaults(func=cmd_batch_launch_report)

    p_coverage_report = sub.add_parser("coverage-report", help="print rulepack, source, golden, and benchmark coverage")
    p_coverage_report.set_defaults(func=cmd_coverage_report)

    p_launch_report = sub.add_parser("launch-report", help="generate launch-readiness review JSON from an offline case bundle")
    p_launch_report.add_argument("bundle_file")
    p_launch_report.set_defaults(func=cmd_launch_report)

    p_launch_report_markdown = sub.add_parser("launch-report-markdown", help="render launch-readiness review JSON as Markdown")
    p_launch_report_markdown.add_argument("review_file")
    p_launch_report_markdown.set_defaults(func=cmd_launch_report_markdown)

    p_launch_report_card = sub.add_parser("launch-report-card", help="render launch-readiness overview card as HTML or PNG")
    p_launch_report_card.add_argument("review_file")
    p_launch_report_card.add_argument("output_file")
    p_launch_report_card.set_defaults(func=cmd_launch_report_card)

    p_launch_report_detail = sub.add_parser("launch-report-detail", help="render detailed launch-readiness report as HTML or PDF")
    p_launch_report_detail.add_argument("review_file")
    p_launch_report_detail.add_argument("output_file")
    p_launch_report_detail.set_defaults(func=cmd_launch_report_detail)

    p_validate = sub.add_parser("validate", help="validate a review JSON file")
    p_validate.add_argument("file")
    p_validate.set_defaults(func=cmd_validate)

    p_case_check = sub.add_parser("case-check", help="check a review JSON against a golden case expectation")
    p_case_check.add_argument("case_file")
    p_case_check.add_argument("review_file")
    p_case_check.set_defaults(func=cmd_case_check)

    p_golden_replay = sub.add_parser("golden-replay", help="check all golden case fixtures")
    p_golden_replay.add_argument("--cases-dir", default=str(SKILL_ROOT / "cases"))
    p_golden_replay.add_argument("--reviews-dir", default=str(SKILL_ROOT / "reviews" / "golden"))
    p_golden_replay.set_defaults(func=cmd_golden_replay)

    p_quality_gate = sub.add_parser("quality-gate", help="run rulepack, source, and golden replay checks")
    p_quality_gate.set_defaults(func=cmd_quality_gate)

    p_rulepack_new = sub.add_parser("rulepack-new", help="print a country rule pack scaffold")
    p_rulepack_new.add_argument("--country-code", required=True)
    p_rulepack_new.add_argument("--country-name", required=True)
    p_rulepack_new.add_argument("--region", default="")
    p_rulepack_new.set_defaults(func=cmd_rulepack_new)

    p_rulepack_validate = sub.add_parser("rulepack-validate", help="validate a rule pack JSON file")
    p_rulepack_validate.add_argument("file")
    p_rulepack_validate.set_defaults(func=cmd_rulepack_validate)

    p_rulepack_index_validate = sub.add_parser("rulepack-index-validate", help="validate rulepack index and all indexed packs")
    p_rulepack_index_validate.set_defaults(func=cmd_rulepack_index_validate)

    p_source_freshness = sub.add_parser("source-freshness", help="report stale or missing rule source links")
    p_source_freshness.add_argument("files", nargs="*")
    p_source_freshness.set_defaults(func=cmd_source_freshness)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
