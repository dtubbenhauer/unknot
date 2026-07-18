# Hard-unknot exploratory searches

This directory records upper-bound searches carried out on slices of the public
hard-unknot data.  They are **exploratory search records**, not lower-bound
certificates.

## Clean runnable scripts

- `scripts/download_hard_unknot_chunks.py` downloads reproducible consecutive
  slices from `gs://gdm-unknotting/hard_unknots.csv`.
- `scripts/hard_unknots_gcs_one_swap_scan.py` switches every crossing, asks SnapPy
  for identifications and intersects the result with the KnotInfo `[1,a]`, `a>1`,
  target set.

These scripts replace the several Colab-specific notebook revisions created during
the exploratory phase.  The final summaries are retained, while intermediate retry
notebooks are not treated as archival theorem data.

## Included summaries

- `hard_chunk_retry_summary.json`: 5,775 source rows and 128,314 one-crossing
  swaps were volume-filtered; no target was confirmed by `identify()`.
- `run_summary_enriched.json`: exact Jones--Alexander--volume matching on source
  diagrams with at most 13 crossings.
- `run_summary_postprocessed.json`: an eight-minute run without a source-crossing
  cutoff; it is explicitly nonexhaustive.
- `fig17_extended_scan_summary.json`: 1,806 variants of the printed 42-crossing
  hard unknot and 75,852 crossing swaps.

Negative search results are included for reproducibility but are never used as
proofs of lower bounds.
