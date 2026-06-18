# Report Templates

Use these templates for final outputs.

The JSON contract below is the single source of truth for output field names and structure. `scripts/qualification_audit_schema.py validate` enforces it. Other references describe usage and must not redefine these fields.

## Core Overview Card

Use this as the one-screen customer-facing artifact. It should fit a mobile-friendly image card or screenshot.

```markdown
# [Product / Route]

Launch view: go | caution | stop | unknown

Origin:
Destinations:
Go-to-market path:
Platform/category:

Top blockers:
1. ...
2. ...
3. ...

Product checkups:
- Admission risk:
- Localization gap:
- Market benchmark:
- Landing condition:

Next actions:
- Owner / action / evidence needed

Benchmark checkups:
- Price checkup:
- Channel checkup:
- Packaging / claim checkup:

Evidence status:
- T1/T2 confirmed:
- T4 user-provided only:
- Needs external verification:

```

Design rules:

- Keep it readable at social-card size.
- Generate the detailed report/PDF first; derive this card from the detailed report's executive snapshot, blocker table, missing-material table, benchmark summary, and evidence counts.
- Use at most 3 top blockers and 3 next actions.
- Include only benchmark sentences that tell the user what the signal means or what to do next. Prefer price checkup, channel checkup, and packaging/claim checkup; avoid vague labels such as "trust signal" or raw review-count dumps.
- Landing conditions must be actionable, such as importer/responsible party, customs file set, label review, logistics/budget, platform admission, fulfillment path, listing materials, or cost check. Do not use bare channel tags as the landing-condition content.
- Do not include long legal explanations or dense tables.
- Do not include generation metadata on the one-page card. Agent, model, generated date, search/information routes, long source links, and benchmark-source boundary text belong in the detailed PDF or appendix.
- If generated as HTML, save the HTML source and a PNG screenshot.

## Detailed PDF

Use this as the full working document.

Recommended sections:

1. Executive snapshot.
2. Scope: product, origin, destinations, platform, category, applicant, business model.
3. Per-destination market reviews.
4. Target-market benchmark research design: sample types, priority channels, sample boundaries, and required fields.
5. Benchmark analysis matrix when benchmark rows exist: price/pack/unit price, packaging/label signals, claims, trust/certification signals, review themes, and takeaway.
6. Benchmark visual evidence when available: render a compact product-image gallery from `image_url`, `image_path`, or screenshot fields; do not invent images.
7. Benchmark summary: reference price band, channel map, packaging conventions, claims and proof, visible trust signals, review themes, gap opportunity, Copy / Avoid / Improve, and verification needed.
8. Localization recommendations: packaging hierarchy, label language, claims wording, channel fit, price/bundle strategy, fulfillment route, and evidence pack.
9. Source candidates and research tasks. Keep long URLs and benchmark-source boundary tables out of the main narrative tables.
10. Platform/category admission requirements.
11. Documents, evidence, source tiers, and freshness.
12. Findings and decision effects.
13. Missing materials and acceptable replacements.
14. Packaging/label fixes.
15. Logistics/budget route review.
16. Applicant-facing remediation wording.
17. Generation note: agent, model if declared, search/information routes used, and generated date.
18. Source-link appendix or attachment: full URLs, source type, tier, checked date, and boundary.
19. Audit log and disclaimer.

If no benchmark rows are supplied, do not invent competitor names, prices, reviews, or live market facts. Output a benchmark research design and mark the analysis matrix as missing until current marketplace, retail, DTC, social, distributor, or user-provided samples are checked.

If generated as HTML, save the HTML source and PDF export.

## Executive Markdown Memo

```markdown
# Qualification Review Decision

## Decision
- Status: approve | conditional_approve | request_more_info | reject | escalate_human | not_applicable
- Risk level: low | medium | high | critical
- One-line reason: ...
- Review date: YYYY-MM-DD

## Scope
| Field | Value |
|---|---|
| Applicant | ... |
| Platform/site | ... |
| Destination market | ... |
| Business model | ... |
| Product/category | ... |
| Brand | ... |
| Review purpose | ... |

## Requirement Coverage
| Requirement | Status | Evidence | Issue | Action |
|---|---|---|---|---|

## Findings
| ID | Severity | Surface | Issue | Decision effect | Required action |
|---|---|---|---|---|---|

## Missing or Invalid Materials
| Material | Why required | Acceptable replacement | Owner | Due |
|---|---|---|---|---|

## Evidence and Sources
| ID | Type | Source/document | Tier | Checked at | What it confirms |
|---|---|---|---|---|---|

## Applicant-Facing Supplement Request
[Clear message that can be sent to the applicant.]

## Internal Notes
[Only include if user needs internal reviewer notes. Redact sensitive data.]

## Disclaimer
This review is an operational qualification assessment based on submitted materials and checked sources. It is not legal advice. Platform and regulatory requirements can change; verify official sources before final enforcement or submission.
```

## Launch Readiness Markdown Memo

Use this for seller-facing product launch, listing preparation, target-market benchmarking, competitor/pricing, packaging, or logistics questions. Keep the first screen practical and action-oriented.

```markdown
# Cross-Border Product Launch Review

## Snapshot
- Product:
- Target market/platform:
- Launch view: go | caution | stop | unknown
- Biggest risk:
- Next action:

## Top Risks Before Listing
| Risk | Impact | Owner | Fix |
|---|---|---|---|

## Target-Market Benchmarks
| Benchmark product | Channel role | Pack/unit price | Positioning | Visible trust signals | What it teaches us |
|---|---|---|---|---|---|

## What The Benchmarks Mean
| Question | Conclusion | Action |
|---|---|---|
| Reference price band | Low / mainstream / premium / specialty | ... |
| Channel map | Which channels set buyer expectations | ... |
| Packaging conventions | What local buyers are used to seeing | ... |
| Claims and proof | Which claims are common and which need substantiation | ... |
| Review themes | Repeated praise, objections, complaints, or usage contexts | ... |
| Gap opportunity | What we can copy, avoid, or improve | ... |

## Localization Recommendations
| Area | Change | Why it matters | Evidence/check |
|---|---|---|---|

## Competitor / Pricing
| Signal | What it means | Action |
|---|---|---|

## Packaging / Label
| Area | Risk | Suggested change |
|---|---|---|

## Platform Admission
| Requirement | Status | Evidence/action |
|---|---|---|

## Logistics / Budget
| Route | Fit | Risk | Preparation |
|---|---|---|---|

## Missing Materials
| Material | Why needed | Who provides it |
|---|---|---|

## Assumptions And Verification Needed
| Item | Current basis | How to verify |
|---|---|---|

## Disclaimer
Operational launch-readiness review only; not legal advice. Verify current platform, regulator, customs, certification, and logistics sources before final enforcement, ordering, printing, or shipment.
```

## JSON Contract

```json
{
  "review_type": "cross_border_ecommerce_qualification",
  "case": {
    "case_id": "",
    "applicant_name": "",
    "applicant_role": "",
    "origin_country": "",
    "platform": "",
    "marketplace_site": "",
    "destination_market": "",
    "destination_markets": [],
    "go_to_market_model": "cross_border_ecommerce|physical_trade|hybrid|unknown",
    "business_model": "",
    "product_category": "",
    "subcategory": "",
    "brand_name": "",
    "review_purpose": "",
    "requested_decision_deadline": "",
    "review_date": "YYYY-MM-DD"
  },
  "decision": {
    "status": "approve|conditional_approve|request_more_info|reject|escalate_human|not_applicable",
    "risk_level": "low|medium|high|critical",
    "risk_score": 0,
    "summary": "",
    "rationale": []
  },
  "go_to_market_route": {
    "model": "cross_border_ecommerce|physical_trade|hybrid|unknown",
    "label": "",
    "primary_checks": [],
    "benchmark_focus": []
  },
  "generation_metadata": {
    "agent": "Codex|Hermes|Claude Code|other",
    "model": "declared model name or 未声明",
    "search_methods": [],
    "generated_at": "YYYY-MM-DD"
  },
  "documents": [
    {
      "document_id": "",
      "document_type": "",
      "file_reference": "",
      "holder": "",
      "issuer": "",
      "number_redacted": "",
      "issue_date": "",
      "expiry_date": "",
      "scope": "",
      "extraction_confidence": "high|medium|low",
      "privacy_level": "public|business_confidential|pii|highly_sensitive"
    }
  ],
  "market_benchmarks": [
    {
      "benchmark_id": "",
      "product_name": "",
      "channel": "",
      "channel_role": "search_marketplace|social_commerce|mass_retail|club_store|specialty|pharmacy|dtc|offline_shelf|other",
      "market": "",
      "pack_size": "",
      "price": "",
      "unit_price": "",
      "image_url": "",
      "image_alt": "",
      "positioning": "mass|mainstream|premium|specialty|luxury|unknown",
      "visible_claims": [],
      "packaging_signals": [],
      "certification_signals": [],
      "review_signals": [],
      "data_basis": "current_checked|user_provided|assumption|not_checked",
      "source_ids": [],
      "evidence_ids": [],
      "takeaway": ""
    }
  ],
  "market_benchmark_summary": {
    "reference_price_band": "",
    "channel_map": "",
    "packaging_conventions": "",
    "claims_and_proof": "",
    "visible_trust_signals": "",
    "review_themes": "",
    "gap_opportunity": "",
    "copy_avoid_improve": "",
    "listing_preparation": "",
    "verification_needed": ""
  },
  "market_reviews": [
    {
      "destination_market": "",
      "origin_country": "",
      "matched_packs": [],
      "decision": {},
      "requirements": [],
      "findings": [],
      "missing_materials": [],
      "source_candidates": [],
      "research_tasks": []
    }
  ],
  "source_candidates": [
    {
      "source_candidate_id": "",
      "origin_country": "",
      "destination_market": "",
      "channel_type": "platform_policy|destination_regulator|customs_import|brand_ip|business_registry|certification_lab|standards_body|logistics_warehouse|origin_export_controls",
      "title": "",
      "why": "",
      "source_tier": "T1|T2|T3|T4|T5",
      "access_method": "",
      "suggested_queries": [],
      "candidate_urls": [],
      "expected_facts": [],
      "freshness_days": 0
    }
  ],
  "research_tasks": [
    {
      "research_task_id": "",
      "task_key": "",
      "priority": "P0|P1|P2",
      "channel_type": "",
      "source_candidate_ids": [],
      "origin_country": "",
      "destination_market": "",
      "platform": "",
      "category": "",
      "instruction": "",
      "recommended_tier": "T1|T2|T3|T4|T5",
      "freshness_days": 0,
      "evidence_fields": [],
      "status": "needs_external_verification|completed|not_applicable"
    }
  ],
  "requirements": [
    {
      "requirement_id": "",
      "surface": "seller|brand_ip|product_category|market_import|certificate|platform_listing|service_provider",
      "requirement": "",
      "status": "satisfied|partial|missing|invalid|not_applicable|needs_external_verification",
      "matched_evidence_ids": [],
      "source_ids": [],
      "notes": ""
    }
  ],
  "findings": [
    {
      "finding_id": "",
      "severity": "critical|high|medium|low",
      "surface": "",
      "requirement": "",
      "submitted_evidence": "",
      "observed_issue": "",
      "business_impact": "",
      "decision_effect": "",
      "required_action": "",
      "acceptable_evidence": "",
      "source_ids": [],
      "confidence": "high|medium|low"
    }
  ],
  "missing_materials": [
    {
      "material": "",
      "why_required": "",
      "acceptable_replacement": "",
      "owner": "",
      "priority": "P0|P1|P2"
    }
  ],
  "evidence": [
    {
      "evidence_id": "",
      "kind": "submitted_document|official_source|registry|issuer_lookup|platform_policy|regulator|other",
      "reference": "",
      "tier": "T1|T2|T3|T4|T5",
      "checked_at": "YYYY-MM-DD",
      "extracted_fact": "",
      "confidence": "high|medium|low"
    }
  ],
  "sources": [
    {
      "source_id": "",
      "title": "",
      "url": "",
      "tier": "T1|T2|T3|T4|T5",
      "checked_at": "YYYY-MM-DD",
      "confirms": ""
    }
  ],
  "remediation": {
    "applicant_message": "",
    "internal_next_steps": []
  },
  "privacy": {
    "redactions_applied": [],
    "sensitive_data_notes": []
  },
  "audit_log": [
    {
      "timestamp": "YYYY-MM-DD",
      "actor": "AI reviewer",
      "action": "",
      "details": ""
    }
  ],
  "disclaimer": "Operational qualification review only; not legal advice."
}
```

## Supplement Request Template

```text
您好，当前申请暂无法完成审核。请补充以下材料：

1. [材料名称]
   - 原因：[为什么需要]
   - 要求：[格式、签发方、有效期、适用范围]
   - 可接受替代：[如有]

请确保材料中的主体名称、品牌、产品范围、销售地区和平台授权范围与本次申请一致。
```
