#!/usr/bin/env python3
"""Check every crossing change on the 17 normalized minimal diagrams of 11a14.

The script computes the full Jones vector for all 17*11=187 crossing
changes, groups them into invariant classes, and computes one Alexander
vector and one SnapPy volume for each class.  It then compares the classes
with:

* the determinant-filtered exact-u=1 Jones index in ``data/``; and
* a compact six-row identification table for the collisions discussed in
  the paper.

A class is never identified by Jones alone.  Hyperbolic volume is used only
to separate database collisions; it is not used as a lower-bound invariant.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import snappy  # noqa: F401  # registers SnapPy support with Spherogram

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.knot_invariants import (  # noqa: E402
    alexander_vector,
    flip_indices,
    full_jones_vector,
    jones_equal_unoriented,
)
from spherogram import Link  # noqa: E402


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def json_vector(text: str) -> list[int]:
    return [int(x) for x in json.loads(text)]


def volume_close(left: float, right: float, tolerance: float = 1e-6) -> bool:
    return math.isfinite(left) and math.isfinite(right) and abs(left - right) <= tolerance


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--representatives",
        default=str(here / "output" / "all_normalized_minimal_pds_11a14.json"),
    )
    parser.add_argument(
        "--u1-index",
        default=str(ROOT / "data" / "knotinfo_exact_u1_jones_index.csv"),
    )
    parser.add_argument(
        "--identification-table",
        default=str(ROOT / "data" / "identification_rows_11a14.csv"),
    )
    parser.add_argument("--output-dir", default=str(here / "output"))
    args = parser.parse_args()

    representatives = json.loads(Path(args.representatives).read_text())
    if len(representatives) != 17:
        raise RuntimeError(f"expected 17 minimal representatives, found {len(representatives)}")
    u1_index = load_csv(Path(args.u1_index))
    identification_rows = load_csv(Path(args.identification_table))
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    raw_records = []
    class_members: dict[tuple[int, ...], list[dict]] = defaultdict(list)
    for representative_index, representative in enumerate(representatives):
        pd = representative["pd"]
        if len(pd) != 11:
            raise RuntimeError(f"representative {representative_index} has {len(pd)} crossings")
        for crossing_index in range(11):
            switched = flip_indices(pd, [crossing_index])
            vector = full_jones_vector(switched)
            record = {
                "representative_index": representative_index,
                "crossing_index_0based": crossing_index,
                "crossing_index_1based": crossing_index + 1,
                "jones_vector": vector,
                "source_pd": pd,
                "switched_pd": switched,
            }
            raw_records.append(record)
            class_members[tuple(vector)].append(record)

    # Stable class order: larger multiplicity first, then lexicographic vector.
    ordered_vectors = sorted(class_members, key=lambda v: (-len(class_members[v]), v))
    vector_to_id = {vector: f"J{index + 1}" for index, vector in enumerate(ordered_vectors)}

    class_rows = []
    u1_checks = []
    for vector in ordered_vectors:
        class_id = vector_to_id[vector]
        members = class_members[vector]
        representative_pd = members[0]["switched_pd"]
        alexander = alexander_vector(representative_pd)
        manifold = Link(representative_pd).exterior()
        volume = float(manifold.volume())
        solution_type = str(manifold.solution_type())
        identify_names = [str(x) for x in manifold.identify()]

        exact_u1_jones_matches = [
            row for row in u1_index
            if jones_equal_unoriented(vector, json_vector(row["jones_vector"]))
        ]
        compact_jones_matches = [
            row for row in identification_rows
            if jones_equal_unoriented(vector, json_vector(row["jones_vector"]))
        ]
        exact_matches = []
        for row in compact_jones_matches:
            same_alexander = alexander == json_vector(row["alexander_vector"])
            same_volume = volume_close(volume, float(row["volume"]))
            if same_alexander and same_volume:
                exact_matches.append(row["knot"])

        for row in exact_u1_jones_matches:
            candidate = next(
                (item for item in identification_rows if item["knot"] == row["knot"]),
                None,
            )
            candidate_alexander = (
                json_vector(candidate["alexander_vector"]) if candidate is not None else None
            )
            candidate_volume = float(row["volume"]) if row.get("volume") else float("nan")
            same_alexander = candidate_alexander == alexander if candidate_alexander else "not_checked"
            same_volume = volume_close(volume, candidate_volume)
            candidate_crossings = int(row["crossing_number"])
            crossing_number_possible = candidate_crossings <= 11
            excluded = (same_alexander is False) or (not same_volume) or (not crossing_number_possible)
            u1_checks.append(
                {
                    "class_id": class_id,
                    "class_count": len(members),
                    "candidate_knot": row["knot"],
                    "candidate_crossing_number": candidate_crossings,
                    "class_jones_vector": json.dumps(list(vector), separators=(",", ":")),
                    "class_alexander_vector": json.dumps(alexander, separators=(",", ":")),
                    "candidate_alexander_vector": (
                        json.dumps(candidate_alexander, separators=(",", ":"))
                        if candidate_alexander else ""
                    ),
                    "alexander_agrees": same_alexander,
                    "computed_volume": f"{volume:.12f}",
                    "candidate_volume": row.get("volume", ""),
                    "volume_agrees_1e-6": same_volume,
                    "candidate_crossing_number_possible": crossing_number_possible,
                    "excluded_as_u1_outcome": excluded,
                }
            )

        class_rows.append(
            {
                "class_id": class_id,
                "count": len(members),
                "jones_vector": json.dumps(list(vector), separators=(",", ":")),
                "alexander_vector": json.dumps(alexander, separators=(",", ":")),
                "computed_volume": f"{volume:.12f}",
                "solution_type": solution_type,
                "snappy_identifications": json.dumps(identify_names, separators=(",", ":")),
                "compact_jones_matches": json.dumps(
                    [row["knot"] for row in compact_jones_matches], separators=(",", ":")
                ),
                "exact_invariant_matches": json.dumps(exact_matches, separators=(",", ":")),
                "exact_u1_jones_matches": json.dumps(
                    [row["knot"] for row in exact_u1_jones_matches], separators=(",", ":")
                ),
                "sample_representative_index": members[0]["representative_index"],
                "sample_crossing_index_1based": members[0]["crossing_index_1based"],
                "sample_switched_pd": json.dumps(representative_pd, separators=(",", ":")),
            }
        )

    record_path = output / "one_crossing_records.csv"
    with record_path.open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "representative_index", "crossing_index_0based", "crossing_index_1based",
            "class_id", "jones_vector", "source_pd", "switched_pd",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in raw_records:
            vector = tuple(record["jones_vector"])
            writer.writerow(
                {
                    **{key: record[key] for key in fields[:3]},
                    "class_id": vector_to_id[vector],
                    "jones_vector": json.dumps(record["jones_vector"], separators=(",", ":")),
                    "source_pd": json.dumps(record["source_pd"], separators=(",", ":")),
                    "switched_pd": json.dumps(record["switched_pd"], separators=(",", ":")),
                }
            )

    class_path = output / "invariant_classes.csv"
    with class_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(class_rows[0]))
        writer.writeheader()
        writer.writerows(class_rows)

    checks_path = output / "u1_candidate_checks.csv"
    with checks_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(u1_checks[0]))
        writer.writeheader()
        writer.writerows(u1_checks)

    all_u1_excluded = bool(u1_checks) and all(
        row["excluded_as_u1_outcome"] for row in u1_checks
    )
    summary = {
        "target": "11a14",
        "minimal_pd_representatives": len(representatives),
        "crossing_changes_per_representative": 11,
        "total_crossing_changes": len(raw_records),
        "distinct_full_jones_vectors": len(class_rows),
        "class_multiplicities": Counter(
            vector_to_id[tuple(record["jones_vector"])] for record in raw_records
        ),
        "exact_u1_index_rows": len(u1_index),
        "exact_u1_jones_collision_rows": len(u1_checks),
        "all_exact_u1_candidates_excluded": all_u1_excluded,
        "conclusion": (
            "No crossing change on any enumerated minimal diagram produces an exact-u=1 "
            "candidate compatible with the recorded invariants."
            if all_u1_excluded else
            "At least one exact-u=1 candidate was not excluded."
        ),
        "files": {
            "one_crossing_records": record_path.name,
            "invariant_classes": class_path.name,
            "u1_candidate_checks": checks_path.name,
        },
    }
    # Counter is not directly JSON serializable.
    summary["class_multiplicities"] = dict(summary["class_multiplicities"])
    (output / "one_crossing_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
