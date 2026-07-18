#!/usr/bin/env python3
"""Determinant screen for two crossing changes in minimal alternating diagrams.

For every ten-crossing KnotInfo entry whose unknotting interval is [2,3],
the script reads the supplied minimal alternating PD code, reconstructs a
Tait graph, flips the Goeritz incidence signs at each pair of crossings, and
computes the determinant of the changed diagram exactly.  A determinant
different from one certifies that the changed diagram is not the unknot.

The calculation is a screen: pairs with determinant one require a stronger
polynomial or recognition test.  The source workbook is never modified.
"""

from __future__ import annotations

import argparse
import ast
import collections
import itertools
import json
from pathlib import Path
from typing import Sequence

import xlrd

from knotinfo_strengthening_scan import (
    COLUMNS,
    as_int,
    determinant_bareiss,
    parse_interval,
)


def tait_graph(pd: Sequence[Sequence[int]], chosen_color: int = 0) -> dict[str, object]:
    """Return vertices and crossing-indexed edges of one checkerboard graph."""
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

    vertices = [i for i, value in enumerate(color) if value == chosen_color]
    index = {vertex: i for i, vertex in enumerate(vertices)}
    edges: list[tuple[int, int]] = []
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
        edges.append((index[incident[0]], index[incident[1]]))
    return {"vertex_count": len(vertices), "edges": edges}


def signed_goeritz(
    vertex_count: int,
    edges: Sequence[tuple[int, int]],
    changed_crossings: set[int],
) -> list[list[int]]:
    laplacian = [[0] * vertex_count for _ in range(vertex_count)]
    for crossing, (first, second) in enumerate(edges):
        weight = -1 if crossing in changed_crossings else 1
        laplacian[first][first] += weight
        laplacian[second][second] += weight
        laplacian[first][second] -= weight
        laplacian[second][first] -= weight
    return [row[:-1] for row in laplacian[:-1]]


def candidate_rows(sheet: xlrd.sheet.Sheet) -> list[int]:
    return [
        row
        for row in range(2, sheet.nrows)
        if str(sheet.cell_value(row, COLUMNS["name"])).startswith("10_")
        and parse_interval(sheet.cell_value(row, COLUMNS["unknotting"])) == (2, 3)
    ]


def analyze_row(sheet: xlrd.sheet.Sheet, row: int) -> dict[str, object]:
    name = str(sheet.cell_value(row, COLUMNS["name"]))
    determinant = as_int(sheet.cell_value(row, COLUMNS["determinant"]))
    pd = ast.literal_eval(str(sheet.cell_value(row, COLUMNS["pd"])))
    graph = tait_graph(pd)
    vertex_count = int(graph["vertex_count"])
    edges = list(graph["edges"])
    original_goeritz = signed_goeritz(vertex_count, edges, set())
    original_determinant = abs(determinant_bareiss(original_goeritz))
    if original_determinant != determinant:
        raise ArithmeticError(
            f"{name}: original determinant {original_determinant} != {determinant}"
        )

    pairs: list[dict[str, object]] = []
    for first, second in itertools.combinations(range(len(pd)), 2):
        changed = {first, second}
        goeritz = signed_goeritz(vertex_count, edges, changed)
        changed_determinant = abs(determinant_bareiss(goeritz))
        pairs.append(
            {
                "positions_1_based": [first + 1, second + 1],
                "determinant": changed_determinant,
                "determinant_obstructs_unknot": changed_determinant != 1,
            }
        )

    unresolved = [item for item in pairs if not item["determinant_obstructs_unknot"]]
    return {
        "knot": name,
        "database_row": row + 1,
        "crossing_count": len(pd),
        "determinant": determinant,
        "tait_vertex_count": vertex_count,
        "tait_edges_by_crossing": [list(edge) for edge in edges],
        "pairs_tested": len(pairs),
        "pairs_obstructed_by_determinant": len(pairs) - len(unresolved),
        "determinant_one_pairs": unresolved,
        "all_pairs_obstructed_by_determinant": not unresolved,
        "all_pairs": pairs,
    }


def validation_case(
    sheet: xlrd.sheet.Sheet, knot_name: str, expected_determinant_one_pairs: int
) -> dict[str, object]:
    row = next(
        row
        for row in range(2, sheet.nrows)
        if str(sheet.cell_value(row, COLUMNS["name"])) == knot_name
    )
    pd = ast.literal_eval(str(sheet.cell_value(row, COLUMNS["pd"])))
    graph = tait_graph(pd)
    determinant_one_pairs = [
        [first + 1, second + 1]
        for first, second in itertools.combinations(range(len(pd)), 2)
        if abs(
            determinant_bareiss(
                signed_goeritz(
                    int(graph["vertex_count"]),
                    list(graph["edges"]),
                    {first, second},
                )
            )
        )
        == 1
    ]
    return {
        "knot": knot_name,
        "pairs_tested": len(pd) * (len(pd) - 1) // 2,
        "determinant_one_pairs": determinant_one_pairs,
        "expected_determinant_one_pair_count": expected_determinant_one_pairs,
        "passed": len(determinant_one_pairs) == expected_determinant_one_pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()

    book = xlrd.open_workbook(str(arguments.workbook), on_demand=True)
    sheet = book.sheet_by_name("sample_dat")
    validations = [
        validation_case(sheet, "5_1", 10),
        validation_case(sheet, "7_1", 0),
    ]
    if not all(item["passed"] for item in validations):
        raise ArithmeticError("a built-in signed-Goeritz validation failed")
    knots = [analyze_row(sheet, row) for row in candidate_rows(sheet)]
    results = {
        "source_workbook": arguments.workbook.name,
        "method": "signed-Goeritz determinant screen for two changes in the supplied minimal diagrams",
        "validation_cases": validations,
        "knots": knots,
    }
    rendered = json.dumps(results, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
