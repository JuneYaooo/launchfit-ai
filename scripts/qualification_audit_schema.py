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
    return {
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

    return {
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
    for idx, finding in enumerate(document_findings + packaging_findings + logistics_findings, start=existing_count + 1):
        finding["finding_id"] = finding.get("finding_id") or f"OFF-{idx:03d}"
        report["findings"].append(finding)
    report["missing_materials"].extend(benchmark_missing + document_missing + packaging_missing + logistics_missing)
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


def _top_findings(report: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings = [item for item in report.get("findings") or [] if isinstance(item, dict)]
    findings.sort(key=lambda item: severity_order.get(str(item.get("severity")), 9))
    return findings[:limit]


def _top_missing(report: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    items = [item for item in report.get("missing_materials") or [] if isinstance(item, dict)]
    items.sort(key=lambda item: priority_order.get(str(item.get("priority")), 9))
    return items[:limit]


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


def render_overview_card_html(report: dict[str, Any]) -> str:
    case = report.get("case") if isinstance(report.get("case"), dict) else {}
    decision = report.get("decision") if isinstance(report.get("decision"), dict) else {}
    route = report.get("go_to_market_route") if isinstance(report.get("go_to_market_route"), dict) else go_to_market_route_profile(_text(case.get("go_to_market_model")) or "unknown")
    destinations = _as_list(case.get("destination_markets")) or _as_list(case.get("destination_market"))
    findings = _top_findings(report)
    missing = _top_missing(report)
    channels = _channel_types(report)
    evidence = _evidence_status(report)
    product = _text(case.get("subcategory") or case.get("product_category") or "Product")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Core Overview Card</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; width: 1200px; min-height: 1600px; background: #eef3f7; color: #172033; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; letter-spacing: 0; }}
    .card {{ margin: 56px; padding: 54px 62px; min-height: 1480px; background: #fff; border: 1px solid #d9e1ec; border-radius: 8px; box-shadow: 0 18px 48px rgba(28,46,70,.14); }}
    .eyebrow {{ color: #1769aa; font-weight: 800; font-size: 24px; margin-bottom: 18px; }}
    h1 {{ font-size: 60px; line-height: 1.05; margin: 0 0 18px; }}
    .summary {{ color: #617086; font-size: 28px; line-height: 1.35; margin-bottom: 28px; max-width: 900px; }}
    .meta {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 28px 0 34px; }}
    .meta > div, .panel {{ border: 1px solid #d9e1ec; border-radius: 8px; padding: 20px; background: #fbfdff; }}
    .label {{ color: #617086; font-size: 17px; font-weight: 750; margin-bottom: 8px; text-transform: uppercase; }}
    .value {{ font-size: 26px; font-weight: 800; line-height: 1.2; }}
    .status {{ color: #167c62; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
    h2 {{ font-size: 30px; margin: 0 0 16px; }}
    ul {{ margin: 0; padding-left: 24px; }}
    li {{ font-size: 22px; line-height: 1.35; margin: 0 0 10px; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .chip {{ font-size: 20px; padding: 9px 12px; border-radius: 6px; background: #edf4fb; color: #1d4f7a; border: 1px solid #c9d9e8; font-weight: 700; }}
    .footer {{ margin-top: 22px; padding-top: 20px; border-top: 2px solid #d9e1ec; color: #617086; font-size: 20px; line-height: 1.35; }}
  </style>
</head>
<body>
  <main class="card">
    <div class="eyebrow">LaunchFit AI · Core Overview Card</div>
    <h1>{_html(product)} launch check</h1>
    <div class="summary">{_html(decision.get("summary") or "Launch readiness depends on completing the research tasks and resolving missing materials.")}</div>
    <section class="meta">
      <div><div class="label">Launch view</div><div class="value status">{_display_label(decision.get("status"))}</div></div>
      <div><div class="label">Go-to-market path</div><div class="value">{_html(route.get("label"))}</div></div>
      <div><div class="label">Origin</div><div class="value">{_html(case.get("origin_country"))}</div></div>
      <div><div class="label">Destinations</div><div class="value">{_html(_joined_text(destinations))}</div></div>
    </section>
    <section class="grid">
      <div class="panel"><h2>Top blockers</h2><ul>{"".join(f"<li>{_html(item.get('observed_issue'))}</li>" for item in findings) or "<li>No blocker supplied</li>"}</ul></div>
      <div class="panel"><h2>Next actions</h2><ul>{"".join(f"<li>{_html(item.get('material'))}: {_html(item.get('why_required'))}</li>" for item in missing) or "<li>Complete P0/P1 research tasks</li>"}</ul></div>
      <div class="panel"><h2>Must-check channels</h2><div class="chips">{"".join(f"<span class='chip'>{_display_label(channel)}</span>" for channel in channels) or "<span class='chip'>source candidates missing</span>"}</div></div>
      <div class="panel"><h2>Evidence status</h2><ul><li>T1/T2 authoritative sources: {evidence['authoritative']}</li><li>T4 user-provided evidence: {evidence['user_provided']}</li><li>Needs external verification: {evidence['needs_external_verification']}</li></ul></div>
    </section>
    <div class="footer">Use this card for quick alignment. Use the detailed PDF for evidence, per-destination review, remediation, and audit trail.</div>
  </main>
</body>
</html>
"""


def render_detailed_pdf_html(report: dict[str, Any]) -> str:
    case = report.get("case") if isinstance(report.get("case"), dict) else {}
    decision = report.get("decision") if isinstance(report.get("decision"), dict) else {}
    route = report.get("go_to_market_route") if isinstance(report.get("go_to_market_route"), dict) else go_to_market_route_profile(_text(case.get("go_to_market_model")) or "unknown")
    benchmark_summary = report.get("market_benchmark_summary") if isinstance(report.get("market_benchmark_summary"), dict) else {}
    market_rows = "".join(
        f"<tr><td>{_html(item.get('destination_market'))}</td><td>{_html(_joined_text(item.get('matched_packs')))}</td><td>{len(item.get('research_tasks') or [])}</td><td>{len(item.get('source_candidates') or [])}</td></tr>"
        for item in report.get("market_reviews") or []
        if isinstance(item, dict)
    )
    candidate_rows = "".join(
        f"<tr><td>{_html(item.get('destination_market'))}</td><td>{_html(item.get('channel_type'))}</td><td>{_html(item.get('title'))}</td><td>{_html(item.get('source_tier'))}</td><td>{_html(_joined_text(item.get('expected_facts')))}</td></tr>"
        for item in (report.get("source_candidates") or [])[:40]
        if isinstance(item, dict)
    )
    task_rows = "".join(
        f"<tr><td>{_html(item.get('priority'))}</td><td>{_html(item.get('destination_market'))}</td><td>{_html(item.get('task_key'))}</td><td>{_html(item.get('instruction'))}</td><td>{_html(item.get('status'))}</td></tr>"
        for item in (report.get("research_tasks") or [])[:50]
        if isinstance(item, dict)
    )
    finding_rows = "".join(
        f"<tr><td>{_html(item.get('severity'))}</td><td>{_html(item.get('surface'))}</td><td>{_html(item.get('observed_issue'))}</td><td>{_html(item.get('required_action'))}</td></tr>"
        for item in report.get("findings") or []
        if isinstance(item, dict)
    )
    missing_rows = "".join(
        f"<tr><td>{_html(item.get('priority'))}</td><td>{_html(item.get('material'))}</td><td>{_html(item.get('why_required'))}</td><td>{_html(item.get('acceptable_replacement'))}</td></tr>"
        for item in report.get("missing_materials") or []
        if isinstance(item, dict)
    )
    evidence_rows = "".join(
        f"<tr><td>{_html(item.get('evidence_id'))}</td><td>{_html(item.get('kind'))}</td><td>{_html(item.get('tier'))}</td><td>{_html(item.get('checked_at'))}</td><td>{_html(item.get('extracted_fact'))}</td></tr>"
        for item in (report.get("evidence") or [])[:50]
        if isinstance(item, dict)
    )
    audit_rows = "".join(
        f"<tr><td>{_html(item.get('timestamp'))}</td><td>{_html(item.get('actor'))}</td><td>{_html(item.get('action'))}</td><td>{_html(item.get('details'))}</td></tr>"
        for item in (report.get("audit_log") or [])[-25:]
        if isinstance(item, dict)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Detailed LaunchFit Review</title>
  <style>
    @page {{ size: A4; margin: 16mm; }}
    body {{ color: #172033; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; line-height: 1.5; letter-spacing: 0; }}
    h1 {{ font-size: 30px; margin: 0 0 8px; }}
    h2 {{ font-size: 20px; margin: 24px 0 10px; color: #1769aa; }}
    p {{ margin: 0 0 10px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 8px 0 18px; font-size: 11px; }}
    th, td {{ border: 1px solid #d9e1ec; padding: 7px; vertical-align: top; text-align: left; }}
    th {{ background: #edf4fb; color: #1d4f7a; }}
    .box {{ border: 1px solid #d9e1ec; border-radius: 6px; padding: 10px 12px; background: #f8fbfd; margin: 10px 0; }}
  </style>
</head>
<body>
  <h1>Detailed LaunchFit Review</h1>
  <div class="box"><strong>Decision:</strong> {_display_label(decision.get('status'))} · {_display_label(decision.get('risk_level'))} · {_html(decision.get('summary'))}</div>
  <h2>Scope</h2>
  <table><tr><th>Product</th><th>Go-to-market path</th><th>Origin</th><th>Destinations</th><th>Platform</th><th>Category</th><th>Applicant</th></tr><tr><td>{_html(case.get('subcategory') or case.get('product_category'))}</td><td>{_html(route.get('label'))}</td><td>{_html(case.get('origin_country'))}</td><td>{_html(_joined_text(_as_list(case.get('destination_markets')) or _as_list(case.get('destination_market'))))}</td><td>{_html(case.get('platform'))}</td><td>{_html(case.get('product_category'))}</td><td>{_html(case.get('applicant_name'))}</td></tr></table>
  <h2>Go-to-market path</h2>
  <table><tr><th>Primary checks</th><th>Benchmark focus</th></tr><tr><td>{_html('; '.join(route.get('primary_checks') or []))}</td><td>{_html('; '.join(route.get('benchmark_focus') or []))}</td></tr></table>
  <h2>Per-destination market reviews</h2>
  <table><tr><th>Destination</th><th>Matched packs</th><th>Research tasks</th><th>Source candidates</th></tr>{market_rows}</table>
  <h2>Benchmark summary</h2>
  <table><tr><th>Reference price band</th><th>Channel map</th><th>Claims/proof</th><th>Verification needed</th></tr><tr><td>{_html(benchmark_summary.get('reference_price_band'))}</td><td>{_html(benchmark_summary.get('channel_map'))}</td><td>{_html(benchmark_summary.get('claims_and_proof'))}</td><td>{_html(benchmark_summary.get('verification_needed'))}</td></tr></table>
  <h2>Source candidates</h2>
  <table><tr><th>Destination</th><th>Channel</th><th>Source</th><th>Tier</th><th>Expected facts</th></tr>{candidate_rows}</table>
  <h2>Research tasks</h2>
  <table><tr><th>Priority</th><th>Destination</th><th>Task</th><th>Instruction</th><th>Status</th></tr>{task_rows}</table>
  <h2>Findings</h2>
  <table><tr><th>Severity</th><th>Surface</th><th>Issue</th><th>Required action</th></tr>{finding_rows}</table>
  <h2>Missing materials</h2>
  <table><tr><th>Priority</th><th>Material</th><th>Why needed</th><th>Acceptable replacement</th></tr>{missing_rows}</table>
  <h2>Evidence and source status</h2>
  <table><tr><th>Evidence ID</th><th>Kind</th><th>Tier</th><th>Checked at</th><th>Fact</th></tr>{evidence_rows}</table>
  <h2>Remediation wording</h2>
  <div class="box">{_html((report.get('remediation') or {}).get('applicant_message'))}</div>
  <h2>Audit log</h2>
  <table><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Details</th></tr>{audit_rows}</table>
  <h2>Disclaimer</h2>
  <p>{_html(report.get('disclaimer') or 'Operational launch-readiness review only; not legal advice.')}</p>
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
                "--window-size=1200,1800",
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
