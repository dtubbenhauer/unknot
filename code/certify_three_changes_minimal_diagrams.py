#!/usr/bin/env python3
"""Certify three-change unknotting witnesses in minimal PD diagrams.

For every ten-crossing KnotInfo row with unknotting interval [2,3], this
script searches triples of crossings in the supplied minimal PD diagram.
It first applies the exact signed-Goeritz determinant screen.  For each
determinant-one triple it constructs a Wirtinger presentation of the changed
diagram and performs explicit Tietze eliminations.  Reduction to one free
generator is a certificate that the changed knot is the unknot.

The same presentation code is checked on the standard diagrams of 3_1,
4_1, 5_1 and 7_1.  The source workbook is never modified.
"""

from __future__ import annotations

import argparse
import ast
import itertools
import json
from pathlib import Path
from typing import Iterable, Sequence

import xlrd

from exhaust_two_changes_minimal_diagrams import (
    candidate_rows,
    signed_goeritz,
    tait_graph,
)
from knotinfo_strengthening_scan import COLUMNS, determinant_bareiss


Word = list[int]


class UnionFind:
    def __init__(self, elements: Iterable[int]) -> None:
        self.parent = {int(element): int(element) for element in elements}

    def find(self, element: int) -> int:
        parent = self.parent[element]
        if parent != element:
            self.parent[element] = self.find(parent)
        return self.parent[element]

    def union(self, first: int, second: int) -> None:
        first_root = self.find(first)
        second_root = self.find(second)
        if first_root == second_root:
            return
        if first_root < second_root:
            self.parent[second_root] = first_root
        else:
            self.parent[first_root] = second_root


def successor(label: int, edge_count: int) -> int:
    return label % edge_count + 1


def change_crossing(labels: Sequence[int], edge_count: int) -> list[int]:
    """Rotate a KnotTheory PD crossing after interchanging over and under."""
    incoming_under, first_upper, outgoing_under, second_upper = map(int, labels)
    if successor(incoming_under, edge_count) != outgoing_under:
        raise ValueError("PD under-strand orientation is inconsistent")
    if successor(second_upper, edge_count) == first_upper:
        # The old upper strand is second_upper -> first_upper.
        return [second_upper, incoming_under, first_upper, outgoing_under]
    if successor(first_upper, edge_count) == second_upper:
        # The old upper strand is first_upper -> second_upper.
        return [first_upper, outgoing_under, second_upper, incoming_under]
    raise ValueError("PD upper-strand orientation is inconsistent")


def changed_pd(
    pd: Sequence[Sequence[int]], changed_crossings: set[int]
) -> list[list[int]]:
    edge_count = 2 * len(pd)
    return [
        change_crossing(labels, edge_count)
        if crossing in changed_crossings
        else list(map(int, labels))
        for crossing, labels in enumerate(pd)
    ]


def inverse_word(word: Sequence[int]) -> Word:
    return [-letter for letter in reversed(word)]


def freely_reduce(word: Sequence[int], cyclic: bool = True) -> Word:
    reduced: Word = []
    for letter in word:
        if reduced and reduced[-1] == -letter:
            reduced.pop()
        else:
            reduced.append(int(letter))
    if cyclic:
        while len(reduced) > 1 and reduced[0] == -reduced[-1]:
            reduced = reduced[1:-1]
    return reduced


def substitute(word: Sequence[int], generator: int, replacement: Word) -> Word:
    result: Word = []
    replacement_inverse = inverse_word(replacement)
    for letter in word:
        if letter == generator:
            result.extend(replacement)
        elif letter == -generator:
            result.extend(replacement_inverse)
        else:
            result.append(letter)
    return freely_reduce(result)


def wirtinger_presentation(pd: Sequence[Sequence[int]]) -> dict[str, object]:
    """Construct a Wirtinger presentation from an oriented KnotTheory PD."""
    edge_count = 2 * len(pd)
    labels = range(1, edge_count + 1)
    arcs = UnionFind(labels)
    for crossing in pd:
        arcs.union(int(crossing[1]), int(crossing[3]))

    roots = sorted({arcs.find(label) for label in labels})
    generator_for_root = {root: index + 1 for index, root in enumerate(roots)}
    generator_by_label = {
        label: generator_for_root[arcs.find(label)] for label in labels
    }
    labels_by_generator = {
        generator: [
            label for label in labels if generator_by_label[label] == generator
        ]
        for generator in generator_for_root.values()
    }

    relators: list[Word] = []
    for incoming_under, first_upper, outgoing_under, second_upper in pd:
        incoming = generator_by_label[int(incoming_under)]
        outgoing = generator_by_label[int(outgoing_under)]
        upper = generator_by_label[int(first_upper)]
        if successor(int(second_upper), edge_count) == int(first_upper):
            # One global choice of Wirtinger sign convention.
            relator = [-outgoing, -upper, incoming, upper]
        elif successor(int(first_upper), edge_count) == int(second_upper):
            relator = [-outgoing, upper, incoming, -upper]
        else:
            raise ValueError("PD upper-strand orientation is inconsistent")
        relators.append(freely_reduce(relator))

    return {
        "generators": sorted(generator_for_root.values()),
        "labels_by_generator": labels_by_generator,
        "relators": relators,
    }


def tietze_reduce(presentation: dict[str, object]) -> dict[str, object]:
    """Eliminate generators that occur once in a relator, recording steps."""
    generators = set(map(int, presentation["generators"]))
    relators = [freely_reduce(word) for word in presentation["relators"]]
    relators = [word for word in relators if word]
    steps: list[dict[str, object]] = []

    while True:
        choice: tuple[int, int, int] | None = None
        for relator_index, relator in enumerate(relators):
            for generator in sorted(generators):
                positions = [
                    index
                    for index, letter in enumerate(relator)
                    if abs(letter) == generator
                ]
                if len(positions) == 1:
                    choice = (relator_index, generator, positions[0])
                    break
            if choice is not None:
                break
        if choice is None:
            break

        relator_index, generator, position = choice
        relator = relators[relator_index]
        rotated = relator[position:] + relator[:position]
        occurrence = rotated[0]
        rest = rotated[1:]
        replacement = (
            inverse_word(rest) if occurrence == generator else list(rest)
        )
        replacement = freely_reduce(replacement, cyclic=False)
        steps.append(
            {
                "eliminated_generator": generator,
                "using_relator": relator,
                "replacement_word": replacement,
            }
        )

        relators = [
            substitute(other, generator, replacement)
            for index, other in enumerate(relators)
            if index != relator_index
        ]
        relators = [word for word in relators if word]
        generators.remove(generator)

    return {
        "remaining_generators": sorted(generators),
        "remaining_relators": relators,
        "elimination_steps": steps,
        "reduces_to_infinite_cyclic": len(generators) == 1 and not relators,
    }


def determinant_of_changes(
    graph: dict[str, object], changed_crossings: set[int]
) -> int:
    matrix = signed_goeritz(
        int(graph["vertex_count"]),
        list(graph["edges"]),
        changed_crossings,
    )
    return abs(determinant_bareiss(matrix))


def certify_changes(
    pd: Sequence[Sequence[int]], changed_crossings: set[int]
) -> dict[str, object]:
    modified = changed_pd(pd, changed_crossings)
    presentation = wirtinger_presentation(modified)
    reduction = tietze_reduce(presentation)
    return {
        "positions_1_based": [position + 1 for position in sorted(changed_crossings)],
        "changed_pd": modified,
        "wirtinger_presentation": presentation,
        "tietze_reduction": reduction,
    }


def analyze_row(sheet: xlrd.sheet.Sheet, row: int) -> dict[str, object]:
    name = str(sheet.cell_value(row, COLUMNS["name"]))
    pd = ast.literal_eval(str(sheet.cell_value(row, COLUMNS["pd"])))
    graph = tait_graph(pd)
    determinant_one_triples = 0
    witness: dict[str, object] | None = None
    for triple in itertools.combinations(range(len(pd)), 3):
        changed = set(triple)
        if determinant_of_changes(graph, changed) != 1:
            continue
        determinant_one_triples += 1
        certificate = certify_changes(pd, changed)
        if certificate["tietze_reduction"]["reduces_to_infinite_cyclic"]:
            witness = certificate
            break
    if witness is None:
        # Finish the determinant-one count for diagnostic output if no witness
        # has been found; normally the loop above exits at the first witness.
        determinant_one_triples = sum(
            determinant_of_changes(graph, set(triple)) == 1
            for triple in itertools.combinations(range(len(pd)), 3)
        )
    return {
        "knot": name,
        "database_row": row + 1,
        "crossing_count": len(pd),
        "determinant_one_triples_examined_through_witness": determinant_one_triples,
        "three_change_unknot_certificate": witness,
        "witness_found": witness is not None,
    }


def workbook_row(sheet: xlrd.sheet.Sheet, name: str) -> int:
    return next(
        row
        for row in range(2, sheet.nrows)
        if str(sheet.cell_value(row, COLUMNS["name"])) == name
    )


def validation_cases(sheet: xlrd.sheet.Sheet) -> list[dict[str, object]]:
    cases = [
        ("3_1", set(), False),
        ("3_1", {0}, True),
        ("4_1", set(), False),
        ("4_1", {0}, True),
        ("5_1", set(), False),
        ("5_1", {0, 1}, True),
        ("7_1", {0, 1}, False),
        ("7_1", {0, 1, 2}, True),
    ]
    results: list[dict[str, object]] = []
    for name, changed, expected in cases:
        row = workbook_row(sheet, name)
        pd = ast.literal_eval(str(sheet.cell_value(row, COLUMNS["pd"])))
        certificate = certify_changes(pd, changed)
        actual = bool(
            certificate["tietze_reduction"]["reduces_to_infinite_cyclic"]
        )
        results.append(
            {
                "knot": name,
                "positions_1_based": [position + 1 for position in sorted(changed)],
                "expected_reduction_to_Z": expected,
                "actual_reduction_to_Z": actual,
                "passed": actual == expected,
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quiet", action="store_true")
    arguments = parser.parse_args()

    book = xlrd.open_workbook(str(arguments.workbook), on_demand=True)
    sheet = book.sheet_by_name("sample_dat")
    validations = validation_cases(sheet)
    if not all(item["passed"] for item in validations):
        raise ArithmeticError("a built-in Wirtinger/Tietze validation failed")
    knots = [analyze_row(sheet, row) for row in candidate_rows(sheet)]
    results = {
        "source_workbook": arguments.workbook.name,
        "method": "signed-Goeritz triple screen followed by Wirtinger/Tietze unknot certificates",
        "validation_cases": validations,
        "knots": knots,
    }
    rendered = json.dumps(results, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")
    if not arguments.quiet:
        print(rendered, end="")


if __name__ == "__main__":
    main()
