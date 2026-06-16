# Rule Pack Governance

Use this reference when people continuously improve country, region, platform, or category coverage.

## Goals

- Keep the skill usable globally through a baseline fallback.
- Let contributors add country and platform knowledge without editing the core skill.
- Preserve auditability: every rule must have source, checked date, owner, and maturity.
- Prevent stale or anecdotal rules from becoming authoritative.

## Rule Pack Types

| Type | Path | Purpose |
|---|---|---|
| Global baseline | `data/rulepacks/global-baseline.json` | Universal fallback for any country |
| Country pack | `data/rulepacks/country-XX.json` | One country, ISO-style code recommended |
| Region pack | `data/rulepacks/region-eu.json` | Regional blocs such as EU/EEA/GCC/ASEAN |
| Platform pack | `data/rulepacks/platform-amazon.json` | Platform-wide requirements independent of country |
| Category overlay | `data/rulepacks/category-food.json` | Category requirements reusable across countries |

Keep packs small and composable. A final review can combine global baseline + platform pack + country pack + category overlay.

## Pack Composition

Composition order is defined in `data/rulepacks/index.json` (`composition_order`):

1. `global` baseline
2. `platform` pack
3. `region` pack
4. `country` pack
5. `category` overlay

Rules:

- Packs are additive: requirements from all applicable packs are merged.
- When two packs define the same `requirement_id`, the later (higher-priority) pack type wins entirely for that requirement.
- `checklist_hints` (optional string list) are verification pointers, not requirements; they are concatenated, never overridden.
- A pack other than `global` should declare `match.keywords` (lowercase substrings). Pack type determines what the keywords match against: `platform` packs match the platform name, `category` packs match the category, `country`/`region` packs match the destination market.
- `scripts/qualification_audit_schema.py checklist` implements this matching and warns when no platform/category/market pack matched.

## Priority Combinations

`data/rulepacks/index.json` may define `priority_combinations` for high-frequency platform/market/category routes such as Amazon US food, TikTok Shop SEA cosmetics, Temu electronics, and Tmall Global China food/cosmetics.

These are routing accelerators, not standalone rule packs:

- `criteria` controls matching against checklist inputs.
- `expected_packs` lists the packs that should contribute to the route.
- `verification_tasks` names official-source checks that must be completed before a final decision.
- `maturity` should stay `seed` until official sources and golden cases support the route.

## Scope Field Syntax

`category_scope`, `applicant_role_scope`, and `business_model_scope` accept either `*` (any) or pipe-separated tokens, e.g. `distributor|marketplace_seller`.

Canonical applicant role tokens: `manufacturer`, `brand_owner`, `distributor`, `importer`, `marketplace_seller`, `agent`, `service_provider`.

## Contribution Workflow

1. Create a pack:

```bash
python3 scripts/qualification_audit_schema.py rulepack-new --country-code DE --country-name Germany > data/rulepacks/country-DE.json
```

2. Fill requirements with official sources where possible.
3. Run validation:

```bash
python3 scripts/qualification_audit_schema.py rulepack-validate data/rulepacks/country-DE.json
```

4. Add or update `data/rulepacks/index.json`.
5. Validate the full index:

```bash
python3 scripts/qualification_audit_schema.py rulepack-index-validate
```

6. Add at least three golden cases under `cases/` and produced review fixtures under `reviews/golden/` before marking the pack `validated` or `production`, and check produced reviews with:

```bash
python3 scripts/qualification_audit_schema.py case-check cases/<case>.json path/to/review.json
python3 scripts/qualification_audit_schema.py golden-replay
python3 scripts/qualification_audit_schema.py quality-gate
```

7. Check source freshness:

```bash
python3 scripts/qualification_audit_schema.py source-freshness
```

8. Mark maturity honestly: `seed`, `validated`, `production`, or `stale`.

## Required Rule Fields

Each requirement should include:

- `requirement_id`
- `surface`
- `category_scope`
- `applicant_role_scope`
- `business_model_scope`
- `requirement`
- `mandatory`: true/false/conditional
- `evidence_expected`
- `decision_effect`
- `source_ids`
- `freshness_days`
- `notes`

## Source Rules

Every T1/T2 rule source must include:

- source_id
- title
- URL
- tier
- checked_at
- language
- confirms

Do not add unsourced rules as authoritative. Put them in `gaps` or `notes` until verified.

## Versioning

Use semantic-ish versions:

- patch: wording/source refresh, no decision logic change
- minor: adds requirements or coverage
- major: changes decision effect or removes/changes core requirement

Every pack should include:

- `version`
- `updated_at`
- `updated_by`
- `change_note`

## Freshness Policy

This section is the canonical default freshness policy. Packs may override per requirement via `freshness_days`; `references/verification-playbook.md` defers to these values for rule sources.

Defaults (matching `global-baseline.json` `freshness_policy`):

- platform policy: 90 days
- regulator pages: 365 days
- customs/tax/import rules: 180 days
- high-risk categories: 30 days or checked per case
- certificate registry lookup: checked per case

If a source is older than its freshness window, mark the related requirement `needs_external_verification`.

Run the dependency-free scanner:

```bash
python3 scripts/qualification_audit_schema.py source-freshness
```

The report also lists source-free seed requirements as `unverified_requirements`. The command exits non-zero only when it finds stale or missing source links, which makes it suitable for CI without failing merely because seed packs are intentionally unfinished.

## Review Quality Gate

A pack can be marked `production` only if:

- at least 80% of mandatory requirements have T1/T2 sources
- no critical requirement is based only on T3/T4/T5
- freshness windows are defined
- at least 3 representative golden cases under `cases/` pass `case-check` with expected decisions
- produced review fixtures exist under `reviews/golden/` and pass `golden-replay`
- privacy notes exist for documents that include PII/KYB data

`rulepack-validate` enforces core schema and maturity gates for a single pack. `rulepack-index-validate` enforces index consistency and validates every indexed pack. Current source freshness is checked separately with `source-freshness`.
