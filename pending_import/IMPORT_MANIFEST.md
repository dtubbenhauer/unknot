# Files still to import from the previous chats

This is a **temporary assembly manifest**, not intended to remain in the public repository.
The files below were located in the ChatGPT File Library, but File Library references cannot be copied into a newly generated archive in this runtime. They need to be downloaded from the file cards and placed at the paths below.

## Required for the paper's stated verification package

### Signature-six and signature-eight Owens scans

Place in `lower_bounds/owens_higher_signature/`:

- `run_signature6_zero_class_scan.py`
- `signature6_zero_class_results.csv`
- `signature6_zero_class_results.xlsx`
- `signature6_zero_class_summary.json`
- `signature6_scan_README.md`
- the corresponding signature-eight script, results and summary (or a single generalized exact script and combined certificate table)

### The 11a14 all-minimal-diagram certificate

Place in `verification/11a14/`:

- `run_11a14_minimal_pd_two_swap_scan_lean.py`
- `enumerate_11a14_reps_only.py`
- `scan_11a14_rep.py`
- `check_11a14_minimal_one_flop_full_jones.py`
- `all_normalized_minimal_pds_11a14.json`
- `summary_11a14_minimal_pd_two_swap.json`
- `per_normalized_rep_two_swap_profiles.json`
- the one-swap Jones--Alexander--volume comparison output

### Identification table

Place in `data/`:

- `unknotting_alex_jones_volume.xlsx`

The raw KnotInfo export should either be included with its license/provenance or replaced by a downloader that records the download date and checksum.

## Relevant exploratory notebooks from the earlier chats

Place in `searches/notebooks/`:

- `scan_10_100_inflation_witnesses_v9_alex_jones_volume.ipynb`
- `hard_unknot_one_swap_search.ipynb`
- `hard_unknot_one_swap_search_alex_jones_volume.ipynb`
- `hard_unknot_one_swap_search_alex_jones_volume_u1_status.ipynb`
- `hard_unknots_gcs_chunk_downloader_only.ipynb`

Older notebook versions should go in `searches/notebooks/archive/` only when they document a materially different experiment. GitHub should not become a dump of every intermediate retry.

## Additional summaries and verification helpers

Place in the appropriate search directory:

- `hard_chunk_scan_range_summary_nonoverlap.csv`
- `target_unknown_intervals_all_1_a_gt_1.csv`
- `target_unknown_intervals_1_2_only.csv`
- `run_interval_u1a_minimal_one_swap_chunked.py`
- `unknotting_row_differences.xlsx`

## Do not commit

- the paper source or PDF;
- private email exports or chat transcripts;
- raw identifiable game replay data;
- cloud credentials;
- the complete third-party hard-unknot bucket unless redistribution is explicitly permitted.
