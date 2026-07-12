# Code, data and Erratum for Machine learning methods and unknotting numbers

We collected the code, searches, verification files and figures relevant for the paper
*Machine learning methods and unknotting numbers* on this page. This is joint work
with Anne Dranowski, Zhen Guo and Yura Kabkov.

The paper itself is maintained separately and will be linked here once it is available.
The repository contains all computational files promised in the paper: the exact
lower-bound certificates, the complete minimal-diagram check for `11a14`, the
exploratory hard-unknot searches, and the files used for the research levels in
`Unknot!`.

An Erratum for the paper can be found at the bottom of this page and in
[`ERRATUM.md`](ERRATUM.md).

## Contact

If you find any errors in the paper, please email me:

`daniel.tubbenhauer@sydney.edu.au`

Same goes for errors related to this page. Also, let us know if there are any
questions about the code or the data.

## Files in this repository

The files are divided into exact lower-bound certificates, the `11a14`
verification, exploratory searches, and input data. The individual directories
contain short README files with more details and commands.

### Lower bounds from the Owens obstruction

The folder [`lower_bounds/owens_u2/`](lower_bounds/owens_u2/) contains the
signature-four calculation. It gives 245 certificates ruling out unknotting number
two: 237 exact values `u=3` and eight improvements from `[2,4]` to `[3,4]`.

The folder
[`lower_bounds/owens_signature_sharp/`](lower_bounds/owens_signature_sharp/)
contains the higher-signature version of the same calculation. It gives

1. 164 signature-six certificates, of which 152 prove `u=4` and twelve improve
   `[3,5]` to `[4,5]`;
2. 24 signature-eight certificates proving `u=5`.

All these calculations use exact arithmetic. The CSV files are the machine-readable
outputs; formatted XLSX copies are included for convenience.

### Montesinos correction-term obstructions

The folder [`lower_bounds/montesinos_u1/`](lower_bounds/montesinos_u1/) contains
the complete scan of the 50 parseable three-tangle Montesinos knots considered in
the paper. The correction-term test obstructs unknotting number one for 49 of them.
The remaining knot is `12n309`, whose determinant is one.

The subfolder `full_certificates/` contains one JSON certificate for each target,
including the plumbing matrix, all correction terms, all compatible affine maps,
and the exact reason each map fails.

The folder
[`lower_bounds/montesinos_signature_sharp/`](lower_bounds/montesinos_signature_sharp/)
contains the seven higher-signature Montesinos certificates: five proving `u=3`
and two proving `u=4`.

### The all-minimal-diagram check for `11a14`

The folder [`verification/11a14/`](verification/11a14/) contains the complete
verification used in the paper.

The code enumerates the 17 normalized minimal diagrams of `11a14` and checks every
single crossing change on every diagram. Thus there are `17 x 11 = 187` rows. The
outputs record the four invariant classes that occur and resolve all apparent
collisions with knots of unknotting number one using the Jones polynomial, the
Alexander polynomial and hyperbolic volume.

The earlier direct two-swap experiment is also retained, but it is kept separate
from the certificate used in the proof.

### Hard-unknot searches

The folder [`searches/hard_unknots/`](searches/hard_unknots/) contains the cleaned
scripts and final summaries from the larger exploratory searches. These include
one-crossing-change searches in slices of the public hard-unknot data and the
extended search around the 42-crossing example used in the paper.

A word of caution: these are searches for witnesses. Finding a short route gives an
upper bound, but failing to find one is not a lower-bound proof. We include the
negative searches for transparency and reproducibility, not as certificates.

### `Unknot!` research levels

The folder [`searches/game_levels/`](searches/game_levels/) contains PD codes and
reproducible PLink figures for the eight ten-crossing research levels

```text
10a6, 10a11, 10a51, 10a54, 10a61, 10a76, 10a77, 10a79
```

and for the connected-sum challenge `4_1#9_10`.

The first three playable research levels are Tortoise (`10a54`), Scream (`10a61`)
and Jellyfish (`10a76`).

### Input data and figures

The folder [`data/`](data/) records the KnotInfo snapshot used in the computations,
the compact invariant indexes needed for the `11a14` check, and the correction to
the `12n873` input discussed in the paper. The complete third-party KnotInfo table
is not redistributed, but its version and checksum are recorded and the relevant
indexes can be rebuilt deterministically.

The folder [`figures/key_knots/`](figures/key_knots/) contains the PLink sources and
PNG files for the main knot diagrams appearing in the paper.

## Running the code

The common Python dependencies can be installed with

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Most scripts use the `database-knotinfo` package. The diagram and search code also
uses SnapPy and Spherogram.

To check that all theorem-critical files are present with the expected sizes, run

```bash
python3 verify_repository.py
```

To check the files against the recorded checksums, run

```bash
sha256sum -c SHA256SUMS
```

The same structural check is run automatically by GitHub Actions. The precise
commands for rebuilding individual tables are given in the README files in the
corresponding directories.

A compact map from the claims in the paper to the relevant files is available in
[`STATUS.md`](STATUS.md).

## Citation

```bibtex
@misc{DranowskiGuoKabkovTubbenhauerUnknotData,
  author = {Dranowski, Anne and Guo, Zhen and Kabkov, Yura and Tubbenhauer, Daniel},
  title  = {Code, data and more for ``Machine learning methods and unknotting numbers''},
  year   = {2026},
  url    = {https://github.com/dtubbenhauer/unknot}
}
```

A machine-readable citation is provided in [`CITATION.cff`](CITATION.cff).

## Erratum

No errors in the paper are known at present.

The repository records one correction to the input data rather than to the paper:
KnotInfo lists `12n873` with interval `[1,3]` and algebraic unknotting number two,
so the interval used in the paper is `[2,3]`. See
[`data/12n873_correction.csv`](data/12n873_correction.csv).
