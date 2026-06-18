# Implementation Blueprint

Use this reference when converting the skill into a product workflow or integrating it into an existing app.

## Recommended Product Modules

| Module | Purpose |
|---|---|
| Case intake | Create review case, define applicant/platform/market/category/purpose |
| Document center | Upload, OCR, classify, extract fields, tag privacy level |
| Benchmark center | Collect competitor screenshots/links/rows, normalize price/pack/channel/review signals, summarize copy/avoid/improve |
| Requirement engine | Generate platform/market/category checklist and rule version |
| Evidence matcher | Match submitted documents and verified sources to requirements |
| Decision engine | Apply severity/blocker logic and produce final status |
| Remediation center | Generate applicant-facing supplement/rejection messages |
| Human review queue | Route escalations, suspected fraud, legal ambiguity, high-risk categories |
| Audit log | Persist reviewer actions, source checks, rule version, and decision history |
| Renewal monitor | Track certificate expiry and platform/rule freshness |

## Data Model

Add these entities if building on an existing app:

```text
ReviewCase
  id, user_id, applicant_name, applicant_role, origin_country, platform, marketplace_site,
  destination_market, destination_markets_json, business_model, product_category, subcategory,
  brand_name, review_purpose, status, risk_level, risk_score,
  created_at, updated_at, decided_at

ReviewDocument
  id, case_id, file_id, document_type, holder, issuer, number_hash,
  number_redacted, issue_date, expiry_date, jurisdiction, scope,
  extraction_json, extraction_confidence, privacy_level, created_at

ReviewRequirement
  id, case_id, surface, requirement, rule_key, rule_version,
  status, source_ids_json, matched_evidence_ids_json, notes

ReviewFinding
  id, case_id, severity, surface, requirement, observed_issue,
  business_impact, decision_effect, required_action,
  acceptable_evidence, confidence, source_ids_json

ReviewEvidence
  id, case_id, kind, reference, tier, checked_at, extracted_fact,
  confidence, document_id, source_id

ReviewSource
  id, case_id, title, url, tier, checked_at, confirms, content_hash

ReviewDecision
  id, case_id, status, risk_level, risk_score, summary,
  rationale_json, remediation_json, decided_by, decided_at

ReviewAuditLog
  id, case_id, actor, action, details_json, created_at
```

Keep uploaded file bytes in the existing file storage layer if one exists; store only metadata, hashes, and redacted values in review tables.

## API Shape

```text
POST   /api/review-cases
GET    /api/review-cases
GET    /api/review-cases/{id}
PATCH  /api/review-cases/{id}

POST   /api/review-cases/{id}/documents
POST   /api/review-cases/{id}/extract
POST   /api/review-cases/{id}/requirements
POST   /api/review-cases/{id}/evaluate
POST   /api/review-cases/{id}/decision
POST   /api/review-cases/{id}/remediation-message
GET    /api/review-cases/{id}/audit-log
```

For streaming apps, reuse the existing SSE pattern:

1. `case_intake`
2. `benchmark_collection`
3. `document_extraction`
4. `rule_mapping`
5. `source_verification`
6. `decision`
7. `remediation`

OCR, live marketplace search/scraping, certificate or trademark registries, company registries, and logistics quote APIs are enhancement inputs. They should feed the same document, benchmark, source, evidence, and logistics structures used by the Skill. Do not create a separate path that treats external tool output as automatically authoritative; record source tier, checked date, confidence, and whether it directly confirms the point.

## Prompt Changes

Replace generic compliance-report prompting with this broader launch-readiness contract:

- The model must output a detailed launch checkup JSON, not generic market-entry advice.
- The output should cover admission/qualification risks, target-market benchmarks, localization recommendations, logistics, remediation, and evidence gaps when those areas are relevant.
- The model must choose one of the fixed decision statuses.
- Findings must be tied to requirements and evidence.
- T4 applicant documents cannot be treated as externally verified.
- Missing platform/market/category scope produces `request_more_info`, not a confident decision.
- Suspected fraud, sanctions, identity issues, or conflicting official sources produce `escalate_human`.

## Frontend Views

| View | Key UI |
|---|---|
| Case list | Status, platform, category, risk, deadline |
| Intake form | Applicant, platform, market, category, brand, purpose |
| Benchmark worksheet | Source type, channel, pack/price/unit price, claims, trust markers, review themes, copy/avoid/improve |
| Document table | Type, holder, expiry, extraction confidence, privacy flag |
| Requirement coverage | Satisfied/partial/missing/invalid/not applicable |
| Findings | Severity, issue, evidence, required action |
| Decision panel | Final status, risk score, rationale, reviewer controls |
| Remediation composer | Applicant-facing supplement request |
| Audit log | Source checks, reviewer actions, decision history |

## Migration From A Compliance Assistant

If starting from a food/FMCG compliance assistant:

1. Keep multimodal extraction and source verification.
2. Keep regulatory/source tier logic.
3. Reuse provider matching only after decision, not as evidence.
4. Replace market recommendation output with requirement coverage.
5. Add review case tables and audit logs.
6. Add fixed decision statuses.
7. Add privacy redaction before displaying extracted document data.
8. Split "regulatory advice" from "qualification decision".

## Testing Strategy

Create golden cases:

- complete low-risk application -> approve
- expired certificate -> request_more_info
- brand authorization missing territory -> request_more_info or reject
- prohibited category -> reject
- suspected forged document -> escalate_human
- platform/market not provided -> request_more_info
- applicant document only, no external verification -> needs_external_verification

For each golden case, test:

- final status
- blocker propagation
- evidence/source linkage
- redaction
- applicant-facing message
- audit log completeness
