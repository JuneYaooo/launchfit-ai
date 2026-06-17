# LaunchFit Live Research Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add origin-country and multi-destination research routing to LaunchFit reports.

**Architecture:** Keep the local CLI dependency-free. Add small helpers for destination normalization, source candidate generation, research task generation, and market review assembly. Preserve legacy single `destination_market` input for report generation while making new bundle validation and templates require `origin_country` plus `destination_markets`.

**Tech Stack:** Python standard library, `unittest`, JSON fixtures, Markdown docs.

---

### Task 1: Tests First

**Files:**
- Create: `tests/test_live_research_routing.py`

- [ ] Write failing `unittest` coverage for missing origin, missing destinations, multi-market report splitting, and research task presence.
- [ ] Run `python3 -m unittest tests.test_live_research_routing -v` and confirm failures are caused by missing behavior.

### Task 2: Bundle Schema Helpers

**Files:**
- Modify: `launchfit/bundles.py`
- Modify: `scripts/qualification_audit_schema.py`

- [ ] Add `origin_country` and `destination_markets` to bundle templates.
- [ ] Add normalization helpers for destination arrays.
- [ ] Update bundle validation to require origin and destination array.
- [ ] Keep report generation tolerant of legacy `destination_market` fixtures.

### Task 3: Research Routing

**Files:**
- Modify: `scripts/qualification_audit_schema.py`

- [ ] Add source candidate generation by origin, destination, platform, and category.
- [ ] Add research task generation for platform policy, regulator, customs/import, company, trademark, certification/lab, standards, logistics, and origin/export checks.
- [ ] Add `market_reviews` assembly and top-level report fields.

### Task 4: Fixtures And Docs

**Files:**
- Modify: `examples/offline-launch-case.json`
- Modify: `examples/batch/food-us.json`
- Modify: `examples/batch/electronics-eu.json`
- Modify: `references/report-templates.md`
- Modify: `references/global-country-framework.md`
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] Update examples to include origin and destination arrays.
- [ ] Document research routing as the core current-information workflow.

### Task 5: Verification

**Files:**
- No new files.

- [ ] Run `python3 -m unittest tests.test_live_research_routing -v`.
- [ ] Run `python3 scripts/qualification_audit_schema.py quality-gate`.
- [ ] Run sample launch-report, validate, markdown render.

