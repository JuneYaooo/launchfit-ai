# LaunchFit Offline MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dependency-free offline case-bundle to launch-readiness report workflow that makes the skill runnable for the README's core promise.

**Architecture:** Extend the existing single helper script rather than introducing a new framework. The script will parse a structured bundle, reuse existing rulepack matching and JSON validation, add deterministic offline checks, and export Markdown from the same report payload.

**Tech Stack:** Python 3 standard library, existing JSON rule packs, existing command-level quality gate.

---

## File Structure

- Modify `scripts/qualification_audit_schema.py`: add `launch-report` and `launch-report-markdown` commands plus pure helper functions for bundle loading, document normalization, benchmark summary, packaging checks, logistics checks, findings, decision selection, and Markdown rendering.
- Add `examples/offline-launch-case.json`: user-editable input bundle.
- Add `examples/offline-launch-report.json`: produced report fixture used by golden replay.
- Add `cases/golden-offline-launch-readiness.json`: expected outcome for the fixture.
- Update `examples/README.md`: document the runnable offline workflow.
- Update `SKILL.md`: advertise the new helper commands and clarify offline evidence labeling.
- Update `README.md` and `README.en.md`: align product claims with the newly runnable MVP boundary.

## Task 1: Add Failing Offline Launch Fixture

**Files:**
- Create: `examples/offline-launch-case.json`
- Create: `cases/golden-offline-launch-readiness.json`
- Create: `examples/offline-launch-report.json`

- [ ] **Step 1: Add an input bundle fixture**

Create `examples/offline-launch-case.json` with an Amazon US chili sauce case that includes applicant data, expired HACCP evidence, brand authorization missing the US territory, packaging claims, three competitor rows, and two logistics rows.

- [ ] **Step 2: Add a golden expectation**

Create `cases/golden-offline-launch-readiness.json` with:

```json
{
  "case_id": "offline-launch-readiness",
  "review_fixture": "examples/offline-launch-report.json",
  "description": "Offline launch-readiness report from a user-provided case bundle should request more information and surface high-risk document/launch blockers.",
  "expected": {
    "status_any_of": ["request_more_info"],
    "min_findings": [
      {"severity": "high"},
      {"severity": "medium"}
    ],
    "require_requirement_status": ["missing", "needs_external_verification"]
  }
}
```

- [ ] **Step 3: Add a placeholder produced fixture**

Create `examples/offline-launch-report.json` with `{}` so the first replay fails for the expected reason.

- [ ] **Step 4: Run failing checks**

Run:

```bash
python3 scripts/qualification_audit_schema.py case-check cases/golden-offline-launch-readiness.json examples/offline-launch-report.json
```

Expected: `FAIL: review_type must be cross_border_ecommerce_qualification`.

## Task 2: Implement Launch Report JSON Generation

**Files:**
- Modify: `scripts/qualification_audit_schema.py`
- Modify: `examples/offline-launch-report.json`

- [ ] **Step 1: Add the failing command assertion**

Run:

```bash
python3 scripts/qualification_audit_schema.py launch-report examples/offline-launch-case.json > /tmp/launchfit-offline-report.json
```

Expected: argparse fails with invalid choice because the command does not exist.

- [ ] **Step 2: Implement pure report helpers**

Add helpers:

```python
def launch_report_from_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    ...

def normalize_bundle_document(raw: dict[str, Any], idx: int) -> dict[str, Any]:
    ...

def build_market_benchmarks(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    ...

def build_packaging_findings(bundle: dict[str, Any], sources: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ...

def build_logistics_findings(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ...

def choose_launch_decision(findings: list[dict[str, Any]], requirements: list[dict[str, Any]], market_benchmarks: list[dict[str, Any]], logistics_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ...
```

Use existing `review_skeleton`, `matching_rulepacks`, `empty_benchmark_summary`, `build_supplement_message`, `parse_date`, and `today`.

- [ ] **Step 3: Add CLI command**

Add parser command:

```bash
launch-report <bundle-json-file>
```

and command function that prints the report JSON with `ensure_ascii=False, indent=2`.

- [ ] **Step 4: Generate and validate**

Run:

```bash
python3 scripts/qualification_audit_schema.py launch-report examples/offline-launch-case.json > /tmp/launchfit-offline-report.json
python3 scripts/qualification_audit_schema.py validate /tmp/launchfit-offline-report.json
```

Expected: `OK`.

- [ ] **Step 5: Refresh produced fixture**

Copy `/tmp/launchfit-offline-report.json` to `examples/offline-launch-report.json`.

- [ ] **Step 6: Run case check**

Run:

```bash
python3 scripts/qualification_audit_schema.py case-check cases/golden-offline-launch-readiness.json examples/offline-launch-report.json
```

Expected: `PASS: offline-launch-readiness`.

## Task 3: Include Example Fixture In Golden Replay

**Files:**
- Modify: `scripts/qualification_audit_schema.py`

- [ ] **Step 1: Run current golden replay to show fixture is not included**

Run:

```bash
python3 scripts/qualification_audit_schema.py golden-replay
```

Expected before implementation: it fails because `reviews/golden/offline-launch-readiness.json` is missing once the new case file exists.

- [ ] **Step 2: Extend replay fallback**

Update `replay_golden_cases` so if a case declares `review_fixture`, it uses that path relative to the project root. Otherwise it continues to use `reviews/golden/<case_id>.json`. This keeps existing review fixtures in place while allowing runnable examples to participate in the gate.

- [ ] **Step 3: Verify replay**

Run:

```bash
python3 scripts/qualification_audit_schema.py golden-replay
```

Expected: 8 golden cases replayed.

## Task 4: Add Markdown Export

**Files:**
- Modify: `scripts/qualification_audit_schema.py`

- [ ] **Step 1: Run failing command assertion**

Run:

```bash
python3 scripts/qualification_audit_schema.py launch-report-markdown examples/offline-launch-report.json > /tmp/launchfit-offline-report.md
```

Expected: argparse fails with invalid choice because the command does not exist.

- [ ] **Step 2: Implement Markdown rendering**

Add:

```python
def render_launch_markdown(report: dict[str, Any]) -> str:
    ...
```

It must include these headings:

```markdown
# Cross-Border Product Launch Review
## Snapshot
## Top Risks Before Listing
## Target-Market Benchmarks
## What The Benchmarks Mean
## Packaging / Label
## Platform Admission
## Logistics / Budget
## Missing Materials
## Assumptions And Verification Needed
```

- [ ] **Step 3: Add CLI command**

Add parser command:

```bash
launch-report-markdown <review-json-file>
```

- [ ] **Step 4: Verify Markdown output**

Run:

```bash
python3 scripts/qualification_audit_schema.py launch-report-markdown examples/offline-launch-report.json > /tmp/launchfit-offline-report.md
rg "## Snapshot|## Target-Market Benchmarks|## Logistics / Budget|## Assumptions And Verification Needed" /tmp/launchfit-offline-report.md
```

Expected: all four headings are printed.

## Task 5: Update Documentation And Skill Instructions

**Files:**
- Modify: `examples/README.md`
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Update examples documentation**

Add an "Offline Launch Readiness MVP" section with commands:

```bash
python3 scripts/qualification_audit_schema.py launch-report examples/offline-launch-case.json > /tmp/launchfit-offline-report.json
python3 scripts/qualification_audit_schema.py validate /tmp/launchfit-offline-report.json
python3 scripts/qualification_audit_schema.py launch-report-markdown /tmp/launchfit-offline-report.json > /tmp/launchfit-offline-report.md
python3 scripts/qualification_audit_schema.py case-check cases/golden-offline-launch-readiness.json /tmp/launchfit-offline-report.json
```

- [ ] **Step 2: Update skill helper commands**

Add `launch-report` and `launch-report-markdown` to `SKILL.md` Script Helper and state that offline bundles label user-provided facts as T4 or `user_provided`.

- [ ] **Step 3: Update READMEs**

Clarify that the repo now contains a runnable local MVP. Keep the same product direction, but make external OCR/API/live verification explicitly framed as integration layers rather than current bundled capabilities.

## Task 6: Final Verification

**Files:**
- Verify all touched files.

- [ ] **Step 1: Run command tests**

Run:

```bash
python3 scripts/qualification_audit_schema.py launch-report examples/offline-launch-case.json > /tmp/launchfit-offline-report.json
python3 scripts/qualification_audit_schema.py validate /tmp/launchfit-offline-report.json
python3 scripts/qualification_audit_schema.py launch-report-markdown /tmp/launchfit-offline-report.json > /tmp/launchfit-offline-report.md
python3 scripts/qualification_audit_schema.py case-check cases/golden-offline-launch-readiness.json /tmp/launchfit-offline-report.json
python3 scripts/qualification_audit_schema.py golden-replay
python3 scripts/qualification_audit_schema.py quality-gate
```

Expected: validation OK, case check PASS, golden replay 8 cases, quality gate OK.

- [ ] **Step 2: Inspect git diff**

Run:

```bash
git diff --stat
git diff --check
```

Expected: no whitespace errors and only planned files changed.

## Self-Review

Spec coverage: the plan creates a case bundle, generates JSON, exports Markdown, validates output, extends golden replay, and updates docs. No spec requirement is left out.

Placeholder scan: no unresolved `TBD`, `TODO`, or "implement later" instructions remain.

Type consistency: the plan consistently uses the existing review JSON contract and the new commands `launch-report` and `launch-report-markdown`.
