#!/usr/bin/env python3
"""Fast structural checks for every theorem-critical repository output."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"verification failed: {message}")


def csv_rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def verify_alexander() -> dict[str, int]:
    all_rows = csv_rows("lower_bounds/alexander_module/all_certificates.csv")
    new_rows = csv_rows("lower_bounds/alexander_module/new_certificates.csv")
    additions = csv_rows("lower_bounds/alexander_module/additional_certificates.csv")
    restricted = csv_rows("lower_bounds/alexander_module/restricted_scan_certificates.csv")
    require(len(all_rows) == 363, "Alexander all-witness count")
    require(len(new_rows) == 362, "Alexander new-witness count")
    require(len(additions) == 13, "Alexander additional-witness count")
    require(len(restricted) == 350, "Alexander restricted-witness count")
    require(len({row["knot"] for row in new_rows}) == 362, "Alexander knot uniqueness")
    require({row["knot"] for row in additions} <= {row["knot"] for row in new_rows}, "Alexander additions included")
    consequences = Counter(row["consequence"] for row in new_rows)
    require(consequences["exact u=2"] == 303, "Alexander exact-u=2 count")
    require(consequences["exact u=3"] == 14, "Alexander exact-u=3 count")
    require(consequences["improved"] == 45, "Alexander non-exact count")
    implied = [row for row in all_rows if row["already_implied_by_workbook"] == "True"]
    require(len(implied) == 1 and implied[0]["knot"] == "12n873", "Alexander implied row")
    field_orders = Counter(int(row["field_order"]) for row in additions)
    require(field_orders == {16: 8, 49: 4, 81: 1}, f"Alexander additional fields: {field_orders}")

    complete = load_json("lower_bounds/alexander_module/complete_scan.json")
    summary = complete["summary"]
    require(summary["gapped_rows_checked"] == 5121, "Alexander complete row count")
    require(summary["reduced_size_maximum"] == 6, "Alexander reduced-size maximum")
    require(summary["finite_field_index_counts"] == {"0": 11, "1": 4504, "2": 588, "3": 18}, "Alexander index distribution")
    require(summary["improves_input_lower_bound"] == 363, "Alexander successful index count")
    require(summary["new_over_previous_scan"] == 13, "Alexander completion count")
    results = complete["results"]
    require(len(results) == 5121, "Alexander complete result rows")
    require(sum(int(row["complete_finite_field_index"]) >= 2 for row in results) == 606, "Alexander positive-index rows")
    require(set(summary["new_knots"]) == {row["knot"] for row in additions}, "Alexander added knot set")
    return {"all": len(all_rows), "new": len(new_rows), "additional": len(additions), "rows": len(results)}


def verify_owens() -> dict[str, int]:
    rows = csv_rows("lower_bounds/owens/valid_determinant_group_certificates.csv")
    require(len(rows) == 5, "valid Owens certificate count")
    require(len({row["knot"] for row in rows}) == 5, "Owens knot uniqueness")
    types = Counter(row["certificate_type"] for row in rows)
    require(types["no Owens determinant solution"] == 1, "Owens determinant count")
    require(types["discriminant groups not isomorphic"] == 4, "Owens group count")
    require(sum(row["consequence"] == "exact u=3" for row in rows) == 4, "Owens exact count")

    full_files = (
        "lower_bounds/owens/full_correction_terms_10_47_10_100.json",
        "lower_bounds/owens/full_correction_terms_10_6_10_61_10_76.json",
    )
    knots = []
    survivor_counts: dict[str, list[int]] = {}
    for relative in full_files:
        for item in load_json(relative)["knots"]:
            knots.append(item["knot"])
            require(not item["owens_obstructs_u_equals_2"], f"unexpected full Owens obstruction for {item['knot']}")
            counts = [len(candidate["surviving_units"]) for candidate in item["candidates"]]
            require(any(counts), f"no surviving Owens isomorphism for {item['knot']}")
            survivor_counts[item["knot"]] = counts
    expected = {"10_6", "10_47", "10_61", "10_76", "10_100"}
    require(set(knots) == expected and len(knots) == 5, "full Owens knot set")
    require(survivor_counts["10_6"] == [2], "10_6 survivor count")
    require(survivor_counts["10_47"] == [2, 2], "10_47 survivor counts")
    require(survivor_counts["10_61"] == [0, 4], "10_61 survivor counts")
    require(survivor_counts["10_76"] == [0, 4], "10_76 survivor counts")
    require(survivor_counts["10_100"] == [4, 0], "10_100 survivor counts")
    return {"positive_certificates": len(rows), "full_negative_cases": len(knots)}


def verify_ten_crossing() -> dict[str, int]:
    pair_data = load_json("verification/ten_crossing_minimal_diagrams/two_change_determinants.json")
    triple_data = load_json("verification/ten_crossing_minimal_diagrams/three_change_unknot_certificates.json")
    require(all(case["passed"] for case in pair_data["validation_cases"]), "pair controls")
    require(all(case["passed"] for case in triple_data["validation_cases"]), "group controls")

    pairs = pair_data["knots"]
    triples = triple_data["knots"]
    require(len(pairs) == len(triples) == 10, "ten-crossing knot count")
    expected_knots = {"10_6", "10_11", "10_47", "10_51", "10_54", "10_61", "10_76", "10_77", "10_79", "10_100"}
    require({item["knot"] for item in pairs} == expected_knots, "pair knot set")
    require({item["knot"] for item in triples} == expected_knots, "triple knot set")
    require(sum(item["pairs_tested"] for item in pairs) == 450, "total pair count")
    for item in pairs:
        require(item["pairs_tested"] == 45, f"pair count for {item['knot']}")
        require(item["all_pairs_obstructed_by_determinant"], f"unobstructed pair for {item['knot']}")
        require(not item["determinant_one_pairs"], f"determinant-one pair for {item['knot']}")

    expected_triples = {
        "10_6": [1, 2, 3], "10_11": [1, 2, 4], "10_47": [1, 2, 4],
        "10_51": [1, 2, 4], "10_54": [1, 2, 3], "10_61": [1, 2, 4],
        "10_76": [1, 2, 4], "10_77": [1, 2, 5], "10_79": [1, 2, 4],
        "10_100": [1, 2, 3],
    }
    for item in triples:
        require(item["witness_found"], f"missing triple witness for {item['knot']}")
        certificate = item["three_change_unknot_certificate"]
        require(certificate["positions_1_based"] == expected_triples[item["knot"]], f"triple positions for {item['knot']}")
        reduction = certificate["tietze_reduction"]
        require(reduction["reduces_to_infinite_cyclic"], f"group reduction for {item['knot']}")
        require(len(reduction["elimination_steps"]) == 9, f"Tietze step count for {item['knot']}")
        require(len(reduction["remaining_generators"]) == 1 and not reduction["remaining_relators"], f"final presentation for {item['knot']}")
    return {"knots": len(pairs), "pairs": 450, "triple_certificates": len(triples)}


def verify_retained_results() -> dict[str, int]:
    checks = {
        "montesinos_u1_targets": len(csv_rows("lower_bounds/montesinos_u1/montesinos_d_obstruction_scan_u1_targets_up_to_13.csv")),
        "montesinos_u1_full": len(csv_rows("lower_bounds/montesinos_u1/full_certificates/index.csv")),
        "montesinos_higher": len(csv_rows("lower_bounds/montesinos_signature_sharp/montesinos_spin_certificates.csv")),
        "minimal_pds_11a14": len(load_json("verification/11a14/output/all_normalized_minimal_pds_11a14.json")),
        "crossing_changes_11a14": len(csv_rows("verification/11a14/output/one_crossing_records.csv")),
        "invariant_classes_11a14": len(csv_rows("verification/11a14/output/invariant_classes.csv")),
        "u1_collisions_11a14": len(csv_rows("verification/11a14/output/u1_candidate_checks.csv")),
    }
    expected = {
        "montesinos_u1_targets": 50,
        "montesinos_u1_full": 50,
        "montesinos_higher": 7,
        "minimal_pds_11a14": 17,
        "crossing_changes_11a14": 187,
        "invariant_classes_11a14": 4,
        "u1_collisions_11a14": 3,
    }
    require(checks == expected, f"retained-result counts: {checks}")
    summary = load_json("verification/11a14/output/one_crossing_summary.json")
    require(summary.get("all_exact_u1_candidates_excluded"), "11a14 collision resolution")
    return checks


def verify_paper_and_layout() -> dict[str, int]:
    tex = (ROOT / "paper/big_data_unknotting.tex").read_text(encoding="utf-8")
    pdf = ROOT / "paper/big_data_unknotting.pdf"
    require(pdf.is_file() and pdf.stat().st_size > 20_000_000, "compiled paper PDF")
    require("prop:ten crossing-minimal-diagrams" in tex, "ten-crossing proposition in paper")
    require("372" in tex and "50" in tex, "completed main counts in paper")
    require("303 & 14 & 45 & 362" in tex, "completed Alexander table in paper")
    require("prop:alex-finite-verification" in tex and "prop:alex-exceptional-primes" in tex, "complete Alexander propositions in paper")
    require("full D{\\&}D obstruction does not recover" in tex, "full D&D conclusion in paper")
    require(not (ROOT / "lower_bounds/owens_u2").exists(), "obsolete Owens u2 directory present")
    require(not (ROOT / "lower_bounds/owens_signature_sharp").exists(), "obsolete zero-class directory present")
    return {"pdf_bytes": pdf.stat().st_size}


def main() -> None:
    report = {
        "status": "OK",
        "alexander": verify_alexander(),
        "owens": verify_owens(),
        "ten_crossing": verify_ten_crossing(),
        "retained": verify_retained_results(),
        "paper": verify_paper_and_layout(),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
