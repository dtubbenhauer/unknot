#!/usr/bin/env python3
"""Fast consistency checks for all theorem-critical repository outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def count_rows(relative: str) -> int:
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text())


def main() -> None:
    checks = {
        "owens_signature4": count_rows("lower_bounds/owens_u2/owens_u2_full_certificates.csv"),
        "owens_signature6": count_rows("lower_bounds/owens_signature_sharp/signature6_zero_class_results.csv"),
        "owens_signature8": count_rows("lower_bounds/owens_signature_sharp/signature8_zero_class_results.csv"),
        "montesinos_u1_targets": count_rows("lower_bounds/montesinos_u1/montesinos_d_obstruction_scan_u1_targets_up_to_13.csv"),
        "montesinos_u1_full_certificates": count_rows("lower_bounds/montesinos_u1/full_certificates/index.csv"),
        "montesinos_higher": count_rows("lower_bounds/montesinos_signature_sharp/montesinos_spin_certificates.csv"),
        "minimal_pds_11a14": len(load_json("verification/11a14/output/all_normalized_minimal_pds_11a14.json")),
        "crossing_changes_11a14": count_rows("verification/11a14/output/one_crossing_records.csv"),
        "invariant_classes_11a14": count_rows("verification/11a14/output/invariant_classes.csv"),
        "u1_collisions_11a14": count_rows("verification/11a14/output/u1_candidate_checks.csv"),
    }
    expected = {
        "owens_signature4": 245,
        "owens_signature6": 164,
        "owens_signature8": 24,
        "montesinos_u1_targets": 50,
        "montesinos_u1_full_certificates": 50,
        "montesinos_higher": 7,
        "minimal_pds_11a14": 17,
        "crossing_changes_11a14": 187,
        "invariant_classes_11a14": 4,
        "u1_collisions_11a14": 3,
    }
    if checks != expected:
        raise SystemExit(json.dumps({"status": "FAILED", "observed": checks, "expected": expected}, indent=2))
    summary = load_json("verification/11a14/output/one_crossing_summary.json")
    if not summary.get("all_exact_u1_candidates_excluded"):
        raise SystemExit("11a14 exact-u=1 collision check failed")
    print(json.dumps({"status": "OK", **checks}, indent=2))


if __name__ == "__main__":
    main()
