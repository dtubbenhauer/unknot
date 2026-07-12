#!/usr/bin/env python3
"""Exact signature-sharp zero-class scan for alternating knots.

The input is the complete pipe-delimited KnotInfo CSV.  For a chosen k, the
program filters to alternating knots with unknotting interval [k,b], b>k, and
absolute signature 2k.  It reconstructs the signed checkerboard Goeritz forms
from the PD code, mirrors when necessary to arrange positive signature, selects
the positive-definite form, checks its determinant, and computes

    m_G(0) = (p^T G p - rank(G))/4,

where Gp = diag(G) modulo two.  Owens' signature-sharp obstruction forces the
comparison value m_Q(0)=-k/2 if u(K)=k.  Failure of the zero-class inequality or
congruence therefore obstructs u(K)=k.

Only the Python standard library is used; all arithmetic is exact.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

Matrix = List[List[int]]
Corner = Tuple[int, int]
State = Dict[str, object]


def parse_interval(value: str):
    match = re.fullmatch(r"\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*", str(value or ""))
    return (int(match.group(1)), int(match.group(2))) if match else None


def parse_pd(value: str) -> List[List[int]]:
    pd = ast.literal_eval(value)
    if not isinstance(pd, list) or not pd or any(
        not isinstance(x, list) or len(x) != 4 for x in pd
    ):
        raise ValueError("PD notation is not a nonempty list of four-tuples")
    return [[int(y) for y in x] for x in pd]


def determinant_bareiss(matrix: Matrix) -> int:
    n = len(matrix)
    if n == 0:
        return 1
    a = [row[:] for row in matrix]
    sign = 1
    previous = 1
    for k in range(n - 1):
        if a[k][k] == 0:
            pivot = next((i for i in range(k + 1, n) if a[i][k] != 0), None)
            if pivot is None:
                return 0
            a[k], a[pivot] = a[pivot], a[k]
            sign *= -1
        pivot_value = a[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                numerator = a[i][j] * pivot_value - a[i][k] * a[k][j]
                if previous != 1:
                    if numerator % previous:
                        raise ArithmeticError("Bareiss division was not exact")
                    numerator //= previous
                a[i][j] = numerator
        previous = pivot_value
        for i in range(k + 1, n):
            a[i][k] = 0
    return sign * a[n - 1][n - 1]


def leading_principal(matrix: Matrix, size: int) -> Matrix:
    return [row[:size] for row in matrix[:size]]


def is_positive_definite(matrix: Matrix) -> bool:
    return all(
        determinant_bareiss(leading_principal(matrix, k)) > 0
        for k in range(1, len(matrix) + 1)
    )


def is_negative_definite(matrix: Matrix) -> bool:
    return is_positive_definite([[-x for x in row] for row in matrix])


def crossing_signs(pd: Sequence[Sequence[int]]) -> List[int]:
    modulus = 2 * len(pd)
    signs = []
    for crossing in pd:
        b, d = crossing[1], crossing[3]
        if b == d % modulus + 1:
            signs.append(1)
        elif d == b % modulus + 1:
            signs.append(-1)
        else:
            raise ValueError(f"PD orientation convention failed at crossing {crossing}")
    return signs


def link_state_from_pd(pd: Sequence[Sequence[int]]) -> State:
    occurrences: Dict[int, List[Corner]] = {}
    for crossing_index, crossing in enumerate(pd):
        for entry, label in enumerate(crossing):
            occurrences.setdefault(label, []).append((crossing_index, entry))
    adjacency: Dict[Corner, Corner] = {}
    for label, pair in occurrences.items():
        if len(pair) != 2:
            raise ValueError(f"PD label {label} occurs {len(pair)} times")
        left, right = pair
        adjacency[left] = right
        adjacency[right] = left
    return {"n": len(pd), "adj": adjacency, "signs": crossing_signs(pd)}


def mirror_state(state: State) -> State:
    n = int(state["n"])
    old_adjacency: Dict[Corner, Corner] = state["adj"]  # type: ignore[assignment]
    old_signs: List[int] = state["signs"]  # type: ignore[assignment]
    new_adjacency: Dict[Corner, Corner] = {}

    def convert(corner: Corner) -> Corner:
        crossing, entry = corner
        return crossing, (entry + old_signs[crossing]) % 4

    for crossing in range(n):
        entries = (0, 3) if old_signs[crossing] == 1 else (0, 1)
        for entry in entries:
            other = old_adjacency[(crossing, entry)]
            left = convert(other)
            right = convert((crossing, entry))
            new_adjacency[left] = right
            new_adjacency[right] = left
    if len(new_adjacency) != 4 * n:
        raise ValueError("Mirror reconstruction did not connect every crossing entry")
    return {"n": n, "adj": new_adjacency, "signs": [-s for s in old_signs]}


def faces_from_state(state: State):
    n = int(state["n"])
    adjacency: Dict[Corner, Corner] = state["adj"]  # type: ignore[assignment]
    unseen: Set[Corner] = {
        (crossing, entry) for crossing in range(n) for entry in range(4)
    }
    faces: List[List[Corner]] = []
    face_of: Dict[Corner, int] = {}
    while unseen:
        start = min(unseen)
        current = start
        face: List[Corner] = []
        while True:
            unseen.remove(current)
            face_of[current] = len(faces)
            face.append(current)
            crossing, entry = current
            current = adjacency[(crossing, (entry + 1) % 4)]
            if current == start:
                break
        faces.append(face)
    return faces, face_of


def checkerboard_components(state: State):
    n = int(state["n"])
    faces, face_of = faces_from_state(state)
    edges = []
    for crossing in range(n):
        edges.append((face_of[(crossing, 0)], face_of[(crossing, 2)], 1, crossing))
        edges.append((face_of[(crossing, 1)], face_of[(crossing, 3)], -1, crossing))

    neighbours: Dict[int, Set[int]] = {i: set() for i in range(len(faces))}
    for left, right, _, _ in edges:
        neighbours[left].add(right)
        neighbours[right].add(left)

    components: List[Set[int]] = []
    unseen = set(neighbours)
    while unseen:
        root = min(unseen)
        stack = [root]
        component: Set[int] = set()
        while stack:
            vertex = stack.pop()
            if vertex in component:
                continue
            component.add(vertex)
            unseen.discard(vertex)
            stack.extend(neighbours[vertex] - component)
        components.append(component)
    components.sort(key=lambda component: (-len(component), tuple(sorted(component))))
    return edges, components


def goeritz_for_component(state: State, component: Set[int]):
    edges, _ = checkerboard_components(state)
    vertices = sorted(component)
    index = {vertex: i for i, vertex in enumerate(vertices)}
    full = [[0 for _ in vertices] for _ in vertices]
    component_edges = []
    for left, right, sign, crossing in edges:
        if left in component and right in component:
            i, j = index[left], index[right]
            full[i][j] += sign
            full[j][i] += sign
            component_edges.append((left, right, sign, crossing))
    for i in range(len(vertices)):
        full[i][i] = -sum(full[j][i] for j in range(len(vertices)) if j != i)
    reduced = [row[1:] for row in full[1:]]
    return reduced, component_edges


def checkerboard_data(state: State):
    _, components = checkerboard_components(state)
    crossing_sign_list: List[int] = state["signs"]  # type: ignore[assignment]
    output = []
    for component in components:
        matrix, edges = goeritz_for_component(state, component)
        if is_positive_definite(matrix):
            matrix_signature = len(matrix)
        elif is_negative_definite(matrix):
            matrix_signature = -len(matrix)
        else:
            raise ValueError("Alternating checkerboard Goeritz matrix was not definite")
        correction = sum(
            sign
            for _, _, sign, crossing in edges
            if sign == crossing_sign_list[crossing]
        )
        knot_signature = -(matrix_signature + correction)
        output.append(
            {"signature": knot_signature, "matrix": matrix, "correction": correction}
        )
    return output


def solve_mod_two(matrix: Matrix, vector: Sequence[int]) -> List[int]:
    n = len(matrix)
    augmented = [
        [matrix[i][j] & 1 for j in range(n)] + [int(vector[i]) & 1]
        for i in range(n)
    ]
    row = 0
    pivots: List[int] = []
    for column in range(n):
        pivot = next((i for i in range(row, n) if augmented[i][column]), None)
        if pivot is None:
            continue
        augmented[row], augmented[pivot] = augmented[pivot], augmented[row]
        for i in range(n):
            if i != row and augmented[i][column]:
                augmented[i] = [x ^ y for x, y in zip(augmented[i], augmented[row])]
        pivots.append(column)
        row += 1
    if row != n:
        raise ValueError("Goeritz matrix is singular modulo two")
    solution = [0] * n
    for i, column in enumerate(pivots):
        solution[column] = augmented[i][-1]
    return solution


def quadratic_energy(matrix: Matrix, vector: Sequence[int]) -> int:
    return sum(
        vector[i] * matrix[i][j] * vector[j]
        for i in range(len(matrix))
        for j in range(len(matrix))
    )


def zero_class_value(matrix: Matrix):
    parity = solve_mod_two(matrix, [matrix[i][i] for i in range(len(matrix))])
    energy = quadratic_energy(matrix, parity)
    return Fraction(energy - len(matrix), 4), parity, energy


def choose_positive_goeritz(pd: Sequence[Sequence[int]], signature: int):
    state = link_state_from_pd(pd)
    mirrored = signature < 0
    if mirrored:
        state = mirror_state(state)
    checkerboards = checkerboard_data(state)
    expected = abs(signature)
    if any(item["signature"] != expected for item in checkerboards):
        raise ValueError(
            f"Gordon-Litherland signature mismatch: expected {expected}, "
            f"got {[item['signature'] for item in checkerboards]}"
        )
    positive = [item for item in checkerboards if is_positive_definite(item["matrix"])]
    if len(positive) != 1:
        raise ValueError(f"Expected one positive Goeritz matrix, found {len(positive)}")
    return positive[0]["matrix"], mirrored


def knot_sort_key(name: str):
    normalized = name.replace("_", "")
    match = re.fullmatch(r"(\d+)([an]?)(\d+)", normalized)
    if match:
        type_order = {"": 0, "a": 1, "n": 2}[match.group(2)]
        return int(match.group(1)), type_order, int(match.group(3))
    return 10**9, 10**9, normalized


def read_knotinfo(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="|"))


def validate_all_alternating(rows) -> int:
    checked = 0
    for row in rows:
        if row.get("alternating") != "Y" or not row.get("pd_notation") or not row.get("signature"):
            continue
        try:
            signature = int(row["signature"])
            pd = parse_pd(row["pd_notation"])
        except (ValueError, SyntaxError):
            continue
        reconstructed = [
            item["signature"] for item in checkerboard_data(link_state_from_pd(pd))
        ]
        if any(value != signature for value in reconstructed):
            raise ValueError(
                f"Signature validation failed for {row.get('name')}: "
                f"recorded {signature}, reconstructed {reconstructed}"
            )
        checked += 1
    return checked


def run_scan(rows, k: int):
    results = []
    for row in rows:
        interval = parse_interval(row.get("unknotting_number", ""))
        if row.get("alternating") != "Y" or interval is None:
            continue
        lower, upper = interval
        if lower != k or upper <= k:
            continue
        signature = int(row["signature"])
        if abs(signature) != 2 * k:
            continue
        pd = parse_pd(row["pd_notation"])
        matrix, mirrored = choose_positive_goeritz(pd, signature)
        recorded_determinant = int(row["determinant"])
        computed_determinant = determinant_bareiss(matrix)
        if computed_determinant != recorded_determinant:
            raise ValueError(
                f"Determinant mismatch for {row['name']}: "
                f"{computed_determinant} != {recorded_determinant}"
            )
        m_g, parity, energy = zero_class_value(matrix)
        m_q = Fraction(-k, 2)
        inequality_ok = m_q >= m_g
        difference = m_q - m_g
        congruence_ok = difference.denominator == 1 and int(difference) % 2 == 0
        obstructs = not (inequality_ok and congruence_ok)
        results.append(
            {
                "knot": row["name"],
                "crossing_number": int(row["crossing_number"]),
                "input_interval": f"[{lower},{upper}]",
                "signature_input": signature,
                "mirrored_to_positive_signature": mirrored,
                "determinant": recorded_determinant,
                "goeritz_rank": len(matrix),
                "m_G_zero": str(m_g),
                "m_Q_zero": str(m_q),
                "inequality_ok": inequality_ok,
                "congruence_ok": congruence_ok,
                f"obstructs_u_{k}": obstructs,
                "new_interval": str(k + 1)
                if upper == k + 1 and obstructs
                else (f"[{k + 1},{upper}]" if obstructs else f"[{lower},{upper}]"),
                "zero_energy": energy,
                "zero_characteristic_parity": json.dumps(parity, separators=(",", ":")),
                "goeritz_matrix": json.dumps(matrix, separators=(",", ":")),
                "pd_notation": json.dumps(pd, separators=(",", ":")),
            }
        )
    results.sort(key=lambda item: knot_sort_key(item["knot"]))
    return results


def write_csv(path: Path, results, k: int):
    fields = [
        "knot",
        "crossing_number",
        "input_interval",
        "signature_input",
        "mirrored_to_positive_signature",
        "determinant",
        "goeritz_rank",
        "m_G_zero",
        "m_Q_zero",
        "inequality_ok",
        "congruence_ok",
        f"obstructs_u_{k}",
        "new_interval",
        "zero_energy",
        "zero_characteristic_parity",
        "goeritz_matrix",
        "pd_notation",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)



def locate_knotinfo_csv() -> Path:
    try:
        import database_knotinfo
    except ImportError as exc:
        raise RuntimeError("Install database-knotinfo or pass input_csv explicitly") from exc
    root = Path(database_knotinfo.__file__).resolve().parent
    matches = list(root.rglob("knotinfo_data_complete.csv"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one KnotInfo CSV, found {matches}")
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path, nargs="?", help="complete pipe-delimited KnotInfo CSV; defaults to database-knotinfo")
    parser.add_argument("--k", type=int, required=True, help="lower endpoint k (signature must be 2k)")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output CSV path")
    parser.add_argument("--summary", type=Path, help="optional JSON summary path")
    parser.add_argument(
        "--validate-all-alternating",
        action="store_true",
        help="reconstruct signatures for every alternating row before scanning",
    )
    args = parser.parse_args()
    if args.k < 1:
        parser.error("--k must be positive")

    input_csv = args.input_csv or locate_knotinfo_csv()
    rows = read_knotinfo(input_csv)
    validated = validate_all_alternating(rows) if args.validate_all_alternating else None
    results = run_scan(rows, args.k)
    write_csv(args.output, results, args.k)

    interval_counts: Dict[str, int] = {}
    crossing_counts: Dict[int, int] = {}
    for result in results:
        interval_counts[result["input_interval"]] = interval_counts.get(result["input_interval"], 0) + 1
        crossing_counts[result["crossing_number"]] = crossing_counts.get(result["crossing_number"], 0) + 1
    summary = {
        "k": args.k,
        "required_absolute_signature": 2 * args.k,
        "raw_csv_rows_after_header": len(rows),
        "data_rows": sum(1 for row in rows if row.get("name") != "Name"),
        "alternating_signatures_validated": validated,
        "eligible_targets": len(results),
        f"obstructed_u_{args.k}": sum(bool(item[f"obstructs_u_{args.k}"]) for item in results),
        "m_G_zero_values": sorted(set(item["m_G_zero"] for item in results)),
        "m_Q_zero": str(Fraction(-args.k, 2)),
        "input_intervals": interval_counts,
        "crossing_numbers": crossing_counts,
        "output_csv": str(args.output),
    }
    if args.summary:
        args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
