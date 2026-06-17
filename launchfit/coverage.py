"""Coverage reporting helpers for LaunchFit AI."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from launchfit.benchmarking import summarize_benchmark_worksheet, validate_benchmark_worksheet


def coverage_report(root: Path) -> dict[str, Any]:
    rulepack_index_path = root / "data" / "rulepacks" / "index.json"
    index = json.loads(rulepack_index_path.read_text(encoding="utf-8"))
    packs = index.get("packs", []) if isinstance(index.get("packs"), list) else []
    by_maturity = Counter(str(pack.get("maturity", "unknown")) for pack in packs if isinstance(pack, dict))
    checked_source_links = 0
    source_tiers: Counter[str] = Counter()
    for pack in packs:
        if not isinstance(pack, dict) or not pack.get("path"):
            continue
        pack_path = root / str(pack["path"])
        if not pack_path.exists():
            continue
        data = json.loads(pack_path.read_text(encoding="utf-8"))
        sources = {str(source.get("source_id")): source for source in data.get("sources", []) if isinstance(source, dict)}
        for req in data.get("requirements", []):
            if not isinstance(req, dict):
                continue
            for source_id in req.get("source_ids") or []:
                source = sources.get(str(source_id))
                if source:
                    checked_source_links += 1
                    source_tiers[str(source.get("tier", "unknown"))] += 1
    worksheet_paths = sorted((root / "examples").glob("*benchmark*.json"))
    source_types: set[str] = set()
    valid_worksheets = 0
    for path in worksheet_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and not validate_benchmark_worksheet(data):
            valid_worksheets += 1
            source_types.update(summarize_benchmark_worksheet(data).get("source_types_covered", []))
    case_paths = sorted((root / "cases").glob("*.json"))
    return {
        "rulepacks": {
            "total": len(packs),
            "by_maturity": dict(sorted(by_maturity.items())),
        },
        "sources": {
            "checked_source_links": checked_source_links,
            "by_tier": dict(sorted(source_tiers.items())),
        },
        "golden_cases": {
            "total": len(case_paths),
            "case_ids": [path.stem for path in case_paths],
        },
        "benchmarking": {
            "worksheet_fixtures": valid_worksheets,
            "source_types_covered": sorted(source_types),
        },
        "high_frequency_routes": [
            {
                "combo_id": combo.get("combo_id"),
                "name": combo.get("name"),
                "maturity": combo.get("maturity", "seed"),
            }
            for combo in index.get("priority_combinations", [])
            if isinstance(combo, dict)
        ],
    }
