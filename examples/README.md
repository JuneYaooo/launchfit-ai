# Runnable Examples

These examples show what the skill can do without a product UI.

## Benchmark-First Workflow

Validate and summarize a broad target-market benchmark worksheet:

```bash
python3 scripts/qualification_audit_schema.py benchmark-validate \
  examples/benchmark-worksheet.json

python3 scripts/qualification_audit_schema.py benchmark-summarize \
  examples/benchmark-worksheet.json \
  > /tmp/launchfit-benchmark-summary.json
```

The worksheet covers direct competitors, substitutes, adjacent references, category leaders, local niche brands, platform best sellers, offline retail shelf products, and DTC/social commerce products. The summary produces price bands, channel maps, packaging conventions, claims/proof, review themes, and copy / avoid / improve actions.

Create and validate a launch bundle:

```bash
python3 scripts/qualification_audit_schema.py bundle-template \
  --platform amazon \
  --market US \
  --category food \
  --product "chili sauce" \
  --origin-country China \
  --go-to-market-model cross_border_ecommerce \
  --destination-market US \
  --destination-market EU \
  > /tmp/launchfit-bundle-template.json

python3 scripts/qualification_audit_schema.py bundle-validate \
  examples/offline-launch-case.json
```

## Offline Launch Readiness MVP

Generate a full launch-readiness report from a case bundle containing product scope, origin country, one or more destination markets, applicant documents, packaging text, competitor rows, and logistics rows:

```bash
python3 scripts/qualification_audit_schema.py launch-report \
  examples/offline-launch-case.json \
  > /tmp/launchfit-offline-report.json
```

Validate the generated JSON:

```bash
python3 scripts/qualification_audit_schema.py validate /tmp/launchfit-offline-report.json
```

Render the same report as a seller-facing Markdown memo:

```bash
python3 scripts/qualification_audit_schema.py launch-report-markdown \
  /tmp/launchfit-offline-report.json \
  > /tmp/launchfit-offline-report.md
```

Generate the two final user-facing deliverables:

```bash
python3 scripts/qualification_audit_schema.py launch-report-card \
  /tmp/launchfit-offline-report.json \
  /tmp/launchfit-core-card.html

python3 scripts/qualification_audit_schema.py launch-report-detail \
  /tmp/launchfit-offline-report.json \
  /tmp/launchfit-detailed-review.html
```

If local Chrome/Chromium is available, the same commands can export a screenshot card and PDF:

```bash
python3 scripts/qualification_audit_schema.py launch-report-card \
  /tmp/launchfit-offline-report.json \
  /tmp/launchfit-core-card.png

python3 scripts/qualification_audit_schema.py launch-report-detail \
  /tmp/launchfit-offline-report.json \
  /tmp/launchfit-detailed-review.pdf
```

Check the generated report against the offline launch golden case:

```bash
python3 scripts/qualification_audit_schema.py case-check \
  cases/golden-offline-launch-readiness.json \
  /tmp/launchfit-offline-report.json
```

Expected result:

```text
OK
PASS: offline-launch-readiness
```

Bundle facts are useful for intake and routing, but they are not external verification. User-provided documents and screenshots are treated as T4 evidence, competitor rows remain `user_provided` unless marked `current_checked`, and unresolved official checks remain `needs_external_verification`. The report also emits `market_reviews`, `source_candidates`, and `research_tasks` so live search, registry APIs, browser checks, or human review can fill the same evidence model for each destination market.

## Amazon US Food Intake Skeleton

Generate a structured review JSON for an Amazon US food/grocery intake:

```bash
python3 scripts/qualification_audit_schema.py review-skeleton \
  --platform amazon \
  --market US \
  --category food \
  --applicant-name "Example Trading Co., Ltd." \
  --applicant-role distributor \
  --business-model marketplace_seller \
  --brand-name "Example Brand" \
  > /tmp/cbec_review_skeleton.json
```

Validate the generated review:

```bash
python3 scripts/qualification_audit_schema.py validate /tmp/cbec_review_skeleton.json
```

Check that it behaves like an applicant-evidence-only intake that still needs external verification:

```bash
python3 scripts/qualification_audit_schema.py case-check \
  cases/golden-unverified-applicant-docs.json \
  /tmp/cbec_review_skeleton.json
```

Expected result:

```text
OK
PASS: golden-unverified-applicant-docs
```

## Golden Replay

Run all produced review fixtures against their expected golden cases:

```bash
python3 scripts/qualification_audit_schema.py golden-replay
```

Expected result:

```text
PASS: golden-brand-authorization-territory
PASS: golden-benchmark-summary
PASS: golden-complete-low-risk
PASS: golden-expired-certificate
PASS: golden-missing-scope
PASS: offline-launch-readiness
PASS: golden-prohibited-category
PASS: golden-suspected-forged-document
PASS: golden-unverified-applicant-docs
OK: 9 golden cases replayed
```

## Target-Market Benchmark Template

Generate a worksheet for collecting comparable products in the target market:

```bash
python3 scripts/qualification_audit_schema.py benchmark-template \
  --market US \
  --category food \
  --product "chili sauce" \
  --platform amazon
```

Use the rows to capture local benchmark products, channel role, pack size, price/unit, claims, packaging signals, visible certifications, review signals, and the takeaway for the launch decision.

## Batch Reports And Coverage

Generate JSON and Markdown reports for every bundle in a directory:

```bash
python3 scripts/qualification_audit_schema.py batch-launch-report \
  examples/batch \
  /tmp/launchfit-batch
```

Inspect Skill coverage:

```bash
python3 scripts/qualification_audit_schema.py coverage-report
```

Run the full publication gate:

```bash
python3 scripts/qualification_audit_schema.py quality-gate
```

Expected result:

```text
OK: rulepack index valid
OK: source freshness clean (116 checked source links)
OK: 9 golden cases replayed
OK: 1 benchmark worksheet fixtures valid
OK: 3 bundle fixtures valid
OK: coverage report generated
```

## Source Freshness

Check whether rule-pack requirements have attached sources and whether attached sources are stale:

```bash
python3 scripts/qualification_audit_schema.py source-freshness
```

## TikTok Shop Malaysia Cosmetics Intake Skeleton

```bash
python3 scripts/qualification_audit_schema.py review-skeleton \
  --platform tiktok \
  --market Malaysia \
  --category cosmetics \
  --applicant-name "Example Beauty Trading Sdn. Bhd." \
  --applicant-role distributor \
  --business-model marketplace_seller \
  --brand-name "Example Beauty" \
  > /tmp/cbec_tiktok_cosmetics.json

python3 scripts/qualification_audit_schema.py validate /tmp/cbec_tiktok_cosmetics.json
python3 scripts/qualification_audit_schema.py case-check \
  cases/golden-unverified-applicant-docs.json \
  /tmp/cbec_tiktok_cosmetics.json
```

## Temu Electronics Intake Skeleton

```bash
python3 scripts/qualification_audit_schema.py review-skeleton \
  --platform temu \
  --market EU \
  --category electronics \
  --applicant-name "Example Electronics Co., Ltd." \
  --applicant-role manufacturer \
  --business-model marketplace_seller \
  --brand-name "Example Tech" \
  > /tmp/cbec_temu_electronics.json

python3 scripts/qualification_audit_schema.py validate /tmp/cbec_temu_electronics.json
python3 scripts/qualification_audit_schema.py case-check \
  cases/golden-unverified-applicant-docs.json \
  /tmp/cbec_temu_electronics.json
```

Expected freshness summary after the current source pass:

```text
checked_source_links: 116
unverified_requirements: []
stale: []
missing: []
```

The Amazon US food, TikTok Shop Malaysia cosmetics, and Temu electronics paths include deeper T1 official source coverage. Other indexed packs now have official or authoritative source entry points, but their maturity remains `seed` until more golden cases and real-case replay are added.
