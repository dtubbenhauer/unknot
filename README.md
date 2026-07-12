# Machine learning methods and unknotting numbers

[![Verify repository](https://github.com/dtubbenhauer/unknot/actions/workflows/verify.yml/badge.svg)](https://github.com/dtubbenhauer/unknot/actions/workflows/verify.yml)

Code, exact certificates, search outputs and figures accompanying joint work of Anne Dranowski, Zhen Guo, Yura Kabkov and Daniel Tubbenhauer.

The paper itself is maintained separately. This repository contains the computational material needed to reproduce or inspect its machine-assisted claims.

## What is here

The main lower-bound results are represented by **489 row-level certificates**:

| family | conclusion tested | certificates | location |
|---|---:|---:|---|
| alternating, signature four | rule out `u = 2` | 245 | `lower_bounds/owens_u2/` |
| alternating, signature six | rule out `u = 3` | 164 | `lower_bounds/owens_signature_sharp/signature6_*` |
| alternating, signature eight | rule out `u = 4` | 24 | `lower_bounds/owens_signature_sharp/signature8_*` |
| nonalternating Montesinos | rule out `u = 1` | 49 of 50 targets | `lower_bounds/montesinos_u1/` |
| higher-signature Montesinos | rule out the lower endpoint | 7 | `lower_bounds/montesinos_signature_sharp/` |

The repository also contains:

- the complete `11a14` minimal-diagram verification: 17 normalized minimal PDs, all 187 single crossing changes, four invariant classes and explicit resolution of every apparent unknotting-number-one collision;
- a correction record for `12n873`;
- a versioned KnotInfo snapshot record and deterministic builders for the compact identification tables used by the computations;
- cleaned scripts and final summaries for the exploratory hard-unknot searches;
- PD codes and reproducible PLink figures for the `Unknot!` research levels and the connected-sum challenge;
- `SHA256SUMS`, a repository-wide verifier and a GitHub Actions workflow.

See [`STATUS.md`](STATUS.md) for the paper-to-file map.

## Quick verification

Create an environment and install the common dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Check the included outputs and their expected row counts:

```bash
python3 verify_repository.py
```

Check file integrity:

```bash
sha256sum -c SHA256SUMS
```

The same structural check runs in GitHub Actions. The exact certificate generators can be rerun separately as described in the README files inside their directories.

## Directory guide

### `lower_bounds/owens_u2/`

The signature-four Owens computation. It includes the generating script, a compact 245-row result table, the full row-level certificate table, a formatted workbook and a summary.

The 245 obstructions give 237 exact values `u=3` and eight improved intervals.

### `lower_bounds/owens_signature_sharp/`

A generalized exact zero-class implementation together with compatibility wrappers and complete outputs for:

- 164 signature-six targets;
- 24 signature-eight targets.

The scripts validate the signature conventions against the installed KnotInfo snapshot before exporting the selected rows.

### `lower_bounds/montesinos_u1/`

The complete three-tangle Montesinos correction-term scan. The compact table has 50 targets and 49 obstructions. The `full_certificates/` directory contains one JSON certificate per target, including:

- the normalized plumbing matrix;
- the correction terms;
- all linking-form-compatible affine identifications in both orientations;
- an exact recorded failure for each rejected identification.

The determinant-one target `12n309` is retained as the unique non-obstructed row.

### `lower_bounds/montesinos_signature_sharp/`

The seven higher-signature Montesinos certificates: five knots whose lower endpoint two is excluded and two knots whose lower endpoint three is excluded.

### `verification/11a14/`

A reproducible Tait-graph/Whitney-flip enumeration of the 17 normalized minimal diagrams of `11a14`, followed by all 187 single crossing changes. The outputs record the four resulting invariant classes and the Jones--Alexander--volume checks excluding the three apparent exact-`u=1` database collisions.

The directory also retains the direct two-crossing Jones scan and compatibility filenames used in the earlier computation.

### `data/`

Provenance and compact identification data. The complete third-party KnotInfo CSV is not redistributed. Instead, `knotinfo_snapshot.json` records the package version and checksum, while the builder scripts reconstruct the relevant indexes from the installed snapshot.

### `searches/hard_unknots/`

Exploratory search code and final summaries. These searches locate possible witnesses and useful diagrams; a failed exploratory search is not treated as a lower-bound proof.

### `searches/game_levels/`

PD codes and PLink drawings for the eight ten-crossing research levels

```text
10a6, 10a11, 10a51, 10a54, 10a61, 10a76, 10a77, 10a79
```

and the connected-sum challenge `4_1#9_10`. The three first playable levels are Tortoise (`10a54`), Scream (`10a61`) and Jellyfish (`10a76`).

## Conventions and safeguards

- Knot names use the compact `10a54`, `11n3` notation in prose.
- Each crossing-change script records its PD crossing-switch convention.
- Jones-only collisions are not promoted silently to knot identifications.
- Missing hyperbolic volume is not counted as a successful volume match.
- Numerical volume is used only as an identification filter, never as an exact lower-bound certificate.
- Search failure is not a lower bound.
- A game score is not a mathematical witness unless its replay can be reconstructed and checked.

## Citation

```bibtex
@misc{DranowskiGuoKabkovTubbenhauerUnknotData,
  author = {Dranowski, Anne and Guo, Zhen and Kabkov, Yura and Tubbenhauer, Daniel},
  title  = {Code, data and more for ``Machine learning methods and unknotting numbers''},
  year   = {2026},
  url    = {https://github.com/dtubbenhauer/unknot}
}
```

A machine-readable citation is provided in `CITATION.cff`.

## Errata and contact

Corrections are recorded in [`ERRATUM.md`](ERRATUM.md). Please report problems to `daniel.tubbenhauer@sydney.edu.au` or open a GitHub issue.
