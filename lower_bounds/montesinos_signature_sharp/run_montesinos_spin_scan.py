#!/usr/bin/env python3
"""Exact spin correction-term certificates for seven Montesinos knots.

For each target, construct the negative-definite star plumbing used in the
paper, compute all correction terms exactly, locate the unique conjugation-
fixed Spin^c class (the spin structure, since the determinant is odd), and
record the correction term in both boundary orientations.

The row-wise choice between ``graph`` and ``minus_graph`` is the orientation
calibration used in the paper after mirroring where necessary.  It is kept
explicit because the translation from a Montesinos presentation to the
orientation of the branched cover is convention-sensitive.
"""
from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import sys
from fractions import Fraction
from pathlib import Path

import database_knotinfo

HERE = Path(__file__).resolve().parent
U1_DIR = HERE.parent / "montesinos_u1"
sys.path.insert(0, str(U1_DIR))
import unknotting_number_one_d_invariant_obstruction as obs  # noqa: E402

# The orientation column is part of the convention calibration in the paper.
TARGETS = {
    "11n_30": {"interval": "[2,3]", "k": 2, "orientation": "graph"},
    "11n_137": {"interval": "[2,3]", "k": 2, "orientation": "graph"},
    "12n_233": {"interval": "[2,3]", "k": 2, "orientation": "minus_graph"},
    "12n_235": {"interval": "[2,3]", "k": 2, "orientation": "graph"},
    "12n_294": {"interval": "[2,3]", "k": 2, "orientation": "graph"},
    "12n_169": {"interval": "[3,4]", "k": 3, "orientation": "graph"},
    "12n_477": {"interval": "[3,4]", "k": 3, "orientation": "graph"},
}


def locate_snapshot(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(path)
        return path
    root = Path(database_knotinfo.__file__).resolve().parent
    matches = list(root.rglob("knotinfo_data_complete.csv"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one KnotInfo CSV, found {matches}")
    return matches[0]


def parse_montesinos(text: str) -> list[Fraction]:
    if not text.startswith("K(") or not text.endswith(")"):
        raise ValueError(f"not a three-tangle Montesinos notation: {text!r}")
    values = [Fraction(piece) for piece in text[2:-1].split(";")]
    if len(values) != 3:
        raise ValueError(f"expected three fractions: {text!r}")
    return values


def matrix_as_json(matrix) -> str:
    return json.dumps(
        [[int(matrix[i, j]) for j in range(matrix.cols)] for i in range(matrix.rows)],
        separators=(",", ":"),
    )


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def congruent_mod_two(left: Fraction, right: Fraction) -> bool:
    difference = left - right
    return difference.denominator == 1 and int(difference) % 2 == 0


def spin_class(q, dmap, representatives):
    """Return the unique class fixed by Spin^c conjugation."""
    qinv = q.inv()
    diagonal = [int(q[i, i]) for i in range(q.rows)]
    fixed = []
    for key, x in representatives.items():
        conjugate_x = tuple(-x[i] - diagonal[i] for i in range(len(x)))
        conjugate_key = obs.key_of_x(qinv, conjugate_x)
        if conjugate_key == key:
            fixed.append((key, x, dmap[key]))
    if len(fixed) != 1:
        raise RuntimeError(f"expected a unique spin class, found {len(fixed)}")
    return fixed[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", help="path to knotinfo_data_complete.csv")
    parser.add_argument("--output", default=str(HERE / "montesinos_spin_certificates.csv"))
    args = parser.parse_args()

    snapshot = locate_snapshot(args.snapshot)
    with snapshot.open(newline="", encoding="utf-8") as handle:
        database_rows = {
            row["name"]: row
            for row in csv.DictReader(handle, delimiter="|")
            if row.get("name") in TARGETS
        }
    if set(database_rows) != set(TARGETS):
        raise RuntimeError(f"missing rows: {sorted(set(TARGETS) - set(database_rows))}")

    rows = []
    for knot, configuration in TARGETS.items():
        database_row = database_rows[knot]
        fractions = parse_montesinos(database_row["montesinos_notation"])
        b, pairs = obs.normalize_fracs(fractions)
        e = obs.seifert_e(b, pairs)
        if e > 0:
            b_used, pairs_used = obs.reverse_seifert(b, pairs)
            negative_definite_source = "reversed normalized Seifert data"
        else:
            b_used, pairs_used = b, pairs
            negative_definite_source = "normalized Seifert data"
        q, weights, arms = obs.star_matrix(b_used, pairs_used)
        determinant = abs(int(q.det()))
        expected_determinant = int(database_row["determinant"])
        if determinant != expected_determinant:
            raise RuntimeError(
                f"{knot}: plumbing determinant {determinant} != table {expected_determinant}"
            )
        dmap, representatives = obs.d_plumbing(q, weights)
        if len(dmap) != determinant:
            raise RuntimeError(f"{knot}: got {len(dmap)} classes, expected {determinant}")
        _, spin_representative, d_graph = spin_class(q, dmap, representatives)
        d_minus_graph = -d_graph
        selected = d_graph if configuration["orientation"] == "graph" else d_minus_graph
        k = int(configuration["k"])
        forced = Fraction(-k, 2)
        inequality_holds = selected <= forced
        congruence_holds = congruent_mod_two(selected, forced)
        rows.append(
            {
                "knot": knot,
                "crossing_number": database_row["crossing_number"],
                "input_interval": configuration["interval"],
                "table_signature": database_row["signature"],
                "signature_after_mirroring_abs": 2 * k,
                "determinant": determinant,
                "montesinos_notation": database_row["montesinos_notation"],
                "fractions": json.dumps([fraction_text(x) for x in fractions], separators=(",", ":")),
                "normalized_b": b,
                "normalized_pairs": json.dumps(pairs, separators=(",", ":")),
                "normalized_e": fraction_text(e),
                "negative_definite_source": negative_definite_source,
                "plumbing_b": b_used,
                "plumbing_pairs": json.dumps(pairs_used, separators=(",", ":")),
                "plumbing_weights": json.dumps(weights, separators=(",", ":")),
                "plumbing_arms": json.dumps(arms, separators=(",", ":")),
                "plumbing_matrix": matrix_as_json(q),
                "spin_representative_x": json.dumps(spin_representative, separators=(",", ":")),
                "d_spin_graph": fraction_text(d_graph),
                "d_spin_minus_graph": fraction_text(d_minus_graph),
                "paper_orientation": configuration["orientation"],
                "d_spin_selected": fraction_text(selected),
                "forced_value_if_u_equals_lower_endpoint": fraction_text(forced),
                "inequality_holds": inequality_holds,
                "congruence_mod_2_holds": congruence_holds,
                "lower_endpoint_obstructed": not (inequality_holds and congruence_holds),
                "conclusion": f"u={k + 1}",
            }
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "database_knotinfo_version": importlib.metadata.version("database-knotinfo"),
        "targets": len(rows),
        "input_interval_2_3": sum(row["input_interval"] == "[2,3]" for row in rows),
        "input_interval_3_4": sum(row["input_interval"] == "[3,4]" for row in rows),
        "obstructed": sum(bool(row["lower_endpoint_obstructed"]) for row in rows),
        "exact_u3": sum(row["conclusion"] == "u=3" for row in rows),
        "exact_u4": sum(row["conclusion"] == "u=4" for row in rows),
        "selected_spin_values": sorted({row["d_spin_selected"] for row in rows}),
        "output": output.name,
        "orientation_note": (
            "The graph/minus_graph choice is the row-wise orientation calibration used in the paper "
            "after mirroring where necessary."
        ),
    }
    output.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
