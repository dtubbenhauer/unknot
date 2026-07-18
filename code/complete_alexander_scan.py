#!/usr/bin/env python3
"""Compute the complete finite-field Alexander nullity index.

This is a research script for the July 2026 KnotInfo workbook.  It first
removes unit pivots from tV-V^T over Z[t,t^-1].  It then tests the relevant
elementary ideals exactly.  A determinantal ideal is proper precisely when it
is contained in a maximal ideal (p,h(t)), equivalently when a finite-field
specialization has the requested nullity.

SymPy is used only for exact univariate gcds, resultants, and factorization.
"""

from __future__ import annotations

import argparse
import ast
import csv
import itertools
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import sympy as sp


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from knotinfo_strengthening_scan import (  # noqa: E402
    COLUMNS,
    compact_name,
    parse_interval,
    read_rows,
)


Laurent = dict[int, int]
T = sp.symbols("t")


def clean(poly: Laurent) -> Laurent:
    return {exponent: coefficient for exponent, coefficient in poly.items() if coefficient}


def add(first: Laurent, second: Laurent, multiplier: int = 1) -> Laurent:
    result = dict(first)
    for exponent, coefficient in second.items():
        result[exponent] = result.get(exponent, 0) + multiplier * coefficient
    return clean(result)


def multiply(first: Laurent, second: Laurent) -> Laurent:
    result: Laurent = {}
    for exponent, coefficient in first.items():
        for other_exponent, other_coefficient in second.items():
            degree = exponent + other_exponent
            result[degree] = result.get(degree, 0) + coefficient * other_coefficient
    return clean(result)


def unit_inverse(poly: Laurent) -> Laurent | None:
    if len(poly) != 1:
        return None
    (exponent, coefficient), = poly.items()
    if coefficient not in (-1, 1):
        return None
    return {-exponent: coefficient}


def seifert_presentation(seifert: Sequence[Sequence[int]]) -> list[list[Laurent]]:
    size = len(seifert)
    return [
        [
            clean({1: int(seifert[row][column]), 0: -int(seifert[column][row])})
            for column in range(size)
        ]
        for row in range(size)
    ]


def remove_unit_pivots(matrix: list[list[Laurent]]) -> list[list[Laurent]]:
    """Split off every visible 1-by-1 unit summand by exact operations."""
    work = [[dict(entry) for entry in row] for row in matrix]
    while work:
        pivot: tuple[int, int, Laurent] | None = None
        for row, entries in enumerate(work):
            for column, entry in enumerate(entries):
                inverse = unit_inverse(entry)
                if inverse is not None:
                    pivot = row, column, inverse
                    break
            if pivot is not None:
                break
        if pivot is None:
            return work

        pivot_row, pivot_column, inverse = pivot
        work[0], work[pivot_row] = work[pivot_row], work[0]
        for row in work:
            row[0], row[pivot_column] = row[pivot_column], row[0]

        work[0] = [multiply(inverse, entry) for entry in work[0]]
        for row in range(1, len(work)):
            coefficient = work[row][0]
            if coefficient:
                work[row] = [
                    add(work[row][column], multiply(coefficient, work[0][column]), -1)
                    for column in range(len(work))
                ]

        # Column operations clear the rest of row zero.  Column zero is now
        # (1,0,...,0)^T, so the lower-right block itself does not change.
        work = [row[1:] for row in work[1:]]
    return work


def determinant(matrix: Sequence[Sequence[Laurent]]) -> Laurent:
    size = len(matrix)
    if size == 0:
        return {0: 1}
    if size == 1:
        return dict(matrix[0][0])
    # Expansion by permutations is fast here: unit reduction leaves size <= 6.
    result: Laurent = {}
    for permutation in itertools.permutations(range(size)):
        inversions = sum(
            permutation[i] > permutation[j]
            for i in range(size)
            for j in range(i + 1, size)
        )
        term: Laurent = {0: -1 if inversions % 2 else 1}
        for row, column in enumerate(permutation):
            term = multiply(term, matrix[row][column])
            if not term:
                break
        result = add(result, term)
    return result


def minors(matrix: Sequence[Sequence[Laurent]], size: int) -> list[Laurent]:
    dimension = len(matrix)
    result: list[Laurent] = []
    for rows in itertools.combinations(range(dimension), size):
        for columns in itertools.combinations(range(dimension), size):
            value = determinant(
                [[matrix[row][column] for column in columns] for row in rows]
            )
            if value:
                result.append(value)
    return result


def normalized_coefficients(poly: Laurent) -> tuple[int, ...]:
    """Multiply by a Laurent unit so the least exponent is zero."""
    if not poly:
        return ()
    least = min(poly)
    greatest = max(poly)
    return tuple(poly.get(exponent, 0) for exponent in range(least, greatest + 1))


def unique_polynomials(polynomials: Iterable[Laurent]) -> list[sp.Poly]:
    seen: set[tuple[int, ...]] = set()
    result: list[sp.Poly] = []
    for polynomial in polynomials:
        coefficients = normalized_coefficients(polynomial)
        if not coefficients:
            continue
        # Multiplication by -1 is a unit and avoids duplicate signs.
        if coefficients[-1] < 0:
            coefficients = tuple(-coefficient for coefficient in coefficients)
        if coefficients in seen:
            continue
        seen.add(coefficients)
        expression = sum(coefficient * T**degree for degree, coefficient in enumerate(coefficients))
        result.append(sp.Poly(expression, T, domain=sp.ZZ))
    return result


def gcd_over_q(polynomials: Sequence[sp.Poly]) -> sp.Poly:
    current = sp.Poly(polynomials[0].as_expr(), T, domain=sp.QQ)
    for polynomial in polynomials[1:]:
        current = sp.gcd(current, sp.Poly(polynomial.as_expr(), T, domain=sp.QQ))
        if current.degree() == 0:
            break
    return current.monic()


def gcd_mod_prime(polynomials: Sequence[sp.Poly], prime: int) -> sp.Poly:
    current = sp.Poly(polynomials[0].as_expr(), T, modulus=prime)
    for polynomial in polynomials[1:]:
        current = sp.gcd(current, sp.Poly(polynomial.as_expr(), T, modulus=prime))
        if current.degree() == 0:
            break
    return current.monic()


def prime_witness(polynomials: Sequence[sp.Poly], prime: int) -> dict[str, object] | None:
    common = gcd_mod_prime(polynomials, prime)
    if common.degree() <= 0:
        return None
    _, factors = sp.factor_list(common.as_expr(), modulus=prime)
    usable = []
    for factor, multiplicity in factors:
        polynomial = sp.Poly(factor, T, modulus=prime).monic()
        if polynomial.degree() > 0 and int(polynomial.nth(0)) % prime:
            usable.append((polynomial.degree(), polynomial, multiplicity))
    if not usable:
        return None
    _, factor, multiplicity = min(usable, key=lambda item: (item[0], str(item[1].as_expr())))
    coefficients = [int(factor.nth(index)) % prime for index in range(factor.degree() + 1)]
    return {
        "prime": prime,
        "extension_degree": factor.degree(),
        "field_order": prime ** factor.degree(),
        "minimal_polynomial_coefficients": coefficients,
        "minimal_polynomial": str(factor.as_expr()),
        "common_factor_multiplicity": multiplicity,
    }


def first_generic_witness(polynomials: Sequence[sp.Poly]) -> dict[str, object]:
    for prime in list(sp.primerange(2, 200)) + list(sp.primerange(211, 2000)):
        witness = prime_witness(polynomials, prime)
        if witness is not None:
            return witness
    raise RuntimeError("failed to find a good reduction below 2000")


def selected_combinations(
    base: sp.Poly,
    others: Sequence[sp.Poly],
    seed: int,
    count: int = 8,
) -> list[sp.Poly]:
    """Return small combinations of others that are coprime to base over Q."""
    _, factor_data = sp.factor_list(base.as_expr())
    selected: list[sp.Poly] = []
    for factor, _ in factor_data:
        divisor = sp.Poly(factor, T, domain=sp.QQ)
        choice = next(
            polynomial
            for polynomial in others
            if sp.rem(sp.Poly(polynomial.as_expr(), T, domain=sp.QQ), divisor) != 0
        )
        if choice not in selected:
            selected.append(choice)
    if not selected:
        selected = list(others)

    rng = random.Random(seed)
    result: list[sp.Poly] = []
    attempts = 0
    while len(result) < count and attempts < 500:
        attempts += 1
        coefficients = [rng.choice((-5, -3, -2, -1, 1, 2, 3, 5)) for _ in selected]
        expression = sum(
            coefficient * polynomial.as_expr()
            for coefficient, polynomial in zip(coefficients, selected)
        )
        combination = sp.Poly(expression, T, domain=sp.ZZ)
        if sp.gcd(
            sp.Poly(base.as_expr(), T, domain=sp.QQ),
            sp.Poly(combination.as_expr(), T, domain=sp.QQ),
        ).degree() != 0:
            continue
        if combination not in result:
            result.append(combination)
    if not result:
        raise RuntimeError("could not construct a coprime combination")
    return result


@dataclass(frozen=True)
class IdealTest:
    proper: bool
    witness: dict[str, object] | None
    rational_gcd_degree: int
    candidate_integer: int | None
    candidate_primes: tuple[int, ...]


def test_proper(polynomials_raw: Iterable[Laurent], seed: int) -> IdealTest:
    polynomials = unique_polynomials(polynomials_raw)
    if not polynomials:
        return IdealTest(True, None, -1, None, ())
    if any(polynomial.degree() == 0 and abs(int(polynomial.nth(0))) == 1 for polynomial in polynomials):
        return IdealTest(False, None, 0, 1, ())

    constants = [abs(int(polynomial.nth(0))) for polynomial in polynomials if polynomial.degree() == 0]
    if constants:
        candidate = math.gcd(*constants)
        if candidate == 1:
            return IdealTest(False, None, 0, 1, ())
        factors = tuple(sorted(sp.factorint(candidate)))
        for prime in factors:
            witness = prime_witness(polynomials, int(prime))
            if witness is not None:
                return IdealTest(True, witness, 0, candidate, factors)
        return IdealTest(False, None, 0, candidate, factors)

    rational_gcd = gcd_over_q(polynomials)
    if rational_gcd.degree() > 0:
        witness = first_generic_witness(polynomials)
        return IdealTest(True, witness, rational_gcd.degree(), 0, ())

    # There are only finitely many exceptional characteristics.  A common
    # factor modulo p forces p to divide every nonzero resultant below.
    base = min(polynomials, key=lambda polynomial: (polynomial.degree(), len(polynomial.terms())))
    others = [polynomial for polynomial in polynomials if polynomial != base]
    combinations = selected_combinations(base, others, seed)
    candidate = 0
    for combination in combinations:
        resultant = abs(int(sp.resultant(base.as_expr(), combination.as_expr(), T)))
        if resultant == 0:
            continue
        candidate = resultant if candidate == 0 else math.gcd(candidate, resultant)
        if candidate == 1:
            break
    if candidate == 0:
        raise RuntimeError("no nonzero resultant produced")
    if candidate == 1:
        return IdealTest(False, None, 0, 1, ())

    factorization = sp.factorint(candidate)
    factors = tuple(sorted(int(prime) for prime in factorization))
    for prime in factors:
        witness = prime_witness(polynomials, prime)
        if witness is not None:
            return IdealTest(True, witness, 0, candidate, factors)
    return IdealTest(False, None, 0, candidate, factors)


def finite_field_index(matrix: list[list[Laurent]], seed: int) -> tuple[int, dict[str, object] | None, list[dict[str, object]]]:
    dimension = len(matrix)
    tests: list[dict[str, object]] = []
    for nullity in range(dimension, 0, -1):
        minor_size = dimension - nullity + 1
        generators = minors(matrix, minor_size)
        test = test_proper(generators, seed + 1009 * nullity)
        record = {
            "nullity": nullity,
            "minor_size": minor_size,
            "number_of_nonzero_minors": len(generators),
            "proper": test.proper,
            "rational_gcd_degree": test.rational_gcd_degree,
            "candidate_integer": str(test.candidate_integer) if test.candidate_integer is not None else None,
            "candidate_primes": list(test.candidate_primes),
        }
        tests.append(record)
        if test.proper:
            return nullity, test.witness, tests
    return 0, None, tests


def run(workbook_path: Path, output_path: Path, limit: int | None = None) -> None:
    existing_path = ROOT / "lower_bounds" / "alexander_module" / "restricted_scan_certificates.csv"
    existing: dict[str, int] = {}
    with existing_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            existing[row["knot"]] = int(row["nullity"])

    book, sheet = read_rows(workbook_path)
    results: list[dict[str, object]] = []
    started = time.time()
    checked = 0
    try:
        for row_number in range(2, sheet.nrows):
            interval = parse_interval(sheet.cell_value(row_number, COLUMNS["unknotting"]))
            if interval is None or interval[0] >= interval[1]:
                continue
            checked += 1
            if limit is not None and checked > limit:
                break
            name = compact_name(str(sheet.cell_value(row_number, COLUMNS["name"])))
            seifert = ast.literal_eval(str(sheet.cell_value(row_number, COLUMNS["seifert"])).strip())
            reduced = remove_unit_pivots(seifert_presentation(seifert))
            index, witness, tests = finite_field_index(reduced, seed=row_number + 1)
            if index > interval[1]:
                raise ValueError(f"{name}: finite-field index {index} exceeds upper bound {interval[1]}")
            previous_relevant_nullity = max(existing.get(name, 0), interval[0])
            results.append(
                {
                    "database_row": row_number + 1,
                    "knot": name,
                    "crossing_number": int(float(sheet.cell_value(row_number, COLUMNS["crossing"]))),
                    "input_interval": [interval[0], interval[1]],
                    "original_size": len(seifert),
                    "reduced_size": len(reduced),
                    "complete_finite_field_index": index,
                    "previous_scan_nullity": existing.get(name, 0),
                    "previous_relevant_lower_bound": previous_relevant_nullity,
                    "new_over_previous_scan": index > previous_relevant_nullity,
                    "improves_input_lower_bound": index > interval[0],
                    "witness": witness,
                    "tests": tests,
                }
            )
            if checked % 100 == 0:
                elapsed = time.time() - started
                print(f"checked {checked}: {elapsed:.1f}s", flush=True)
    finally:
        book.release_resources()

    summary = {
        "workbook": str(workbook_path),
        "gapped_rows_checked": checked if limit is None else min(checked, limit),
        "elapsed_seconds": round(time.time() - started, 3),
        "reduced_size_maximum": max((int(row["reduced_size"]) for row in results), default=0),
        "finite_field_index_counts": {
            str(index): sum(int(row["complete_finite_field_index"]) == index for row in results)
            for index in sorted({int(row["complete_finite_field_index"]) for row in results})
        },
        "improves_input_lower_bound": sum(bool(row["improves_input_lower_bound"]) for row in results),
        "new_over_previous_scan": sum(bool(row["new_over_previous_scan"]) for row in results),
        "new_knots": [row["knot"] for row in results if row["new_over_previous_scan"]],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "workbook",
        type=Path,
        nargs="?",
        default=ROOT / "knotinfo_data_complete(11).xls",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "complete_alexander_scan.json",
    )
    parser.add_argument("--limit", type=int)
    arguments = parser.parse_args()
    run(arguments.workbook, arguments.output, arguments.limit)


if __name__ == "__main__":
    main()
