---
name: launchfit-ai
description: Use when reviewing cross-border product launch readiness, target-market benchmarks, marketplace/category admission, packaging or claims, documents, brand authorization, certificates, logistics, or remediation for products moving from an origin country to one or more destination markets.
metadata:
  short-description: LaunchFit AI / 出海体检官
---

# LaunchFit AI / 出海体检官

Use this skill as LaunchFit AI / 出海体检官: turn a cross-border product idea or messy launch package into an AI checkup report that shows whether it can sell, where it may get blocked, what to fix, what to prepare, and whether it can move forward.

This skill is not only for low-frequency compliance review. It supports high-frequency seller workflows before and during launch: product feasibility, target-market benchmarking, competitor and pricing checks, packaging and label readiness, logistics planning, platform admission, qualification review, and applicant-facing remediation.

When the user asks for a final qualification decision, the output must remain auditable: approve, conditionally approve, request more information, reject, or escalate to human review.

## Start Here

The useful outcome is not generic advice. The useful outcome is a next-action package:

1. **Scope:** origin country, destination markets, go-to-market model, platform/offline channel, category, product, applicant role, business model.
2. **Route split:** decide whether this is `cross_border_ecommerce`, `physical_trade`, `hybrid`, or still `unknown`.
3. **Admission-risk screen:** what can block platform listing, import, export, label, brand/IP, logistics, or margin.
4. **Market evidence plan:** where to get current information and benchmark signals for each destination.
5. **Actions:** who must provide which material, which source to check, and what evidence field to capture.
6. **Generation note:** which agent generated the report, which model was declared, which search/information routes were used, and the generated date.

Target-market benchmarking is an agent responsibility. The agent 主动检索 marketplace, retail, DTC, social, distributor, and public shopping surfaces before asking for user screenshots. 用户提供的搜索渠道只能作为补充 evidence or a preferred route to check; do not treat it as a prerequisite, and 不能把找对标的责任推给用户.

If the user has not provided origin country and destination markets, ask for exactly those two missing inputs first. If they gave only one destination, continue with one. If they gave multiple destinations, split the work by destination.

If the sales path is unclear, ask whether the user is doing cross-border ecommerce, physical export/import trade, or both. If the user cannot answer yet, set `go_to_market_model` to `unknown` and make route confirmation a P0 task.

## Operating Loop

Follow this loop for every real case:

1. **Lock scope** before analysis: `origin_country`, `destination_markets[]`, `go_to_market_model`, platform/offline channel, category, product, applicant role, business model.
2. **Classify route** before benchmarking: ecommerce checks platform/category/listing/fulfillment first; physical trade checks export/import/customs/responsible party/distributor channel first; hybrid runs both tracks separately.
3. **Run admission-risk screen before market benchmarking:** identify prohibited/restricted product, mandatory documents, registration, label, claim, authorization, logistics, or route blockers.
4. **Route each destination** through rule packs and source candidates. Never merge `US, EU` into one market.
5. **Generate research tasks** before conclusions: platform policy when relevant, destination regulator, customs/import, brand/IP, business registry, certification/lab, standards, logistics/warehouse, origin/export, offline/retail/distributor channels when relevant, agent-found benchmark channels, and user search channels.
6. **Actively gather benchmark rows:** for each destination, look for direct competitors, imported substitutes, local substitutes, platform best sellers, offline shelf references, DTC/social examples, and large-pack/unit-price anchors. Record product, channel, pack size, price/unit price if visible, positioning, packaging signals, claims, trust signals, review themes, source URL, checked date, data basis, and visual evidence fields (`image_url`, `image_alt`) when product images or screenshots are available.
7. **Separate facts by source tier:** T1/T2 can support decisions; T4 user material and commercial listing/search signals can only support market evidence unless externally verified.
8. **Give the seller next actions first:** launch view, go-to-market path, blockers, research tasks, missing materials, then deeper evidence tables.

## Final Deliverables

For a complete LaunchFit review, produce two user-facing deliverables:

1. **Core overview card**
   - Purpose: one-screen decision aid for founders, sellers, clients, and operators.
   - Format: image card when image generation or screenshot tooling is available; otherwise HTML card that can be screenshot.
   - Contents: product and route, origin and destinations, launch view, top 3 blockers, must-check channels, next actions, and confidence/evidence status.
   - Rule: no dense legal explanation, no long tables, no unsupported pass/fail claim. Include a small corner/footer generation note naming agent, declared model, search/information routes, and generated date.

2. **Detailed PDF**
   - Purpose: auditable working document for compliance, operations, suppliers, service providers, and internal handoff.
   - Format: PDF generated from structured HTML/Markdown or an equivalent document export.
   - Contents: scope, per-destination market reviews, benchmark table, source candidates, research tasks, evidence table, findings, missing materials, packaging/label fixes, logistics review, remediation wording, audit log, and disclaimer.
   - Rule: every important conclusion links to evidence/source tier or stays `needs_external_verification`. Include generation metadata so readers know whether the report used user materials, rule packs, agent active search, commercial benchmark search, official-source candidates, or other declared channels. Keep long source/search URLs and “对标来源与核验边界” in an appendix or attachment instead of the main body. When benchmark rows include `image_url`, render a compact “对标商品图” section so product packaging and listing visuals are easy to compare.

Use the chat response to summarize the deliverables and next actions. Do not make the chat transcript the main artifact when the user asked for a review output.

## Hard Gates

- No origin country → no final decision.
- No destination market → no final decision.
- Unknown go-to-market model → no final pass decision; confirm whether the path is cross-border ecommerce, physical trade, or hybrid.
- Multiple destinations → one `market_review` per destination.
- Cross-border ecommerce → platform/category/listing/fulfillment checks are P0.
- Physical trade → origin export, destination import/customs, importer/responsible-party, Incoterms/logistics, and offline channel checks are P0.
- Current platform, regulator, registry, competitor price, logistics, or legal facts → verify current sources or mark `needs_external_verification`.
- User-provided screenshots, documents, platform links, supplier channels, search URLs, and industry databases → record as `user_search_channels`, T4 evidence, or `external_checks`; do not treat them as authoritative by default.
- Any missing, expired, mismatched, out-of-scope, forged-looking, or applicant-only core evidence → no pass decision.

## Core Modes

| Mode | Use when | Output |
|---|---|---|
| Launch intake | User provides a product, target market, platform, category, or launch idea | Scope, assumptions, missing inputs, launch-readiness checklist |
| Product feasibility | User asks whether a product can or should be sold in a market | Opportunity/risk view, obvious blockers, verification plan, next actions |
| Go-to-market route triage | User has not clarified whether this is cross-border ecommerce, physical trade, or hybrid | Route classification, P0 checks by route, assumptions to confirm |
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
- Go-to-market model: `cross_border_ecommerce`, `physical_trade`, `hybrid`, or `unknown`.
- Business model: export, import, cross-border bonded, direct mail, marketplace FBA/FBT/FBM, domestic-to-overseas, overseas-to-China.
- Commercial goal: new product selection, launch readiness, listing approval, pricing, packaging, logistics, blocked review, remediation, or SOP design.
- Platform/channel and market: marketplace name when ecommerce is involved; importer, distributor, retail, wholesale, or offline channel when physical trade is involved; destination country/region, store site, warehouse model.
- Origin and destinations: product origin country/region plus one or more destination countries/regions. If multiple destinations are provided, split the review by destination instead of merging rules into one market string.
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
   - Classify `go_to_market_model` before benchmarking: `cross_border_ecommerce`, `physical_trade`, `hybrid`, or `unknown`.
   - Assign initial risk: low, medium, high, critical.

2. **Frame the launch question**
   - Load `references/launch-readiness-playbook.md` for product feasibility, target-market benchmarking, competitor/pricing, packaging/label, logistics/budget, or seller-facing launch questions.
   - If the user asks "can this sell" or "what should I prepare", produce a launch-readiness answer first, not a narrow compliance memo.
   - Run a route-specific admission-risk screen before benchmark conclusions: ecommerce prioritizes platform/category/listing/fulfillment; physical trade prioritizes export/import/customs/responsible party/offline channel; hybrid separates both.
   - Separate commercial assumptions from verified facts: product positioning, benchmark product signals, price band, competitor signals, origin country, target markets, logistics route, platform route, importer/distributor route, and retail/offline channel route.
   - For each origin/destination pair, generate source candidates and research tasks before relying on any market rule or commercial signal.
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
python3 scripts/qualification_audit_schema.py benchmark-validate examples/benchmark-worksheet.json
python3 scripts/qualification_audit_schema.py benchmark-summarize examples/benchmark-worksheet.json
python3 scripts/qualification_audit_schema.py bundle-template --platform amazon --market US --category food --product "chili sauce" --origin-country China --go-to-market-model cross_border_ecommerce --destination-market US --destination-market EU
python3 scripts/qualification_audit_schema.py bundle-validate examples/offline-launch-case.json
python3 scripts/qualification_audit_schema.py launch-report examples/offline-launch-case.json
python3 scripts/qualification_audit_schema.py launch-report-markdown examples/offline-launch-report.json
python3 scripts/qualification_audit_schema.py launch-report-card examples/offline-launch-report.json /tmp/launchfit-card.html
python3 scripts/qualification_audit_schema.py launch-report-card examples/offline-launch-report.json /tmp/launchfit-card.png
python3 scripts/qualification_audit_schema.py launch-report-detail examples/offline-launch-report.json /tmp/launchfit-detail.html
python3 scripts/qualification_audit_schema.py launch-report-detail examples/offline-launch-report.json /tmp/launchfit-detail.pdf
python3 scripts/qualification_audit_schema.py batch-launch-report examples/batch /tmp/launchfit-batch
python3 scripts/qualification_audit_schema.py coverage-report
python3 scripts/qualification_audit_schema.py validate path/to/review.json
python3 scripts/qualification_audit_schema.py case-check cases/golden-expired-certificate.json path/to/review.json
python3 scripts/qualification_audit_schema.py golden-replay
python3 scripts/qualification_audit_schema.py quality-gate
python3 scripts/qualification_audit_schema.py rulepack-new --country-code DE --country-name Germany
python3 scripts/qualification_audit_schema.py rulepack-validate data/rulepacks/global-baseline.json
python3 scripts/qualification_audit_schema.py rulepack-index-validate
python3 scripts/qualification_audit_schema.py source-freshness
```

Command routing:

| User intent | Command |
|---|---|
| Need benchmark worksheet | `benchmark-template` |
| Validate benchmark rows | `benchmark-validate` |
| Summarize benchmark rows | `benchmark-summarize` |
| Create launch bundle | `bundle-template` |
| Validate bundle | `bundle-validate` |
| Generate launch report | `launch-report` |
| Render Markdown memo | `launch-report-markdown` |
| Generate overview card | `launch-report-card` |
| Generate detailed HTML/PDF | `launch-report-detail` |
| Batch reports | `batch-launch-report` |
| Check Skill health | `quality-gate` |
| Inspect coverage | `coverage-report` |

The script is dependency-free for JSON/Markdown/HTML generation so it can run in constrained environments; PNG/PDF export uses local Chrome/Chromium when available. `checklist` builds its output from the rule packs in `data/rulepacks/`, includes matching `priority_combinations`, and warns when no platform/category/market pack matched. `review-skeleton` creates a JSON-contract-compliant intake review with requirements, attached official sources where available, target-market benchmark slots, findings, missing materials, remediation wording, and an audit log; it defaults to `request_more_info` because applicant documents and evidence matching are still required before approval. `benchmark-template` creates a target-market benchmark worksheet for direct competitors, substitutes, adjacent references, category leaders, local niche brands, platform best sellers, offline retail shelf products, and DTC/social commerce products. `benchmark-summarize` turns rows into price bands, channel maps, packaging conventions, claims/proof, review signals, and copy / avoid / improve actions. `bundle-template` accepts `--go-to-market-model` so ecommerce, physical trade, hybrid, and unknown routes do not share one review path. `launch-report` turns a case bundle into a full launch-readiness JSON report covering go-to-market route, documents, target-market benchmarks, packaging/claims, logistics, platform or offline channel admission, missing materials, remediation, and per-destination research routing. New bundles require product origin and destination markets; generated reports include `go_to_market_route`, `market_reviews`, `source_candidates`, and `research_tasks` so live search, registry APIs, browser checks, user-provided search channels, or human review can fill the same evidence model. `launch-report-markdown` renders the same JSON as a seller-facing memo. `launch-report-card` renders the core overview card to HTML or PNG; `launch-report-detail` renders the detailed review to HTML or PDF. Bundle facts are not external verification: user-provided documents and screenshots are T4 evidence, competitor rows remain `user_provided` unless marked `current_checked`, and unresolved official checks remain `needs_external_verification`. OCR, live search/scraping, registry checks, user platform links, supplier channels, industry databases, and freight quotes are enhancement inputs that should populate `user_search_channels` or `external_checks`, not hard dependencies. All indexed rule-pack requirements have source IDs; the deepest source-backed high-frequency routes are Amazon US food, TikTok Shop Malaysia/ASEAN cosmetics, and Temu electronics. `golden-replay` checks all produced review fixtures and declared example fixtures against expectations under `cases/`. `quality-gate` runs rulepack validation, source freshness, golden replay, benchmark worksheet validation, bundle fixture validation, and coverage generation together. Pack maturity is still `seed`, so use sources for intake and routing until more golden cases and real-case replay support promotion to `validated` or `production`.

## Common Mistakes

| Mistake | Correction |
|---|---|
| Giving advice before origin/destination scope is known | Ask only for origin country and destination markets, then continue. |
| Treating a screenshot or supplier statement as proof | Mark it T4 and create a research task for official confirmation. |
| Merging multiple destinations into one checklist | Split into `market_reviews[]`; summarize only after per-market review. |
| Starting with legalistic compliance language for seller questions | Start with can sell / can list / what to fix next. |
| Listing sources without actions | Convert every source into a research task with evidence fields and owner. |
| Saying current prices or rules are current without checking | Mark `needs_external_verification` or cite checked source/date. |

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
