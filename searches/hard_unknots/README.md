# Hard-unknot exploratory searches

These files record exploratory upper-bound searches carried out on slices of the hard-unknot data. They are **search summaries**, not lower-bound certificates.

- `hard_chunk_retry_summary.json`: 5,775 source rows and 128,314 one-crossing swaps were volume-filtered; no target was confirmed by `identify()`.
- `run_summary_enriched.json`: exact Jones--Alexander--volume matching on the source diagrams with at most 13 crossings.
- `run_summary_postprocessed.json`: an eight-minute, no-source-crossing-cutoff run; it is explicitly nonexhaustive.
- `fig17_extended_scan_summary.json`: a scan of 1,806 variants of the printed 42-crossing hard unknot.

The notebooks and worker scripts that generated these summaries are listed in `../../pending_import/IMPORT_MANIFEST.md`. They must be copied into this directory before the repository is advertised as a complete archival release.
