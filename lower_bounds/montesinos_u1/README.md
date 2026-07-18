# Montesinos obstruction to unknotting number one

The driver `montesinos_d_obstruction_scan.py` contains the complete list of 50
parseable three-tangle Montesinos targets from the paper.  For each target the worker
constructs a negative-definite star plumbing, verifies its determinant, computes all
correction terms exactly and tests every linking-form-compatible affine map in both
orientations.

## Compact table

`montesinos_d_obstruction_scan_u1_targets_up_to_13.csv` is the 50-row summary used
for the appendix counts.  Forty-nine rows are obstructed; the remaining row is
`12n309`, whose determinant is one.

## Full certificates

`full_certificates/` contains one JSON file per target.  Each file records

- the full plumbing matrix and normalized Seifert data;
- every Spin-c correction term in both orientations;
- every compatible cyclic generator;
- every affine map tested in both orientations; and
- the first exact parity/sign failure for each rejected map.

The directory index records 2,456 Spin-c classes and 13,498 affine maps in total.
Rebuild it with

```bash
python lower_bounds/montesinos_u1/export_full_certificates.py --workers 12
```
