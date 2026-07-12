#!/usr/bin/env python3
"""Build the exact-u=1 Jones index used by the 11a14 verification.

The script reads the CSV snapshot distributed by ``database-knotinfo`` and
computes the full normalized Jones vector from every available PD code whose
recorded unknotting number is exactly one.  This replaces a large historical
Excel workbook by a deterministic, auditable index.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.metadata
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.knot_invariants import full_jones_vector  # noqa: E402


def locate_snapshot(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(path)
        return path
    import database_knotinfo

    root = Path(database_knotinfo.__file__).resolve().parent
    candidates = list(root.rglob("knotinfo_data_complete.csv"))
    if len(candidates) != 1:
        raise RuntimeError(f"expected one KnotInfo CSV, found {candidates}")
    return candidates[0]


def worker(item: tuple[str, str, str, str, str, str]) -> dict[str, str]:
    name, crossings, determinant, signature, volume, pd_literal = item
    pd = ast.literal_eval(pd_literal)
    vector = full_jones_vector(pd)
    return {
        "knot": name,
        "crossing_number": crossings,
        "determinant": determinant,
        "signature": signature,
        "volume": volume,
        "jones_vector": json.dumps(vector, separators=(",", ":")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", help="path to knotinfo_data_complete.csv")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent / "knotinfo_exact_u1_jones_index.csv"),
    )
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument(
        "--determinants",
        default="25,27,35,39",
        help="comma-separated determinant filter; empty means all exact-u=1 rows",
    )
    args = parser.parse_args()

    snapshot = locate_snapshot(args.snapshot)
    determinant_filter = {x.strip() for x in args.determinants.split(",") if x.strip()}
    selected = []
    total_exact_u1 = 0
    with snapshot.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="|"):
            if row.get("unknotting_number") != "1" or not row.get("pd_notation"):
                continue
            total_exact_u1 += 1
            if determinant_filter and row.get("determinant") not in determinant_filter:
                continue
            selected.append(
                (
                    row["name"],
                    row.get("crossing_number", ""),
                    row.get("determinant", ""),
                    row.get("signature", ""),
                    row.get("volume", ""),
                    row["pd_notation"],
                )
            )

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(worker, selected, chunksize=8))
    records.sort(key=lambda row: (int(row["crossing_number"]), row["knot"]))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["knot", "crossing_number", "determinant", "signature", "volume", "jones_vector"]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    summary = {
        "database_knotinfo_version": importlib.metadata.version("database-knotinfo"),
        "snapshot_path_at_generation": str(snapshot),
        "snapshot_sha256": digest,
        "total_exact_u1_rows_with_pd": total_exact_u1,
        "determinant_filter": sorted(determinant_filter, key=int) if determinant_filter else [],
        "indexed_exact_u1_rows": len(records),
        "output": output.name,
    }
    output.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
