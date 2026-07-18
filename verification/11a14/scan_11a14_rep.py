#!/usr/bin/env python3
"""Run the direct two-swap Jones scan for one normalized representative."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from enumerate_minimal_diagrams import flip_indices, jones_profile_from_pd

HERE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("representative_index", type=int)
    args = parser.parse_args()
    output = HERE / "output"
    reps = json.loads((output / "all_normalized_minimal_pds_11a14.json").read_text())
    pd = reps[args.representative_index]["pd"]
    counts = Counter()
    hits = []
    for i, j in combinations(range(len(pd)), 2):
        profile = tuple(jones_profile_from_pd(flip_indices(pd, [i, j])))
        counts[profile] += 1
        if profile in {(1,), (-1,)}:
            hits.append([i, j])
    result = {
        "representative_index": args.representative_index,
        "two_swap_tests": len(pd) * (len(pd) - 1) // 2,
        "unknot_jones_hits": len(hits),
        "hit_pairs_0based": hits,
        "distinct_profiles": len(counts),
        "profile_counts": [
            {"profile": list(profile), "count": count}
            for profile, count in counts.most_common()
        ],
    }
    path = output / f"rep_scan_{args.representative_index:03d}.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
