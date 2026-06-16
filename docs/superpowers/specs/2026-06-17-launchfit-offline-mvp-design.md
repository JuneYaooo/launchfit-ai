# LaunchFit Offline MVP Design

## Goal

Make this skill project practically deliver the README promise in an offline, auditable MVP: given a structured product case bundle with applicant data, document fields, packaging text, competitor signals, and logistics options, produce a launch-readiness report that covers benchmarking, pricing, packaging, logistics, platform admission, qualification gaps, and remediation.

## Scope

This iteration builds a dependency-free CLI workflow inside `scripts/qualification_audit_schema.py`. It does not add OCR, live marketplace scraping, registry lookups, freight APIs, UI, database persistence, or MCP integrations. Those remain productization layers described in `references/implementation-blueprint.md`.

The MVP must not pretend offline inputs are externally verified. It must preserve the existing evidence model by marking user-provided facts as `T4`, benchmark rows as `user_provided` unless explicitly checked, and unresolved external checks as `needs_external_verification`.

## User Workflow

1. User creates or edits a case bundle JSON.
2. User runs a CLI command to generate a launch report JSON.
3. User optionally exports the report to Markdown.
4. User validates the JSON with the existing validator.
5. User runs `quality-gate` to verify rule packs, source freshness, golden cases, and the new offline launch fixture.

## Case Bundle

The bundle is a JSON object with these top-level sections:

- `case`: applicant, product, platform, market, category, business model, brand, purpose.
- `documents`: extracted document fields such as type, holder, issuer, dates, scope, territory, brand, product, and confidence.
- `packaging`: front label text, back label text, claims, ingredients/materials, warnings, languages, units, and visible certification marks.
- `competitors`: benchmark rows with product, channel, role, pack size, price, unit price, positioning, visible claims, packaging signals, certifications, review signals, and source basis.
- `logistics`: route rows with mode, destination, time, cost basis, constraints, risks, and preparation steps.
- `sources`: optional user-supplied sources that can be linked to competitor or logistics rows.

## Report Behavior

The launch report reuses the existing review JSON contract so the current validator still works. It fills:

- `case` from the bundle.
- `documents` from extracted document fields.
- `market_benchmarks` and `market_benchmark_summary` from competitors.
- `requirements`, `findings`, `missing_materials`, `evidence`, and `sources` from matched rule packs plus offline checks.
- `remediation.applicant_message` with concrete supplement requests.
- `audit_log` with generated bundle, rule pack, evidence, and export actions.

Decision mapping:

- `reject`: prohibited category, critical unfixable mismatch, or critical blocker explicitly detected.
- `escalate_human`: suspected forged document, conflicting authoritative evidence, sanctions/export-control marker, or highly sensitive legal ambiguity marker.
- `request_more_info`: missing mandatory scope, missing required documents, expired document, applicant-only evidence for mandatory requirement, or no benchmark/logistics basis for a requested launch decision.
- `conditional_approve`: no critical/high blocker remains, but bounded packaging, logistics, source verification, or missing low/medium items remain.
- `approve`: all mandatory requirements are satisfied by matching evidence and no critical/high/medium launch blockers remain.

For this MVP, generated reports should usually be `request_more_info` or `conditional_approve`; `approve` is allowed only for complete test fixtures with satisfied requirements and matching evidence.

## Offline Checks

Document checks:

- Expired document creates high finding and missing material.
- Holder mismatch against applicant name creates high finding.
- Brand authorization missing territory/platform/category creates high finding.
- Document scope that does not mention the product/category creates medium or high finding based on mandatory requirement.
- Low extraction confidence creates medium finding.
- `suspected_forgery: true` creates critical finding and `escalate_human`.

Packaging checks:

- Regulated claims such as disease treatment, cure, medical effect, SPF, organic, FDA approved, CE/FCC, antimicrobial, hypoallergenic, or child safety require evidence.
- Missing market language or warnings creates a packaging finding.
- Certification marks on packaging require matching evidence.
- Food/cosmetics/supplements/electronics category hints trigger category-specific label checks using existing rule packs where available.

Benchmark checks:

- Normalize competitor rows into `market_benchmarks`.
- Summarize price band, channel map, packaging conventions, claims/proof, trust signals, review themes, gap opportunity, copy/avoid/improve, listing preparation, and verification needed.
- Do not invent prices or product names.
- Rows without source basis remain `user_provided` or `not_checked`.

Logistics checks:

- Compare routes by fit, time, cost driver, constraints, risks, and preparation.
- Create findings for category-route risks such as battery, liquid, aerosol, food shelf life, cold chain, dangerous goods, fragile, or high value.
- Do not invent freight rates.

## Files

- Modify `scripts/qualification_audit_schema.py`: add bundle parsing, launch report generation, Markdown export, validation checks, CLI commands, and quality-gate coverage.
- Add `examples/offline-launch-case.json`: runnable case bundle matching README scenarios.
- Add `examples/offline-launch-report.json`: produced golden fixture.
- Add `cases/golden-offline-launch-readiness.json`: expectation for the new generated report.
- Update `examples/README.md`: show the new end-to-end commands.
- Update `README.md` and `README.en.md`: clarify the project now supports a local offline MVP and that OCR/API/live verification remain integration layers.
- Update `SKILL.md`: route users to the new `launch-report` and `launch-report-markdown` commands.

## Testing

Tests are command-level because this project currently uses a dependency-free single-script helper instead of a test framework. The implementation must:

- Generate a valid report from `examples/offline-launch-case.json`.
- Export a Markdown memo containing Snapshot, Target-Market Benchmarks, Packaging/Label, Logistics/Budget, Missing Materials, and Assumptions/Verification sections.
- Pass `validate` on the generated JSON.
- Pass `case-check` against the new offline launch golden case.
- Pass `golden-replay`.
- Pass `quality-gate`.

## Self-Review

- No live capability is claimed; offline and user-provided evidence are explicitly labeled.
- The design uses the existing JSON contract instead of creating a parallel report schema.
- The scope is a single coherent subsystem: case bundle to launch report.
- Ambiguous decisions default to `request_more_info` unless evidence supports a stronger status.
