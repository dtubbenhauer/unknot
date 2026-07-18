#!/usr/bin/env python3
"""Verify every positive complete-scan witness in the original Seifert matrix.

The elementary-ideal scan works with unit-reduced presentations.  This script
independently evaluates each recorded witness in the unreduced KnotInfo matrix
and performs exact Gaussian elimination in F_p[x]/(h).
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import xlrd

from knotinfo_strengthening_scan import COLUMNS


ROOT = Path(__file__).resolve().parents[1]
Element = tuple[int, ...]


@dataclass(frozen=True)
class FiniteField:
    prime: int
    modulus: tuple[int, ...]

    def __post_init__(self) -> None:
        degree = len(self.modulus) - 1
        if degree < 1 or self.modulus[-1] % self.prime != 1:
            raise ValueError("the modulus must be monic and nonconstant")
        object.__setattr__(self, "degree", degree)
        object.__setattr__(self, "order", self.prime**degree)
        object.__setattr__(self, "zero", (0,) * degree)
        object.__setattr__(self, "one", (1,) + (0,) * (degree - 1))
        alpha = ((-self.modulus[0]) % self.prime,) if degree == 1 else (0, 1) + (0,) * (degree - 2)
        object.__setattr__(self, "alpha", alpha)

    def constant(self, value: int) -> Element:
        return (value % self.prime,) + (0,) * (self.degree - 1)

    def add(self, left: Element, right: Element) -> Element:
        return tuple((a + b) % self.prime for a, b in zip(left, right))

    def subtract(self, left: Element, right: Element) -> Element:
        return tuple((a - b) % self.prime for a, b in zip(left, right))

    def multiply(self, left: Element, right: Element) -> Element:
        degree = self.degree
        product = [0] * (2 * degree - 1)
        for i, a in enumerate(left):
            for j, b in enumerate(right):
                product[i + j] = (product[i + j] + a * b) % self.prime
        for power in range(2 * degree - 2, degree - 1, -1):
            coefficient = product[power] % self.prime
            if not coefficient:
                continue
            for j in range(degree):
                product[power - degree + j] = (
                    product[power - degree + j] - coefficient * self.modulus[j]
                ) % self.prime
        return tuple(product[:degree])

    def power(self, value: Element, exponent: int) -> Element:
        result = self.one
        base = value
        while exponent:
            if exponent & 1:
                result = self.multiply(result, base)
            base = self.multiply(base, base)
            exponent >>= 1
        return result

    def inverse(self, value: Element) -> Element:
        if value == self.zero:
            raise ZeroDivisionError("zero has no inverse")
        return self.power(value, self.order - 2)


def specialized_matrix(seifert: Sequence[Sequence[int]], field: FiniteField) -> list[list[Element]]:
    size = len(seifert)
    return [
        [
            field.subtract(
                field.multiply(field.constant(int(seifert[row][column])), field.alpha),
                field.constant(int(seifert[column][row])),
            )
            for column in range(size)
        ]
        for row in range(size)
    ]


def rank(matrix: list[list[Element]], field: FiniteField) -> int:
    work = [[entry for entry in row] for row in matrix]
    nrows = len(work)
    ncols = len(work[0]) if work else 0
    result = 0
    for column in range(ncols):
        pivot = next((row for row in range(result, nrows) if work[row][column] != field.zero), None)
        if pivot is None:
            continue
        work[result], work[pivot] = work[pivot], work[result]
        inverse = field.inverse(work[result][column])
        work[result] = [field.multiply(entry, inverse) for entry in work[result]]
        for row in range(nrows):
            if row == result:
                continue
            coefficient = work[row][column]
            if coefficient != field.zero:
                work[row] = [
                    field.subtract(entry, field.multiply(coefficient, pivot_entry))
                    for entry, pivot_entry in zip(work[row], work[result])
                ]
        result += 1
        if result == nrows:
            break
    return result


def run(workbook: Path, scan_path: Path, output: Path) -> None:
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    targets = [row for row in scan["results"] if int(row["complete_finite_field_index"]) >= 2]
    book = xlrd.open_workbook(str(workbook), on_demand=True)
    sheet = book.sheet_by_index(0)
    records: list[dict[str, object]] = []
    try:
        for row in targets:
            witness = row["witness"]
            if not isinstance(witness, dict):
                raise ValueError(f"missing witness for {row['knot']}")
            prime = int(witness["prime"])
            coefficients = tuple(int(value) % prime for value in witness["minimal_polynomial_coefficients"])
            field = FiniteField(prime, coefficients)
            database_row = int(row["database_row"])
            seifert = ast.literal_eval(str(sheet.cell_value(database_row - 1, COLUMNS["seifert"])).strip())
            computed_rank = rank(specialized_matrix(seifert, field), field)
            nullity = len(seifert) - computed_rank
            expected = int(row["complete_finite_field_index"])
            passed = nullity == expected
            records.append(
                {
                    "database_row": database_row,
                    "knot": row["knot"],
                    "matrix_size": len(seifert),
                    "prime": prime,
                    "extension_degree": field.degree,
                    "field_order": field.order,
                    "rank": computed_rank,
                    "nullity": nullity,
                    "expected_index": expected,
                    "passed": passed,
                }
            )
            if not passed:
                raise ValueError(f"direct witness verification failed for {row['knot']}")
    finally:
        book.release_resources()

    payload = {
        "summary": {
            "complete_scan_file": scan_path.name,
            "witnesses_checked": len(records),
            "all_passed": all(record["passed"] for record in records),
        },
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument(
        "--scan",
        type=Path,
        default=ROOT / "lower_bounds" / "alexander_module" / "complete_scan.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "direct_rank_verification.json",
    )
    arguments = parser.parse_args()
    run(arguments.workbook, arguments.scan, arguments.output)


if __name__ == "__main__":
    main()
