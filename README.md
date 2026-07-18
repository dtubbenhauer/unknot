# Code, data and Erratum for *Machine learning methods and unknotting numbers*

This repository contains supplementary computational material for joint work
with Anne Dranowski, Zhen Guo and Yura Kabkov, titled

> *Machine learning methods and unknotting numbers*

The paper itself is not included in this repository.

The goal is transparency: the repository provides the code, exact certificate
data, verification files, exploratory searches and figures used in the work.
An Erratum can be found at the bottom of this page and in
[`ERRATUM.md`](ERRATUM.md).

## Contact

If you find any errors in the paper **please email me**:

[daniel.tubbenhauer@sydney.edu.au](mailto:daniel.tubbenhauer@sydney.edu.au?subject=[GitHub]%20unknotting-numbers)

Same goes for any errors related to this page. Please also get in touch if there
are questions about the code or the data.

## Main results

Relative to the recorded KnotInfo snapshot, the certified lower-bound
computations give 422 distinct improvements: 372 exact unknotting numbers and
50 further lower-bound improvements.

| method | distinct improvements | exact values | further lower-bound improvements |
|---|---:|---:|---:|
| finite-field Alexander module | 362 | 317 | 45 |
| Owens determinant and discriminant-group conditions | 5 | 4 | 1 |
| Montesinos correction terms | 56 | 51 | 5 |
| overlap at `13a4877` | -1 | 0 | -1 |
| **total** | **422** | **372** | **50** |

The repository also contains a complete minimal-diagram calculation for the ten
ten-crossing knots

```text
10_6, 10_11, 10_47, 10_51, 10_54,
10_61, 10_76, 10_77, 10_79, 10_100.
```

Every minimal diagram of each of these knots has diagram unknotting number
three. This does **not** determine the ordinary unknotting number: a two-change
route could occur in a nonminimal diagram, so the ordinary KnotInfo intervals
remain `[2,3]`.

## Main files and directories

### Finite-field Alexander-module certificates

The folder
[`lower_bounds/alexander_module/`](lower_bounds/alexander_module/) contains the
complete calculation. For a Seifert matrix `V`, a finite field `F` and a
nonzero element `alpha` in `F`, the certificate is

$$
\text{nullity}_{F}(\alpha V-V^T)\leq e(K)\leq u(K),
$$

where `e(K)` is the Nakanishi index.

The scan checks all 5,121 database rows having a gap in the recorded unknotting
interval. It produces 363 successful certificates; one is the already implied
`12n873` consistency case, leaving 362 genuinely new improvements. These are
303 exact values `u=2`, fourteen exact values `u=3`, and 45 further lower-bound
improvements.

The archived files include the complete elementary-ideal scan, the explicit
finite-field witnesses, the 362 new certificates, and the thirteen certificates
missed by the restricted field scan. The latter use `F_16`, `F_49` or `F_81`.
The examples `13n1457` and `13n2414` already show why extension fields matter:
specialization over `F_4` gives nullity two and three, respectively, whereas
the only nonzero specialization over `F_2` has nullity zero.

The file
[`lower_bounds/alexander_module/COMPLETENESS.md`](lower_bounds/alexander_module/COMPLETENESS.md)
explains why the finite-field calculation is exhaustive, bounds the necessary
extension degree, discusses exceptional primes, and records

```text
beta(K) <= e(K) <= beta(K) + 1.
```

The possible gap is genuine for `9_38`.

### Owens obstruction

The folder [`lower_bounds/owens/`](lower_bounds/owens/) contains the corrected
determinant and discriminant-group calculations. Five conclusions survive the
necessary conditions: four exact values `u=3` and one improvement from `[2,5]`
to `[3,5]`.

It also contains the full correction-term comparison for the five eligible
ten-crossing knots. Every one of these tests has a surviving candidate, so this
calculation does not prove ordinary unknotting number three for any of them.

### Montesinos correction-term obstructions

The folder [`lower_bounds/montesinos_u1/`](lower_bounds/montesinos_u1/)
contains the complete unknotting-number-one target calculation, including one
JSON certificate for each target. The folder
[`lower_bounds/montesinos_signature_sharp/`](lower_bounds/montesinos_signature_sharp/)
contains the higher-signature calculation.

Together these give 56 improvements: 44 exact values `u=2`, five exact values
`u=3`, two exact values `u=4`, and five improvements from `[1,3]` to `[2,3]`.

### Ten-crossing minimal diagrams

The folder
[`verification/ten_crossing_minimal_diagrams/`](verification/ten_crossing_minimal_diagrams/)
contains all 450 two-change determinant tests and an explicit three-change
unknot certificate for each of the ten knots. The three-change certificates are
checked by Wirtinger presentations and Tietze eliminations.

### The all-minimal-diagram check for `11a14`

The folder [`verification/11a14/`](verification/11a14/) contains the 17
normalized minimal diagrams of `11a14` and all 187 single crossing changes.
The outputs record the four invariant classes that occur and resolve the
apparent collisions with knots of unknotting number one using the Jones
polynomial, the Alexander polynomial and hyperbolic volume.

### Exploratory searches and `Unknot!`

The folder [`searches/hard_unknots/`](searches/hard_unknots/) contains the
cleaned scripts and final summaries from the hard-unknot searches. These are
searches for witnesses: finding a short route gives an upper bound, but failure
to find one is not a lower-bound proof. The negative searches are included for
transparency, not as mathematical certificates.

The folder [`searches/game_levels/`](searches/game_levels/) contains the
research-level data and reproducible PLink figures used for `Unknot!`.

### Input data and figures

The folder [`data/`](data/) records the KnotInfo snapshot, the provenance of the
workbook used in the computations, compact derived indexes, and the `12n873`
input correction. The complete third-party KnotInfo workbook is not
redistributed.

The folder [`figures/key_knots/`](figures/key_knots/) contains PLink sources and
PNG files for the principal knot diagrams.

The concise numerical summary is [`RESULTS.md`](RESULTS.md), while
[`STATUS.md`](STATUS.md) maps the computational claims to their archived files.

## Requirements

The common Python dependencies can be installed with

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

The scripts use the `database-knotinfo` package. Diagram calculations also use
SnapPy and Spherogram. Exact integer, polynomial and finite-field arithmetic is
used for the theorem-critical calculations.

## Reproducing the main calculations

The complete KnotInfo workbook is not included. Its filename, dimensions and
SHA-256 checksum are recorded in
[`data/workbook_provenance.json`](data/workbook_provenance.json). After placing
a matching copy on your computer, set `WORKBOOK` to its path.

To rebuild the complete finite-field Alexander-module scan and verify every
positive witness directly in the original Seifert matrix, run

```bash
python3 code/complete_alexander_scan.py "$WORKBOOK" \
  --output build/complete_alexander_scan.json
python3 code/verify_complete_alexander_witnesses.py "$WORKBOOK" \
  --scan build/complete_alexander_scan.json \
  --output build/direct_rank_verification.json
```

To repeat the full Owens comparison for the five eligible ten-crossing knots,
run

```bash
python3 code/full_owens_correction_terms.py "$WORKBOOK" \
  --knots 10_6 10_47 10_61 10_76 10_100 \
  --output build/full_owens_five_knots.json --quiet
```

To rebuild the minimal-diagram calculations, run

```bash
python3 code/exhaust_two_changes_minimal_diagrams.py "$WORKBOOK" \
  --output build/two_change_determinants.json
python3 code/certify_three_changes_minimal_diagrams.py "$WORKBOOK" \
  --output build/three_change_unknot_certificates.json --quiet
```

The individual certificate directories contain further rebuilding and
verification instructions. The archived outputs can be inspected without the
third-party workbook.

## Repository contents

The principal contents are

```text
README.md
ERRATUM.md
RESULTS.md
STATUS.md
CITATION.cff
LICENSE
requirements.txt
code/
data/
figures/
lower_bounds/
searches/
verification/
```

The paper and its source files are not part of this repository.

## Citation

```bibtex
@misc{DranowskiGuoKabkovTubbenhauerUnknotData,
  author = {Dranowski, A. and Guo, Z. and Kabkov, Y. and Tubbenhauer, D.},
  title  = {Code and more for the paper ``Machine learning methods and unknotting numbers''},
  year   = {2026},
  url    = {https://github.com/dtubbenhauer/unknot}
}
```

A machine-readable citation is provided in [`CITATION.cff`](CITATION.cff).

## Erratum

The zero-class part of the Owens obstruction in an earlier draft of the paper
used the wrong orientation. For the correctly oriented positive Goeritz lattice
of an alternating knot,

$$
m_G(0)=-\frac{\sigma(K)}{4}.
$$

Consequently, the zero-class comparison is an equality in the
signature-sharp setting and does not give the claimed obstruction. The corrected
scan checks all 653 signature-four, 164 signature-six and 24 signature-eight
targets and finds no zero-class obstruction. The five valid conclusions listed
above follow instead from a determinant obstruction and four complete
discriminant-group obstructions. Full details are in
[`ERRATUM.md`](ERRATUM.md).

The repository also records an input-data correction for `12n873`. The source
snapshot lists the interval `[1,3]`, while the algebraic unknotting number is
two; the corrected interval used in the computations is therefore `[2,3]`.
See [`data/12n873_correction.csv`](data/12n873_correction.csv).
