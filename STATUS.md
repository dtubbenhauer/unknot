# Repository completeness

This table maps each machine-readable claim in the revised paper to its archival
material.

| paper computation | repository material | verified status |
|---|---|---|
| complete finite-field Alexander index, 5,121 rows and index distribution 11/4,504/588/18 | `lower_bounds/alexander_module/complete_scan.json` | complete |
| finite-field Alexander certificates, 363 total/362 new witnesses | `lower_bounds/alexander_module/all_certificates.csv`, `new_certificates.csv` | complete |
| 13 additions beyond the restricted field scan | `lower_bounds/alexander_module/additional_certificates.csv` | complete |
| direct verification in original Seifert matrices | `code/verify_complete_alexander_witnesses.py` | exact rerun script included |
| corrected oriented zero-class audit | `lower_bounds/summary.json` | 653/164/24 targets, zero obstructions |
| five valid Owens determinant/group certificates | `lower_bounds/owens/valid_determinant_group_certificates.csv` | complete |
| full Owens tests for five ten-crossing knots | `lower_bounds/owens/full_correction_terms_*.json` | complete; every knot has a survivor |
| Montesinos `u != 1`, 50 targets/49 obstructions | `lower_bounds/montesinos_u1/` | complete |
| higher Montesinos, five `u=3` and two `u=4` | `lower_bounds/montesinos_signature_sharp/` | complete |
| ten-crossing two-change determinant screen | `verification/ten_crossing_minimal_diagrams/two_change_determinants.json` | 450/450 pairs obstructed |
| ten-crossing three-change witnesses | `verification/ten_crossing_minimal_diagrams/three_change_unknot_certificates.json` | 10/10 reduce to `Z` |
| `11a14` minimal diagrams | `verification/11a14/output/all_normalized_minimal_pds_11a14.json` | 17/17 |
| `11a14` single crossing changes | `verification/11a14/output/one_crossing_records.csv` | 187/187 |
| `11a14` invariant collision resolution | `verification/11a14/output/invariant_classes.csv`, `u1_candidate_checks.csv` | complete |
| `12n873` input correction | `data/12n873_correction.csv` | complete |
| input provenance | `data/knotinfo_snapshot.json`, `data/workbook_provenance.json` | complete |
| revised manuscript | `paper/big_data_unknotting.tex`, `paper/big_data_unknotting.pdf` | complete, 30 pages |
| hard-unknot exploratory searches | `searches/hard_unknots/` | summaries and cleaned scripts included |
| game research levels and figures | `searches/game_levels/` | complete |

The obsolete `lower_bounds/owens_u2/` and
`lower_bounds/owens_signature_sharp/` directories are intentionally absent.
