#!/usr/bin/env python3
"""Small exact invariant helpers used by the repository verification scripts.

The Jones vector convention is

    [minimum_degree, maximum_degree, coefficients from low to high]

for the variable t with V_unknot(t)=1.  Alexander vectors are normalized up
to multiplication by a unit so that the minimum degree is zero and the first
nonzero coefficient is positive.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import sympy as sp
from spherogram import Link


class DSU:
    def __init__(self) -> None:
        self.parent: dict[int, int] = {}

    def find(self, x: int) -> int:
        if x not in self.parent:
            self.parent[x] = x
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def component_count(self) -> int:
        return len({self.find(x) for x in self.parent})


def _poly_add(p: dict[int, int], q: dict[int, int]) -> dict[int, int]:
    result = dict(p)
    for exponent, coefficient in q.items():
        result[exponent] = result.get(exponent, 0) + coefficient
        if result[exponent] == 0:
            del result[exponent]
    return result


def _poly_mul(p: dict[int, int], q: dict[int, int]) -> dict[int, int]:
    result: dict[int, int] = {}
    for e1, c1 in p.items():
        for e2, c2 in q.items():
            exponent = e1 + e2
            result[exponent] = result.get(exponent, 0) + c1 * c2
    return {e: c for e, c in result.items() if c}


def bracket_from_pd(pd: Sequence[Sequence[int]]) -> dict[int, int]:
    """Return the Kauffman bracket as an exponent-to-coefficient dictionary."""
    delta = {2: -1, -2: -1}
    labels = {int(x) for crossing in pd for x in crossing}
    total: dict[int, int] = {}
    crossing_count = len(pd)
    for mask in range(1 << crossing_count):
        dsu = DSU()
        for label in labels:
            dsu.find(label)
        a_count = b_count = 0
        for index, crossing in enumerate(pd):
            a, b, c, d = map(int, crossing)
            if ((mask >> index) & 1) == 0:
                a_count += 1
                dsu.union(a, b)
                dsu.union(c, d)
            else:
                b_count += 1
                dsu.union(b, c)
                dsu.union(d, a)
        factor = {0: 1}
        for _ in range(dsu.component_count() - 1):
            factor = _poly_mul(factor, delta)
        total = _poly_add(total, _poly_mul({a_count - b_count: 1}, factor))
    return total


def full_jones_vector(pd: Sequence[Sequence[int]]) -> list[int]:
    """Compute the normalized Jones vector using exact integer arithmetic."""
    if not pd:
        return [0, 0, 1]
    bracket = bracket_from_pd(pd)
    writhe = int(Link(pd).writhe())
    sign = -1 if ((-3 * writhe) % 2) else 1
    polynomial: dict[int, int] = {}
    for a_exponent, coefficient in bracket.items():
        normalized_exponent = a_exponent - 3 * writhe
        if normalized_exponent % 4:
            raise ValueError(
                "normalized bracket exponent is not divisible by four: "
                f"{normalized_exponent}"
            )
        t_exponent = -normalized_exponent // 4
        polynomial[t_exponent] = polynomial.get(t_exponent, 0) + sign * int(coefficient)
    polynomial = {e: c for e, c in polynomial.items() if c}
    minimum, maximum = min(polynomial), max(polynomial)
    coefficients = [int(polynomial.get(e, 0)) for e in range(minimum, maximum + 1)]
    while coefficients and coefficients[0] == 0:
        coefficients.pop(0)
        minimum += 1
    while coefficients and coefficients[-1] == 0:
        coefficients.pop()
        maximum -= 1
    return [int(minimum), int(maximum), *coefficients]


def mirror_jones_vector(vector: Sequence[int]) -> list[int]:
    minimum, maximum = int(vector[0]), int(vector[1])
    return [-maximum, -minimum, *[int(x) for x in reversed(vector[2:])]]


def jones_equal_unoriented(left: Sequence[int], right: Sequence[int]) -> bool:
    a, b = list(map(int, left)), list(map(int, right))
    return a == b or a == mirror_jones_vector(b)


def alexander_vector(pd: Sequence[Sequence[int]]) -> list[int]:
    """Compute a unit-normalized Alexander vector from a Seifert matrix."""
    t = sp.symbols("t")
    matrix = sp.Matrix(Link(pd).seifert_matrix())
    polynomial = sp.Poly(sp.expand((matrix - t * matrix.T).det()), t)
    data = polynomial.as_dict()
    if not data:
        return [0, 0, 0]
    minimum = min(key[0] for key in data)
    maximum = max(key[0] for key in data)
    coefficients = [int(data.get((e,), 0)) for e in range(minimum, maximum + 1)]
    while coefficients and coefficients[0] == 0:
        coefficients.pop(0)
        minimum += 1
    while coefficients and coefficients[-1] == 0:
        coefficients.pop()
        maximum -= 1
    if coefficients and coefficients[0] < 0:
        coefficients = [-x for x in coefficients]
    return [0, int(maximum - minimum), *coefficients]


def flip_crossing(crossing: Sequence[int]) -> list[int]:
    """Switch a PD crossing by [a,b,c,d] -> [b,c,d,a]."""
    a, b, c, d = map(int, crossing)
    return [b, c, d, a]


def flip_indices(pd: Sequence[Sequence[int]], indices: Iterable[int]) -> list[list[int]]:
    chosen = set(indices)
    return [
        flip_crossing(crossing) if index in chosen else [int(x) for x in crossing]
        for index, crossing in enumerate(pd)
    ]
