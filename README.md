# Machine learning methods and unknotting numbers

This repository contains supplementary computational material for joint work with Anne Dranowski, Zhen Guo, Yura Kabkov and Daniel Tubbenhauer, titled

> Machine learning methods and unknotting numbers

The arXiv version will be available at

> arXiv:TBA

The paper itself is deliberately **not** stored in this repository. The repository is for code, search outputs, exact certificate data and errata.

The repository contains four main groups of files:

1. `lower_bounds/owens_u2/`, the machine-readable output of the signature-four Owens zero-class scan;
2. `lower_bounds/montesinos_u1/`, the scripts and exact output of the Montesinos correction-term scan obstructing unknotting number one;
3. `searches/hard_unknots/`, summaries of the exploratory hard-unknot and one-swap searches;
4. `searches/game_levels/`, the PD codes and PLink drawings used for the first `Unknot!` research levels and the connected-sum challenge.

The goal is transparency. Successful lower-bound claims are accompanied by exact finite certificate data. Exploratory searches are kept separate and labelled as such: they locate possible witnesses or useful diagrams, but failed searches are not proofs.

## Contact

If you find any errors in the paper, code or data, please email

> daniel.tubbenhauer@sydney.edu.au

## Main files

### `lower_bounds/owens_u2/owens_u2_sharp_signature_kills.csv`

This is the row-level output for the alternating signature-four batch. Each row records the knot, its input interval, determinant, signature, the zero-class value of the positive Goeritz form and the finite list of candidate Owens matrices.

The file contains the 245 certified successes used in the paper. Of these, 237 knots have exact unknotting number three and eight have their lower bound improved from two to three.

### `lower_bounds/montesinos_u1/montesinos_d_obstruction_scan.py`

This is the batch driver for the nonalternating Montesinos scan. It normalizes the rational tangles, constructs a definite star-shaped plumbing, checks the determinant, computes correction terms and tests every affine identification compatible with the linking form in both orientations.

### `lower_bounds/montesinos_u1/montesinos_d_obstruction_scan_u1_targets_up_to_13.csv`

This is the complete row-level output for the 50 parseable three-tangle Montesinos targets in the stated range. It records the fractions, plumbing weights and arms, determinant checks, number of maps tested and the outcome of the basic and stronger correction-term tests.

The basic test obstructs unknotting number one for 49 knots.

### `searches/hard_unknots/*.json`

These files summarize several exploratory searches performed on hard-unknot diagrams. They record the precise search range, number of swaps tested, identification policy, errors and limitations.

They are included because negative and near-miss searches matter for reproducibility. They are not presented as exhaustive classifications unless the file explicitly says so.

### `searches/game_levels/research_levels.json`

This file stores the PD codes for the eight ten-crossing research levels

    10a6, 10a11, 10a51, 10a54, 10a61, 10a76, 10a77, 10a79,

together with the connected-sum challenge `4_1#9_10`. The corrected panel uses `10a54`, not `10a47`.

### `pending_import/IMPORT_MANIFEST.md`

This is a temporary assembly checklist. It records the final notebooks and certificate files created in earlier chats that still need to be copied from the File Library into the repository archive. It should be deleted once those files have been imported.

## Requirements

The exact lower-bound scripts use Python. The current collection uses some combination of

1. the Python standard library;
2. `sympy`, for exact rational and integer arithmetic;
3. `pandas` and `openpyxl`, for the identification tables;
4. SnapPy and Spherogram, for knot diagrams, hyperbolic data and identification;
5. `tqdm`, for progress reporting.

Install the common dependencies with

    python3 -m pip install -r requirements.txt

The certificate computations should use exact arithmetic whenever possible. Hyperbolic volume is used only as an identification filter or collision breaker, not as an exact lower-bound certificate.

## Reproducing the included lower-bound scans

For the Montesinos scan, run

    python3 lower_bounds/montesinos_u1/montesinos_d_obstruction_scan.py INPUT.csv

The exact input schema and command-line options are documented in the script.

The signature-four Owens table currently records the exact output used in the paper. The final public repository should also contain the generating script and the higher-signature scan files listed in `pending_import/IMPORT_MANIFEST.md`.

## Important conventions

The repository uses the following conventions.

- Knot names are normalized to the `10a54`, `11n3` style in prose and to stable ASCII identifiers in data files.
- A crossing swap in PD notation uses the convention documented by the corresponding notebook or script; every search file must state its convention.
- A database identification is promoted only under the invariant policy recorded by that run. Jones-only matches are not silently treated as exact identifications.
- Missing volume is not a successful volume match.
- Search failure is not a lower bound.
- A game score is not a mathematical witness unless the replay can be reconstructed and checked.

## Relation to the paper

The computations support the machine-checkable parts of

> Machine learning methods and unknotting numbers

joint with Anne Dranowski, Zhen Guo and Yura Kabkov.

The paper states the obstruction arguments and mathematical conclusions. This repository records the finite computations, candidate searches and verification data. The manuscript source and compiled PDF are maintained separately on Overleaf and arXiv.

The suggested citation is

    @misc{DranowskiGuoKabkovTubbenhauerUnknottingData,
      author = {Dranowski, A. and Guo, Z. and Kabkov, Y. and Tubbenhauer, D.},
      title = {Code, data and more for ``Machine learning methods and unknotting numbers''},
      year = {2026},
      url = {https://github.com/dtubbenhauer/unknotting-number-data}
    }

## Repository contents

Current intended contents:

    README.md
    LICENSE
    requirements.txt
    lower_bounds/
    searches/

The temporary directory `pending_import/` is part of this draft archive only and should disappear before the public release.

## Erratum

Empty so far.
