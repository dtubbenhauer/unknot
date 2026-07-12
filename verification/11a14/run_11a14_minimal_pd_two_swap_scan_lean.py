#!/usr/bin/env python3
"""Legacy direct two-swap scan on all 17 minimal PD representatives.

This reproduces the earlier exploratory calculation retained from the previous
chat workflow.  It is stronger as a direct search than the single-flop table
check, but the paper's all-minimal-diagram theorem is certified by
``check_one_crossing_changes.py``.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from enumerate_minimal_diagrams import flip_indices, jones_profile_from_pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"


def is_unknot_profile(profile):
    values = tuple(int(x) for x in profile)
    return values in {(1,), (-1,)}


def main() -> None:
    reps = json.loads((OUT / "all_normalized_minimal_pds_11a14.json").read_text())
    rows = []
    global_profiles = Counter()
    hits = []
    for representative_index, representative in enumerate(reps):
        pd = representative["pd"]
        for i, j in combinations(range(len(pd)), 2):
            switched = flip_indices(pd, [i, j])
            profile = tuple(jones_profile_from_pd(switched))
            global_profiles[profile] += 1
            hit = is_unknot_profile(profile)
            row = {
                "representative_index": representative_index,
                "crossing_i_0based": i,
                "crossing_j_0based": j,
                "crossing_i_1based": i + 1,
                "crossing_j_1based": j + 1,
                "jones_profile": json.dumps(profile, separators=(",", ":")),
                "unknot_jones_profile": hit,
            }
            rows.append(row)
            if hit:
                hits.append({**row, "source_pd": pd, "switched_pd": switched})
    path = OUT / "two_swap_records.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "target": "11a14",
        "minimal_pd_representatives": len(reps),
        "two_swap_tests_per_representative": 55,
        "total_two_swap_tests": len(rows),
        "unknot_jones_hits": len(hits),
        "distinct_jones_profiles": len(global_profiles),
        "top_profiles": [
            {"profile": list(profile), "count": count}
            for profile, count in global_profiles.most_common(20)
        ],
    }
    (OUT / "two_swap_hits.json").write_text(json.dumps(hits, indent=2) + "\n")
    (OUT / "two_swap_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
