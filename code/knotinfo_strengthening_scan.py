#!/usr/bin/env python3
"""Exact scans strengthening the results in big_data_unknotting.

The script performs two independent searches in the July 2026 KnotInfo
workbook.

1. Finite-field Alexander-module certificates.
   If V is a Seifert matrix and alpha is a nonzero element of a finite
   field F, then nullity_F(alpha*V - V^T) is a lower bound for the
   Nakanishi index, hence for the unknotting number.

2. The determinant and finite-group parts of the Owens signature-four
   obstruction.  The script reconstructs a Goeritz presentation from a PD
   code, audits the orientation-sensitive zero-class calculation, and compares
   the complete primary exponent profiles of the discriminant groups with
   those of every candidate Owens matrix.

Only integer arithmetic and arithmetic in explicitly constructed finite
fields are used.  The source workbook is never modified.
"""

from __future__ import annotations

import argparse
import ast
import collections
import csv
import itertools
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import xlrd


COLUMNS = {
    "name": 0,
    "alternating": 4,
    "dt_name": 8,
    "pd": 26,
    "crossing": 28,
    "unknotting": 32,
    "signature": 46,
    "determinant": 104,
    "seifert": 106,
    "algebraic_unknotting": 188,
}


def parse_interval(value: object) -> tuple[int, int] | None:
    text = str(value).strip()
    match = re.fullmatch(r"\[(\d+),(\d+)\]", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    try:
        exact = int(float(text))
    except (TypeError, ValueError):
        return None
    return exact, exact


def as_int(value: object) -> int:
    return int(float(value))


def compact_name(name: str) -> str:
    """Convert KnotInfo names such as 13n_85 to the paper's 13n85 style."""
    return re.sub(r"([an])_", r"\1", name)


def determinant_bareiss(matrix: Sequence[Sequence[int]]) -> int:
    """Fraction-free exact determinant."""
    n = len(matrix)
    if n == 0:
        return 1
    if any(len(row) != n for row in matrix):
        raise ValueError("determinant requires a square matrix")
    work = [list(map(int, row)) for row in matrix]
    sign = 1
    previous = 1
    for k in range(n - 1):
        if work[k][k] == 0:
            swap = next((i for i in range(k + 1, n) if work[i][k]), None)
            if swap is None:
                return 0
            work[k], work[swap] = work[swap], work[k]
            sign = -sign
        pivot = work[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                numerator = work[i][j] * pivot - work[i][k] * work[k][j]
                if numerator % previous:
                    raise ArithmeticError("Bareiss division was not exact")
                work[i][j] = numerator // previous
        previous = pivot
        for i in range(k + 1, n):
            work[i][k] = 0
    return sign * work[-1][-1]


def prime_divisors(number: int) -> list[int]:
    number = abs(number)
    result: list[int] = []
    divisor = 2
    while divisor * divisor <= number:
        if number % divisor == 0:
            result.append(divisor)
            while number % divisor == 0:
                number //= divisor
        divisor = 3 if divisor == 2 else divisor + 2
    if number > 1:
        result.append(number)
    return result


def rank_mod_prime(matrix: Sequence[Sequence[int]], prime: int) -> int:
    """Row rank over F_p."""
    if not matrix:
        return 0
    work = [[int(entry) % prime for entry in row] for row in matrix]
    nrows = len(work)
    ncols = len(work[0])
    rank = 0
    for column in range(ncols):
        pivot = next(
            (row for row in range(rank, nrows) if work[row][column]), None
        )
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        inverse = pow(work[rank][column], -1, prime)
        for j in range(column, ncols):
            work[rank][j] = work[rank][j] * inverse % prime
        for row in range(rank + 1, nrows):
            coefficient = work[row][column]
            if coefficient:
                for j in range(column, ncols):
                    work[row][j] = (
                        work[row][j] - coefficient * work[rank][j]
                    ) % prime
        rank += 1
        if rank == nrows:
            break
    return rank


def specialized_matrix(
    seifert: Sequence[Sequence[int]], prime: int, alpha: int
) -> list[list[int]]:
    n = len(seifert)
    return [
        [
            (alpha * int(seifert[i][j]) - int(seifert[j][i])) % prime
            for j in range(n)
        ]
        for i in range(n)
    ]


@dataclass(frozen=True)
class QuadraticField:
    """F_p[x]/(x^2+c1*x+c0), with alpha the class of x."""

    prime: int
    c0: int
    c1: int
    label: str

    def __post_init__(self) -> None:
        p = self.prime
        # A quadratic is irreducible exactly when it has no root in F_p.
        if any((a * a + self.c1 * a + self.c0) % p == 0 for a in range(p)):
            raise ValueError(f"reducible polynomial for {self.label}")
        q = p * p
        add = [[0] * q for _ in range(q)]
        neg = [0] * q
        multiply = [[0] * q for _ in range(q)]
        for x in range(q):
            x0, x1 = x % p, x // p
            neg[x] = (-x0) % p + p * ((-x1) % p)
            for y in range(q):
                y0, y1 = y % p, y // p
                add[x][y] = (x0 + y0) % p + p * ((x1 + y1) % p)
                constant = (x0 * y0 - x1 * y1 * self.c0) % p
                linear = (
                    x0 * y1 + x1 * y0 - x1 * y1 * self.c1
                ) % p
                multiply[x][y] = constant + p * linear
        inverse = [0] * q
        for x in range(1, q):
            inverse[x] = next(y for y in range(1, q) if multiply[x][y] == 1)
        object.__setattr__(self, "order", q)
        object.__setattr__(self, "alpha", p)  # code for 0 + 1*x
        object.__setattr__(self, "_add", add)
        object.__setattr__(self, "_neg", neg)
        object.__setattr__(self, "_multiply", multiply)
        object.__setattr__(self, "_inverse", inverse)

    @property
    def polynomial(self) -> str:
        pieces = ["x^2"]
        if self.c1:
            pieces.append("x" if self.c1 == 1 else f"{self.c1}*x")
        if self.c0:
            pieces.append("1" if self.c0 == 1 else str(self.c0))
        return "+".join(pieces)

    def rank_specialization(self, seifert: Sequence[Sequence[int]]) -> int:
        p = self.prime
        n = len(seifert)
        add = self._add
        neg = self._neg
        multiply = self._multiply
        alpha = self.alpha
        work = [
            [
                add[multiply[alpha][int(seifert[i][j]) % p]][
                    neg[int(seifert[j][i]) % p]
                ]
                for j in range(n)
            ]
            for i in range(n)
        ]
        rank = 0
        for column in range(n):
            pivot = next(
                (row for row in range(rank, n) if work[row][column]), None
            )
            if pivot is None:
                continue
            work[rank], work[pivot] = work[pivot], work[rank]
            inverse = self._inverse[work[rank][column]]
            for j in range(column, n):
                work[rank][j] = multiply[work[rank][j]][inverse]
            for row in range(rank + 1, n):
                coefficient = work[row][column]
                if coefficient:
                    negative = neg[coefficient]
                    for j in range(column, n):
                        work[row][j] = add[work[row][j]][
                            multiply[negative][work[rank][j]]
                        ]
            rank += 1
            if rank == n:
                break
        return rank


QUADRATIC_FIELDS = (
    QuadraticField(2, 1, 1, "F_4"),
    QuadraticField(3, 1, 0, "F_9"),
    QuadraticField(5, 1, 1, "F_25"),
)
SCALAR_PRIMES = (2, 3, 5, 7, 11)


def validate_seifert_matrix(
    seifert: Sequence[Sequence[int]], determinant: int
) -> None:
    n = len(seifert)
    if n == 0 or any(len(row) != n for row in seifert):
        raise ValueError("invalid Seifert matrix shape")
    skew = [
        [int(seifert[i][j]) - int(seifert[j][i]) for j in range(n)]
        for i in range(n)
    ]
    symmetric = [
        [int(seifert[i][j]) + int(seifert[j][i]) for j in range(n)]
        for i in range(n)
    ]
    if abs(determinant_bareiss(skew)) != 1:
        raise ValueError("V-V^T is not unimodular")
    if abs(determinant_bareiss(symmetric)) != determinant:
        raise ValueError("V+V^T does not reproduce the determinant")


def best_alexander_witness(
    seifert: Sequence[Sequence[int]],
) -> dict[str, object]:
    n = len(seifert)
    witnesses: list[dict[str, object]] = []
    for prime in SCALAR_PRIMES:
        for alpha in range(1, prime):
            matrix = specialized_matrix(seifert, prime, alpha)
            nullity = n - rank_mod_prime(matrix, prime)
            witnesses.append(
                {
                    "kind": "scalar",
                    "field": f"F_{prime}",
                    "field_order": prime,
                    "prime": prime,
                    "specialization": str(alpha),
                    "minimal_polynomial": f"x-{alpha}",
                    "nullity": nullity,
                }
            )
    for field in QUADRATIC_FIELDS:
        nullity = n - field.rank_specialization(seifert)
        witnesses.append(
            {
                "kind": "quadratic",
                "field": field.label,
                "field_order": field.order,
                "prime": field.prime,
                "specialization": "x",
                "minimal_polynomial": field.polynomial,
                "nullity": nullity,
            }
        )
    # Maximize the certified lower bound, then prefer the smallest field and
    # the scalar witness when equally small.
    return max(
        witnesses,
        key=lambda item: (
            int(item["nullity"]),
            -int(item["field_order"]),
            item["kind"] == "scalar",
        ),
    )


def read_rows(workbook_path: Path) -> tuple[xlrd.book.Book, xlrd.sheet.Sheet]:
    book = xlrd.open_workbook(str(workbook_path), on_demand=True)
    if book.sheet_names() != ["sample_dat"]:
        raise ValueError(f"unexpected sheets: {book.sheet_names()}")
    sheet = book.sheet_by_name("sample_dat")
    expected_headers = {key: key for key in ()}
    del expected_headers  # The explicit checks below give clearer errors.
    for column, header in [
        (COLUMNS["name"], "name"),
        (COLUMNS["unknotting"], "unknotting_number"),
        (COLUMNS["seifert"], "seifert_matrix"),
    ]:
        if str(sheet.cell_value(0, column)) != header:
            raise ValueError(f"unexpected header in column {column}")
    return book, sheet


def run_alexander_scan(sheet: xlrd.sheet.Sheet) -> tuple[list[dict], dict]:
    successes: list[dict] = []
    checked = 0
    for row_number in range(2, sheet.nrows):
        input_interval = parse_interval(
            sheet.cell_value(row_number, COLUMNS["unknotting"])
        )
        if input_interval is None or input_interval[0] >= input_interval[1]:
            continue
        checked += 1
        raw = str(sheet.cell_value(row_number, COLUMNS["seifert"])).strip()
        seifert = ast.literal_eval(raw)
        witness = best_alexander_witness(seifert)
        certified = int(witness["nullity"])
        if certified <= input_interval[0]:
            continue
        determinant = as_int(
            sheet.cell_value(row_number, COLUMNS["determinant"])
        )
        validate_seifert_matrix(seifert, determinant)
        output_lower = min(certified, input_interval[1])
        output_interval = (output_lower, input_interval[1])
        algebraic_raw = str(
            sheet.cell_value(row_number, COLUMNS["algebraic_unknotting"])
        ).strip()
        already_implied = False
        try:
            already_implied = float(algebraic_raw) >= output_lower
        except ValueError:
            pass
        exact = output_interval[0] == output_interval[1]
        record = {
            "database_row": row_number + 1,
            "knot": compact_name(
                str(sheet.cell_value(row_number, COLUMNS["name"]))
            ),
            "knotinfo_name": str(
                sheet.cell_value(row_number, COLUMNS["name"])
            ),
            "dt_name": str(sheet.cell_value(row_number, COLUMNS["dt_name"])),
            "alternating": str(
                sheet.cell_value(row_number, COLUMNS["alternating"])
            ),
            "crossing_number": as_int(
                sheet.cell_value(row_number, COLUMNS["crossing"])
            ),
            "input_interval": f"[{input_interval[0]},{input_interval[1]}]",
            "certified_lower_bound": certified,
            "output_interval": (
                str(output_interval[0])
                if exact
                else f"[{output_interval[0]},{output_interval[1]}]"
            ),
            "consequence": f"exact u={output_interval[0]}" if exact else "improved",
            "signature": as_int(sheet.cell_value(row_number, COLUMNS["signature"])),
            "determinant": determinant,
            "seifert_size": len(seifert),
            "algebraic_unknotting_in_workbook": algebraic_raw,
            "already_implied_by_workbook": already_implied,
            **witness,
        }
        successes.append(record)

    genuinely_new = [r for r in successes if not r["already_implied_by_workbook"]]
    summary_counter = collections.Counter(
        (
            r["input_interval"],
            r["output_interval"],
            r["alternating"],
            r["consequence"],
        )
        for r in genuinely_new
    )
    summary = {
        "gapped_rows_checked": checked,
        "all_certificate_successes": len(successes),
        "already_implied_by_workbook": len(successes) - len(genuinely_new),
        "genuinely_new": len(genuinely_new),
        "new_exact_u2": sum(r["consequence"] == "exact u=2" for r in genuinely_new),
        "new_exact_u3": sum(r["consequence"] == "exact u=3" for r in genuinely_new),
        "new_nonexact_improvements": sum(
            r["consequence"] == "improved" for r in genuinely_new
        ),
        "breakdown": [
            {
                "input_interval": key[0],
                "output_interval": key[1],
                "alternating": key[2],
                "consequence": key[3],
                "count": count,
            }
            for key, count in sorted(summary_counter.items())
        ],
    }
    return successes, summary


def pd_goeritz_forms(pd: Sequence[Sequence[int]]) -> tuple[list[list[int]], list[list[int]]]:
    """Return the two reduced Tait-graph Laplacians of a PD diagram."""
    occurrences: dict[int, list[tuple[int, int]]] = collections.defaultdict(list)
    for crossing, labels in enumerate(pd):
        if len(labels) != 4:
            raise ValueError("each PD crossing must have four labels")
        for position, label in enumerate(labels):
            occurrences[int(label)].append((crossing, position))
    edge_involution: dict[tuple[int, int], tuple[int, int]] = {}
    for label, darts in occurrences.items():
        if len(darts) != 2:
            raise ValueError(f"PD label {label} occurs {len(darts)} times")
        edge_involution[darts[0]] = darts[1]
        edge_involution[darts[1]] = darts[0]

    face_of: dict[tuple[int, int], int] = {}
    faces: list[list[tuple[int, int]]] = []
    for dart in edge_involution:
        if dart in face_of:
            continue
        face_number = len(faces)
        cycle: list[tuple[int, int]] = []
        current = dart
        while current not in face_of:
            face_of[current] = face_number
            cycle.append(current)
            crossing, position = edge_involution[current]
            current = (crossing, (position + 1) % 4)
        if current != dart:
            raise ValueError("face permutation did not close at its start")
        faces.append(cycle)
    if len(faces) != len(pd) + 2:
        raise ValueError("PD code failed Euler's formula")

    dual_adjacency = [set() for _ in faces]
    for dart, opposite in edge_involution.items():
        first = face_of[dart]
        second = face_of[opposite]
        if first != second:
            dual_adjacency[first].add(second)
            dual_adjacency[second].add(first)
    color: list[int | None] = [None] * len(faces)
    for start in range(len(faces)):
        if color[start] is not None:
            continue
        color[start] = 0
        stack = [start]
        while stack:
            face = stack.pop()
            for neighbor in dual_adjacency[face]:
                if color[neighbor] is None:
                    color[neighbor] = 1 - int(color[face])
                    stack.append(neighbor)
                elif color[neighbor] == color[face]:
                    raise ValueError("face dual is not bipartite")

    forms: list[list[list[int]]] = []
    for chosen_color in (0, 1):
        vertices = [i for i, value in enumerate(color) if value == chosen_color]
        index = {vertex: i for i, vertex in enumerate(vertices)}
        laplacian = [[0] * len(vertices) for _ in vertices]
        for crossing in range(len(pd)):
            incident = list(
                dict.fromkeys(
                    face_of[(crossing, position)]
                    for position in range(4)
                    if color[face_of[(crossing, position)]] == chosen_color
                )
            )
            if len(incident) != 2:
                raise ValueError("crossing does not meet two regions of each color")
            first, second = map(index.get, incident)
            laplacian[first][first] += 1
            laplacian[second][second] += 1
            laplacian[first][second] -= 1
            laplacian[second][first] -= 1
        forms.append([row[:-1] for row in laplacian[:-1]])
    return forms[0], forms[1]


def solve_mod_two(matrix: Sequence[Sequence[int]], rhs: Sequence[int]) -> list[int]:
    n = len(matrix)
    work = [
        [int(matrix[i][j]) & 1 for j in range(n)] + [int(rhs[i]) & 1]
        for i in range(n)
    ]
    rank = 0
    pivot_columns: list[int] = []
    for column in range(n):
        pivot = next((i for i in range(rank, n) if work[i][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        for row in range(n):
            if row != rank and work[row][column]:
                for j in range(column, n + 1):
                    work[row][j] ^= work[rank][j]
        pivot_columns.append(column)
        rank += 1
    if rank != n:
        raise ValueError("odd determinant expected in mod-two solve")
    solution = [0] * n
    for row, column in enumerate(pivot_columns):
        solution[column] = work[row][n]
    return solution


def goeritz_zero_class_m4(goeritz: Sequence[Sequence[int]]) -> int:
    """Return 4*m_G(0) for a reduced graph Laplacian.

    In the zero class a characteristic covector is G*z with
    G*z = diag(G) mod 2.  For a graph Laplacian, apply simultaneously the
    parity-preserving 1-Lipschitz truncation that sends even integers to 0
    and odd integers to +/-1.  This cannot increase any edge contribution
    to the Dirichlet energy.  Thus these truncated vectors suffice.
    """
    n = len(goeritz)
    parity = solve_mod_two(goeritz, [goeritz[i][i] for i in range(n)])
    odd = [i for i, value in enumerate(parity) if value]
    minimum = math.inf
    for signs in itertools.product((-1, 1), repeat=len(odd)):
        vector = [0] * n
        for index, sign in zip(odd, signs):
            vector[index] = sign
        value = sum(
            vector[i] * goeritz[i][j] * vector[j]
            for i in range(n)
            for j in range(n)
        )
        minimum = min(minimum, value)
    return int(minimum) - n


def owens_triples(determinant: int) -> list[tuple[int, int, int]]:
    triples: list[tuple[int, int, int]] = []
    for m1 in range(2, (determinant + 3) // 4 + 1, 2):
        for a in range(m1):
            denominator = 2 * m1 - 1
            numerator = determinant + 4 * a * a
            if numerator % denominator:
                continue
            twice_m2_minus_one = numerator // denominator
            if (twice_m2_minus_one + 1) % 2:
                continue
            m2 = (twice_m2_minus_one + 1) // 2
            if m2 % 2 == 0 and m2 >= m1:
                triples.append((m1, m2, a))
    return triples


def owens_matrix(triple: tuple[int, int, int]) -> list[list[int]]:
    m1, m2, a = triple
    return [
        [m1, 1, a, 0],
        [1, 2, 0, 0],
        [a, 0, m2, 1],
        [0, 0, 1, 2],
    ]


def p_adic_valuation(number: int, prime: int, cutoff: int) -> int:
    """The p-adic valuation, with zero represented by ``cutoff``."""
    number %= prime**cutoff
    if number == 0:
        return cutoff
    valuation = 0
    while number % prime == 0:
        valuation += 1
        number //= prime
    return valuation


def p_primary_exponents(
    matrix: Sequence[Sequence[int]], prime: int, determinant: int
) -> tuple[int, ...]:
    """Positive p-exponents in the Smith form of a full-rank matrix.

    This is local Smith reduction over Z/(p^(v_p(det)+1)).  A returned tuple
    (1, 1, 3), for example, denotes Z/p + Z/p + Z/p^3.
    """
    determinant_valuation = 0
    remaining = abs(determinant)
    while remaining % prime == 0:
        determinant_valuation += 1
        remaining //= prime
    cutoff = determinant_valuation + 1
    modulus = prime**cutoff
    work = [[int(entry) % modulus for entry in row] for row in matrix]
    size = len(work)
    valuations: list[int] = []

    for start in range(size):
        valuation, pivot_row, pivot_column = min(
            (
                p_adic_valuation(work[row][column], prime, cutoff),
                row,
                column,
            )
            for row in range(start, size)
            for column in range(start, size)
        )
        if valuation == cutoff:
            break
        work[start], work[pivot_row] = work[pivot_row], work[start]
        for row in work:
            row[start], row[pivot_column] = row[pivot_column], row[start]

        prime_power = prime**valuation
        unit_modulus = prime ** (cutoff - valuation)
        unit = (work[start][start] // prime_power) % unit_modulus
        unit_inverse = pow(unit, -1, unit_modulus)

        for row in range(start + 1, size):
            quotient = (
                (work[row][start] // prime_power) * unit_inverse
            ) % unit_modulus
            for column in range(start, size):
                work[row][column] = (
                    work[row][column] - quotient * work[start][column]
                ) % modulus

        for column in range(start + 1, size):
            quotient = (
                (work[start][column] // prime_power) * unit_inverse
            ) % unit_modulus
            for row in range(start, size):
                work[row][column] = (
                    work[row][column] - quotient * work[row][start]
                ) % modulus
        valuations.append(valuation)

    positive = tuple(sorted(value for value in valuations if value))
    if sum(positive) != determinant_valuation:
        raise ArithmeticError("local Smith reduction lost determinant valuation")
    return positive


def discriminant_group_profile(
    matrix: Sequence[Sequence[int]], determinant: int
) -> tuple[tuple[int, tuple[int, ...]], ...]:
    """Complete primary exponent profile of the presented finite group."""
    return tuple(
        (prime, p_primary_exponents(matrix, prime, determinant))
        for prime in prime_divisors(determinant)
    )


def run_owens_scan(sheet: xlrd.sheet.Sheet) -> tuple[list[dict], dict]:
    obstructions: list[dict] = []
    eligible_signature_four = 0
    determinant_count = 0
    group_count = 0
    signature_six = 0
    signature_eight = 0
    oriented_zero_class_checks = collections.Counter()

    for row_number in range(2, sheet.nrows):
        interval = parse_interval(
            sheet.cell_value(row_number, COLUMNS["unknotting"])
        )
        if (
            interval is None
            or interval[0] >= interval[1]
            or str(sheet.cell_value(row_number, COLUMNS["alternating"])) != "Y"
        ):
            continue
        signature = abs(as_int(sheet.cell_value(row_number, COLUMNS["signature"])))
        lower = interval[0]
        if signature != 2 * lower or lower not in (2, 3, 4):
            continue
        pd = ast.literal_eval(str(sheet.cell_value(row_number, COLUMNS["pd"])))
        determinant = as_int(
            sheet.cell_value(row_number, COLUMNS["determinant"])
        )
        goeritz, dual = pd_goeritz_forms(pd)
        if abs(determinant_bareiss(goeritz)) != determinant:
            raise ValueError("Goeritz determinant mismatch")
        if abs(determinant_bareiss(dual)) != determinant:
            raise ValueError("dual Goeritz determinant mismatch")
        m4_values = {
            goeritz_zero_class_m4(goeritz),
            goeritz_zero_class_m4(dual),
        }
        required_m4 = -2 * lower
        # The correctly oriented spin correction term of an alternating knot
        # equals -sigma/4.  The two unsigned graph Laplacians correspond to
        # opposite boundary orientations, so one must realize required_m4.
        if required_m4 not in m4_values:
            raise ValueError("oriented zero-class identity failed")
        oriented_zero_class_checks[lower] += 1

        if lower == 3:
            signature_six += 1
            continue
        if lower == 4:
            signature_eight += 1
            continue

        eligible_signature_four += 1
        name = str(sheet.cell_value(row_number, COLUMNS["name"]))
        triples = owens_triples(determinant)
        if not triples:
            determinant_count += 1
            obstructions.append(
                {
                    "database_row": row_number + 1,
                    "knot": compact_name(name),
                    "knotinfo_name": name,
                    "input_interval": f"[{interval[0]},{interval[1]}]",
                    "output_interval": (
                        str(interval[1])
                        if interval[1] == 3
                        else f"[3,{interval[1]}]"
                    ),
                    "consequence": (
                        "exact u=3" if interval[1] == 3 else "improved"
                    ),
                    "certificate_type": "no Owens determinant solution",
                    "determinant": determinant,
                    "primes": json.dumps(prime_divisors(determinant)),
                    "goeritz_group_profile": "",
                    "owens_candidates": "[]",
                }
            )
            continue

        primes = prime_divisors(determinant)
        goeritz_profile = discriminant_group_profile(goeritz, determinant)
        candidates = []
        compatible = []
        for triple in triples:
            profile = discriminant_group_profile(
                owens_matrix(triple), determinant
            )
            item = {
                "triple": list(triple),
                "group_profile": [
                    [prime, list(exponents)] for prime, exponents in profile
                ],
            }
            candidates.append(item)
            if profile == goeritz_profile:
                compatible.append(item)
        if not compatible:
            group_count += 1
            obstructions.append(
                {
                    "database_row": row_number + 1,
                    "knot": compact_name(name),
                    "knotinfo_name": name,
                    "input_interval": f"[{interval[0]},{interval[1]}]",
                    "output_interval": (
                        str(interval[1])
                        if interval[1] == 3
                        else f"[3,{interval[1]}]"
                    ),
                    "consequence": "exact u=3" if interval[1] == 3 else "improved",
                    "certificate_type": "discriminant groups not isomorphic",
                    "determinant": determinant,
                    "primes": json.dumps(primes),
                    "goeritz_group_profile": json.dumps(
                        [
                            [prime, list(exponents)]
                            for prime, exponents in goeritz_profile
                        ],
                        separators=(",", ":"),
                    ),
                    "owens_candidates": json.dumps(candidates, separators=(",", ":")),
                }
            )

    summary = {
        "signature_four_eligible": eligible_signature_four,
        "zero_class_obstructions_after_orientation_check": 0,
        "determinant_obstructions": determinant_count,
        "group_obstructions": group_count,
        "total_obstructions": len(obstructions),
        "exact_u3": sum(
            item["consequence"] == "exact u=3" for item in obstructions
        ),
        "nonexact_improvements": sum(
            item["consequence"] == "improved" for item in obstructions
        ),
        "signature_six_eligible": signature_six,
        "signature_six_zero_class_obstructions": 0,
        "signature_eight_eligible": signature_eight,
        "signature_eight_zero_class_obstructions": 0,
        "oriented_zero_class_checks": {
            str(lower): count
            for lower, count in sorted(oriented_zero_class_checks.items())
        },
    }
    return obstructions, summary


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--tex", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("strengthening_results"))
    arguments = parser.parse_args()

    _book, sheet = read_rows(arguments.workbook)
    alexander_rows, alexander_summary = run_alexander_scan(sheet)
    owens_rows, owens_summary = run_owens_scan(sheet)

    output_dir = arguments.output_dir
    write_csv(output_dir / "alexander_module_certificates.csv", alexander_rows)
    write_csv(
        output_dir / "alexander_module_new_certificates.csv",
        [row for row in alexander_rows if not row["already_implied_by_workbook"]],
    )
    write_csv(output_dir / "owens_certificates.csv", owens_rows)
    summary = {
        "source_workbook": arguments.workbook.name,
        "source_tex": arguments.tex.name if arguments.tex else None,
        "alexander_module_scan": alexander_summary,
        "owens_scan": owens_summary,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
