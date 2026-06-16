# Runnable Examples

These examples show what the skill can do without a product UI.

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
PASS: golden-complete-low-risk
PASS: golden-expired-certificate
PASS: golden-missing-scope
PASS: golden-prohibited-category
PASS: golden-suspected-forged-document
PASS: golden-unverified-applicant-docs
OK: 7 golden cases replayed
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

Run the full publication gate:

```bash
python3 scripts/qualification_audit_schema.py quality-gate
```

Expected result:

```text
OK: rulepack index valid
OK: source freshness clean (116 checked source links)
OK: 7 golden cases replayed
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
