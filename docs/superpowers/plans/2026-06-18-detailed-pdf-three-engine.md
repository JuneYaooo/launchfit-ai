# Detailed PDF Three-Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the detailed PDF as a complete three-engine cross-border FMCG report while keeping the core card concise.

**Architecture:** Keep the existing JSON contract and extend only the HTML/PDF renderer in `scripts/qualification_audit_schema.py`. Reuse current report fields for findings, missing materials, benchmarks, source candidates, research tasks, packaging, logistics, remediation, evidence, and audit log.

**Tech Stack:** Python stdlib, unittest, Chrome PDF export through the existing CLI.

---

### Task 1: Lock Report Structure With Tests

**Files:**
- Modify: `tests/test_deliverable_generation.py`

- [x] Add a failing test that `render_detailed_pdf_html()` contains `Engine 1：准入与合规审核`, `Engine 2：本地化适配`, `Engine 3：全链路落地`, `市场准入概览`, `包装本地化`, `渠道与落地路径`, `成本与时间线`, and `待查证项`.
- [x] Add a failing test that the real Mantova run contains China import, Chinese label, origin certificate, importer/customs, source candidates, research tasks, and evidence tier summaries in the detailed report.
- [x] Run `python3 -m unittest tests.test_deliverable_generation -v` and confirm the new tests fail for missing sections.

### Task 2: Expand Detailed PDF Renderer

**Files:**
- Modify: `scripts/qualification_audit_schema.py`

- [x] Add small HTML helpers for empty-state rows, route-check translation, and pending-verification rows.
- [x] Replace the brief-only detailed PDF body with a structured report:
  - one-page decision summary
  - product file
  - Engine 1 compliance/admission review
  - Engine 2 localization/benchmarking review
  - Engine 3 implementation/logistics/channel review
  - evidence and pending-verification appendix
  - audit log and disclaimer
- [x] Keep old English compatibility anchors hidden for existing tests.
- [x] Run `python3 -m unittest tests.test_deliverable_generation -v` and confirm it passes.

### Task 3: Regenerate Real Run Artifacts

**Files:**
- Modify: `examples/real-runs/mantova-olive-oil-china-import/outputs/detailed-report.html`
- Modify: `examples/real-runs/mantova-olive-oil-china-import/outputs/detailed-report.pdf`
- Modify if deterministic output changes: `examples/real-runs/mantova-olive-oil-china-import/outputs/report.json`, `core-card.html`, `core-card.png`

- [x] Run the existing `launch-report`, `launch-report-card`, and `launch-report-detail` commands for the Mantova bundle.
- [x] Open or inspect the generated HTML/PDF content for section completeness and no local path leakage.

### Task 4: Verify, Commit, Push

**Files:**
- All modified files.

- [x] Run `python3 -m unittest tests.test_live_research_routing tests.test_deliverable_generation tests.test_go_to_market_model tests.test_readme_examples -v`.
- [x] Run `python3 scripts/qualification_audit_schema.py quality-gate`.
- [x] Run `python3 scripts/qualification_audit_schema.py validate examples/real-runs/mantova-olive-oil-china-import/outputs/report.json`.
- [x] Run `git diff --check`.
- [ ] Commit with `git commit -m "feat: expand detailed launch report"`.
- [ ] Push to `origin main`.
