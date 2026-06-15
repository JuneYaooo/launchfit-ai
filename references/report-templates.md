# Report Templates

Use these templates for final outputs.

The JSON contract below is the single source of truth for output field names and structure. `scripts/qualification_audit_schema.py validate` enforces it. Other references describe usage and must not redefine these fields.

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

Use this for seller-facing product launch, listing preparation, competitor/pricing, packaging, or logistics questions. Keep the first screen practical and action-oriented.

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
    "platform": "",
    "marketplace_site": "",
    "destination_market": "",
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
