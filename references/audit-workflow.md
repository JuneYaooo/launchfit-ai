# Audit Workflow

This reference defines the operating model for cross-border e-commerce qualification review. Output field names must follow the JSON contract in `references/report-templates.md`.

## Review Surfaces

| Surface | Examples | Primary risk |
|---|---|---|
| Seller/KYB | Business license, tax registration, legal representative, bank/payee, beneficial owner, store operator | False entity, sanctions, account mismatch |
| Brand/IP | Trademark certificate, brand authorization, distribution agreement, chain of authorization | Unauthorized selling, wrong territory/class, expired right |
| Product/category | Product photos, formula, ingredient list, category selection, claims, restricted product status | Prohibited listing, category gating failure |
| Market/import | Importer of record, customs documents, registrations, local representative, labeling | Customs hold, illegal sale, missing local entity |
| Certificate/report | FDA registration, CE, FCC, CPSR, COA, MSDS/SDS, ISO, HACCP, Halal, Organic, test report | Forged, expired, out-of-scope, wrong holder |
| Platform listing | Marketplace category requirements, product detail page claims, images, warning labels | Listing rejection, takedown, account enforcement |
| Service provider | Testing lab, logistics provider, compliance agent, customs broker | Unqualified provider, no accreditation, bad handoff |

## Case Intake Fields

Collect or infer:

- `case_id`
- `applicant_name`
- `applicant_role`
- `origin_country`
- `platform`
- `marketplace_site`
- `destination_market`
- `destination_markets`
- `go_to_market_model` (`cross_border_ecommerce`, `physical_trade`, `hybrid`, or `unknown`)
- `business_model`
- `product_category`
- `subcategory`
- `brand_name`
- `review_purpose`
- `submitted_documents`
- `requested_decision_deadline`

If `origin_country`, `destination_markets`, `go_to_market_model`, `category`, or `review_purpose` is absent, treat the review as incomplete and produce an intake checklist rather than a final decision. If `go_to_market_model` is `cross_border_ecommerce` or `hybrid`, platform is a required P0 scope field. If `go_to_market_model` is `physical_trade`, platform can be empty, but importer/distributor/offline channel and customs route become P0 scope fields. If more than one destination is provided, create destination-specific review tracks rather than combining rules into one market.

## Review Stages

### 1. Intake normalization and route split

Normalize applicant, brand, product, platform, market, and document names. Convert translated names into a canonical table and preserve originals.

Classify the sales route before benchmarking:

| `go_to_market_model` | Primary route | P0 checks |
|---|---|---|
| `cross_border_ecommerce` | Marketplace or social-commerce launch | Platform/category admission, listing claims, brand/IP, fulfillment and warehouse rules |
| `physical_trade` | Export/import, importer, distributor, retail, wholesale, or offline shelf | Origin export, destination import/customs, importer/responsible party, local registration/label, Incoterms and logistics |
| `hybrid` | Ecommerce plus physical import/distribution | Run ecommerce and physical-trade checks separately, then merge blockers |
| `unknown` | User has not clarified route | Ask route question or make route confirmation a P0 research task |

### 2. Document inventory

Create a line item for every submitted document:

| Field | Meaning |
|---|---|
| `document_id` | Stable local identifier |
| `document_type` | License, certificate, report, authorization, label, screenshot, contract, etc. |
| `holder` | Entity/person named on the document |
| `issuer` | Issuing authority or organization |
| `number` | License/certificate/report number, redacted when needed |
| `issue_date` | As shown |
| `expiry_date` | As shown |
| `scope` | Product/category/territory/standard covered |
| `language` | Document language |
| `extraction_confidence` | high/medium/low |
| `privacy_level` | public/business_confidential/pii/highly_sensitive |

### 3. Requirement mapping

For each platform/market/category, produce:

- mandatory documents
- conditional documents
- disallowed product/category signals
- label/claim constraints
- entity/local representative requirements
- brand/IP requirements
- renewals and validity constraints
- manual review triggers

### 4. Evidence matching

Match every requirement to evidence:

| Status | Meaning |
|---|---|
| `satisfied` | Direct evidence meets requirement |
| `partial` | Evidence exists but scope/date/name/category does not fully match |
| `missing` | No submitted evidence |
| `invalid` | Evidence is expired, contradictory, unverifiable, or out of scope |
| `not_applicable` | Requirement does not apply after scope review |
| `needs_external_verification` | Submitted evidence must be checked in official/issuer database |

### 5. Findings and decision

Convert mismatches into findings. Apply `references/decision-rules.md` and choose a final status.

### 6. Remediation

For every non-approve finding, provide:

- exact missing/failing material
- why it matters
- who should provide it
- acceptable replacement
- target format
- deadline or validity expectation
- applicant-facing wording

### 7. Audit log

Record:

- review date and reviewer/agent
- rule/source version or checked date
- files reviewed
- sources checked
- assumptions
- final decision
- escalation reason if applicable

## Minimum Decision Package

Every final review should include:

- one-line decision
- scope snapshot
- requirement coverage table
- findings table
- evidence table
- missing/invalid materials
- remediation request
- source/freshness table
- privacy redaction note
- disclaimer and escalation note
