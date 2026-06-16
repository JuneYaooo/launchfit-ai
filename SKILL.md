---
name: cross-border-product-ai-checkup
description: Use this skill when the user wants an AI checkup for a cross-border e-commerce product before launch: whether the product can sell, is worth launching, what similar products in the target market are doing, what may block marketplace listing, what documents or labels are missing, how benchmark/pricing/logistics look, and what remediation wording is needed. Covers target-market benchmarking, product feasibility, packaging or label review, platform/category admission, qualification review, brand authorization, certificate/license validation, logistics budget comparison, and auditable approve/request/reject/escalate decisions for platforms such as Amazon, TikTok Shop, Shopee, Temu, Lazada, AliExpress, Tmall Global, JD Worldwide, Walmart Marketplace, eBay, or similar marketplaces.
metadata:
  short-description: Cross-border product AI checkup
---

# Cross-border Product AI Checkup

Use this skill to turn a cross-border product idea or messy launch package into an AI checkup report: can it sell, where it may get blocked, what to fix, what to prepare, and whether it can move forward.

This skill is not only for low-frequency compliance review. It supports high-frequency seller workflows before and during launch: product feasibility, target-market benchmarking, competitor and pricing checks, packaging and label readiness, logistics planning, platform admission, qualification review, and applicant-facing remediation.

When the user asks for a final qualification decision, the output must remain auditable: approve, conditionally approve, request more information, reject, or escalate to human review.

## Core Modes

| Mode | Use when | Output |
|---|---|---|
| Launch intake | User provides a product, target market, platform, category, or launch idea | Scope, assumptions, missing inputs, launch-readiness checklist |
| Product feasibility | User asks whether a product can or should be sold in a market | Opportunity/risk view, obvious blockers, verification plan, next actions |
| Target-market benchmarking | User asks how similar products are sold in the destination market, or provides competitor screenshots/links | Benchmark product table plus summary of price band, channel map, packaging conventions, trust signals, review themes, and copy/avoid/improve actions |
| Competitor/pricing review | User provides competitor screenshots, product links, channel info, or pricing questions | Competitor table, unit price normalization, channel/price bands, positioning and differentiation notes |
| Packaging/label readiness | User provides packaging, label text, claims, ingredients/materials, or listing copy | Label/claim risks, localization notes, required changes, evidence needed |
| Logistics/budget review | User asks about air/sea/rail/warehouse/local delivery routes | Cost/time/risk comparison, route constraints, preparation checklist |
| Document review | User provides licenses, certificates, reports, labels, authorization letters, screenshots, PDFs, or images | Extracted fields, inconsistencies, red flags, evidence table |
| Platform/category review | User names a marketplace, market, or product category | Current-rule verification plan and required qualification checklist |
| Decision memo | User asks whether an application can pass | Decision, reasons, evidence, source URLs, remediation |
| Remediation | User asks how to fix failed materials | Supplement request, revised document list, applicant-facing wording |
| Rulebook design | User is building an internal审核/准入 process | Rule matrix, data model, severity taxonomy, audit trail |

## Always Establish Scope

Before issuing a final decision, identify:

- Applicant type: manufacturer, brand owner, distributor, importer, marketplace seller, agent, service provider.
- Business model: export, import, cross-border bonded, direct mail, marketplace FBA/FBT/FBM, domestic-to-overseas, overseas-to-China.
- Commercial goal: new product selection, launch readiness, listing approval, pricing, packaging, logistics, blocked review, remediation, or SOP design.
- Platform and market: marketplace name, destination country/region, store site, warehouse model.
- Product scope: category, subcategory, HS/code if relevant, regulated attributes, claims, ingredients/materials.
- Market signals: benchmark products in the target market, competitor products, channel examples, target consumer, price band, packaging benchmark, review signals, certifications/claims used by local leaders, or known constraints.
- Brand/IP scope: brand owner, trademark region/class, authorization chain, license territory, validity period.
- Documents submitted: file name, document type, issuer, holder, number, issue date, expiry date, scope, language.
- Requested outcome: launch feasibility, target-market benchmark, platform onboarding, category gating, product listing approval, customs/import readiness, logistics budget, packaging/label recommendations, pricing guidance, service-provider qualification.

If any blocker is missing, ask only the minimum necessary question. Otherwise proceed with assumptions and flag them.

## Workflow

1. **Triage the case**
   - Load `references/audit-workflow.md`.
   - Classify the case as product launch, seller/KYB, brand/IP, product/category, market/import, platform listing, logistics/budget, target-market benchmark, competitor/pricing, packaging/label, or service-provider review.
   - Assign initial risk: low, medium, high, critical.

2. **Frame the launch question**
   - Load `references/launch-readiness-playbook.md` for product feasibility, target-market benchmarking, competitor/pricing, packaging/label, logistics/budget, or seller-facing launch questions.
   - If the user asks "can this sell" or "what should I prepare", produce a launch-readiness answer first, not a narrow compliance memo.
   - Separate commercial assumptions from verified facts: product positioning, benchmark product signals, price band, competitor signals, target market, logistics route, and platform route.
   - For current benchmark products, competitor pricing, platform requirements, freight costs, or regulatory facts, verify current sources and cite checked dates.

3. **Build the document inventory**
   - Load `references/document-taxonomy.md` when reviewing documents or creating required-material lists.
   - Extract fields at document level, not just summary level.
   - Check consistency across applicant name, registered address, brand owner, product name, category, territory, validity dates, and issuer.

4. **Map platform, country, and category rules**
   - Load `references/platform-market-matrix.md` when a platform, marketplace site, or target country is involved.
   - Load `references/global-country-framework.md` for country/region routing, especially when no country-specific rule pack exists.
   - Check `data/rulepacks/index.json` for available rule packs and combine them per its `composition_order` (global -> platform -> region -> country -> category). If no country pack exists, use `data/rulepacks/global-baseline.json` and verify official sources in real time.
   - Do not rely on memory for current platform rules. Verify current requirements from official platform/regulator sources before definitive conclusions.

5. **Apply decision rules**
   - Load `references/decision-rules.md`.
   - Convert every issue into a finding with severity, rule basis, evidence, impact, and required action.
   - A single critical blocker can force reject or human escalation even if the score is otherwise high.

6. **Verify evidence and currency**
   - Load `references/verification-playbook.md` whenever making claims about laws, platform rules, registries, or certificate validity.
   - Cite source URL, source tier, checked date, and whether the source directly confirms the point.
   - If the source is stale, indirect, applicant-provided only, or social content, downgrade confidence.

7. **Protect sensitive data**
   - Load `references/privacy-security.md` whenever documents include personal data, license numbers, identity documents, contracts, bank info, or contact info.
   - Redact unnecessary sensitive values in user-facing output.

8. **Output the result**
   - Load `references/report-templates.md`.
   - For launch-readiness work, provide a practical "can sell / can list / what to fix next" answer first, then target-market benchmark, competitor/pricing/logistics/packaging notes as relevant.
   - For target-market benchmarks, do not stop at a product list. Organize the final answer into benchmark rows, what the market teaches us, what to copy, what to avoid, what to improve, and what must be verified before ordering, printing, or listing.
   - For qualification decisions, provide a concise executive decision first, then detailed findings, evidence table, missing materials, remediation, and audit log.

## Decision Statuses

Use exactly one final status:

- `approve`: No material blocker. Remaining issues are low-risk operational notes.
- `conditional_approve`: Can proceed only after clearly bounded low/medium fixes.
- `request_more_info`: Cannot decide because material evidence is missing.
- `reject`: Critical non-compliance, invalid authorization, prohibited product, forged/expired material, or unfixable mismatch.
- `escalate_human`: Legal ambiguity, suspected fraud, sanctions/export-control concern, high-value dispute, privacy-sensitive identity issue, or conflicting authoritative sources.
- `not_applicable`: The requested review type does not apply to the given platform/category/market.

## Evidence Rules

Field names follow the JSON contract in `references/report-templates.md`. Every important conclusion must include:

- `evidence_id`
- `kind` (submitted_document, official_source, registry, issuer_lookup, platform_policy, regulator, other)
- `reference` (document or source)
- `tier`
- `checked_at`
- `extracted_fact`
- `confidence`

Link conclusions back to rules: requirements reference evidence via `matched_evidence_ids`, and findings reference sources via `source_ids`.

Never invent license numbers, registration numbers, certificates, platform rules, official names, expiration dates, or issuer names. If no source confirms a requirement, write `not verified` and explain what to verify.

## Source Tiers

| Tier | Source |
|---|---|
| T1 | Official marketplace policy, official regulator, government registry, court/customs/regulatory database |
| T2 | Official accreditation body, certification body registry, standards body, official lab accreditation lookup |
| T3 | Major law firm, customs broker, compliance consultant, trade association |
| T4 | Applicant-provided documents, supplier statements, screenshots, emails, contracts |
| T5 | Social posts, forum comments, informal videos, unverifiable claims |

T4 evidence can prove what the applicant submitted, but not necessarily that the fact is true. Verify externally when the decision depends on it.

## Hard Rules

- Do not provide a pass decision when required documents are missing, expired, mismatched, outside scope, or only asserted by the applicant.
- Do not treat a document image as genuine just because it looks professional.
- Do not treat marketplace rules as stable; require source checking for current decisions.
- Do not expose full personal identity numbers, bank accounts, private addresses, phone numbers, or emails unless the user explicitly needs a machine-readable internal record.
- Do not call social media or seller anecdotes authoritative for qualification review.
- Do not present benchmark products, competitor prices, freight costs, or platform policies as current unless they were checked from current sources.
- Do not give legal advice as final authority. Phrase legal conclusions as operational review findings requiring official/professional confirmation where appropriate.

## Script Helper

Use `scripts/qualification_audit_schema.py` to create or validate structured review JSON:

```bash
python3 scripts/qualification_audit_schema.py sample
python3 scripts/qualification_audit_schema.py checklist --platform amazon --market US --category food
python3 scripts/qualification_audit_schema.py review-skeleton --platform amazon --market US --category food --applicant-name "Example Trading Co., Ltd." --applicant-role distributor --business-model marketplace_seller --brand-name "Example Brand"
python3 scripts/qualification_audit_schema.py benchmark-template --market US --category food --product "chili sauce" --platform amazon
python3 scripts/qualification_audit_schema.py validate path/to/review.json
python3 scripts/qualification_audit_schema.py case-check cases/golden-expired-certificate.json path/to/review.json
python3 scripts/qualification_audit_schema.py golden-replay
python3 scripts/qualification_audit_schema.py quality-gate
python3 scripts/qualification_audit_schema.py rulepack-new --country-code DE --country-name Germany
python3 scripts/qualification_audit_schema.py rulepack-validate data/rulepacks/global-baseline.json
python3 scripts/qualification_audit_schema.py rulepack-index-validate
python3 scripts/qualification_audit_schema.py source-freshness
```

The script is intentionally dependency-free so it can run in constrained environments. `checklist` builds its output from the rule packs in `data/rulepacks/`, includes matching `priority_combinations`, and warns when no platform/category/market pack matched. `review-skeleton` creates a JSON-contract-compliant intake review with requirements, attached official sources where available, target-market benchmark slots, findings, missing materials, remediation wording, and an audit log; it defaults to `request_more_info` because applicant documents and evidence matching are still required before approval. `benchmark-template` creates a target-market benchmark worksheet for collecting comparable local products, channels, pack sizes, prices, claims, packaging signals, certifications, review signals, and takeaways. All indexed rule-pack requirements have source IDs; the deepest source-backed high-frequency routes are Amazon US food, TikTok Shop Malaysia/ASEAN cosmetics, and Temu electronics. `golden-replay` checks all produced review fixtures under `reviews/golden/` against expectations under `cases/`. `quality-gate` runs rulepack validation, source freshness, and golden replay together. Pack maturity is still `seed`, so use sources for intake and routing until more golden cases and real-case replay support promotion to `validated` or `production`.

## Reference Map

| File | Load when |
|---|---|
| `references/audit-workflow.md` | Any real review or rulebook design |
| `references/launch-readiness-playbook.md` | Product feasibility, target-market benchmarking, competitor/pricing, packaging/label, logistics/budget, and seller-facing launch-readiness outputs |
| `references/document-taxonomy.md` | Documents, materials, certificates, labels, authorization chains |
| `references/platform-market-matrix.md` | Platform, country, category, or marketplace-specific scope |
| `references/global-country-framework.md` | Any country/region not yet covered by a mature rule pack |
| `references/rulepack-governance.md` | Adding, reviewing, versioning, and maintaining country/platform rule packs |
| `references/decision-rules.md` | Findings, severity, scoring, final decisions |
| `references/verification-playbook.md` | Source checking, freshness, certificate verification, search templates |
| `references/privacy-security.md` | PII, KYB/KYC, contracts, confidential documents |
| `references/report-templates.md` | JSON, Markdown memo, supplement request, internal audit record |
| `references/implementation-blueprint.md` | Productizing this skill in an app/backend |
