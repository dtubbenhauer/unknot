# Repository completeness

This file maps the machine-readable claims in the paper to repository paths.

| paper computation | repository material | status |
|---|---|---|
| signature-four Owens batch, 245 knots | `lower_bounds/owens_u2/` | complete |
| signature-six Owens batch, 164 knots | `lower_bounds/owens_signature_sharp/signature6_*` | complete |
| signature-eight Owens batch, 24 knots | `lower_bounds/owens_signature_sharp/signature8_*` | complete |
| Montesinos `u != 1`, 50 targets/49 obstructions | `lower_bounds/montesinos_u1/`, including `full_certificates/` | complete |
| higher Montesinos, five `u=3` and two `u=4` | `lower_bounds/montesinos_signature_sharp/` | complete |
| `11a14` minimal diagrams | `verification/11a14/output/all_normalized_minimal_pds_11a14.json` | 17/17 |
| `11a14` single crossing changes | `verification/11a14/output/one_crossing_records.csv` | 187/187 |
| `11a14` invariant collision resolution | `verification/11a14/output/invariant_classes.csv` and `u1_candidate_checks.csv` | complete |
| `12n873` input correction | `data/12n873_correction.csv` | complete |
| KnotInfo input provenance | `data/knotinfo_snapshot.json` and deterministic index builder | complete |
| hard-unknot exploratory searches | `searches/hard_unknots/` | summaries and cleaned scripts included |
| game research levels and figures | `searches/game_levels/` | complete |

The temporary `pending_import/` directory from the assembly draft has been removed.
Byte-for-byte intermediate Colab retries are not treated as archival theorem data;
the cleaned runnable scripts and final summaries are retained instead.
