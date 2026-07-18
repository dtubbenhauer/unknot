#!/usr/bin/env python3
"""Enumerate normalized reduced alternating minimal diagrams of 11a14.

Method: extract a checkerboard/Tait multigraph from the standard PD, enumerate
its Whitney-flip class, enumerate planar rotation systems for each graph,
construct medial PD codes, keep alternating knots with the target Jones
profile, and deduplicate by Spherogram-normalized PD code.

This is the cleaned repository version of the script used in the exploratory
chat calculations.  It requires networkx and spherogram.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict, deque
from itertools import combinations, permutations, product
from pathlib import Path

import networkx as nx
from spherogram import Link
from spherogram.links.simplify import dual_graph_as_nx

TARGET_KNOT = "11a14"
TARGET_PD = [
    [4,2,5,1],[8,4,9,3],[14,9,15,10],[12,5,13,6],[6,13,7,14],
    [18,11,19,12],[22,20,1,19],[20,16,21,15],[16,22,17,21],
    [10,17,11,18],[2,8,3,7],
]


def strip0(coeffs):
    coeffs = [int(c) for c in coeffs]
    i, j = 0, len(coeffs)
    while i < j and coeffs[i] == 0:
        i += 1
    while j > i and coeffs[j - 1] == 0:
        j -= 1
    return tuple(coeffs[i:j] or [0])


def poly_add(p, q):
    r = dict(p)
    for e, c in q.items():
        r[e] = r.get(e, 0) + c
        if r[e] == 0:
            del r[e]
    return r


def poly_mul(p, q):
    r = {}
    for e1, c1 in p.items():
        for e2, c2 in q.items():
            e = e1 + e2
            r[e] = r.get(e, 0) + c1 * c2
    return {e: c for e, c in r.items() if c}


class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        if x not in self.p:
            self.p[x] = x
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra

    def n_components(self):
        return len({self.find(x) for x in self.p})


def bracket_from_pd(pd):
    delta = {2: -1, -2: -1}
    labels = {int(x) for q in pd for x in q}
    total = {}
    n = len(pd)
    for mask in range(1 << n):
        dsu = DSU()
        for x in labels:
            dsu.find(x)
        ac = bc = 0
        for i, (a, b, c, d) in enumerate(pd):
            a, b, c, d = map(int, (a, b, c, d))
            if ((mask >> i) & 1) == 0:
                ac += 1
                dsu.union(a, b)
                dsu.union(c, d)
            else:
                bc += 1
                dsu.union(b, c)
                dsu.union(d, a)
        factor = {0: 1}
        for _ in range(dsu.n_components() - 1):
            factor = poly_mul(factor, delta)
        total = poly_add(total, poly_mul({ac - bc: 1}, factor))
    return total


def jones_profile_from_pd(pd):
    if not pd:
        return (1,)
    bracket = bracket_from_pd(pd)
    residues = sorted({int(e) % 4 for e in bracket})
    if len(residues) != 1:
        raise ValueError(f"bad bracket residues {residues}")
    mx, mn = max(bracket), min(bracket)
    return strip0([int(bracket.get(e, 0)) for e in range(mx, mn - 1, -4)])


def flip_crossing(q):
    a, b, c, d = map(int, q)
    return [b, c, d, a]


def flip_indices(pd, idxs):
    chosen = set(idxs)
    return [flip_crossing(q) if i in chosen else [int(x) for x in q] for i, q in enumerate(pd)]


def plain_pd_from_spherogram(link):
    return [[int(getattr(x, "label", x)) + 1 for x in q] for q in link.PD_code()]


def sorted_spherogram_pd_key(pd):
    return tuple(sorted(tuple(q) for q in plain_pd_from_spherogram(Link(pd))))


def extract_tait_graph_from_pd(pd):
    link = Link(pd)
    faces = link.faces()
    cs_face = {}
    for face_index, face in enumerate(faces):
        for cs in face:
            cs_face[(cs.crossing.label, cs.strand_index)] = face_index
    dual = dual_graph_as_nx(link)
    colors = nx.bipartite.color(dual)
    counts = Counter(colors.values())
    chosen = min(counts, key=lambda c: (counts[c], c))
    edges = {}
    for crossing in link.crossings:
        fs = [cs_face[(crossing.label, j)] for j in range(4)]
        for u, v in [(fs[0], fs[2]), (fs[1], fs[3])]:
            if colors[u] == chosen and colors[v] == chosen:
                edges[int(crossing.label)] = (u, v)
                break
        else:
            raise RuntimeError("could not find same-color opposite face pair")
    info = {
        "chosen_color": int(chosen),
        "face_color_counts": {str(k): int(v) for k, v in counts.items()},
        "num_faces": len(faces),
    }
    return edges, info


def graph_vertices(edges):
    return sorted({x for uv in edges.values() for x in uv})


def multigraph_iso_key(edges):
    vertices = graph_vertices(edges)
    best = None
    for perm in permutations(range(len(vertices))):
        mapping = dict(zip(vertices, perm))
        pairs = sorted(tuple(sorted((mapping[u], mapping[v]))) for u, v in edges.values())
        key = tuple(pairs)
        if best is None or key < best:
            best = key
    return best


def flip_edges_at_cut(edges, a, b, side):
    new = {}
    for e, (u, v) in edges.items():
        uu, vv = u, v
        if u in side and v == a:
            vv = b
        elif u in side and v == b:
            vv = a
        elif v in side and u == a:
            uu = b
        elif v in side and u == b:
            uu = a
        new[e] = (uu, vv)
    return new


def possible_whitney_flips(edges):
    vertices = graph_vertices(edges)
    graph = nx.Graph()
    graph.add_nodes_from(vertices)
    for u, v in edges.values():
        if u != v:
            graph.add_edge(u, v)
    for a, b in combinations(vertices, 2):
        reduced = graph.copy()
        reduced.remove_nodes_from([a, b])
        components = [set(c) for c in nx.connected_components(reduced)]
        if len(components) < 2:
            continue

        def attaches(part, x):
            return any(
                (u in part and v == x) or (v in part and u == x)
                for u, v in edges.values()
            )

        for mask in range(1, (1 << len(components)) - 1):
            if not (mask & 1):
                continue
            side = set().union(
                *(components[i] for i in range(len(components)) if (mask >> i) & 1)
            )
            complement = set(vertices) - {a, b} - side
            if not (
                attaches(side, a)
                and attaches(side, b)
                and attaches(complement, a)
                and attaches(complement, b)
            ):
                continue
            new = flip_edges_at_cut(edges, a, b, side)
            if multigraph_iso_key(new) != multigraph_iso_key(edges):
                yield {"cut": [a, b], "side": sorted(side), "edges": new}


def enumerate_whitney_graphs(initial_edges):
    representatives = []
    queue = deque([initial_edges])
    seen = set()
    transitions = []
    while queue:
        edges = queue.popleft()
        key = multigraph_iso_key(edges)
        if key in seen:
            continue
        seen.add(key)
        index = len(representatives)
        representatives.append(edges)
        for flip in possible_whitney_flips(edges):
            transitions.append(
                {"source_index": index, "cut": flip["cut"], "side": flip["side"]}
            )
            queue.append(flip["edges"])
    return representatives, transitions


def cyclic_orders(seq):
    seq = tuple(seq)
    first = min(seq)
    rest = [x for x in seq if x != first]
    for perm in permutations(rest):
        yield (first,) + perm


def ribbon_faces(vertices, edges, rotation):
    def other(dart):
        vertex, edge = dart
        u, v = edges[edge]
        return (v, edge) if vertex == u else (u, edge)

    rho = {}
    for vertex, seq in rotation.items():
        for i, edge in enumerate(seq):
            rho[(vertex, edge)] = (vertex, seq[(i + 1) % len(seq)])
    phi = {dart: rho[other(dart)] for dart in rho}
    seen = set()
    faces = []
    for dart in rho:
        if dart in seen:
            continue
        cycle = []
        current = dart
        while current not in seen:
            seen.add(current)
            cycle.append(current)
            current = phi[current]
        faces.append(cycle)
    return faces


def build_medial_pd(vertices, edges, rotation):
    arc = {}
    position = {}
    label = 1
    for vertex in sorted(vertices):
        for i, edge in enumerate(rotation[vertex]):
            arc[(vertex, edge)] = label
            position[(vertex, edge)] = i
            label += 1

    def previous_edge(vertex, edge):
        seq = rotation[vertex]
        return seq[(position[(vertex, edge)] - 1) % len(seq)]

    pd = []
    for edge in sorted(edges):
        u, v = edges[edge]
        pd.append(
            [
                arc[(u, previous_edge(u, edge))],
                arc[(u, edge)],
                arc[(v, previous_edge(v, edge))],
                arc[(v, edge)],
            ]
        )
    return pd


def enumerate_planar_diagrams_for_tait_graph(edges):
    vertices = graph_vertices(edges)
    incident = defaultdict(list)
    for edge, (u, v) in edges.items():
        incident[u].append(edge)
        incident[v].append(edge)
    order_lists = [list(cyclic_orders(incident[v])) for v in vertices]
    total = math.prod(len(x) for x in order_lists)
    diagrams = []
    for combination in product(*order_lists):
        rotation = dict(zip(vertices, combination))
        face_count = len(ribbon_faces(vertices, edges, rotation))
        if len(vertices) - len(edges) + face_count != 2:
            continue
        pd = build_medial_pd(vertices, edges, rotation)
        try:
            link = Link(pd)
            if (
                len(link.crossings) == len(edges)
                and len(link.link_components) == 1
                and link.is_alternating()
            ):
                diagrams.append(
                    {
                        "pd": pd,
                        "rotation": {int(k): list(v) for k, v in rotation.items()},
                        "dt_code": [list(t) for t in link.DT_code()],
                    }
                )
        except Exception:
            pass
    return diagrams, total


def enumerate_representatives():
    started = time.time()
    target_profile = jones_profile_from_pd(TARGET_PD)
    initial_edges, tait_info = extract_tait_graph_from_pd(TARGET_PD)
    whitney_graphs, transitions = enumerate_whitney_graphs(initial_edges)
    raw = []
    graph_audits = []
    for graph_index, edges in enumerate(whitney_graphs):
        diagrams, total = enumerate_planar_diagrams_for_tait_graph(edges)
        matches = []
        for diagram in diagrams:
            pd0 = diagram["pd"]
            if jones_profile_from_pd(pd0) == target_profile:
                selected = dict(diagram)
                selected["assignment"] = "medial"
                matches.append(selected)
                raw.append({"graph_index": graph_index, **selected})
            else:
                pd1 = flip_indices(pd0, range(len(pd0)))
                if jones_profile_from_pd(pd1) == target_profile:
                    selected = dict(diagram)
                    selected["pd"] = pd1
                    selected["assignment"] = "all_crossings_switched"
                    matches.append(selected)
                    raw.append({"graph_index": graph_index, **selected})
        graph_audits.append(
            {
                "graph_index": graph_index,
                "candidate_rotation_systems": total,
                "planar_alternating_knot_diagrams": len(diagrams),
                "target_jones_diagrams_raw": len(matches),
                "vertices": graph_vertices(edges),
                "edges": {str(k): [int(v[0]), int(v[1])] for k, v in edges.items()},
            }
        )

    representatives_by_key = {}
    for diagram in raw:
        key = sorted_spherogram_pd_key(diagram["pd"])
        if key not in representatives_by_key:
            link = Link(diagram["pd"])
            representatives_by_key[key] = {
                "source_graph_index": diagram["graph_index"],
                "assignment": diagram.get("assignment"),
                "pd": plain_pd_from_spherogram(link),
                "normalized_sorted_pd": [list(q) for q in key],
                "dt_code": [list(t) for t in link.DT_code()],
                "writhe": int(link.writhe()),
            }
    paper_key = sorted_spherogram_pd_key(TARGET_PD)
    if paper_key not in representatives_by_key:
        link = Link(TARGET_PD)
        representatives_by_key[paper_key] = {
            "source_graph_index": "paper_only",
            "assignment": "paper",
            "pd": TARGET_PD,
            "normalized_sorted_pd": [list(q) for q in paper_key],
            "dt_code": [list(t) for t in link.DT_code()],
            "writhe": int(link.writhe()),
        }
    representatives = list(representatives_by_key.values())
    metadata = {
        "target_knot": TARGET_KNOT,
        "target_pd": TARGET_PD,
        "target_jones_profile": list(target_profile),
        "tait_info": tait_info,
        "whitney_graph_count": len(whitney_graphs),
        "whitney_transition_count": len(transitions),
        "raw_target_diagrams": len(raw),
        "normalized_minimal_pd_reps": len(representatives),
        "graph_audits": graph_audits,
        "elapsed_seconds": round(time.time() - started, 3),
    }
    return representatives, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "output")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    representatives, metadata = enumerate_representatives()
    (args.output_dir / "all_normalized_minimal_pds_11a14.json").write_text(
        json.dumps(representatives, indent=2) + "\n"
    )
    (args.output_dir / "enumeration_summary.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (args.output_dir / "all_normalized_minimal_pds_11a14.txt").open("w") as handle:
        for index, representative in enumerate(representatives):
            handle.write(f"pd_id={index}\n{json.dumps(representative['pd'])}\n\n")
    print(json.dumps(metadata, indent=2))
    if len(representatives) != 17:
        raise RuntimeError(f"Expected 17 representatives, found {len(representatives)}")


if __name__ == "__main__":
    main()
