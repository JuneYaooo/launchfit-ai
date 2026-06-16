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
  rulepack-new --country-code CODE --country-name NAME
  rulepack-validate <json-file>
  rulepack-index-validate
  source-freshness [json-file ...]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any


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

DEFINITIVE_STATUSES = {"approve", "conditional_approve", "reject"}
MATURE_PACKS = {"validated", "production"}
AUTHORITATIVE_TIERS = {"T1", "T2"}

REQUIRED_CASE_FIELDS = (
    "applicant_name",
    "platform",
    "destination_market",
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
            "platform": "Amazon",
            "marketplace_site": "US",
            "destination_market": "United States",
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
            "packaging_conventions": "",
            "common_claims_and_proof": "",
            "review_themes": "",
            "gap_opportunity": "",
            "listing_preparation": "",
        },
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

    decision = data.get("decision") if isinstance(data.get("decision"), dict) else {}
    status = decision.get("status")
    _require(status in ALLOWED_DECISIONS, f"decision.status must be one of {sorted(ALLOWED_DECISIONS)}", errors)
    _require(decision.get("risk_level") in ALLOWED_RISK_LEVELS, f"decision.risk_level must be one of {sorted(ALLOWED_RISK_LEVELS)}", errors)

    case = data.get("case") if isinstance(data.get("case"), dict) else {}
    if status in DEFINITIVE_STATUSES:
        for field in REQUIRED_CASE_FIELDS:
            _require(bool(case.get(field)), f"case.{field} is required for a definitive '{status}' decision", errors)

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
    payload = benchmark_template(
        market=args.market,
        category=args.category,
        product=args.product or "",
        platform=args.platform or "",
        count=args.count,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


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

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    checked_links = freshness.get("checked_source_links", 0) if freshness else 0
    print("OK: rulepack index valid")
    print(f"OK: source freshness clean ({checked_links} checked source links)")
    print(f"OK: {len(passes)} golden cases replayed")
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
