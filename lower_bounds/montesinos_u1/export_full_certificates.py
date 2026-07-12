#!/usr/bin/env python3
"""Export complete machine-readable Montesinos u!=1 certificates.

For each of the 50 targets this script records the plumbing matrix, every
correction term, the linking-form-compatible generators, and every affine map
considered in both orientations.  A failed map records its first exact
parity/sign violation; a map passing the basic test also records whether it
passes the stronger Ni--Wu sequence test.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import montesinos_d_obstruction_scan as batch  # noqa: E402
import unknotting_number_one_d_invariant_obstruction as obs  # noqa: E402


def ftext(value) -> str:
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def key_sort(key):
    return tuple((x.numerator, x.denominator) for x in key)


def serialize_key(key):
    return [ftext(x) for x in key]


def integer_matrix(matrix):
    return [[int(matrix[i, j]) for j in range(matrix.cols)] for i in range(matrix.rows)]


def build_certificate(name: str, metadata: dict) -> dict:
    fracs = metadata["fractions"]
    b, pairs = obs.normalize_fracs(fracs)
    e = obs.seifert_e(b, pairs)
    if e > 0:
        b_used, pairs_used = obs.reverse_seifert(b, pairs)
        orientation = "reverse_of_knotinfo_montesinos_orientation"
    else:
        b_used, pairs_used = b, pairs
        orientation = "knotinfo_montesinos_orientation"
    q, weights, arms = obs.star_matrix(b_used, pairs_used)
    determinant = abs(int(q.det()))
    if determinant != int(metadata["determinant"]):
        raise RuntimeError(f"{name}: determinant mismatch {determinant} != {metadata['determinant']}")
    dmap, representatives = obs.d_plumbing(q, weights)
    if len(dmap) != determinant:
        raise RuntimeError(f"{name}: expected {determinant} classes, got {len(dmap)}")
    qinv = q.inv()
    keys = sorted(dmap, key=key_sort)
    ids = {key: index for index, key in enumerate(keys)}
    classes = [
        {
            "class_id": ids[key],
            "key_mod_1": serialize_key(key),
            "representative_x": list(representatives[key]),
            "d_graph": ftext(dmap[key]),
            "d_minus_graph": ftext(-dmap[key]),
        }
        for key in keys
    ]

    # Identify one cyclic generator, then use integer coordinates in Z/DZ.
    # This avoids repeating matrix/Fraction arithmetic inside every affine map.
    base_generator = next(
        key for key in keys if obs.order(qinv, representatives, key) == determinant
    )
    zero = obs.key_of_x(qinv, tuple(0 for _ in representatives[base_generator]))
    coordinate_to_key = [zero]
    current = zero
    for _ in range(1, determinant):
        current = obs.add_key(qinv, representatives, current, base_generator)
        coordinate_to_key.append(current)
    if len(set(coordinate_to_key)) != determinant:
        raise RuntimeError(f"{name}: cyclic coordinate construction failed")
    key_to_coordinate = {key: coordinate for coordinate, key in enumerate(coordinate_to_key)}
    base_linking = obs.self_link(qinv, representatives[base_generator])

    generator_coordinates = []
    generators = []
    from math import gcd
    for coordinate in range(determinant):
        if gcd(coordinate, determinant) != 1:
            continue
        self_linking = obs.frac_mod1(coordinate * coordinate * base_linking)
        if self_linking in (Fraction(2, determinant), obs.frac_mod1(Fraction(-2, determinant))):
            key = coordinate_to_key[coordinate]
            generator_coordinates.append(coordinate)
            generators.append(
                {
                    "coordinate_mod_D": coordinate,
                    "class_id": ids[key],
                    "key_mod_1": serialize_key(key),
                    "self_linking": ftext(self_linking),
                }
            )

    lens = obs.d_lens(determinant, 2)
    affine_maps = []
    map_number = 0
    for sign, label in ((1, "graph"), (-1, "minus_graph")):
        for generator_coordinate in generator_coordinates:
            for offset_coordinate in range(determinant):
                map_number += 1
                n_values = []
                first_failure = None
                for i in range(determinant):
                    image_coordinate = (offset_coordinate + i * generator_coordinate) % determinant
                    image = coordinate_to_key[image_coordinate]
                    difference = lens[i] - sign * dmap[image]
                    if difference.denominator != 1:
                        first_failure = {
                            "i": i,
                            "image_coordinate": image_coordinate,
                            "image_class_id": ids[image],
                            "difference": ftext(difference),
                            "reason": "difference_not_integral",
                        }
                        break
                    if difference < 0:
                        first_failure = {
                            "i": i,
                            "image_coordinate": image_coordinate,
                            "image_class_id": ids[image],
                            "difference": ftext(difference),
                            "reason": "difference_negative",
                        }
                        break
                    if int(difference) % 2:
                        first_failure = {
                            "i": i,
                            "image_coordinate": image_coordinate,
                            "image_class_id": ids[image],
                            "difference": ftext(difference),
                            "reason": "difference_not_even",
                        }
                        break
                    n_values.append(int(difference // 2))
                basic_pass = first_failure is None
                v_sequence = obs.possible_N(n_values) if basic_pass else None
                affine_maps.append(
                    {
                        "map_id": map_number,
                        "orientation": label,
                        "generator_coordinate": generator_coordinate,
                        "offset_coordinate": offset_coordinate,
                        "generator_class_id": ids[coordinate_to_key[generator_coordinate]],
                        "offset_class_id": ids[coordinate_to_key[offset_coordinate]],
                        "basic_pass": basic_pass,
                        "first_failure": first_failure,
                        "n_values_if_basic_pass": n_values if basic_pass else None,
                        "niwu_pass": v_sequence is not None if basic_pass else False,
                        "v_sequence_if_pass": v_sequence,
                    }
                )
    return {
        "knot": name,
        "crossing_number": metadata["crossing"],
        "input_interval": metadata["interval"],
        "determinant_table": metadata["determinant"],
        "montesinos_notation": metadata["montesinos"],
        "fractions": [ftext(x) for x in fracs],
        "normalized_seifert": {
            "b": b,
            "pairs": pairs,
            "e": ftext(e),
        },
        "negative_definite_seifert": {
            "orientation": orientation,
            "b": b_used,
            "pairs": pairs_used,
            "e": ftext(obs.seifert_e(b_used, pairs_used)),
        },
        "plumbing": {
            "matrix": integer_matrix(q),
            "weights": weights,
            "arms": arms,
            "determinant": determinant,
        },
        "spin_c_classes": classes,
        "compatible_generators": generators,
        "cyclic_base_generator_class_id": ids[base_generator],
        "cyclic_base_self_linking": ftext(base_linking),
        "maps_per_orientation": len(generator_coordinates) * determinant,
        "affine_maps": affine_maps,
        "basic_pass_count": sum(item["basic_pass"] for item in affine_maps),
        "niwu_pass_count": sum(item["niwu_pass"] for item in affine_maps),
        "obstructed_basic": not any(item["basic_pass"] for item in affine_maps),
        "obstructed_full": not any(item["niwu_pass"] for item in affine_maps),
    }


def build_timed(item):
    name, metadata = item
    started = time.time()
    certificate = build_certificate(name, metadata)
    return name, metadata, certificate, round(time.time() - started, 3)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    output = HERE / "full_certificates"
    output.mkdir(parents=True, exist_ok=True)
    index_rows = []
    started = time.time()
    items = list(batch.KNOTS.items())
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        for index, result in enumerate(executor.map(build_timed, items, chunksize=1), start=1):
            name, metadata, certificate, seconds = result
            path = output / f"{name}.json"
            text = json.dumps(certificate, indent=2, sort_keys=True) + "\n"
            path.write_text(text)
            index_rows.append(
                {
                    "knot": name,
                    "input_interval": metadata["interval"],
                    "determinant": metadata["determinant"],
                    "spin_c_classes": len(certificate["spin_c_classes"]),
                    "compatible_generators": len(certificate["compatible_generators"]),
                    "affine_maps_total": len(certificate["affine_maps"]),
                    "basic_pass_count": certificate["basic_pass_count"],
                    "niwu_pass_count": certificate["niwu_pass_count"],
                    "obstructed_basic": certificate["obstructed_basic"],
                    "obstructed_full": certificate["obstructed_full"],
                    "file": path.name,
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "seconds": seconds,
                }
            )
            print(f"[{index}/{len(items)}] {name}: maps={len(certificate['affine_maps'])} obstructed={certificate['obstructed_full']}", flush=True)
    with (output / "index.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(index_rows[0]))
        writer.writeheader()
        writer.writerows(index_rows)
    summary = {
        "targets": len(index_rows),
        "obstructed_basic": sum(row["obstructed_basic"] for row in index_rows),
        "obstructed_full": sum(row["obstructed_full"] for row in index_rows),
        "total_spin_c_classes": sum(row["spin_c_classes"] for row in index_rows),
        "total_affine_maps_both_orientations": sum(row["affine_maps_total"] for row in index_rows),
        "elapsed_seconds": round(time.time() - started, 3),
        "workers": args.workers,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
