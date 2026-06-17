# LaunchFit Skill Complete Lite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LaunchFit AI a benchmark-first, complete-lite Skill with deterministic CLI workflows, stronger benchmark handling, bundle validation, batch reports, coverage reporting, and clear enhancement adapter boundaries.

**Architecture:** Keep the project dependency-free and Skill-first. Add lightweight modules only where they reduce growth in the existing single script, while preserving `scripts/qualification_audit_schema.py` as the stable command entrypoint. Implement benchmark-first functionality before any broad refactor.

**Tech Stack:** Python 3 standard library, JSON fixtures, existing rulepacks, command-level golden tests.

---

## File Structure

- Modify `scripts/qualification_audit_schema.py`: add command routing for new commands and reuse existing report generation.
- Create `launchfit/__init__.py`: package marker.
- Create `launchfit/benchmarking.py`: benchmark template, validation, normalization, and summary helpers.
- Create `launchfit/bundles.py`: case bundle template and validation helpers.
- Create `launchfit/coverage.py`: rulepack/golden/source/benchmark coverage report helpers.
- Create `launchfit/adapters.py`: offline adapter result contracts for OCR, source/web, registry, and logistics enhancement inputs.
- Add `examples/benchmark-worksheet.json`: broad benchmark worksheet with multiple benchmark source types.
- Add `examples/batch/`: small directory of runnable case bundles for batch report generation.
- Add `cases/golden-benchmark-summary.json`: benchmark-specific golden expectation.
- Update `examples/README.md`, `README.md`, `README.en.md`, `SKILL.md`, `references/launch-readiness-playbook.md`, and `references/implementation-blueprint.md`.

## Task 1: Benchmark Worksheet Commands

**Files:**
- Create: `launchfit/__init__.py`
- Create: `launchfit/benchmarking.py`
- Create: `examples/benchmark-worksheet.json`
- Modify: `scripts/qualification_audit_schema.py`
- Create: `cases/golden-benchmark-summary.json`

- [ ] **Step 1: Write failing command checks**

Run:

```bash
python3 scripts/qualification_audit_schema.py benchmark-validate examples/benchmark-worksheet.json
python3 scripts/qualification_audit_schema.py benchmark-summarize examples/benchmark-worksheet.json
```

Expected: argparse reports `invalid choice` for both commands.

- [ ] **Step 2: Add benchmark worksheet fixture**

Create `examples/benchmark-worksheet.json` with `worksheet_type`, `scope`, `benchmarks`, and rows for direct competitor, substitute, adjacent reference, category leader, local niche brand, platform best seller, offline retail shelf, and DTC/social commerce.

- [ ] **Step 3: Implement benchmark helpers**

Add functions in `launchfit/benchmarking.py`:

```python
def benchmark_template(market: str, category: str, product: str = "", platform: str = "", count: int = 8) -> dict:
    ...

def validate_benchmark_worksheet(data: dict) -> list[str]:
    ...

def summarize_benchmark_worksheet(data: dict) -> dict:
    ...
```

Validation must fail for missing product name, channel, invalid source type, invalid data basis, invalid channel role, invalid positioning, or missing checked date when `data_basis` is `current_checked`.

- [ ] **Step 4: Wire CLI commands**

Update `scripts/qualification_audit_schema.py` so:

```bash
python3 scripts/qualification_audit_schema.py benchmark-validate examples/benchmark-worksheet.json
python3 scripts/qualification_audit_schema.py benchmark-summarize examples/benchmark-worksheet.json
```

return validation OK and a JSON summary.

- [ ] **Step 5: Add benchmark golden case**

Create `cases/golden-benchmark-summary.json` that expects the benchmark summary to include direct competitors, substitutes, adjacent references, offline retail, and DTC/social commerce source types.

## Task 2: Bundle Template And Validation

**Files:**
- Create: `launchfit/bundles.py`
- Modify: `scripts/qualification_audit_schema.py`
- Modify: `examples/offline-launch-case.json`

- [ ] **Step 1: Write failing command checks**

Run:

```bash
python3 scripts/qualification_audit_schema.py bundle-template --platform amazon --market US --category food --product "chili sauce"
python3 scripts/qualification_audit_schema.py bundle-validate examples/offline-launch-case.json
```

Expected: argparse reports `invalid choice`.

- [ ] **Step 2: Implement bundle helpers**

Add functions in `launchfit/bundles.py`:

```python
def bundle_template(platform: str, market: str, category: str, product: str = "") -> dict:
    ...

def validate_case_bundle(data: dict) -> tuple[list[str], list[str]]:
    ...

def bundle_benchmarks(data: dict) -> list[dict]:
    ...
```

`bundle_benchmarks` must support `benchmarks` and the backward-compatible `competitors` alias.

- [ ] **Step 3: Wire CLI commands**

Update `scripts/qualification_audit_schema.py` with:

```bash
bundle-template --platform PLATFORM --market MARKET --category CATEGORY --product PRODUCT
bundle-validate <bundle-json-file>
```

`bundle-validate` prints warnings for empty optional sections and exits non-zero only for hard schema errors.

## Task 3: Batch Reports And Coverage Report

**Files:**
- Create: `launchfit/coverage.py`
- Create: `examples/batch/food-us.json`
- Create: `examples/batch/electronics-eu.json`
- Modify: `scripts/qualification_audit_schema.py`

- [ ] **Step 1: Write failing command checks**

Run:

```bash
python3 scripts/qualification_audit_schema.py batch-launch-report examples/batch /tmp/launchfit-batch
python3 scripts/qualification_audit_schema.py coverage-report
```

Expected: argparse reports `invalid choice`.

- [ ] **Step 2: Add batch fixtures**

Create two small case bundles under `examples/batch/`, one food/US and one electronics/EU. Keep them compact but valid under `bundle-validate`.

- [ ] **Step 3: Implement batch command**

`batch-launch-report <input-dir> <output-dir>` must generate one `.json` report and one `.md` report per bundle file.

- [ ] **Step 4: Implement coverage report**

`coverage-report` must output JSON with:

```json
{
  "rulepacks": {"total": 0, "by_maturity": {}},
  "sources": {"checked_source_links": 0, "stale": 0, "missing": 0},
  "golden_cases": {"total": 0},
  "benchmarking": {"worksheet_fixtures": 0, "source_types_covered": []},
  "high_frequency_routes": []
}
```

Use existing rulepack index, source freshness, and cases directory.

## Task 4: Quality Gate And Golden Expansion

**Files:**
- Modify: `scripts/qualification_audit_schema.py`
- Modify: `examples/offline-launch-report.json`

- [ ] **Step 1: Extend quality-gate**

Add bundle fixture validation, benchmark worksheet validation, and coverage report generation to `quality-gate`.

- [ ] **Step 2: Verify gate failure on bad benchmark fixture**

Temporarily copy `examples/benchmark-worksheet.json` to `/tmp/bad-benchmark.json`, delete one benchmark product name, and run:

```bash
python3 scripts/qualification_audit_schema.py benchmark-validate /tmp/bad-benchmark.json
```

Expected: non-zero exit and an error mentioning missing product name.

- [ ] **Step 3: Verify full gate**

Run:

```bash
python3 scripts/qualification_audit_schema.py quality-gate
```

Expected: rulepack index valid, source freshness clean, golden replay passes, benchmark worksheet valid, bundle fixtures valid, coverage report generated.

## Task 5: Documentation And Skill Routing

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `SKILL.md`
- Modify: `examples/README.md`
- Modify: `references/launch-readiness-playbook.md`
- Modify: `references/implementation-blueprint.md`

- [ ] **Step 1: Update README files**

Position the project as a benchmark-first lightweight Skill. Make clear that OCR/search/registry/logistics APIs are enhancement inputs, not hard dependencies.

- [ ] **Step 2: Update SKILL command routing**

Add a table mapping user intent to commands:

```text
Need benchmark worksheet -> benchmark-template
Validate benchmark rows -> benchmark-validate
Summarize benchmark rows -> benchmark-summarize
Create launch bundle -> bundle-template
Validate bundle -> bundle-validate
Generate report -> launch-report
Batch reports -> batch-launch-report
Check health -> quality-gate
```

- [ ] **Step 3: Update examples README**

Add end-to-end benchmark-first commands:

```bash
python3 scripts/qualification_audit_schema.py benchmark-validate examples/benchmark-worksheet.json
python3 scripts/qualification_audit_schema.py benchmark-summarize examples/benchmark-worksheet.json
python3 scripts/qualification_audit_schema.py bundle-validate examples/offline-launch-case.json
python3 scripts/qualification_audit_schema.py batch-launch-report examples/batch /tmp/launchfit-batch
python3 scripts/qualification_audit_schema.py coverage-report
```

## Task 6: Final Verification And Commit

**Files:**
- Verify all touched files.

- [ ] **Step 1: Run full verification**

Run:

```bash
python3 scripts/qualification_audit_schema.py benchmark-validate examples/benchmark-worksheet.json
python3 scripts/qualification_audit_schema.py benchmark-summarize examples/benchmark-worksheet.json > /tmp/launchfit-benchmark-summary.json
python3 scripts/qualification_audit_schema.py bundle-validate examples/offline-launch-case.json
python3 scripts/qualification_audit_schema.py batch-launch-report examples/batch /tmp/launchfit-batch
python3 scripts/qualification_audit_schema.py coverage-report > /tmp/launchfit-coverage.json
python3 scripts/qualification_audit_schema.py launch-report examples/offline-launch-case.json > /tmp/launchfit-offline-report.json
python3 scripts/qualification_audit_schema.py validate /tmp/launchfit-offline-report.json
python3 scripts/qualification_audit_schema.py launch-report-markdown /tmp/launchfit-offline-report.json > /tmp/launchfit-offline-report.md
python3 scripts/qualification_audit_schema.py golden-replay
python3 scripts/qualification_audit_schema.py quality-gate
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 2: Commit**

Run:

```bash
git add launchfit scripts examples cases README.md README.en.md SKILL.md references docs
git commit -m "feat: complete lightweight benchmark-first skill"
```

## Self-Review

Spec coverage: benchmark-first workflow is covered by Task 1 and docs. Lightweight Skill boundary is covered by adapter contracts and docs. Bundle, batch, coverage, and quality-gate requirements are covered by Tasks 2-4.

Placeholder scan: this plan uses no `TBD`, `TODO`, or unresolved placeholders.

Type consistency: commands use the same names across tasks: `benchmark-validate`, `benchmark-summarize`, `bundle-template`, `bundle-validate`, `batch-launch-report`, and `coverage-report`.
