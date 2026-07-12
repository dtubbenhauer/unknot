# The all-minimal-diagram check for `11a14`

This directory contains the complete certificate behind the minimal-diagram result.

1. `enumerate_minimal_diagrams.py` extracts a checkerboard Tait multigraph from the
   paper PD, enumerates its Whitney-flip class and all planar rotation systems, and
   deduplicates the resulting alternating minimal PD codes.
2. `check_one_crossing_changes.py` checks all eleven crossing changes on each of the
   17 normalized representatives.

Run

```bash
python verification/11a14/enumerate_minimal_diagrams.py
python verification/11a14/check_one_crossing_changes.py
```

The output directory records:

- all 17 normalized minimal PD representatives;
- all 187 crossing-change rows;
- the four full Jones/Alexander/volume classes;
- the three exact-`u=1` Jones collisions and their exclusion.

The class multiplicities are `68, 68, 34, 17`.  The exact identifications are
`8_10`, `8_8`, and `8_16` for three classes.  The fourth has volume about
`5.69302`; its only exact-`u=1` Jones collision in the determinant-filtered KnotInfo
index is `13n_585`, which is excluded both by crossing number and by volume.

For completeness, `run_11a14_minimal_pd_two_swap_scan_lean.py` retains the earlier
direct two-swap experiment.  It tests 935 crossing pairs and finds no unknot Jones
profile.  This exploratory result is recorded separately from the 187-row certificate
used in the paper.
