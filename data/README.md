# Input data and compact identification indexes

The paper uses a KnotInfo snapshot as its table input.  The complete third-party
snapshot is not redistributed here.  Instead this directory contains its exact
provenance and the small derived indexes needed by the included verification
scripts.

## Files

- `knotinfo_snapshot.json` records the `database-knotinfo` release, row count and
  SHA-256 checksum used to regenerate the data.
- `workbook_provenance.json` records the exact `.xls` workbook used for the new
  certificate scans, including its shape, byte size and SHA-256 checksum.
- `build_knotinfo_u1_jones_index.py` deterministically computes full Jones vectors
  for exact-unknotting-number-one rows.  For the `11a14` check it first filters by
  determinant; this is lossless because the determinant is the absolute value of
  the Jones polynomial at `-1`.
- `knotinfo_exact_u1_jones_index.csv` is the resulting 54-row index for
  determinants `25, 27, 35, 39`.  The summary records that the full snapshot has
  1,516 exact-`u=1` rows with PD codes.
- `identification_rows_11a14.csv` contains the six collision rows used to identify
  the four invariant classes arising in the minimal-diagram scan.
- `12n873_correction.csv` records the database consistency correction discussed in
  the paper.

Rebuild the exact-`u=1` index with

```bash
python data/build_knotinfo_u1_jones_index.py
```

Pass `--determinants ''` to compute the much larger unfiltered index.  The filtered
file is sufficient for `11a14` because the four output classes have determinants
`25`, `27`, `35` and `39`.
