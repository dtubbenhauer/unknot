#!/usr/bin/env python3
"""Exact full Owens correction-term tests for selected alternating knots.

The source data (PD code, signature, determinant) are read from the supplied
KnotInfo workbook.  For each knot, the script:

* reconstructs both positive graph-Laplacian Goeritz forms;
* chooses the boundary orientation by the spin identity m_G(0)=-sigma/4;
* computes the complete function m_G by finite characteristic-covector
  enumeration;
* enumerates every rank-four Owens matrix allowed for a signature-four,
  two-crossing unknotting sequence;
* checks every group isomorphism coker(Q) -> coker(G).

All matrix and correction-term arithmetic is exact.  The script currently
targets cyclic discriminant groups, which includes the five signature-four
ten-crossing knots tested in the paper and the built-in 9_10 validation case.
"""

from __future__ import annotations

import argparse
import ast
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Sequence

import xlrd

from knotinfo_strengthening_scan import (
    COLUMNS,
    as_int,
    determinant_bareiss,
    goeritz_zero_class_m4,
    owens_matrix,
    owens_triples,
    pd_goeritz_forms,
)


Matrix = list[list[int]]
Label = tuple[int, ...]


def fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def inverse_matrix(matrix: Sequence[Sequence[int]]) -> list[list[Fraction]]:
    """Return the exact inverse by Gauss--Jordan elimination."""
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("inverse requires a nonempty square matrix")
    work = [
        [Fraction(int(entry)) for entry in row]
        + [Fraction(int(i == j)) for j in range(size)]
        for i, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot = next(
            (row for row in range(column, size) if work[row][column]), None
        )
        if pivot is None:
            raise ValueError("matrix is singular")
        work[column], work[pivot] = work[pivot], work[column]
        scale = work[column][column]
        work[column] = [entry / scale for entry in work[column]]
        for row in range(size):
            if row == column:
                continue
            scale = work[row][column]
            if scale:
                work[row] = [
                    left - scale * right
                    for left, right in zip(work[row], work[column])
                ]
    return [row[size:] for row in work]


def adjugate_matrix(matrix: Sequence[Sequence[int]]) -> tuple[int, Matrix]:
    determinant = determinant_bareiss(matrix)
    if determinant <= 0:
        raise ValueError("a positive determinant is required")
    inverse = inverse_matrix(matrix)
    adjugate: Matrix = []
    for row in inverse:
        adjugate_row: list[int] = []
        for entry in row:
            scaled = entry * determinant
            if scaled.denominator != 1:
                raise ArithmeticError("det(A) A^-1 was not integral")
            adjugate_row.append(scaled.numerator)
        adjugate.append(adjugate_row)
    return determinant, adjugate


def is_positive_definite(matrix: Sequence[Sequence[int]]) -> bool:
    """Sylvester's criterion, using exact leading principal minors."""
    return all(
        determinant_bareiss([row[:size] for row in matrix[:size]]) > 0
        for size in range(1, len(matrix) + 1)
    )


def characteristic_vectors(
    matrix: Sequence[Sequence[int]],
) -> Iterable[tuple[int, ...]]:
    """Enumerate the finite box sufficient for every m_A minimum."""
    coordinate_ranges = [
        range(-int(matrix[i][i]), int(matrix[i][i]) + 1, 2)
        for i in range(len(matrix))
    ]
    return itertools.product(*coordinate_ranges)


def discriminant_label(
    vector: Sequence[int], adjugate: Sequence[Sequence[int]], determinant: int
) -> Label:
    """Canonical label for [vector] in coker(A), via A^-1 vector mod Z."""
    return tuple(
        sum(int(adjugate[i][j]) * int(vector[j]) for j in range(len(vector)))
        % determinant
        for i in range(len(vector))
    )


def correction_term_table(matrix: Sequence[Sequence[int]]) -> dict[Label, Fraction]:
    """Compute the complete m_A table by exact finite enumeration."""
    if not is_positive_definite(matrix):
        raise ValueError("correction-term matrix is not positive definite")
    determinant, adjugate = adjugate_matrix(matrix)
    rank = len(matrix)
    minima: dict[Label, Fraction] = {}
    for vector in characteristic_vectors(matrix):
        label = discriminant_label(vector, adjugate, determinant)
        numerator = sum(
            int(vector[i]) * int(adjugate[i][j]) * int(vector[j])
            for i in range(rank)
            for j in range(rank)
        )
        value = Fraction(numerator - rank * determinant, 4 * determinant)
        if label not in minima or value < minima[label]:
            minima[label] = value
    if len(minima) != determinant:
        raise ArithmeticError(
            f"enumeration found {len(minima)} classes, expected {determinant}"
        )
    return minima


def add_multiple(label: Label, multiple: int, modulus: int) -> Label:
    return tuple(multiple * entry % modulus for entry in label)


def label_order(label: Label, modulus: int) -> int:
    orders = [
        modulus // math.gcd(modulus, int(entry)) for entry in label
    ]
    return math.lcm(*orders)


def cyclic_coordinates(labels: Iterable[Label], modulus: int) -> tuple[Label, dict[Label, int]]:
    label_set = set(labels)
    generator = next(
        (label for label in sorted(label_set) if label_order(label, modulus) == modulus),
        None,
    )
    if generator is None:
        raise ValueError(f"discriminant group of order {modulus} is not cyclic")
    coordinates = {
        add_multiple(generator, multiple, modulus): multiple
        for multiple in range(modulus)
    }
    if set(coordinates) != label_set:
        raise ArithmeticError("chosen generator does not enumerate the label set")
    return generator, coordinates


def congruent_mod_two(left: Fraction, right: Fraction) -> bool:
    difference = left - right
    return difference.denominator == 1 and difference.numerator % 2 == 0


def full_isomorphism_check(
    source: dict[Label, Fraction], target: dict[Label, Fraction], determinant: int
) -> dict[str, object]:
    """Check all isomorphisms source -> target for Owens's two conditions."""
    source_generator, source_coordinates = cyclic_coordinates(source, determinant)
    target_generator, _ = cyclic_coordinates(target, determinant)
    units = [unit for unit in range(1, determinant) if math.gcd(unit, determinant) == 1]
    survivors: list[int] = []
    failures: list[dict[str, object]] = []
    for unit in units:
        failure: dict[str, object] | None = None
        for source_label, coordinate in sorted(
            source_coordinates.items(), key=lambda item: item[1]
        ):
            target_coordinate = unit * coordinate % determinant
            target_label = add_multiple(
                target_generator, target_coordinate, determinant
            )
            source_value = source[source_label]
            target_value = target[target_label]
            inequality = source_value >= target_value
            congruence = congruent_mod_two(source_value, target_value)
            if not (inequality and congruence):
                failure = {
                    "unit": unit,
                    "source_coordinate": coordinate,
                    "target_coordinate": target_coordinate,
                    "source_value": fraction_text(source_value),
                    "target_value": fraction_text(target_value),
                    "difference": fraction_text(source_value - target_value),
                    "inequality_holds": inequality,
                    "congruence_holds": congruence,
                }
                break
        if failure is None:
            survivors.append(unit)
        else:
            failures.append(failure)
    return {
        "source_generator": list(source_generator),
        "target_generator": list(target_generator),
        "units_checked": units,
        "surviving_units": survivors,
        "first_failure_by_unit": failures,
    }


def table_in_cyclic_order(
    table: dict[Label, Fraction], determinant: int
) -> dict[str, object]:
    generator, _ = cyclic_coordinates(table, determinant)
    return {
        "generator": list(generator),
        "values": [
            fraction_text(table[add_multiple(generator, index, determinant)])
            for index in range(determinant)
        ],
    }


def workbook_row(sheet: xlrd.sheet.Sheet, knot_name: str) -> int:
    matches = [
        row
        for row in range(2, sheet.nrows)
        if str(sheet.cell_value(row, COLUMNS["name"])) == knot_name
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one workbook row for {knot_name}, found {len(matches)}")
    return matches[0]


def analyze_knot(sheet: xlrd.sheet.Sheet, knot_name: str) -> dict[str, object]:
    row = workbook_row(sheet, knot_name)
    determinant = as_int(sheet.cell_value(row, COLUMNS["determinant"]))
    signature = as_int(sheet.cell_value(row, COLUMNS["signature"]))
    if abs(signature) != 4:
        raise ValueError(f"{knot_name}: this script expects absolute signature 4")
    # Owens states the signature-sharp case after reflecting so that the
    # signature is +4.  Reflection preserves the unsigned checkerboard graph
    # pair and selects the member with spin value -1.
    effective_signature = abs(signature)
    pd = ast.literal_eval(str(sheet.cell_value(row, COLUMNS["pd"])))
    goeritz_forms = pd_goeritz_forms(pd)
    for form in goeritz_forms:
        if determinant_bareiss(form) != determinant:
            raise ArithmeticError(f"{knot_name}: Goeritz determinant mismatch")
    expected_spin_m4 = -effective_signature
    oriented = [
        form
        for form in goeritz_forms
        if goeritz_zero_class_m4(form) == expected_spin_m4
    ]
    if len(oriented) != 1:
        raise ArithmeticError(
            f"{knot_name}: expected one Goeritz form with 4m(0)={expected_spin_m4}"
        )
    goeritz = oriented[0]
    goeritz_table = correction_term_table(goeritz)
    zero_label = (0,) * len(goeritz)
    if goeritz_table[zero_label] != Fraction(-effective_signature, 4):
        raise ArithmeticError(f"{knot_name}: spin correction-term check failed")

    candidates: list[dict[str, object]] = []
    for triple in owens_triples(determinant):
        matrix = owens_matrix(triple)
        table = correction_term_table(matrix)
        comparison = full_isomorphism_check(table, goeritz_table, determinant)
        candidates.append(
            {
                "triple_m1_m2_a": list(triple),
                "matrix": matrix,
                "correction_terms_cyclic_order": table_in_cyclic_order(
                    table, determinant
                ),
                **comparison,
            }
        )

    return {
        "knot": knot_name,
        "database_row": row + 1,
        "determinant": determinant,
        "workbook_signature": signature,
        "signature_after_reflection_if_needed": effective_signature,
        "goeritz_forms": [
            {
                "matrix": form,
                "rank": len(form),
                "four_times_spin_value": goeritz_zero_class_m4(form),
                "selected_orientation": form is goeritz,
            }
            for form in goeritz_forms
        ],
        "oriented_goeritz_correction_terms_cyclic_order": table_in_cyclic_order(
            goeritz_table, determinant
        ),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "owens_obstructs_u_equals_2": bool(candidates)
        and all(not item["surviving_units"] for item in candidates),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument(
        "--knots",
        nargs="+",
        default=["10_6", "10_47", "10_61", "10_76", "10_100"],
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quiet", action="store_true")
    arguments = parser.parse_args()

    book = xlrd.open_workbook(str(arguments.workbook), on_demand=True)
    sheet = book.sheet_by_name("sample_dat")
    results = {
        "source_workbook": arguments.workbook.name,
        "method": "full Owens correction-term comparison",
        "knots": [analyze_knot(sheet, name) for name in arguments.knots],
    }
    rendered = json.dumps(results, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")
    if not arguments.quiet:
        print(rendered, end="")


if __name__ == "__main__":
    main()
