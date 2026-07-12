#!/usr/bin/env python3
"""Exploratory one-crossing-swap scan of hard unknot diagrams.

This is a cleaned command-line replacement for the historical Colab notebooks.
It streams source rows, finds a PD code in each row, switches every crossing by
``[a,b,c,d] -> [b,c,d,a]``, and records SnapPy identifications that occur in the
KnotInfo target set with interval ``[1,a]``, ``a>1``.

A hit is a candidate/witness for follow-up, not a lower-bound certificate.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from pathlib import Path

import database_knotinfo
import pandas as pd
import snappy  # noqa: F401
from spherogram import Link

INTERVAL = re.compile(r"^\[\s*1\s*,\s*(\d+)\s*\]$")


def normalize_name(text: str) -> str:
    value = str(text).split("(", 1)[0].strip()
    match = re.fullmatch(r"K?(\d+)([an])_?(\d+)", value)
    if match:
        return f"{match.group(1)}{match.group(2)}_{match.group(3)}"
    match = re.fullmatch(r"(\d+)_([0-9]+)", value)
    return value if not match else f"{match.group(1)}_{match.group(2)}"


def locate_database() -> Path:
    root = Path(database_knotinfo.__file__).resolve().parent
    matches = list(root.rglob("knotinfo_data_complete.csv"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one KnotInfo CSV, found {matches}")
    return matches[0]


def load_targets() -> dict[str, dict[str, str]]:
    with locate_database().open(newline="", encoding="utf-8") as handle:
        targets = {}
        for row in csv.DictReader(handle, delimiter="|"):
            match = INTERVAL.match(row.get("unknotting_number") or "")
            if match and int(match.group(1)) > 1:
                targets[normalize_name(row["name"])] = {
                    "interval": row["unknotting_number"],
                    "crossing_number": row.get("crossing_number", ""),
                }
        return targets


def parse_pd(value) -> list[list[int]] | None:
    if isinstance(value, list):
        candidate = value
    else:
        text = str(value).strip()
        if not text.startswith("["):
            return None
        try:
            candidate = ast.literal_eval(text)
        except Exception:
            return None
    if not candidate or not all(isinstance(q, (list, tuple)) and len(q) == 4 for q in candidate):
        return None
    try:
        return [[int(x) for x in q] for q in candidate]
    except Exception:
        return None


def pd_from_row(row: pd.Series) -> list[list[int]] | None:
    preferred = [name for name in row.index if "pd" in str(name).lower()]
    for name in preferred + [name for name in row.index if name not in preferred]:
        candidate = parse_pd(row[name])
        if candidate is not None:
            return candidate
    return None


def switch(pd_code: list[list[int]], index: int) -> list[list[int]]:
    result = []
    for j, crossing in enumerate(pd_code):
        a, b, c, d = crossing
        result.append([b, c, d, a] if j == index else [a, b, c, d])
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hard-csv", default="gs://gdm-unknotting/hard_unknots.csv")
    parser.add_argument("--start-row", type=int, default=0)
    parser.add_argument("--max-diagrams", type=int, default=1000)
    parser.add_argument("--chunksize", type=int, default=1000)
    parser.add_argument("--output-dir", default="hard_unknot_one_swap_scan")
    parser.add_argument("--save-flipped-pd", action="store_true")
    args = parser.parse_args()

    targets = load_targets()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    hits_path = output / "candidate_hits.csv"
    log_path = output / "diagram_log.jsonl"
    errors_path = output / "errors.csv"
    hit_fields = [
        "source_row", "source_crossings", "crossing_index_0based", "matched_knot",
        "matched_interval", "matched_crossings", "computed_volume", "solution_type",
        "identify_names", "flipped_pd",
    ]
    error_fields = ["source_row", "crossing_index_0based", "error"]
    hit_handle = hits_path.open("w", newline="", encoding="utf-8")
    error_handle = errors_path.open("w", newline="", encoding="utf-8")
    hit_writer = csv.DictWriter(hit_handle, fieldnames=hit_fields)
    error_writer = csv.DictWriter(error_handle, fieldnames=error_fields)
    hit_writer.writeheader()
    error_writer.writeheader()

    row_number = scanned = swaps = hit_count = 0
    try:
        for frame in pd.read_csv(args.hard_csv, chunksize=args.chunksize):
            for _, row in frame.iterrows():
                if row_number < args.start_row:
                    row_number += 1
                    continue
                if scanned >= args.max_diagrams:
                    break
                pd_code = pd_from_row(row)
                current_row = row_number
                row_number += 1
                if pd_code is None:
                    continue
                scanned += 1
                row_hits = 0
                for crossing_index in range(len(pd_code)):
                    swaps += 1
                    flipped = switch(pd_code, crossing_index)
                    try:
                        manifold = Link(flipped).exterior()
                        names = sorted({normalize_name(str(x)) for x in manifold.identify()})
                        target_names = [name for name in names if name in targets]
                        for name in target_names:
                            hit_count += 1
                            row_hits += 1
                            hit_writer.writerow(
                                {
                                    "source_row": current_row,
                                    "source_crossings": len(pd_code),
                                    "crossing_index_0based": crossing_index,
                                    "matched_knot": name,
                                    "matched_interval": targets[name]["interval"],
                                    "matched_crossings": targets[name]["crossing_number"],
                                    "computed_volume": float(manifold.volume()),
                                    "solution_type": str(manifold.solution_type()),
                                    "identify_names": json.dumps(names, separators=(",", ":")),
                                    "flipped_pd": json.dumps(flipped, separators=(",", ":")) if args.save_flipped_pd else "",
                                }
                            )
                    except Exception as exc:
                        error_writer.writerow(
                            {"source_row": current_row, "crossing_index_0based": crossing_index, "error": repr(exc)}
                        )
                with log_path.open("a", encoding="utf-8") as log:
                    log.write(json.dumps({"source_row": current_row, "crossings": len(pd_code), "hits": row_hits}) + "\n")
                if scanned % 10 == 0 or row_hits:
                    print(f"scanned={scanned} swaps={swaps} hits={hit_count}", flush=True)
            if scanned >= args.max_diagrams:
                break
    finally:
        hit_handle.close()
        error_handle.close()

    summary = {
        "hard_csv": args.hard_csv,
        "start_row": args.start_row,
        "source_diagrams_scanned": scanned,
        "one_crossing_swaps": swaps,
        "candidate_hits": hit_count,
        "warning": "Candidate hits require proof-grade follow-up; a failed search is not a lower bound.",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
