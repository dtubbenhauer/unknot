# Code and data for *Machine learning methods and unknotting numbers*

This repository contains the paper, exact certificate data, verification scripts,
figures, and exploratory search records for work by Anne Dranowski, Zhen Guo,
Yura Kabkov, and Daniel Tubbenhauer.

> **Corrected and completed repository, 18 July 2026.** This is a complete replacement for the
> earlier repository snapshot. The old signature-four, signature-six, and
> signature-eight zero-class Owens batches contained an orientation error and are
> intentionally absent. Do not merge the old `lower_bounds/owens_u2/` or
> `lower_bounds/owens_signature_sharp/` directories into this version.

The correction and its mathematical consequences are documented in
[`ERRATUM.md`](ERRATUM.md). A concise numerical summary is in
[`RESULTS.md`](RESULTS.md), and [`STATUS.md`](STATUS.md) maps every computational
claim in the paper to a repository path.

## Main certified results

Relative to the recorded KnotInfo snapshot, the lower-bound computations give
422 distinct improvements:

| source | distinct improvements | exact values | non-exact improvements |
|---|---:|---:|---:|
| finite-field Alexander module | 362 | 317 | 45 |
| Owens determinant/group conditions | 5 | 4 | 1 |
| Montesinos correction terms | 56 | 51 | 5 |
| overlap at `13a4877` | -1 | 0 | -1 |
| **total** | **422** | **372** | **50** |

There is also a diagrammatic result for the ten unresolved ten-crossing knots

```text
10_6, 10_11, 10_47, 10_51, 10_54,
10_61, 10_76, 10_77, 10_79, 10_100.
```

Every minimal diagram of each of these knots has diagram unknotting number
exactly three. The computation exhausts all 450 crossing pairs and supplies an
explicit three-change Wirtinger--Tietze unknot certificate for each knot.

This does **not** determine the ordinary unknotting number of these knots: their
KnotInfo intervals remain `[2,3]`, since a two-change route could occur in a
nonminimal diagram. The complete Owens comparison included here also records why
the five signature-eligible cases are not obstructed.

## Repository map

| path | contents |
|---|---|
| [`paper/`](paper/) | revised TeX source, all figures, and compiled PDF |
| [`code/`](code/) | exact scripts for the complete Alexander, Owens, and ten-crossing computations |
| [`lower_bounds/alexander_module/`](lower_bounds/alexander_module/) | the complete 5,121-row elementary-ideal scan, all 363 successful witnesses, the 362 genuinely new improvements, and the 13 additions beyond the restricted scan |
| [`lower_bounds/owens/`](lower_bounds/owens/) | five valid determinant/group certificates and full ten-crossing correction-term comparisons |
| [`lower_bounds/montesinos_u1/`](lower_bounds/montesinos_u1/) | 50 complete unknotting-number-one target certificates |
| [`lower_bounds/montesinos_signature_sharp/`](lower_bounds/montesinos_signature_sharp/) | seven higher signature-sharp Montesinos certificates |
| [`verification/ten_crossing_minimal_diagrams/`](verification/ten_crossing_minimal_diagrams/) | all 450 pair determinants and ten three-change unknot certificates |
| [`verification/11a14/`](verification/11a14/) | 17 minimal diagrams, 187 crossing changes, and invariant collision checks |
| [`data/`](data/) | input provenance and compact derived indexes |
| [`searches/`](searches/) | hard-unknot exploratory searches and `Unknot!` research-level data |
| [`figures/`](figures/) | standalone sources for the key-knot figures |

## Fast verification

The repository-level verifier uses only the Python standard library:

```bash
python3 verify_repository.py
```

It checks the complete Alexander index distribution and certificate counts, the full five-knot Owens
outcome, every ten-crossing pair and triple record, the Montesinos outputs, the
`11a14` outputs, and the presence of the revised paper.

For byte-level verification, run

```bash
sha256sum -c SHA256SUMS
```

Both checks are also run by the included GitHub Actions workflow.

## Reproducing the new computations

The complete third-party KnotInfo workbook is not redistributed. Its filename,
shape, and SHA-256 checksum are recorded in
[`data/workbook_provenance.json`](data/workbook_provenance.json). Place a matching
copy anywhere locally and set `WORKBOOK` to its path.

Install the computational dependencies with

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Rebuild the complete finite-field Alexander index. This exhausts all primes and
extension degrees through the elementary-ideal criterion; it is not a bounded
list of trial fields.

```bash
python3 code/complete_alexander_scan.py "$WORKBOOK" \
  --output build/complete_alexander_scan.json
python3 code/verify_complete_alexander_witnesses.py "$WORKBOOK" \
  --scan build/complete_alexander_scan.json \
  --output build/direct_rank_verification.json
```

The earlier restricted Alexander scan and the corrected Owens determinant/group
audit can be rebuilt with

```bash
python3 code/knotinfo_strengthening_scan.py "$WORKBOOK" \
  --tex paper/big_data_unknotting.tex \
  --output-dir build/lower_bounds
```

Run the complete Owens correction-term comparison on the five eligible
ten-crossing knots:

```bash
python3 code/full_owens_correction_terms.py "$WORKBOOK" \
  --knots 10_6 10_47 10_61 10_76 10_100 \
  --output build/full_owens_five_knots.json --quiet
```

Rebuild the minimal-diagram certificates:

```bash
python3 code/exhaust_two_changes_minimal_diagrams.py "$WORKBOOK" \
  --output build/two_change_determinants.json
python3 code/certify_three_changes_minimal_diagrams.py "$WORKBOOK" \
  --output build/three_change_unknot_certificates.json --quiet
```

Equivalent convenience targets are provided by the `Makefile`; for example,

```bash
make reproduce-new WORKBOOK=/absolute/path/to/knotinfo_data_complete.xls
```

The complete Alexander scan takes several minutes on a typical laptop. The
archived `complete_scan.json` contains every ideal test, so ordinary repository
verification does not rerun it.

The individual Montesinos and `11a14` directories contain their own rebuilding
instructions.

## Building the paper

The PDF is already included. To rebuild it on a full TeX Live installation:

```bash
make paper
```

## Exploratory data

The hard-unknot searches are retained for transparency, but negative search
results are not used as lower-bound proofs. Their status is stated explicitly in
[`searches/hard_unknots/README.md`](searches/hard_unknots/README.md).

## Uploading this replacement

This repository is designed to replace the old contents, not to be overlaid on
them. After emptying the old GitHub repository, upload every file and directory
from this package. In particular, keep `.github/workflows/verify.yml`, which runs
the structural and checksum checks on every push.

## Contact

Please report paper or data errors to `daniel.tubbenhauer@sydney.edu.au`.

## Citation

```bibtex
@misc{DranowskiGuoKabkovTubbenhauerUnknotData,
  author = {Dranowski, Anne and Guo, Zhen and Kabkov, Yura and Tubbenhauer, Daniel},
  title  = {Code and data for ``Machine learning methods and unknotting numbers''},
  year   = {2026},
  url    = {https://github.com/dtubbenhauer/unknot}
}
```

A machine-readable citation is provided in [`CITATION.cff`](CITATION.cff).

## License

The repository software is released under the [Unlicense](LICENSE). Third-party
data and software retain their respective licenses.
