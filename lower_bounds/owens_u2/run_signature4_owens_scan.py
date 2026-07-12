#!/usr/bin/env python3
"""Exact signature-four Owens zero-class scan.

Input: the complete pipe-delimited KnotInfo CSV.
Filter: alternating knots with interval [2,b], b>2, and |signature|=4.

For each target the program reconstructs the positive-definite Goeritz form,
checks its determinant, computes m_G(0), enumerates every rank-four Owens
matrix in the normal form

    [[m1,1,a,0], [1,2,0,0], [a,0,m2,1], [0,0,1,2]],

with 0 <= a < m1 <= m2 and m1,m2 even, and applies the zero-class test.
The determinant equation is

    (2m1-1)(2m2-1)-4a^2 = det(K).

Only certified obstructions are written to the output CSV.  All arithmetic is
exact and uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
HELPER = HERE.parent / "owens_signature_sharp" / "run_signature_sharp_zero_class_scan.py"
spec = importlib.util.spec_from_file_location("owens_zero", HELPER)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load helper module {HELPER}")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def owens_matrix(m1: int, m2: int, a: int):
    return [
        [m1, 1, a, 0],
        [1, 2, 0, 0],
        [a, 0, m2, 1],
        [0, 0, 1, 2],
    ]


def enumerate_candidates(determinant: int):
    candidates = []
    # Since a < m1 <= m2, the determinant is at least 4*m1-3.
    for m1 in range(2, (determinant + 3) // 4 + 1, 2):
        x = 2 * m1 - 1
        for a in range(m1):
            numerator = determinant + 4 * a * a
            if numerator % x:
                continue
            y = numerator // x
            if y <= 0 or y % 2 == 0:
                continue
            m2 = (y + 1) // 2
            if m2 < m1 or m2 % 2:
                continue
            q = owens_matrix(m1, m2, a)
            if mod.determinant_bareiss(q) != determinant:
                raise AssertionError("candidate determinant mismatch")
            if not mod.is_positive_definite(q):
                continue
            candidates.append(
                {
                    "m1": m1,
                    "m2": m2,
                    "a": a,
                    "two_m1_minus_1": x,
                    "two_m2_minus_1": y,
                    "matrix": q,
                    "m_Q_zero": "-1",
                }
            )
    return candidates


def run(rows, target_names=None):
    successes = []
    eligible = 0
    for row in rows:
        if target_names is not None and row.get("name") not in target_names:
            continue
        interval = mod.parse_interval(row.get("unknotting_number", ""))
        if row.get("alternating") != "Y" or interval is None:
            continue
        lower, upper = interval
        if lower != 2 or upper <= 2:
            continue
        eligible += 1
        signature = int(row["signature"])
        if abs(signature) != 4:
            continue
        pd = mod.parse_pd(row["pd_notation"])
        matrix, mirrored = mod.choose_positive_goeritz(pd, signature)
        determinant = int(row["determinant"])
        if mod.determinant_bareiss(matrix) != determinant:
            raise ValueError(f"determinant mismatch for {row['name']}")
        m_g, parity, energy = mod.zero_class_value(matrix)
        candidates = enumerate_candidates(determinant)
        m_q = Fraction(-1, 1)
        inequality_ok = bool(candidates) and all(m_q >= m_g for _ in candidates)
        difference = m_q - m_g
        congruence_ok = bool(candidates) and difference.denominator == 1 and int(difference) % 2 == 0
        obstructs = not candidates or not (inequality_ok and congruence_ok)
        if not obstructs:
            continue
        successes.append(
            {
                "knot": row["name"],
                "crossing_number": int(row["crossing_number"]),
                "input_interval": f"[{lower},{upper}]",
                "signature_input": signature,
                "mirrored_to_positive_signature": mirrored,
                "determinant": determinant,
                "goeritz_rank": len(matrix),
                "m_G_zero": str(m_g),
                "m_Q_zero": str(m_q) if candidates else "no_candidate_matrix",
                "candidate_count": len(candidates),
                "candidate_parameters": json.dumps(candidates, separators=(",", ":")),
                "inequality_ok_for_all_candidates": inequality_ok,
                "congruence_ok_for_all_candidates": congruence_ok,
                "obstructs_u_2": True,
                "new_interval": "3" if upper == 3 else f"[3,{upper}]",
                "zero_energy": energy,
                "zero_characteristic_parity": json.dumps(parity, separators=(",", ":")),
                "goeritz_matrix": json.dumps(matrix, separators=(",", ":")),
                "pd_notation": json.dumps(pd, separators=(",", ":")),
            }
        )
    successes.sort(key=lambda item: mod.knot_sort_key(item["knot"]))
    return eligible, successes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path, nargs="?", help="complete KnotInfo CSV; defaults to database-knotinfo")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--targets", type=Path, help="optional CSV containing a knot column; restrict verification to these knots")
    args = parser.parse_args()

    input_csv = args.input_csv or mod.locate_knotinfo_csv()
    rows = mod.read_knotinfo(input_csv)
    target_names = None
    if args.targets:
        with args.targets.open(newline="", encoding="utf-8-sig") as handle:
            target_rows = list(csv.DictReader(handle))
        target_names = set()
        for item in target_rows:
            raw = item.get("knot") or item.get("name")
            if raw:
                # KnotInfo uses underscores, while prose/data sometimes omits them.
                name = str(raw).strip()
                if "_" not in name:
                    import re
                    name = re.sub(r"^(\d+)([an])(\d+)$", r"\1\2_\3", name)
                    name = re.sub(r"^(\d+)_(\d+)$", r"\1_\2", name)
                target_names.add(name)
    eligible, results = run(rows, target_names)
    fields = list(results[0]) if results else []
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    summary = {
        "data_rows": sum(1 for row in rows if row.get("name") != "Name"),
        "eligible_rows_checked": eligible,
        "target_count": None if target_names is None else len(target_names),
        "signature_four_successes": len(results),
        "exact_u_3": sum(item["input_interval"] == "[2,3]" for item in results),
        "improved_to_3_4": sum(item["input_interval"] == "[2,4]" for item in results),
        "no_candidate_matrix": [item["knot"] for item in results if item["candidate_count"] == 0],
        "m_G_zero_values": sorted({item["m_G_zero"] for item in results}),
        "output_csv": str(args.output),
    }
    if args.summary:
        args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
